# cartella: service/menu_service.py

import uuid
import asyncio
from typing import Optional, List
from repository.menu_repository import MenuRepository
from model.menu import MenuItem, Menu
from pydantic import ValidationError

class MenuService:
    """
    Contiene la logica di business per la gestione del menu e dell'inventario.
    Chiama i metodi del repository in modo non bloccante.
    """
    def __init__(self, menu_repo: MenuRepository):
        self._menu_repo = menu_repo

    # --- Metodi di Creazione (Create) ---
    async def create_menu_item(self, kitchen_id: uuid.UUID, menu_item: MenuItem) -> bool:
        """
        Aggiunge un nuovo piatto al menu di una cucina.
        """
        # Controlla se il piatto esiste già per evitare la sovrascrittura accidentale
        if await self.get_menu_item(kitchen_id, menu_item.dish_id):
            print(f"ERROR (MenuService): Il piatto con ID {menu_item.dish_id} esiste già.")
            return False

        # Esegue la chiamata bloccante del repository in un thread separato.
        try:
            await asyncio.to_thread(self._menu_repo.create_menu_item, kitchen_id, menu_item)
            return True
        except ValidationError as e:
            print(f"ERROR (MenuService): Dati del piatto non validi: {e}")
            return False

    # --- Metodi di Lettura (Read) ---
    async def get_menu_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> Optional[MenuItem]:
        """Recupera un piatto specifico in modo non bloccante."""
        item = await asyncio.to_thread(self._menu_repo.get_menu_item, kitchen_id, dish_id)
        return item
    
    async def get_menu(self, kitchen_id: uuid.UUID) -> Optional[Menu]:
        """Recupera l'intero menu di una cucina in modo non bloccante."""
        menu = await asyncio.to_thread(self._menu_repo.get_menu, kitchen_id)
        return menu

    async def is_dish_available(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Controlla se un piatto ha una quantità disponibile > 0 in modo non bloccante.
        """
        item = await self.get_menu_item(kitchen_id, dish_id)
        return item is not None and item.available_quantity > 0

    # --- Metodi di Aggiornamento (Update) ---
    async def update_menu_item(self, kitchen_id: uuid.UUID, menu_item: MenuItem) -> bool:
        """
        Aggiorna un piatto esistente nel menu.
        """
        # Verifica che il piatto esista prima di tentare l'aggiornamento.
        if not await self.get_menu_item(kitchen_id, menu_item.dish_id):
            print(f"ERROR (MenuService): Il piatto con ID {menu_item.dish_id} non esiste. Impossibile aggiornare.")
            return False
            
        try:
            await asyncio.to_thread(self._menu_repo.create_menu_item, kitchen_id, menu_item)
            return True
        except ValidationError as e:
            print(f"ERROR (MenuService): Dati del piatto non validi: {e}")
            return False

    async def commit_order_dish(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Esegue il decremento della quantità in modo atomico e non bloccante.
        """
        # Eseguiamo la chiamata bloccante del repository in un thread separato.
        result_code = await asyncio.to_thread(self._menu_repo.atomic_decrement_quantity, kitchen_id, dish_id)

        # Interpreta il risultato.
        if result_code >= 0:
            print(f"INFO (MenuService): Scorta per piatto {dish_id} decrementata. Nuova quantità: {result_code}")
            return True
        else:
            if result_code == -1:
                print(f"ERROR (MenuService): Tentativo di decrementare un piatto ({dish_id}) non esistente.")
            elif result_code == -3:
                print(f"ERROR (MenuService): Piatto {dish_id} esaurito. Impossibile decrementare.")
            return False

    async def restock_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID, amount: int = 1) -> bool:
        """
        Incrementa la quantità di un piatto in modo atomico e non bloccante.
        """
        # Eseguiamo la chiamata bloccante del repository in un thread separato.
        result_code = await asyncio.to_thread(self._menu_repo.atomic_increment_quantity, kitchen_id, dish_id, amount)

        if result_code >= 0:
            print(f"INFO (MenuService): Scorta per piatto {dish_id} incrementata. Nuova quantità: {result_code}")
            return True
        else:
            print(f"ERROR (MenuService): Impossibile fare il restock per il piatto {dish_id}.")
            return False

    # --- Metodi di Cancellazione (Delete) ---
    async def delete_menu_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Elimina un piatto dal menu di una cucina.
        """
        # Verifica che il piatto esista prima di tentare la cancellazione.
        if not await self.get_menu_item(kitchen_id, dish_id):
            print(f"ERROR (MenuService): Il piatto con ID {dish_id} non esiste. Impossibile eliminare.")
            return False
            
        return await asyncio.to_thread(self._menu_repo.delete_menu_item, kitchen_id, dish_id)