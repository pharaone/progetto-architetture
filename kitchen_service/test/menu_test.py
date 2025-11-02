import uuid
import pytest
from unittest import mock
from service.menu_service import MenuService
from model.menu import MenuItem
from repository.menu_repository import MenuRepository

# --- Fixture per l'impostazione dei test ---

@pytest.fixture
def mock_menu_repo():
    """Crea un mock per MenuRepository."""
    repo = mock.MagicMock(spec=MenuRepository)
    repo.get_menu_item = mock.MagicMock()
    repo.get_dish_quantity = mock.MagicMock()
    repo.create_menu_item = mock.MagicMock()
    repo.delete_menu_item = mock.MagicMock()
    repo.atomic_decrement_quantity = mock.MagicMock()
    repo.atomic_increment_quantity = mock.MagicMock()
    return repo

@pytest.fixture
def menu_service(mock_menu_repo):
    """Crea un'istanza di MenuService con il repository mockato."""
    return MenuService(mock_menu_repo)

# --- Test per get_menu_item ---

@pytest.mark.asyncio
async def test_get_menu_item_success(menu_service, mock_menu_repo):
    """Verifica che la funzione recuperi un piatto esistente."""
    dish_id = uuid.uuid4()
    
    expected_item = MenuItem(dish_id=dish_id, name="Pizza", available_quantity=10, price=12.50)
    
    mock_menu_repo.get_menu_item.return_value = expected_item
    
    result = await menu_service.get_menu_item(dish_id)
    
    assert result == expected_item
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_get_menu_item_not_found(menu_service, mock_menu_repo):
    """Verifica che la funzione ritorni None se il piatto non esiste."""
    dish_id = uuid.uuid4()
    
    mock_menu_repo.get_menu_item.return_value = None
    
    result = await menu_service.get_menu_item(dish_id)
    
    assert result is None
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)

# --- Test per is_dish_available (CORRETTI) ---

@pytest.mark.asyncio
async def test_is_dish_available_true(menu_service, mock_menu_repo):
    """Verifica che un piatto con quantità > 0 sia disponibile."""
    dish_id = uuid.uuid4()
    
    dish_item = MenuItem(dish_id=dish_id, name="Pizza", available_quantity=5, price=9.00)
    mock_menu_repo.get_menu_item.return_value = dish_item
    
    result = await menu_service.is_dish_available(dish_id)
    
    assert result is True
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_is_dish_available_zero_quantity(menu_service, mock_menu_repo):
    """Verifica che un piatto con quantità = 0 non sia disponibile."""
    dish_id = uuid.uuid4()
    
    dish_item = MenuItem(dish_id=dish_id, name="Pizza", available_quantity=0, price=9.00)
    mock_menu_repo.get_menu_item.return_value = dish_item

    result = await menu_service.is_dish_available(dish_id)

    assert result is False
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_is_dish_available_not_found(menu_service, mock_menu_repo):
    """Verifica che la funzione ritorni False se il piatto non esiste."""
    dish_id = uuid.uuid4()
    
    mock_menu_repo.get_menu_item.return_value = None
    
    result = await menu_service.is_dish_available(dish_id)
    
    assert result is False
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)

# --- Nuovi Test Aggiunti ---

@pytest.mark.asyncio
async def test_create_menu_item_success(menu_service, mock_menu_repo):
    """Verifica che la creazione di un piatto chiami il metodo del repository."""
    new_dish = MenuItem(dish_id=uuid.uuid4(), name="Tiramisù", available_quantity=20, price=7.50)
    
    # Il metodo prima verifica se il piatto esiste
    mock_menu_repo.get_menu_item.return_value = None  # Non esiste
    mock_menu_repo.create_menu_item.return_value = None  # Il metodo create non ha return value

    result = await menu_service.create_menu_item(new_dish)

    assert result is True
    mock_menu_repo.get_menu_item.assert_called_once_with(new_dish.dish_id)
    mock_menu_repo.create_menu_item.assert_called_once_with(new_dish)

@pytest.mark.asyncio
async def test_delete_menu_item_success(menu_service, mock_menu_repo):
    """Verifica che l'eliminazione di un piatto chiami il metodo del repository."""
    dish_id = uuid.uuid4()
    existing_dish = MenuItem(dish_id=dish_id, name="Pizza", available_quantity=5, price=9.00)
    
    mock_menu_repo.get_menu_item.return_value = existing_dish  # Il piatto esiste
    mock_menu_repo.delete_menu_item.return_value = True

    result = await menu_service.delete_menu_item(dish_id)

    assert result is True
    mock_menu_repo.get_menu_item.assert_called_once_with(dish_id)
    mock_menu_repo.delete_menu_item.assert_called_once_with(dish_id)

# --- Test per commit_order_dish e restock_item (invariati ma ora funzionanti) ---

@pytest.mark.asyncio
async def test_commit_order_dish_success(menu_service, mock_menu_repo):
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = 5
    result = await menu_service.commit_order_dish(dish_id)
    assert result is True
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_commit_order_dish_not_found(menu_service, mock_menu_repo):
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = -1
    result = await menu_service.commit_order_dish(dish_id)
    assert result is False
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_commit_order_dish_out_of_stock(menu_service, mock_menu_repo):
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = -3
    result = await menu_service.commit_order_dish(dish_id)
    assert result is False
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(dish_id)

@pytest.mark.asyncio
async def test_restock_item_success(menu_service, mock_menu_repo):
    dish_id = uuid.uuid4()
    restock_amount = 5
    mock_menu_repo.atomic_increment_quantity.return_value = 15
    result = await menu_service.restock_item(dish_id, restock_amount)
    assert result is True
    mock_menu_repo.atomic_increment_quantity.assert_called_once_with(
        dish_id, restock_amount
    )

@pytest.mark.asyncio
async def test_restock_item_failure(menu_service, mock_menu_repo):
    dish_id = uuid.uuid4()
    restock_amount = 5
    mock_menu_repo.atomic_increment_quantity.return_value = -1
    result = await menu_service.restock_item(dish_id, restock_amount)
    assert result is False
    mock_menu_repo.atomic_increment_quantity.assert_called_once_with(
        dish_id, restock_amount
    )