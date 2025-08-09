# cartella: test/status_test.py

import unittest
from unittest.mock import Mock
import uuid
import asyncio

# Importa le classi necessarie
from model.order import Order
from model.status import StatusEnum 
from repository.order_status_repository import OrderStatusRepository
from service.status_service import OrderStatusService

class TestOrderStatusService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = Mock(spec=OrderStatusRepository)
        self.status_service = OrderStatusService(status_repo=self.mock_repo)

    def test_create_initial_status(self):
        # --- Questo test è già corretto e rimane invariato ---
        order = Order(
            order_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            dish_id=uuid.uuid4(),
            delivery_address="Via Test 123",
            kitchen_id=uuid.uuid4() 
        )
        
        asyncio.run(self.status_service.create_initial_status(order))

        self.mock_repo.save.assert_called_once()
        saved_status = self.mock_repo.save.call_args[0][0]
        self.assertEqual(saved_status.status, StatusEnum.RECEIVED)

    def test_update_status_calls_repository_correctly(self):
        """
        TEST: Verifica che l'aggiornamento di stato chiami il metodo
        corretto del repository.
        """
        # --- ARRANGE ---
        order_id = uuid.uuid4()
        # CORREZIONE: Usa il nome corretto del membro dell'enum
        new_status = StatusEnum.READY_FOR_PICKUP
        
        self.mock_repo.update_status.return_value = True

        # --- ACT ---
        result = asyncio.run(self.status_service.update_status(order_id, new_status))

        # --- ASSERT ---
        self.assertTrue(result)
        self.mock_repo.update_status.assert_called_once_with(order_id, new_status)