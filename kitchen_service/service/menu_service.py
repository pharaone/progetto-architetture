# cartella: service/menu_service.py

import uuid
from repository.menu_repository import MenuRepository

class MenuService:
    """
    Contiene la logica di business per la gestione dell'inventario dei piatti.
    Chiama i metodi atomici del repository per garantire operazioni sicure.
    """
    def __init__(self, menu_repo: MenuRepository):
        self._menu_repo = menu_repo

    async def is_dish_available(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Controlla se un piatto ha una quantità disponibile > 0.
        """
        item = self._menu_repo.get_menu_item(kitchen_id, dish_id)
        return item and item.available_quantity > 0

    async def commit_order_dish(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        MIGLIORAMENTO: Esegue il decremento della quantità in modo atomico.
        Questa funzione ora contiene la logica di business per interpretare
        il risultato dell'operazione atomica del repository.
        """
        # 1. Chiama il metodo atomico del repository.
        #    Non c'è più bisogno di leggere prima e scrivere dopo.
        result_code = self._menu_repo.atomic_decrement_quantity(kitchen_id, dish_id)

        # 2. Interpreta il risultato. Questa è la logica di business.
        #    Un codice di ritorno >= 0 significa che il decremento è riuscito.
        if result_code >= 0:
            print(f"INFO (MenuService): Scorta per piatto {dish_id} decrementata. Nuova quantità: {result_code}")
            return True
        else:
            # Qui gestisci i diversi tipi di fallimento.
            if result_code == -1:
                print(f"ERROR (MenuService): Tentativo di decrementare un piatto ({dish_id}) non esistente.")
            elif result_code == -3:
                print(f"ERROR (MenuService): Piatto {dish_id} esaurito. Impossibile decrementare.")
            return False

    async def restock_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID, amount: int = 1) -> bool:
        """
        MIGLIORAMENTO: Incrementa la quantità di un piatto (es. per un ordine annullato)
        usando un'operazione atomica.
        """
        # Nota: questo richiede l'aggiunta di 'atomic_increment_quantity' al repository.
        result_code = self._menu_repo.atomic_increment_quantity(kitchen_id, dish_id, amount)

        if result_code >= 0:
            print(f"INFO (MenuService): Scorta per piatto {dish_id} incrementata. Nuova quantità: {result_code}")
            return True
        else:
            print(f"ERROR (MenuService): Impossibile fare il restock per il piatto {dish_id}.")
            return False