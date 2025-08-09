import uuid
from typing import Dict, Optional, List
from model.kitchen import KitchenAvailability

class KitchenAvailabilityRepository:
    def __init__(self):
        # CORREZIONE: La chiave del dizionario è ora uuid.UUID, non str.
        self._availabilities: Dict[uuid.UUID, KitchenAvailability] = {}

    def save(self, availability: KitchenAvailability) -> None:
        """Salva (crea o sovrascrive) lo stato completo di una cucina."""
        # CORREZIONE: L'ID è un oggetto UUID.
        self._availabilities[availability.kitchen_id] = availability

    def update_fields(self, kitchen_id: uuid.UUID, current_load: Optional[int] = None,
                      max_load: Optional[int] = None,
                      is_operational: Optional[bool] = None) -> bool:
        """Aggiorna uno o più campi di una cucina esistente."""
        # CORREZIONE: Controlla l'esistenza usando l'oggetto UUID.
        if kitchen_id in self._availabilities:
            kitchen = self._availabilities[kitchen_id]
            if current_load is not None:
                kitchen.current_load = current_load
            if max_load is not None:
                kitchen.max_load = max_load
            if is_operational is not None:
                kitchen.is_operational = is_operational
            return True
        return False

    def get_by_id(self, kitchen_id: uuid.UUID) -> Optional[KitchenAvailability]:
        """Recupera lo stato di una cucina tramite il suo ID."""
        # CORREZIONE: Cerca usando l'oggetto UUID.
        return self._availabilities.get(kitchen_id)

    def get_all(self) -> List[KitchenAvailability]:
        """Recupera lo stato di tutte le cucine."""
        return list(self._availabilities.values())