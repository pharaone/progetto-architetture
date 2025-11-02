import uuid
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from service.status_service import OrderStatusService
from model.order import Order
from model.status import StatusEnum, OrderStatus


@pytest_asyncio.fixture
def repo_mock():
    """Mock del repository degli stati (sincrono)."""
    return MagicMock()

@pytest_asyncio.fixture
def producer_mock():
    """Mock del producer (async)."""
    mock = MagicMock()
    mock.publish_status_update = AsyncMock()
    return mock

@pytest_asyncio.fixture
def kitchen_repo_mock():
    """Mock del kitchen repository."""
    return MagicMock()

@pytest_asyncio.fixture
def service(repo_mock, producer_mock, kitchen_repo_mock):
    """Istanza del service con i mock necessari."""
    return OrderStatusService(
        status_repo=repo_mock,
        producer=producer_mock,
        kitchen_repo=kitchen_repo_mock
    )


# ============================================================
# TEST: get_by_id
# ============================================================
@pytest.mark.asyncio
async def test_get_by_id_success(service, repo_mock):
    """Test recupero stato ordine esistente."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    expected_status = OrderStatus(
        order_id=order_id,
        status=StatusEnum.PREPARING,
        kitchen_id=kitchen_id
    )
    
    repo_mock.get_by_id.return_value = expected_status
    
    result = await service.get_by_id(order_id)
    
    assert result == expected_status
    repo_mock.get_by_id.assert_called_once_with(order_id)

@pytest.mark.asyncio
async def test_get_by_id_not_found(service, repo_mock):
    """Test recupero stato ordine non esistente."""
    order_id = uuid.uuid4()
    repo_mock.get_by_id.return_value = None
    
    result = await service.get_by_id(order_id)
    
    assert result is None
    repo_mock.get_by_id.assert_called_once_with(order_id)


# ============================================================
# TEST: update_status
# ============================================================
@pytest.mark.asyncio
async def test_update_status_success(service, repo_mock, producer_mock):
    """Test aggiornamento stato con successo."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    
    current_status = OrderStatus(order_id=order_id, status=StatusEnum.PENDING, kitchen_id=kitchen_id)
    updated_status = OrderStatus(order_id=order_id, status=StatusEnum.PREPARING, kitchen_id=kitchen_id)
    
    repo_mock.get_by_id.return_value = current_status
    repo_mock.update_status.return_value = updated_status

    result = await service.update_status(order_id, StatusEnum.PREPARING)

    assert result is True
    repo_mock.get_by_id.assert_called_once_with(order_id)
    repo_mock.update_status.assert_called_once_with(order_id, StatusEnum.PREPARING)
    producer_mock.publish_status_update.assert_awaited_once_with(updated_status)

@pytest.mark.asyncio
async def test_update_status_already_same(service, repo_mock):
    """Test aggiornamento stato quando è già quello desiderato."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    
    current_status = OrderStatus(order_id=order_id, status=StatusEnum.PREPARING, kitchen_id=kitchen_id)
    repo_mock.get_by_id.return_value = current_status

    result = await service.update_status(order_id, StatusEnum.PREPARING)

    assert result is False
    repo_mock.get_by_id.assert_called_once_with(order_id)
    repo_mock.update_status.assert_not_called()

@pytest.mark.asyncio
async def test_update_status_not_found(service, repo_mock):
    """Test aggiornamento stato ordine non esistente."""
    order_id = uuid.uuid4()
    repo_mock.get_by_id.return_value = None

    result = await service.update_status(order_id, StatusEnum.CANCELLED)

    assert result is False
    repo_mock.get_by_id.assert_called_once_with(order_id)
    repo_mock.update_status.assert_not_called()
