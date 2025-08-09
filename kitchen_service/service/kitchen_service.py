import uuid
from repository.kitchen_repository import KitchenAvailabilityRepository

class KitchenService:
    """
    Contiene la logica di business relativa alla disponibilità e al carico delle cucine.
    """
    def __init__(self, kitchen_repo: KitchenAvailabilityRepository):
        self._kitchen_repo = kitchen_repo

    async def increment_load(self, kitchen_id: uuid.UUID) -> bool:
        """
        Incrementa il carico di una cucina e la disattiva se raggiunge la capacità massima.
        """
        kitchen = await self._kitchen_repo.get_by_id(kitchen_id)
        if not kitchen:
            # LOG: La cucina specificata non esiste.
            return False
        
        if not kitchen.is_operational:
            # LOG: Tentativo di assegnare un ordine a una cucina già piena o non operativa.
            return False

        kitchen.current_load += 1
        
        # Logica di business: se il carico raggiunge il massimo, la cucina non accetta più ordini.
        if kitchen.current_load >= kitchen.max_load:
            kitchen.is_operational = False
        
        # Salviamo l'intero stato aggiornato.
        await self._kitchen_repo.save(kitchen)
        return True

    async def decrement_load(self, kitchen_id: uuid.UUID) -> bool:
        """
        Decrementa il carico di una cucina (es. quando un ordine è pronto)
        e la riattiva se torna sotto la capacità massima.
        """
        kitchen = await self._kitchen_repo.get_by_id(kitchen_id)
        if not kitchen:
            return False

        if kitchen.current_load > 0:
            kitchen.current_load -= 1
        
        # Logica di business: se la cucina era piena e ora si è liberato uno slot,
        # torna ad essere operativa.
        if not kitchen.is_operational and kitchen.current_load < kitchen.max_load:
            kitchen.is_operational = True
            
        await self._kitchen_repo.save(kitchen)
        return True

    async def set_operational_status(self, kitchen_id: uuid.UUID, status: bool) -> bool:
        """
        Metodo per forzare lo stato operativo di una cucina (es. per apertura/chiusura).
        """
        return await self._kitchen_repo.update_fields(kitchen_id, is_operational=status)
