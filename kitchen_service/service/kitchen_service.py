import uuid
import asyncio
from repository.kitchen_repository import KitchenAvailabilityRepository
from typing import Optional
from model.kitchen import KitchenAvailability

class KitchenService:
    """
    Contiene la logica di business relativa alla disponibilità e al carico delle cucine.
    Tutte le operazioni sono asincrone per evitare di bloccare l'event loop.
    """
    def __init__(self, kitchen_repo: KitchenAvailabilityRepository):
        self._kitchen_repo = kitchen_repo

    async def get_by_id(self, kitchen_id: uuid.UUID) -> Optional[KitchenAvailability]:
        """Recupera una cucina in modo non bloccante."""
        return await asyncio.to_thread(self._kitchen_repo.get_by_id, kitchen_id)

    async def increment_load(self, kitchen_id: uuid.UUID) -> bool:
        """
        Incrementa il carico di una cucina in modo atomico e non bloccante.
        """
        kitchen = await self.get_by_id(kitchen_id)
        if not kitchen or not kitchen.is_operational:
            return False
        
        new_load = kitchen.current_load + 1
        new_status = False if new_load >= kitchen.max_load else kitchen.is_operational

        return await asyncio.to_thread(
            self._kitchen_repo.update_fields,
            kitchen_id=kitchen_id,
            current_load=new_load,
            is_operational=new_status
        )

    async def decrement_load(self, kitchen_id: uuid.UUID) -> bool:
        """
        Decrementa il carico di una cucina in modo atomico e non bloccante.
        """
        kitchen = await self.get_by_id(kitchen_id)
        if not kitchen or kitchen.current_load <= 0:
            return False

        new_load = kitchen.current_load - 1
        new_status = True if new_load < kitchen.max_load else kitchen.is_operational
            
        return await asyncio.to_thread(
            self._kitchen_repo.update_fields,
            kitchen_id=kitchen_id,
            current_load=new_load,
            is_operational=new_status
        )

    async def set_operational_status(self, kitchen_id: uuid.UUID, status: bool) -> bool:
        """
        Metodo asincrono per forzare lo stato operativo di una cucina.
        """
        return await asyncio.to_thread(self._kitchen_repo.update_fields, kitchen_id, is_operational=status)