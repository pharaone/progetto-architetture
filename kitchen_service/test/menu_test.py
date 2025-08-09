# cartella: tests/service/test_menu_service.py

import unittest
from unittest.mock import Mock
import uuid

# Importa le classi necessarie
from model.menu import MenuItem # Assumendo che il modello sia MenuItem
from repository.menu_repository import MenuRepository
from service.menu_service import MenuService

class TestMenuService(unittest.TestCase):
    """
    Suite di test aggiornata per il MenuService sincrono e atomico.
    """

    def setUp(self):
        """
        Prepara l'ambiente prima di ogni test.
        """
        # Creiamo un "mock" del MenuRepository.
        # È un oggetto finto che possiamo controllare.
        self.mock_repo = Mock(spec=MenuRepository)
        
        # Istanziamo il servizio da testare, passandogli il repository finto.
        self.menu_service = MenuService(menu_repo=self.mock_repo)

    async def test_commit_order_dish_succeeds_when_repository_returns_positive(self):
        """
        TEST: Verifica che il commit di un ordine abbia successo (return True)
        quando il repository atomico restituisce un codice >= 0.
        """
        # --- ARRANGE (Prepara lo scenario) ---
        kitchen_id = uuid.uuid4()
        dish_id = uuid.uuid4()
        
        # Diciamo al mock: "Quando ti chiameranno atomic_decrement_quantity,
        # simula un successo restituendo la nuova quantità, es. 4".
        self.mock_repo.atomic_decrement_quantity.return_value = 4

        # --- ACT (Esegui l'azione da testare) ---
        result = self.menu_service.commit_order_dish(kitchen_id, dish_id)

        # --- ASSERT (Verifica il risultato) ---
        # 1. Il risultato del servizio deve essere True
        self.assertTrue(result)
        
        # 2. Il metodo atomico del repository deve essere stato chiamato
        #    esattamente una volta con i parametri corretti.
        self.mock_repo.atomic_decrement_quantity.assert_called_once_with(kitchen_id, dish_id)

    async def test_commit_order_dish_fails_when_repository_returns_out_of_stock(self):
        """
        TEST: Verifica che il commit di un ordine fallisca (return False)
        se il repository atomico restituisce il codice di "esaurito" (-3).
        """
        # --- ARRANGE ---
        kitchen_id = uuid.uuid4()
        dish_id = uuid.uuid4()
        
        # Diciamo al mock di simulare un fallimento per scorta esaurita
        self.mock_repo.atomic_decrement_quantity.return_value = -3

        # --- ACT ---
        result = self.menu_service.commit_order_dish(kitchen_id, dish_id)

        # --- ASSERT ---
        # 1. Il risultato del servizio deve essere False
        self.assertFalse(result)
        
        # 2. Il metodo atomico del repository deve comunque essere stato chiamato
        self.mock_repo.atomic_decrement_quantity.assert_called_once_with(kitchen_id, dish_id)

    async def test_is_dish_available_returns_true_for_positive_quantity(self):
        """
        TEST: Verifica che il controllo di disponibilità funzioni correttamente
        quando un piatto è in stock.
        """
        # --- ARRANGE ---
        kitchen_id = uuid.uuid4()
        dish_id = uuid.uuid4()
        # Creiamo un finto oggetto MenuItem con quantità positiva
        fake_item = MenuItem(dish_id=dish_id, name="Pizza", price=10.0, available_quantity=1)
        
        # Diciamo al mock del repository di restituire questo oggetto quando viene interrogato
        self.mock_repo.get_menu_item.return_value = fake_item

        # --- ACT ---
        result = self.menu_service.is_dish_available(kitchen_id, dish_id)

        # --- ASSERT ---
        self.assertTrue(result)
        self.mock_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)