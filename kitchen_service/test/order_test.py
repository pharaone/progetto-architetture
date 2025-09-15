# ======================================================================
# --- File: tests/test_order_orchestration_service.py ---
# ======================================================================
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from model.order import Order
from model.messaging_models import OrderRequest
from model.status import StatusEnum
from service.order_service import OrderOrchestrationService
from producers.producers import EventProducer

# To make the test environment asynchronous
pytestmark = pytest.mark.asyncio

# ======================================================================
# --- Fixtures to Mock Dependencies ---
# ======================================================================

@pytest.fixture
def mock_order_repo():
    """Mocks the OrderRepository to simulate database interactions."""
    mock = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.save = AsyncMock()
    return mock

@pytest.fixture
def mock_kitchen_service():
    """Mocks the KitchenService."""
    mock = AsyncMock()
    mock.get_all_operational = AsyncMock()
    mock.increment_load = AsyncMock()
    mock.decrement_load = AsyncMock()
    return mock

@pytest.fixture
def mock_menu_service():
    """Mocks the MenuService."""
    mock = AsyncMock()
    mock.get_menu_item = AsyncMock()
    mock.decrement_item_quantity = AsyncMock()
    mock.increment_item_quantity = AsyncMock()
    return mock

@pytest.fixture
def mock_status_service():
    """Mocks the OrderStatusService."""
    mock = AsyncMock()
    mock.create_initial_status = AsyncMock()
    mock.update_status = AsyncMock()
    mock.get_by_id = AsyncMock()
    return mock

@pytest.fixture
def mock_event_producer():
    """Mocks the Kafka EventProducer."""
    mock = AsyncMock()
    mock.publish_acceptance_response = AsyncMock()
    mock.publish_status_update = AsyncMock()
    return mock

@pytest.fixture
def order_orchestration_service(
    mock_order_repo,
    mock_kitchen_service,
    mock_menu_service,
    mock_status_service,
    mock_event_producer,
):
    """
    Creates an instance of the OrderOrchestrationService
    with all its dependencies mocked.
    """
    return OrderOrchestrationService(
        order_repo=mock_order_repo,
        kitchen_service=mock_kitchen_service,
        menu_service=mock_menu_service,
        status_service=mock_status_service,
        event_producer=mock_event_producer,
    )


# ======================================================================
# --- Test Cases ---
# ======================================================================

async def test_handle_newly_assigned_order_success(
    order_orchestration_service,
    mock_order_repo,
    mock_kitchen_service,
    mock_menu_service,
    mock_status_service,
):
    """
    Tests successful handling of a new order:
    - Decrements menu item quantity.
    - Increments kitchen load.
    - Saves order and initial status.
    """
    # Arrange: Create a mock order and configure mock behavior
    assigned_order = Order(
        order_id=uuid.uuid4(),
        kitchen_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="123 Main St",
    )
    mock_menu_service.decrement_item_quantity.return_value = True
    mock_kitchen_service.increment_load.return_value = True

    # Act: Call the method being tested
    result = await order_orchestration_service.handle_newly_assigned_order(assigned_order)

    # Assert: Verify correct behavior
    assert result is True
    mock_menu_service.decrement_item_quantity.assert_called_once_with(
        assigned_order.kitchen_id, assigned_order.dish_id
    )
    mock_kitchen_service.increment_load.assert_called_once_with(assigned_order.kitchen_id)
    mock_order_repo.save.assert_called_once_with(assigned_order)
    mock_status_service.create_initial_status.assert_called_once_with(assigned_order)


async def test_handle_newly_assigned_order_rollback_on_load_failure(
    order_orchestration_service, mock_menu_service, mock_kitchen_service
):
    """
    Tests that if kitchen load fails to update, a rollback occurs
    on the menu item quantity.
    """
    # Arrange: Setup mock behavior to simulate a failure
    assigned_order = Order(
        order_id=uuid.uuid4(),
        kitchen_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="123 Main St",
    )
    mock_menu_service.decrement_item_quantity.return_value = True
    mock_kitchen_service.increment_load.return_value = False

    # Act
    result = await order_orchestration_service.handle_newly_assigned_order(assigned_order)

    # Assert
    assert result is False
    mock_menu_service.decrement_item_quantity.assert_called_once()
    mock_kitchen_service.increment_load.assert_called_once()
    mock_menu_service.increment_item_quantity.assert_called_once_with(
        assigned_order.kitchen_id, assigned_order.dish_id
    )

async def test_handle_order_status_update_ready_for_pickup(
    order_orchestration_service,
    mock_order_repo,
    mock_status_service,
    mock_kitchen_service,
    mock_event_producer,
):
    """
    Tests that a "ready for pickup" status update
    decrements kitchen load and publishes a status update.
    """
    # Arrange
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    mock_order = MagicMock()
    mock_order.kitchen_id = kitchen_id
    mock_order.dish_id = uuid.uuid4()
    mock_order_repo.get_by_id.return_value = mock_order

    mock_status_service.update_status.return_value = True
    mock_status_service.get_by_id.return_value = MagicMock()  # Mock the final status

    # Act
    result = await order_orchestration_service.handle_order_status_update(
        order_id, StatusEnum.READY_FOR_PICKUP
    )

    # Assert
    assert result is True
    mock_order_repo.get_by_id.assert_called_once_with(order_id)
    mock_status_service.update_status.assert_called_once_with(
        order_id, StatusEnum.READY_FOR_PICKUP
    )
    mock_kitchen_service.decrement_load.assert_called_once_with(kitchen_id)
    mock_event_producer.publish_status_update.assert_called_once()


async def test_check_availability_and_propose_finds_available_kitchen(
    order_orchestration_service, mock_kitchen_service, mock_menu_service, mock_event_producer
):
    """
    Tests that the service publishes an 'acceptance response'
    when a kitchen can handle the order.
    """
    # Arrange
    request = OrderRequest(
        order_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        kitchen_id=uuid.uuid4(), # This kitchen_id is just for the model
    )
    mock_kitchen_1 = MagicMock()
    mock_kitchen_1.kitchen_id = uuid.uuid4()
    mock_kitchen_2 = MagicMock()
    mock_kitchen_2.kitchen_id = uuid.uuid4()
    mock_kitchen_service.get_all_operational.return_value = [mock_kitchen_1, mock_kitchen_2]

    # Configure the first kitchen to be available
    mock_menu_item_1 = MagicMock()
    mock_menu_item_1.available_quantity = 5
    mock_menu_service.get_menu_item.side_effect = [mock_menu_item_1, None] # First kitchen is available, second is not

    # Act
    await order_orchestration_service.check_availability_and_propose(request)

    # Assert
    assert mock_event_producer.publish_acceptance_response.call_count == 2
    # Verify the response for the available kitchen
    mock_event_producer.publish_acceptance_response.assert_any_call(
        mock_kitchen_1.kitchen_id, request.order_id, True
    )
    # Verify the response for the unavailable kitchen
    mock_event_producer.publish_acceptance_response.assert_any_call(
        mock_kitchen_2.kitchen_id, request.order_id, False
    )