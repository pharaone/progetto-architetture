# --- CODICE ASINCRONO: services/order_orchestration_service.py ---
import uuid
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
    Ora non richiede più kitchen_id dal clients.
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
        Fase 1: il clients invia solo dish_id e order_id.
        Itera tutte le cucine operative e pubblica le candidature.
        """
        kitchens = await self._kitchen_service.get_all_operational()
        for kitchen in kitchens:
            menu_item = await self._menu_service.get_menu_item(kitchen.kitchen_id, request.dish_id)
            can_handle = menu_item is not None and menu_item.available_quantity > 0
            await self._event_producer.publish_acceptance_response(
                kitchen.kitchen_id,
                request.order_id,
                can_handle
            )

    async def handle_newly_assigned_order(self, order: Order) -> bool:
        """
        Fase 2: riceve un ordine già assegnato a una cucina.
        Nessun cambiamento, perché order.kitchen_id è interno e valido.
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
            # Rollback
            await self._menu_service.increment_item_quantity(order.kitchen_id, order.dish_id)
            return False

        # 3. Salva ordine e stato iniziale
        await self._order_repo.save(order)
        await self._status_service.create_initial_status(order)
        
        return True

    async def handle_order_status_update(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """
        Fase 3: riceve solo order_id e nuovo status.
        Recupera la cucina dall'ordine salvato.
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            return False
        kitchen_id = order.kitchen_id

        status_updated = await self._status_service.update_status(order_id, new_status)
        if not status_updated:
            return False

        # Logica di business
        if new_status == StatusEnum.READY_FOR_PICKUP:
            await self._kitchen_service.decrement_load(kitchen_id)
        elif new_status == StatusEnum.CANCELLED:
            await self._kitchen_service.decrement_load(kitchen_id)
            await self._menu_service.increment_item_quantity(kitchen_id, order.dish_id)

        # Notifica lo stato aggiornato
        updated_status = await self._status_service.get_by_id(order_id)
        if updated_status:
            await self._event_producer.publish_status_update(updated_status)

        return True
