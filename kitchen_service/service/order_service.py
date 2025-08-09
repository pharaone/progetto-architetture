# --- CODICE FINALE E COMPLETO: services/order_orchestration_service.py ---
import uuid
from typing import Optional

# Assumiamo che OrderRequest sia definito in model.order
from model.order import Order
from model.messaging_models import OrderRequest
from model.status import StatusEnum
from repository.order_repository import OrderRepository
from producers.producers import EventProducer
from .kitchen_service import KitchenService
from .menu_service import MenuService
from .status_service import OrderStatusService

class OrderOrchestrationService:
    """
    Servizio principale che orchestra gli altri servizi per gestire il ciclo di vita di un ordine.
    È il cervello di questo microservizio.
    """
    def __init__(self, 
                 order_repo: OrderRepository,
                 kitchen_service: KitchenService, 
                 menu_service: MenuService, 
                 status_service: OrderStatusService,
                 event_producer: EventProducer):
        self._order_repo = order_repo
        self._kitchen_service = kitchen_service
        self._menu_service = menu_service
        self._status_service = status_service
        self._event_producer = event_producer

    async def check_availability_and_propose(self, request: OrderRequest):
        """
        Logica della "Candidatura" (Fase 1). Controlla se la cucina può gestire la richiesta
        e pubblica la sua risposta.
        """
        kitchen_id = request.kitchen_id
        
        # 1. Controlla se la cucina è operativa
        kitchen = await self._kitchen_service.get_by_id(kitchen_id)
        if not kitchen or not kitchen.is_operational:
            await self._event_producer.publish_acceptance_response(kitchen_id, request.order_id, can_handle=False)
            return

        # 2. Controlla se il piatto è disponibile
        menu_item = await self._menu_service.get_menu_item(kitchen_id, request.dish_id)
        if not menu_item or menu_item.available_quantity <= 0:
            await self._event_producer.publish_acceptance_response(kitchen_id, request.order_id, can_handle=False)
            return
        
        # 3. Se entrambi i controlli passano, la cucina si candida!
        await self._event_producer.publish_acceptance_response(kitchen_id, request.order_id, can_handle=True)

    async def handle_newly_assigned_order(self, order: Order) -> bool:
        """
        Logica dell'"Assegnazione" (Fase 2). Chiamata quando il microservizio riceve
        un nuovo ordine già assegnato a una cucina.
        """
        if not order.kitchen_id:
            return False
            
        # 1. Decrementa la quantità del piatto dal menù/inventario.
        quantity_updated = await self._menu_service.decrement_item_quantity(order.kitchen_id, order.dish_id)
        if not quantity_updated:
            return False

        # 2. Incrementa il carico di lavoro della cucina.
        load_updated = await self._kitchen_service.increment_load(order.kitchen_id)
        if not load_updated:
            # AZIONE CORRETTIVA (Rollback): Ripristina la quantità del piatto.
            await self._menu_service.increment_item_quantity(order.kitchen_id, order.dish_id)
            return False

        # 3. Se tutto va bene, salva l'ordine e crea il suo stato iniziale.
        await self._order_repo.save(order)
        await self._status_service.create_initial_status(order)
        
        return True

    async def handle_order_status_update(self, order_id: uuid.UUID, kitchen_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """
        Logica del "Monitoraggio" (Fase 3). Gestisce le conseguenze di un cambio di stato.
        """
        status_updated = await self._status_service.update_status(order_id, new_status)
        if not status_updated:
            return False

        # Logica di business: se l'ordine è pronto, decrementa il carico della cucina.
        if new_status == StatusEnum.READY_FOR_PICKUP:
            await self._kitchen_service.decrement_load(kitchen_id)
        
        # Logica di business: se l'ordine viene annullato, ripristina le risorse.
        elif new_status == StatusEnum.CANCELLED:
            order = await self._order_repo.get_by_id(order_id)
            if order:
                await self._kitchen_service.decrement_load(order.kitchen_id)
                await self._menu_service.increment_item_quantity(order.kitchen_id, order.dish_id)

        # Notifica il cambio di stato
        updated_status = await self._status_service.get_by_id(order_id)
        if updated_status:
            await self._event_producer.publish_status_update(updated_status)

        return True
