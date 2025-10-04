from aiokafka import AIOKafkaConsumer # SPOSTATO: Importato qui per buona pratica
import uuid
import asyncio
from typing import Optional
from settings import settings # Importa le settings per accedere ai broker Kafka

from repository.kitchen_repository import KitchenAvailabilityRepository
from repository.order_status_repository import OrderStatusRepository
from model.kitchen import KitchenAvailability
from model.messaging_models import OrderAssignment, OrderRequest
from service.menu_service import MenuService
from producers.producers import EventProducer
from service.status_service import OrderStatusService
from model.status import StatusEnum  # Assicurati che il percorso sia corretto

class KitchenService:
    """
    Contiene la logica di business relativa alla disponibilità e al carico delle cucine.
    Tutte le operazioni sono asincrone per evitare di bloccare l'event loop.
    """
    def __init__(self, kitchen_repo: KitchenAvailabilityRepository, menu_service: MenuService, producer: EventProducer, status_service: OrderStatusService):
        self._kitchen_repo = kitchen_repo
        self._menu_service = menu_service
        self._producers = producer
        self._status_service = status_service


    async def get_by_id(self) -> Optional[KitchenAvailability]:
        """Recupera una cucina in modo non bloccante."""
        return await asyncio.to_thread(self._kitchen_repo.get_by_id)

    async def increment_load(self) -> bool:
        """
        Incrementa il carico di una cucina in modo atomico e non bloccante.
        """
        kitchen = await self.get_by_id()
        if not kitchen or not kitchen.is_operational:
            return False
        
        new_load = kitchen.current_load + 1
        new_status = False if new_load >= kitchen.max_load else kitchen.is_operational

        return await asyncio.to_thread(
            self._kitchen_repo.update_fields,
            current_load=new_load,
            is_operational=new_status
        )

    async def decrement_load(self) -> bool:
        """
        Decrementa il carico di una cucina in modo atomico e non bloccante.
        """
        kitchen = await self.get_by_id()
        if not kitchen or kitchen.current_load <= 0:
            return False

        new_load = kitchen.current_load - 1
        new_status = True if new_load < kitchen.max_load else kitchen.is_operational
            
        return await asyncio.to_thread(
            self._kitchen_repo.update_fields,
            current_load=new_load,
            is_operational=new_status
        )

    async def set_operational_status(self, status: bool) -> bool:
        """
        Metodo asincrono per forzare lo stato operativo di una cucina.
        """
        return await asyncio.to_thread(self._kitchen_repo.update_fields, is_operational=status)
    
    async def handle_availability_request(self, request: OrderRequest) -> None:
        """
        Controlla se la cucina singola è operativa, non satura e se il piatto richiesto è disponibile,
        e pubblica la risposta di candidatura.
        """
        # Recupera la cucina singola tramite il suo ID
        kitchen = await asyncio.to_thread(self._kitchen_repo.get_by_id)

        print(f"DEBUG ETCD: Dati letti per la cucina: {kitchen}")

        # Controlla se è operativa e non satura
        if not kitchen or not kitchen.is_operational or kitchen.current_load >= kitchen.max_load:
            print(f"⚠️ Cucina non disponibile per ordine {request.order_id}")
            await self._producers.publish_acceptance_response(
                kitchen_id=self._kitchen_repo.kitchen_id,
                order_id=request.order_id,
                can_handle=False
            )
            return

        # Controlla la disponibilità del piatto richiesto
        dish_available = await self._menu_service.is_dish_available(request.dish_id)
        if dish_available <= 0:
            print(f"⚠️ Piatto {request.dish_id} non disponibile per ordine {request.order_id}")
            await self._producers.publish_acceptance_response(
                kitchen_id=self._kitchen_repo.kitchen_id,
                order_id=request.order_id,
                can_handle=False
            )
            return

        # Altrimenti la cucina può gestire l'ordine
        print(f"✅ Cucina disponibile per ordine {request.order_id}")
        await self._producers.publish_acceptance_response(
            kitchen_id=self._kitchen_repo.kitchen_id,
            order_id=request.order_id,
            can_handle=True
        )

        
    async def handle_order_assignment(self, order: OrderAssignment) -> bool:
        """
        Gestisce l'assegnazione di un ordine:
        - incrementa il carico della cucina
        - decrementa la scorta del piatto
        """
        print(f"Ricevuta assegnazione ordine {order.order_id} per piatto {order.dish_id}.")
        load_ok = await self.increment_load()
        if not load_ok:
            print(f"Impossibile incrementare il carico per ordine {order.order_id}.")
            return False

        # ASSUNZIONE: commit_order_dish è il metodo che decrementa Redis (MenuService)
        dish_ok = await self._menu_service.commit_order_dish(order.dish_id)
        if not dish_ok:
            print(f"Errore: Piatto {order.dish_id} non disponibile o errore Redis. Ripristino carico cucina.")
            await self.decrement_load()
            return False
        
        print(f"Ordine {order.order_id} elaborato con successo. Scorta decrementata, carico incrementato.")
        print(f"📢 Innesco l'aggiornamento di stato per l'ordine {order.order_id} a 'PREPARING'...")
        await self._status_service.update_status(order.order_id, StatusEnum.PREPARING)
        return True
    

