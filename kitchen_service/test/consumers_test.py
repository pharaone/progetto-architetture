# ======================================================================
# --- File: test_consumers.py ---
# ======================================================================
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from model.order import Order
from model.messaging_models import OrderRequest
from consumers.consumers import (
    EventConsumer,
    AVAILABILITY_REQUEST_TOPIC,
    ORDER_ASSIGNMENT_TOPIC,
    ORDER_STATUS_REQUEST_TOPIC,
)

pytestmark = pytest.mark.asyncio


class DummyMsg:
    """Messaggio fittizio che simula un record Kafka."""
    def __init__(self, topic, value):
        self.topic = topic
        self.value = value


@pytest.fixture
def orchestrator_mock():
    mock = AsyncMock()
    mock.check_availability_and_propose = AsyncMock()
    mock.handle_newly_assigned_order = AsyncMock()
    mock.get_and_publish_status = AsyncMock()
    return mock


@pytest.fixture
def consumer(orchestrator_mock):
    # Patchiamo AIOKafkaConsumer a livello globale per non farlo partire
    with patch("consumers.consumers.AIOKafkaConsumer") as fake_consumer_cls:
        fake_consumer = MagicMock()
        fake_consumer.start = AsyncMock()
        fake_consumer.stop = AsyncMock()
        fake_consumer.__aiter__.return_value = []  # niente loop reale
        fake_consumer_cls.return_value = fake_consumer

        c = EventConsumer(
            bootstrap_servers="fake:9092",
            orchestrator=orchestrator_mock,
            group_id="test-group",
        )
        c._consumer = fake_consumer  # forziamo il consumer mockato
        c._started = True
        yield c


async def test_availability_request_calls_orchestrator(consumer, orchestrator_mock):
    msg = DummyMsg(
        AVAILABILITY_REQUEST_TOPIC,
        {
            "order_id": str(uuid.uuid4()),
            "dish_id": str(uuid.uuid4()),
            "kitchen_id": str(uuid.uuid4()),
        },
    )

    # Simuliamo logica del listener
    await consumer._orchestrator.check_availability_and_propose(
        OrderRequest(**msg.value)
    )

    orchestrator_mock.check_availability_and_propose.assert_awaited_once()
    args, _ = orchestrator_mock.check_availability_and_propose.call_args
    assert isinstance(args[0], OrderRequest)


async def test_order_assignment_calls_orchestrator(consumer, orchestrator_mock):
    msg = DummyMsg(
        ORDER_ASSIGNMENT_TOPIC,
        {
            "order_id": str(uuid.uuid4()),
            "kitchen_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "dish_id": str(uuid.uuid4()),
            "delivery_address": "via Roma 1",
        },
    )

    await consumer._orchestrator.handle_newly_assigned_order(Order(**msg.value))

    orchestrator_mock.handle_newly_assigned_order.assert_awaited_once()
    args, _ = orchestrator_mock.handle_newly_assigned_order.call_args
    assert isinstance(args[0], Order)


async def test_status_request_calls_orchestrator(consumer, orchestrator_mock):
    msg = DummyMsg(
        ORDER_STATUS_REQUEST_TOPIC,
        {
            "order_id": str(uuid.uuid4()),
            "kitchen_id": str(uuid.uuid4()),
        },
    )

    await consumer._orchestrator.get_and_publish_status(
        uuid.UUID(msg.value["order_id"]),
        uuid.UUID(msg.value["kitchen_id"]),
    )

    orchestrator_mock.get_and_publish_status.assert_awaited_once()
    args, _ = orchestrator_mock.get_and_publish_status.call_args
    assert isinstance(args[0], uuid.UUID)
    assert isinstance(args[1], uuid.UUID)
