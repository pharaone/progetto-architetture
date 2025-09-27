import uuid
from sqlalchemy.orm import Session

from menu_service.model.dish import Dish
from menu_service.repository.dish_repository import DishRepository


class MenuService:
    def __init__(self, session: Session):
        self.session = session
        self.dish_repo = DishRepository(session)

    def get_menu(self) -> list[Dish]:
        """Return all dishes in the menu."""
        return self.dish_repo.get_all()

    def new_dish(self, name: str, price: float, description: str) -> Dish:
        """Create a new dish."""
        dish = Dish(name=name, price=price, description=description)
        return self.dish_repo.add(dish)

    def get_dish(self, dish_id: uuid.UUID) -> Dish | None:
        """Retrieve a single dish by its ID."""
        return self.dish_repo.get_by_id(dish_id)


def get_menu_service(session: Session) -> MenuService:
    return MenuService(session)
