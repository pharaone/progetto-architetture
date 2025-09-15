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
    repo.add_menu_item = mock.MagicMock()  # New method
    repo.delete_menu_item = mock.MagicMock()  # New method
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
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    
    expected_item = MenuItem(dish_id=dish_id, name="Pizza", available_quantity=10, price=12.50)
    
    # Correction: The mock should return the MenuItem instance, as the service expects this.
    mock_menu_repo.get_menu_item.return_value = expected_item
    
    result = await menu_service.get_menu_item(kitchen_id, dish_id)
    
    assert result == expected_item
    mock_menu_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_get_menu_item_not_found(menu_service, mock_menu_repo):
    """Verifica che la funzione ritorni None se il piatto non esiste."""
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    
    mock_menu_repo.get_menu_item.return_value = None
    
    result = await menu_service.get_menu_item(kitchen_id, dish_id)
    
    assert result is None
    mock_menu_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)

# --- Test per is_dish_available (CORRETTI) ---

@pytest.mark.asyncio
async def test_is_dish_available_true(menu_service, mock_menu_repo):
    """Verifica che un piatto con quantità > 0 sia disponibile."""
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    
    dish_item = MenuItem(dish_id=dish_id, name="Pasta", available_quantity=5, price=9.00)
    mock_menu_repo.get_menu_item.return_value = dish_item
    
    result = await menu_service.is_dish_available(kitchen_id, dish_id)
    
    assert result is True
    mock_menu_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_is_dish_available_zero_quantity(menu_service, mock_menu_repo):
    """Verifica che un piatto con quantità = 0 non sia disponibile."""
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    
    dish_item = MenuItem(dish_id=dish_id, name="Lasagna", available_quantity=0, price=10.00)
    mock_menu_repo.get_menu_item.return_value = dish_item

    result = await menu_service.is_dish_available(kitchen_id, dish_id)

    assert result is False
    mock_menu_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_is_dish_available_not_found(menu_service, mock_menu_repo):
    """Verifica che la funzione ritorni False se il piatto non esiste."""
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    
    mock_menu_repo.get_menu_item.return_value = None
    
    result = await menu_service.is_dish_available(kitchen_id, dish_id)
    
    assert result is False
    mock_menu_repo.get_menu_item.assert_called_once_with(kitchen_id, dish_id)

# --- Nuovi Test Aggiunti ---

@pytest.mark.asyncio
async def test_add_menu_item_success(menu_service, mock_menu_repo):
    """Verifica che l'aggiunta di un piatto chiami il metodo del repository."""
    kitchen_id = uuid.uuid4()
    new_dish = MenuItem(dish_id=uuid.uuid4(), name="Tiramisù", available_quantity=20, price=7.50)

    # In questo test, verifichiamo solo che il metodo del repository venga chiamato.
    # Non è necessario un valore di ritorno specifico.
    await menu_service.add_menu_item(kitchen_id, new_dish)

    mock_menu_repo.add_menu_item.assert_called_once_with(kitchen_id, new_dish)

@pytest.mark.asyncio
async def test_delete_menu_item_success(menu_service, mock_menu_repo):
    """Verifica che l'eliminazione di un piatto chiami il metodo del repository."""
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()

    await menu_service.delete_menu_item(kitchen_id, dish_id)

    mock_menu_repo.delete_menu_item.assert_called_once_with(kitchen_id, dish_id)

# --- Test per commit_order_dish e restock_item (invariati ma ora funzionanti) ---

@pytest.mark.asyncio
async def test_commit_order_dish_success(menu_service, mock_menu_repo):
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = 5
    result = await menu_service.commit_order_dish(kitchen_id, dish_id)
    assert result is True
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_commit_order_dish_not_found(menu_service, mock_menu_repo):
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = -1
    result = await menu_service.commit_order_dish(kitchen_id, dish_id)
    assert result is False
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_commit_order_dish_out_of_stock(menu_service, mock_menu_repo):
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    mock_menu_repo.atomic_decrement_quantity.return_value = -3
    result = await menu_service.commit_order_dish(kitchen_id, dish_id)
    assert result is False
    mock_menu_repo.atomic_decrement_quantity.assert_called_once_with(kitchen_id, dish_id)

@pytest.mark.asyncio
async def test_restock_item_success(menu_service, mock_menu_repo):
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    restock_amount = 5
    mock_menu_repo.atomic_increment_quantity.return_value = 15
    result = await menu_service.restock_item(kitchen_id, dish_id, restock_amount)
    assert result is True
    mock_menu_repo.atomic_increment_quantity.assert_called_once_with(
        kitchen_id, dish_id, restock_amount
    )

@pytest.mark.asyncio
async def test_restock_item_failure(menu_service, mock_menu_repo):
    kitchen_id = uuid.uuid4()
    dish_id = uuid.uuid4()
    restock_amount = 5
    mock_menu_repo.atomic_increment_quantity.return_value = -1
    result = await menu_service.restock_item(kitchen_id, dish_id, restock_amount)
    assert result is False
    mock_menu_repo.atomic_increment_quantity.assert_called_once_with(
        kitchen_id, dish_id, restock_amount
    )