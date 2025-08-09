# cartella: services/order_status_service.py

import uuid
import asyncio # <-- Importa la libreria asyncio
from typing import Optional

# Importa i tuoi modelli e il repository
from model.order import Order
from model.status import OrderStatus, StatusEnum
from repository.order_status_repository import OrderStatusRepository

class OrderStatusService:
    """
    Servizio ASINCRONO specializzato nella gestione dello stato degli ordini.
    Usa asyncio.to_thread per chiamare il repository sincrono in modo non bloccante.
    """
    def __init__(self, status_repo: OrderStatusRepository):
        self._status_repo = status_repo

    async def create_initial_status(self, order: Order) -> Optional[OrderStatus]:
        """Crea il record di stato iniziale quando un ordine viene assegnato."""
        if not order.kitchen_id:
            return None
            
        status = OrderStatus(
            order_id=order.order_id,
            kitchen_id=order.kitchen_id,
            status=StatusEnum.RECEIVED
        )
        
        # Eseguiamo la chiamata bloccante 'save' in un thread separato
        await asyncio.to_thread(self._status_repo.save, status)
        
        print(f"INFO (StatusService): Stato iniziale creato per l'ordine {order.order_id}")
        return status

    async def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """Aggiorna lo stato di un ordine esistente in modo sicuro e non bloccante."""
        print(f"INFO (StatusService): Tentativo di aggiornare lo stato dell'ordine {order_id} a '{new_status.value}'...")
        
        # Eseguiamo la chiamata bloccante 'update_status' del repository in un thread separato.
        # Questo libera l'event loop per gestire altre operazioni.
        success = await asyncio.to_thread(self._status_repo.update_status, order_id, new_status)
        
        if success:
            print(f"INFO (StatusService): Stato per l'ordine {order_id} aggiornato con successo.")
        else:
            print(f"ERROR (StatusService): Fallito l'aggiornamento dello stato per l'ordine {order_id}.")
            
        return success