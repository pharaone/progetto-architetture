import uuid
import pytest
from unittest.mock import MagicMock

from service.menu_service import MenuService
from model.dish import Dish
from repository.dish_repository import DishRepository


@pytest.fixture
def mock_dish_repo():
    """Mock per DishRepository."""
    repo = MagicMock(spec=DishRepository)
    repo.get_all = MagicMock()
    repo.get_by_id = MagicMock()
    repo.add = MagicMock()
    repo.update = MagicMock()
    repo.delete = MagicMock()
    return repo


@pytest.fixture
def menu_service(mock_dish_repo):
    """Istanza di MenuService con repository mockato."""
    return MenuService(mock_dish_repo)


# ============================================================
# TEST: get_menu
# ============================================================
def test_get_menu_success(menu_service, mock_dish_repo):
    """Test recupero di tutti i piatti."""
    expected_dishes = [
        Dish(id=uuid.uuid4(), name="Pizza", price=10.50, description="Pizza margherita"),
        Dish(id=uuid.uuid4(), name="Pasta", price=8.00, description="Pasta al pomodoro"),
    ]
    
    mock_dish_repo.get_all.return_value = expected_dishes
    
    result = menu_service.get_menu()
    
    assert result == expected_dishes
    mock_dish_repo.get_all.assert_called_once()


def test_get_menu_empty(menu_service, mock_dish_repo):
    """Test recupero menu vuoto."""
    mock_dish_repo.get_all.return_value = []
    
    result = menu_service.get_menu()
    
    assert result == []
    mock_dish_repo.get_all.assert_called_once()


# ============================================================
# TEST: get_dish
# ============================================================
def test_get_dish_success(menu_service, mock_dish_repo):
    """Test recupero di un piatto specifico."""
    dish_id = uuid.uuid4()
    expected_dish = Dish(id=dish_id, name="Pizza", price=10.50, description="Pizza margherita")
    
    mock_dish_repo.get_by_id.return_value = expected_dish
    
    result = menu_service.get_dish(dish_id)
    
    assert result == expected_dish
    mock_dish_repo.get_by_id.assert_called_once_with(dish_id)


def test_get_dish_not_found(menu_service, mock_dish_repo):
    """Test recupero di un piatto non esistente."""
    dish_id = uuid.uuid4()
    mock_dish_repo.get_by_id.return_value = None
    
    result = menu_service.get_dish(dish_id)
    
    assert result is None
    mock_dish_repo.get_by_id.assert_called_once_with(dish_id)


# ============================================================
# TEST: new_dish
# ============================================================
def test_new_dish_success(menu_service, mock_dish_repo):
    """Test creazione di un nuovo piatto."""
    name = "Tiramisù"
    price = 6.00
    description = "Dolce italiano"
    expected_dish = Dish(id=uuid.uuid4(), name=name, price=price, description=description)
    
    mock_dish_repo.add.return_value = expected_dish
    
    result = menu_service.new_dish(name, price, description)
    
    assert result == expected_dish
    mock_dish_repo.add.assert_called_once()

