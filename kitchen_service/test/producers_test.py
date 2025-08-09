import uuid
import json
import pytest
from unittest.mock import AsyncMock, patch

# Importa le classi da testare e i modelli necessari
from producers.producers import EventProducer, ACCEPTANCE_RESPONSE_TOPIC, STATUS_UPDATE_TOPIC
from model.status import OrderStatus, StatusEnum

# ======================================================================
# --- Test per EventProducer ---
# ======================================================================

@pytest.fixture
def mock_kafka_producer_client():
    """
    Fixture che crea un mock del client AIOKafkaProducer.
    Questo ci permette di intercettare le chiamate senza una vera connessione a Kafka.
    """
    # Usiamo 'patch' per sostituire temporaneamente la classe AIOKafkaProducer
    # con un nostro mock durante l'esecuzione dei test.
    with patch('producers.producers.AIOKafkaProducer') as MockKafkaClient:
        # Configuriamo il mock per avere i metodi start, stop e send_and_wait asincroni
        mock_instance = MockKafkaClient.return_value
        mock_instance.start = AsyncMock()
        mock_instance.stop = AsyncMock()
        mock_instance.send_and_wait = AsyncMock()
        yield mock_instance # Restituisce l'istanza del mock al test

@pytest.mark.asyncio
async def test_publish_acceptance_response(mock_kafka_producer_client):
    """
    TEST: Verifica che la risposta di "candidatura" venga pubblicata correttamente.
    """
    # --- SETUP ---
    producer = EventProducer(bootstrap_servers="fake:9092")
    # Dobbiamo avviare manualmente il producer per impostare self._started = True
    # e per usare il nostro mock_kafka_producer_client.
    await producer.start()

    kitchen_id = uuid.uuid4()
    order_id = uuid.uuid4()
    can_handle = True

    # --- ESECUZIONE ---
    await producer.publish_acceptance_response(kitchen_id, order_id, can_handle)

    # --- VERIFICA ---
    # Controlliamo che il metodo 'send_and_wait' del client Kafka finto sia stato chiamato
    mock_kafka_producer_client.send_and_wait.assert_called_once()
    
    # Estraiamo gli argomenti con cui è stato chiamato
    call_args = mock_kafka_producer_client.send_and_wait.call_args
    
    # Verifichiamo che il topic sia corretto
    assert call_args.args[0] == ACCEPTANCE_RESPONSE_TOPIC
    
    # Verifichiamo che il messaggio (value) abbia la struttura e i dati corretti
    sent_message = call_args.kwargs['value']
    expected_message = {"kitchen_id": kitchen_id, "order_id": order_id, "can_handle": can_handle}
    assert sent_message == expected_message


@pytest.mark.asyncio
async def test_publish_status_update(mock_kafka_producer_client):
    """
    TEST: Verifica che l'aggiornamento di stato venga pubblicato correttamente.
    """
    # --- SETUP ---
    producer = EventProducer(bootstrap_servers="fake:9092")
    await producer.start()

    status_update = OrderStatus(
        order_id=uuid.uuid4(),
        kitchen_id=uuid.uuid4(),
        status=StatusEnum.PREPARING
    )

    # --- ESECUZIONE ---
    await producer.publish_status_update(status_update)

    # --- VERIFICA ---
    mock_kafka_producer_client.send_and_wait.assert_called_once()
    
    call_args = mock_kafka_producer_client.send_and_wait.call_args
    
    # Verifichiamo il topic
    assert call_args.args[0] == STATUS_UPDATE_TOPIC
    
    # Verifichiamo che il messaggio sia il dizionario corretto del nostro oggetto Pydantic
    sent_message = call_args.kwargs['value']
    # CORREZIONE: Usiamo model_dump() invece del deprecato dict()
    assert sent_message == status_update.model_dump()
