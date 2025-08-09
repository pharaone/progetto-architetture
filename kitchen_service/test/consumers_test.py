# cartella: tests/messaging/test_consumers.py

import uuid
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Importa le classi da testare e i modelli necessari
# CORREZIONE: Aggiornato il percorso di import per rispecchiare la tua struttura
from consumers.consumers import EventConsumer, AVAILABILITY_REQUEST_TOPIC, ORDER_ASSIGNMENT_TOPIC, ORDER_STATUS_REQUEST_TOPIC
from model.order import Order
from model.messaging_models import OrderRequest
from service.order_service import OrderOrchestrationService

# ======================================================================
# --- Test per EventConsumer ---
# ======================================================================

@pytest.fixture
def mock_orchestrator():
    """Crea un mock per il servizio di orchestrazione."""
    mock = MagicMock(spec=OrderOrchestrationService)
    mock.check_availability_and_propose = AsyncMock()
    mock.handle_newly_assigned_order = AsyncMock()
    mock.get_and_publish_status = AsyncMock()
    return mock

def create_fake_kafka_message(topic: str, value: dict):
    """Funzione di utilità per creare un oggetto messaggio Kafka finto."""
    message = MagicMock()
    message.topic = topic
    message.value = value
    return message

@pytest.mark.asyncio
async def test_consumer_handles_availability_request(mock_orchestrator):
    """
    TEST: Verifica che un messaggio sul topic AVAILABILITY_REQUEST_TOPIC
    venga smistato correttamente.
    """
    # --- ARRANGE (Prepara lo scenario) ---
    request_data = {"order_id": str(uuid.uuid4()), "dish_id": str(uuid.uuid4())}
    fake_message = create_fake_kafka_message(AVAILABILITY_REQUEST_TOPIC, request_data)
    
    # Creiamo un mock del client AIOKafkaConsumer
    # e gli diciamo di "produrre" un solo messaggio e poi fermarsi.
    mock_consumer_client = AsyncMock()
    mock_consumer_client.__aiter__.return_value = [fake_message]

    # --- ACT (Esegui l'azione) ---
    # CORREZIONE: Il percorso per 'patch' deve essere il percorso completo del modulo
    # dove AIOKafkaConsumer è importato e usato.
    with patch('consumers.consumers.AIOKafkaConsumer', return_value=mock_consumer_client):
        consumer = EventConsumer(
            bootstrap_servers="fake:9092",
            orchestrator=mock_orchestrator,
            group_id="test-group"
        )
        await consumer.start()
        # Eseguiamo il listen come un task che possiamo fermare
        listen_task = asyncio.create_task(consumer.listen())
        await asyncio.sleep(0.01) # Diamo tempo al loop di eseguire un ciclo
        listen_task.cancel() # Fermiamo il loop infinito

    # --- ASSERT (Verifica il risultato) ---
    mock_orchestrator.check_availability_and_propose.assert_called_once()
    # Verifica che il mock sia stato chiamato con il tipo di oggetto corretto
    called_with_arg = mock_orchestrator.check_availability_and_propose.call_args[0][0]
    assert isinstance(called_with_arg, OrderRequest)
    assert str(called_with_arg.order_id) == request_data["order_id"]
    pass

@pytest.mark.asyncio
async def test_consumer_handles_order_assignment(mock_orchestrator):
    """
    TEST: Verifica che un messaggio sul topic ORDER_ASSIGNMENT_TOPIC
    venga smistato correttamente.
    """
    # --- ARRANGE ---
    # CORREZIONE: Tutti i campi ID ora usano str(uuid.uuid4()) per
    # generare stringhe di UUID validi, che passeranno la validazione di Pydantic.
    order_data = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()), # <-- CORRETTO
        "dish_id": str(uuid.uuid4()),
        "delivery_address": "Via Test 123",
        "kitchen_id": str(uuid.uuid4())
    }
    fake_message = create_fake_kafka_message(ORDER_ASSIGNMENT_TOPIC, order_data)
    mock_consumer_client = AsyncMock()
    mock_consumer_client.__aiter__.return_value = [fake_message]

    # --- ACT ---
    with patch('consumers.consumers.AIOKafkaConsumer', return_value=mock_consumer_client):
        consumer = EventConsumer("fake:9092", mock_orchestrator, "test-group")
        await consumer.start()
        listen_task = asyncio.create_task(consumer.listen())
        await asyncio.sleep(0.01)
        listen_task.cancel()

    # --- ASSERT ---
    # Ora questa verifica avrà successo perché la funzione verrà chiamata
# --- ASSERT ---
    mock_orchestrator.handle_newly_assigned_order.assert_called_once()

    order_arg = mock_orchestrator.handle_newly_assigned_order.call_args[0][0]
    assert isinstance(order_arg, Order)
    assert str(order_arg.order_id) == order_data["order_id"]

@pytest.mark.asyncio
async def test_consumer_ignores_invalid_order_assignment(mock_orchestrator):
    invalid_data = {  # manca customer_id, per esempio
        "order_id": str(uuid.uuid4()),
        "dish_id": str(uuid.uuid4()),
        "delivery_address": "Via Test 123",
        "kitchen_id": str(uuid.uuid4())
    }
    fake_message = create_fake_kafka_message(ORDER_ASSIGNMENT_TOPIC, invalid_data)
    mock_consumer_client = AsyncMock()
    mock_consumer_client.__aiter__.return_value = [fake_message]

    with patch('consumers.consumers.AIOKafkaConsumer', return_value=mock_consumer_client):
        consumer = EventConsumer("fake:9092", mock_orchestrator, "test-group")
        await consumer.start()
        listen_task = asyncio.create_task(consumer.listen())
        await asyncio.sleep(0.01)
        listen_task.cancel()
    mock_orchestrator.handle_newly_assigned_order.assert_not_called()

@pytest.mark.asyncio
async def test_consumer_ignores_unrelated_topic(mock_orchestrator):
    other_topic_data = {"foo": "bar"}
    fake_message = create_fake_kafka_message("some_random_topic", other_topic_data)
    mock_consumer_client = AsyncMock()
    mock_consumer_client.__aiter__.return_value = [fake_message]

    with patch('consumers.consumers.AIOKafkaConsumer', return_value=mock_consumer_client):
        consumer = EventConsumer("fake:9092", mock_orchestrator, "test-group")
        await consumer.start()
        listen_task = asyncio.create_task(consumer.listen())
        await asyncio.sleep(0.01)
        listen_task.cancel()

    mock_orchestrator.handle_newly_assigned_order.assert_not_called()

@pytest.mark.asyncio
async def test_consumer_continues_after_service_error(mock_orchestrator):
    mock_orchestrator.handle_newly_assigned_order.side_effect = RuntimeError("Service failure")

    order_data = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "dish_id": str(uuid.uuid4()),
        "delivery_address": "Via Test 123",
        "kitchen_id": str(uuid.uuid4())
    }
    fake_message = create_fake_kafka_message(ORDER_ASSIGNMENT_TOPIC, order_data)
    mock_consumer_client = AsyncMock()
    mock_consumer_client.__aiter__.return_value = [fake_message, fake_message]  # due messaggi

    with patch('consumers.consumers.AIOKafkaConsumer', return_value=mock_consumer_client):
        consumer = EventConsumer("fake:9092", mock_orchestrator, "test-group")
        await consumer.start()
        listen_task = asyncio.create_task(consumer.listen())
        await asyncio.sleep(0.05)
        listen_task.cancel()

    assert mock_orchestrator.handle_newly_assigned_order.call_count >= 2
