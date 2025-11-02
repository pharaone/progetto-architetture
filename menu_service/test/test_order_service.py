import uuid
import pytest
from unittest.mock import MagicMock, patch

from service.order_service import OrderService
from model.order import Order
from model.enum.order_status import OrderStatus
from repository.order_repository import OrderRepository
from repository.user_repository import UserRepository
from model.user import User
from consumers.message.order_status_message import OrderStatusMessage


@pytest.fixture
def mock_order_repo():
    """Mock per OrderRepository."""
    repo = MagicMock(spec=OrderRepository)
    repo.get_all = MagicMock()
    repo.get_by_id = MagicMock()
    repo.add = MagicMock()
    repo.update = MagicMock()
    return repo


@pytest.fixture
def mock_user_repo():
    """Mock per UserRepository."""
    repo = MagicMock(spec=UserRepository)
    repo.get_by_id = MagicMock()
    return repo


@pytest.fixture
def order_service(mock_order_repo, mock_user_repo):
    """Istanza di OrderService con repository mockati."""
    return OrderService(mock_order_repo, mock_user_repo)


# ============================================================
# TEST: new_order
# ============================================================
def test_new_order_success(order_service, mock_order_repo, mock_user_repo):
    """Test creazione di un nuovo ordine."""
    dish_id = uuid.uuid4()
    user_id = uuid.uuid4()
    order_id = uuid.uuid4()
    
    expected_order = Order(
        id=order_id,
        dish_id=dish_id,
        user_id=user_id,
        status=OrderStatus.PENDING.value
    )
    expected_user = User(id=user_id, email="test@test.com", region="Centro")
    
    mock_order_repo.add.return_value = expected_order
    mock_user_repo.get_by_id.return_value = expected_user
    
    # Mock della chiamata HTTP al routing service (deve patchare dove viene importato, non dove è definito)
    with patch('service.order_service.start_order', return_value=None) as mock_start:
        result = order_service.new_order(dish_id, user_id)
    
    assert result == expected_order
    mock_order_repo.add.assert_called_once()
    mock_user_repo.get_by_id.assert_called_once_with(user_id)
    # Verifica che start_order sia stato chiamato
    mock_start.assert_called_once()


# ============================================================
# TEST: get_order_status
# ============================================================
def test_get_order_status_success(order_service, mock_order_repo):
    """Test recupero stato ordine dell'utente."""
    order_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    expected_order = Order(
        id=order_id,
        dish_id=uuid.uuid4(),
        user_id=user_id,
        status=OrderStatus.PREPARING.value
    )
    
    mock_order_repo.get_by_id.return_value = expected_order
    
    result = order_service.get_order_status(order_id, user_id)
    
    assert result == expected_order
    mock_order_repo.get_by_id.assert_called_once_with(order_id)


def test_get_order_status_wrong_user(order_service, mock_order_repo):
    """Test recupero ordine di un altro utente."""
    order_id = uuid.uuid4()
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    
    order = Order(
        id=order_id,
        dish_id=uuid.uuid4(),
        user_id=other_user_id,  # Altro utente
        status=OrderStatus.PREPARING.value
    )
    
    mock_order_repo.get_by_id.return_value = order
    
    result = order_service.get_order_status(order_id, user_id)
    
    assert result is None
    mock_order_repo.get_by_id.assert_called_once_with(order_id)


def test_get_order_status_not_found(order_service, mock_order_repo):
    """Test recupero ordine non esistente."""
    order_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_order_repo.get_by_id.return_value = None
    
    result = order_service.get_order_status(order_id, user_id)
    
    assert result is None
    mock_order_repo.get_by_id.assert_called_once_with(order_id)


# ============================================================
# TEST: get_my_orders
# ============================================================
def test_get_my_orders_success(order_service, mock_order_repo):
    """Test recupero di tutti gli ordini dell'utente."""
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    
    all_orders = [
        Order(id=uuid.uuid4(), dish_id=uuid.uuid4(), user_id=user_id, status="pending"),
        Order(id=uuid.uuid4(), dish_id=uuid.uuid4(), user_id=other_user_id, status="preparing"),
        Order(id=uuid.uuid4(), dish_id=uuid.uuid4(), user_id=user_id, status="completed"),
    ]
    
    mock_order_repo.get_all.return_value = all_orders
    
    result = order_service.get_my_orders(user_id)
    
    assert len(result) == 2
    assert all(order.user_id == user_id for order in result)
    mock_order_repo.get_all.assert_called_once()


def test_get_my_orders_empty(order_service, mock_order_repo):
    """Test recupero ordini quando l'utente non ne ha."""
    user_id = uuid.uuid4()
    mock_order_repo.get_all.return_value = []
    
    result = order_service.get_my_orders(user_id)
    
    assert result == []
    mock_order_repo.get_all.assert_called_once()


# ============================================================
# TEST: update_order_status
# ============================================================
def test_update_order_status_success(order_service, mock_order_repo):
    """Test aggiornamento stato ordine."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    
    existing_order = Order(
        id=order_id,
        dish_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status="pending"
    )
    updated_order = Order(
        id=order_id,
        dish_id=existing_order.dish_id,
        user_id=existing_order.user_id,
        status="preparing"
    )
    
    mock_order_repo.get_by_id.return_value = existing_order
    mock_order_repo.update.return_value = updated_order
    
    message = OrderStatusMessage(
        order_id=order_id,
        kitchen_id=kitchen_id,
        status=OrderStatus.PREPARING
    )
    
    result = order_service.update_order_status(message)
    
    assert result == updated_order
    mock_order_repo.get_by_id.assert_called_once_with(order_id)
    mock_order_repo.update.assert_called_once_with(order_id, status="preparing")


def test_update_order_status_not_found(order_service, mock_order_repo):
    """Test aggiornamento stato ordine non esistente."""
    order_id = uuid.uuid4()
    
    mock_order_repo.get_by_id.return_value = None
    
    message = OrderStatusMessage(
        order_id=order_id,
        status=OrderStatus.PREPARING
    )
    
    result = order_service.update_order_status(message)
    
    assert result is None
    mock_order_repo.get_by_id.assert_called_once_with(order_id)
    mock_order_repo.update.assert_not_called()


# ============================================================
# TEST: assign_order
# ============================================================
def test_assign_order_success(order_service, mock_order_repo):
    """Test assegnazione ordine a una cucina."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    
    updated_order = Order(
        id=order_id,
        dish_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        kitchen_id=kitchen_id,
        status="received"
    )
    
    mock_order_repo.update.return_value = updated_order
    
    result = order_service.assign_order(order_id, kitchen_id)
    
    assert result == updated_order
    mock_order_repo.update.assert_called_once_with(order_id, kitchen_id=kitchen_id)

