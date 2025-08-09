# cartella: tests/api/test_api_main.py

import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient

# Importa l'app FastAPI e le funzioni "provider" dal tuo file API
# Dobbiamo anche importare le classi di servizio per poterle "mockare"
from api.api import app, get_orchestrator
from service.order_service import OrderOrchestrationService
from model.status import StatusEnum

# ======================================================================
# --- Oggetti Finti (Mock) per i Servizi ---
# ======================================================================

# Creiamo dei mock che verranno usati per sostituire i servizi reali
mock_orchestrator = MagicMock(spec=OrderOrchestrationService)
# Configuriamo i metodi asincroni del mock
mock_orchestrator.handle_order_status_update = AsyncMock(return_value=True)

# Sostituiamo il servizio reale con il nostro mock usando la dependency injection di FastAPI
app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

# ======================================================================
# --- Suite di Test per l'API ---
# ======================================================================

class TestKitchenApi(unittest.TestCase):
    
    def setUp(self):
        # Il TestClient ci permette di inviare richieste HTTP alla nostra app
        self.client = TestClient(app)
        # Resettiamo i mock prima di ogni test per avere un ambiente pulito
        mock_orchestrator.reset_mock()

    def test_get_kitchen_status_endpoint(self):
        """
        TEST: Verifica che l'endpoint GET /kitchen funzioni.
        Nota: Questo test è semplificato. In un caso reale, dovremmo mockare
        anche il kitchen_repo per controllare la risposta.
        """
        # Per questo test, assumiamo che il kitchen_repo in-memory abbia dei dati.
        # In un'app più complessa, useremmo dependency_overrides anche per i repo.
        response = self.client.get("/kitchen")
        
        # ASSERT: Verifichiamo la risposta
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("kitchen_id", data)
        self.assertIn("is_operational", data)

    def test_update_order_status_success(self):
        """
        TEST: Verifica che l'endpoint PATCH /orders/{order_id}/status chiami
        correttamente il servizio di orchestrazione quando i dati sono validi.
        """
        # ARRANGE: Prepariamo i dati per il test
        order_id = uuid.uuid4()
        request_body = {"status": "ready"} # Deve corrispondere a StatusUpdateRequest

        # ACT: Inviamo una richiesta PATCH finta al nostro endpoint
        response = self.client.patch(f"/orders/{order_id}/status", json=request_body)

        # ASSERT: Verifichiamo il risultato
        # 1. La risposta HTTP deve essere corretta (202 Accepted)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"message": "Richiesta di aggiornamento stato accettata."})

        # 2. Il servizio di orchestrazione deve essere stato chiamato esattamente una volta
        mock_orchestrator.handle_order_status_update.assert_called_once()
        
        # 3. Verifichiamo che sia stato chiamato con i parametri giusti
        call_args = mock_orchestrator.handle_order_status_update.call_args
        self.assertEqual(call_args.kwargs['order_id'], order_id)
        self.assertEqual(call_args.kwargs['new_status'], StatusEnum.READY)

    def test_update_order_status_not_found(self):
        """
        TEST: Verifica che l'API restituisca un errore 404 se il servizio
        segnala che l'ordine non è stato trovato.
        """
        # ARRANGE
        order_id = uuid.uuid4()
        request_body = {"status": "delivered"}
        
        # Diciamo al nostro mock di simulare un fallimento
        mock_orchestrator.handle_order_status_update.return_value = False

        # ACT
        response = self.client.patch(f"/orders/{order_id}/status", json=request_body)

        # ASSERT
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Ordine non trovato o aggiornamento fallito."})