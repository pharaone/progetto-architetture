# cartella: services/order_status_service.py

import uuid
import asyncio
from typing import Optional
from producers.producers import EventProducer
# Importa i tuoi modelli e il repository
from model.status import OrderStatus, StatusEnum
from repository.order_status_repository import OrderStatusRepository
from repository.kitchen_repository import KitchenAvailabilityRepository

class OrderStatusService:
    """
    Servizio ASINCRONO specializzato nella gestione dello stato degli ordini.
    Usa asyncio.to_thread per chiamare il repository sincrono in modo non bloccante.
    """
    def __init__(self, status_repo: OrderStatusRepository, producer: EventProducer, kitchen_repo: KitchenAvailabilityRepository):
        self._status_repo = status_repo
        self._producer = producer
        self._kitchen_repository = kitchen_repo


    async def get_by_id(self, order_id: uuid.UUID) -> Optional[OrderStatus]:
        """
        Recupera lo stato di un ordine tramite il suo ID in modo non bloccante.
        """
        # Eseguiamo la chiamata bloccante del repository in un thread separato.
        status = await asyncio.to_thread(self._status_repo.get_by_id, order_id)
        
        if not status:
            print(f"INFO (StatusService): Nessuno stato trovato per l'ordine {order_id}.")
        
        return status
    
    async def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """
        Chiama il repository per aggiornare lo stato e, se l'aggiornamento avviene,
        pubblica la notifica su Kafka.
        """
        print(f"SERVICE: Tentativo di aggiornare l'ordine {order_id} a '{new_status.value}'...")
        
        # Prima controlliamo se l'ordine esiste per distinguere tra "ordine non trovato" e "stato già uguale"
        current_status = await asyncio.to_thread(
            self._status_repo.get_by_id, order_id
        )
        
        if current_status is None:
            print(f"SERVICE: Ordine {order_id} non trovato nel database.")
            return False
        
        # Controlla se lo stato è già quello desiderato
        if current_status.status == new_status:
            print(f"SERVICE: Lo stato dell'ordine {order_id} è già '{new_status.value}'. Nessun aggiornamento necessario.")
            return False
        
        # Se arriviamo qui, lo stato è diverso e l'ordine esiste, procediamo con l'aggiornamento
        updated_status_obj = await asyncio.to_thread(
            self._status_repo.update_status, order_id, new_status
        )
        
        if updated_status_obj:
            # L'aggiornamento è avvenuto con successo!
            print(f"SERVICE: Stato per l'ordine {order_id} aggiornato da '{current_status.status.value}' a '{new_status.value}'. Notifica in corso...")
            
            # Usa l'oggetto COMPLETO restituito dal repository
            await self._producer.publish_status_update(updated_status_obj)
            
            return True # L'operazione complessiva è riuscita
        else:
            # Questo non dovrebbe mai accadere se l'ordine esiste e lo stato è diverso
            print(f"SERVICE: Errore inaspettato durante l'aggiornamento dell'ordine {order_id}.")
            return False
    
    async def save(self, order_status: OrderStatus) -> None:
        """Salva lo stato di un ordine in modo non bloccante."""
        print(f"SERVICE: Salvataggio dello stato per l'ordine {order_status.order_id}")
        
        # <<< CORREZIONE 1: Usa _status_repo (con underscore)
        # <<< CORREZIONE 2: Usa await asyncio.to_thread per non bloccare l'app
        await asyncio.to_thread(self._status_repo.save, order_status)