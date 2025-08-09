import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock

# Importa tutti i modelli e servizi necessari
from model.order import Order
from model.status import OrderStatus, StatusEnum
from repository.order_repository import OrderRepository
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.status_service import OrderStatusService
from service.order_service import OrderOrchestrationService
from producers.producers import EventProducer


# ======================================================================
# --- Fixture per i mock dei servizi dipendenti ---
# ======================================================================
@pytest.fixture
def mock_services():
    """Crea e restituisce una tupla con tutti i mock necessari."""
    mock_order_repo = MagicMock(spec=OrderRepository)
    mock_order_repo.save = AsyncMock()
    mock_order_repo.get_by_id = AsyncMock(return_value=None)

    mock_kitchen_service = MagicMock(spec=KitchenService)
    mock_kitchen_service.increment_load = AsyncMock(return_value=True)
    mock_kitchen_service.decrement_load = AsyncMock()

    mock_menu_service = MagicMock(spec=MenuService)
    mock_menu_service.decrement_item_quantity = AsyncMock(return_value=True)
    mock_menu_service.increment_item_quantity = AsyncMock()

    mock_status_service = MagicMock(spec=OrderStatusService)
    mock_status_service.create_initial_status = AsyncMock()
    mock_status_service.update_status = AsyncMock(return_value=True)
    mock_status_service.get_by_id = AsyncMock(return_value=OrderStatus(order_id=uuid.uuid4(), kitchen_id=uuid.uuid4()))

    mock_event_producer = MagicMock(spec=EventProducer)
    mock_event_producer.publish_acceptance_response = AsyncMock()
    mock_event_producer.publish_status_update = AsyncMock()

    return (mock_order_repo, mock_kitchen_service, mock_menu_service, mock_status_service, mock_event_producer)


# ======================================================================
# --- Test per OrderOrchestrationService ---
# ======================================================================

@pytest.mark.asyncio
async def test_orchestration_handle_new_order_happy_path(mock_services):
    """TEST: Flusso corretto quando tutte le operazioni hanno successo."""
    mock_order_repo, mock_kitchen_service, mock_menu_service, mock_status_service, mock_event_producer = mock_services

    order = Order(
        order_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="123 Main St",
        kitchen_id=uuid.uuid4()
    )

    orchestrator = OrderOrchestrationService(
        order_repo=mock_order_repo,
        kitchen_service=mock_kitchen_service,
        menu_service=mock_menu_service,
        status_service=mock_status_service,
        event_producer=mock_event_producer
    )

    result = await orchestrator.handle_newly_assigned_order(order)

    assert result is True
    mock_menu_service.decrement_item_quantity.assert_called_once_with(order.kitchen_id, order.dish_id)
    mock_kitchen_service.increment_load.assert_called_once_with(order.kitchen_id)
    mock_order_repo.save.assert_called_once_with(order)
    mock_status_service.create_initial_status.assert_called_once_with(order)


@pytest.mark.asyncio
async def test_orchestration_handle_new_order_fails_if_kitchen_is_full(mock_services):
    """TEST: L'ordine fallisce se la cucina è piena e la quantità del piatto viene ripristinata."""
    # CORREZIONE: Spacchetta tutti e 5 i mock
    mock_order_repo, mock_kitchen_service, mock_menu_service, mock_status_service, mock_event_producer = mock_services

    # Setup scenario di fallimento
    mock_kitchen_service.increment_load.return_value = False  # Fallimento

    order = Order(
        order_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="...",
        kitchen_id=uuid.uuid4()
    )

    orchestrator = OrderOrchestrationService(
        order_repo=mock_order_repo,
        kitchen_service=mock_kitchen_service,
        menu_service=mock_menu_service,
        status_service=mock_status_service,
        # CORREZIONE: Aggiunto il producer mancante
        event_producer=mock_event_producer
    )

    result = await orchestrator.handle_newly_assigned_order(order)

    assert result is False
    mock_menu_service.decrement_item_quantity.assert_called_once()
    mock_kitchen_service.increment_load.assert_called_once()
    # Verifica del rollback
    mock_menu_service.increment_item_quantity.assert_called_once_with(order.kitchen_id, order.dish_id)
    mock_order_repo.save.assert_not_called()
    mock_status_service.create_initial_status.assert_not_called()


@pytest.mark.asyncio
async def test_orchestration_handle_order_ready_status_update(mock_services):
    """TEST: Il carico della cucina viene decrementato quando un ordine è pronto."""
    # CORREZIONE: Spacchetta tutti e 5 i mock
    mock_order_repo, mock_kitchen_service, mock_menu_service, mock_status_service, mock_event_producer = mock_services

    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()

    orchestrator = OrderOrchestrationService(
        order_repo=mock_order_repo,
        kitchen_service=mock_kitchen_service,
        menu_service=mock_menu_service,
        status_service=mock_status_service,
        # CORREZIONE: Aggiunto il producer mancante
        event_producer=mock_event_producer
    )

    await orchestrator.handle_order_status_update(order_id, kitchen_id, StatusEnum.READY_FOR_PICKUP)

    mock_kitchen_service.decrement_load.assert_called_once_with(kitchen_id)
    # Verifica che il producer sia stato chiamato per notificare l'aggiornamento
    mock_event_producer.publish_status_update.assert_called_once()
