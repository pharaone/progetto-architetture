import uuid
import pytest
import pytest_asyncio
from unittest.mock import MagicMock

from service.status_service import OrderStatusService
from model.order import Order
from model.status import StatusEnum, OrderStatus


@pytest_asyncio.fixture
def repo_mock():
    """Mock del repository degli stati (sincrono)."""
    return MagicMock()


@pytest_asyncio.fixture
def service(repo_mock):
    """Istanza del service con il repo mockato."""
    return OrderStatusService(status_repo=repo_mock)


# ============================================================
# TEST: create_initial_status
# ============================================================
@pytest.mark.asyncio
async def test_create_initial_status_success(service, repo_mock):
    order = Order(
        kitchen_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="Via Roma",
    )

    repo_mock.save.return_value = None  # mock del metodo sincrono

    status = await service.create_initial_status(order)

    assert isinstance(status, OrderStatus)
    assert status.order_id == order.order_id
    assert status.kitchen_id == order.kitchen_id
    assert status.status == StatusEnum.RECEIVED
    repo_mock.save.assert_called_once_with(status)


@pytest.mark.asyncio
async def test_create_initial_status_no_kitchen(service, repo_mock):
    # Qui kitchen_id è opzionale solo se lo hai definito così nel modello Order
    # Se è obbligatorio, serve una classe fittizia
    class FakeOrder:
        def __init__(self):
            self.order_id = uuid.uuid4()
            self.kitchen_id = None

    order = FakeOrder()
    result = await service.create_initial_status(order)

    assert result is None
    repo_mock.save.assert_not_called()


# ============================================================
# TEST: update_status
# ============================================================
@pytest.mark.asyncio
async def test_update_status_success(service, repo_mock):
    order_id = uuid.uuid4()
    repo_mock.update_status.return_value = True

    result = await service.update_status(order_id, StatusEnum.PREPARING)

    assert result is True
    repo_mock.update_status.assert_called_once_with(order_id, StatusEnum.PREPARING)


@pytest.mark.asyncio
async def test_update_status_fail(service, repo_mock):
    order_id = uuid.uuid4()
    repo_mock.update_status.return_value = False

    result = await service.update_status(order_id, StatusEnum.CANCELLED)

    assert result is False
    repo_mock.update_status.assert_called_once_with(order_id, StatusEnum.CANCELLED)
