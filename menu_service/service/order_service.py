import uuid

from sqlalchemy.orm import Session

from menu_service.model.order import Order
from menu_service.repository.order_repository import OrderRepository


class OrderService:
    def __init__(self, session: Session):
        self.session = session
        self.order_repo = OrderRepository(session)

    def new_order(self, dish_id: uuid.UUID, user_id: int) -> Order:
        """Create a new order for a user."""
        order = Order(dish_id=dish_id, user_id=user_id)
        return self.order_repo.add(order)

    def get_order_status(self, order_id: uuid.UUID, user_id: uuid.UUID) -> Order | None:
        """Get a specific order if it belongs to the user."""
        order = self.order_repo.get_by_id(order_id)
        if order and order.user_id == user_id:
            return order
        return None

    def get_my_orders(self, user_id: uuid.UUID) -> list[Order]:
        """Get all orders for a specific user."""
        all_orders = self.order_repo.get_all()
        return [order for order in all_orders if order.user_id == user_id]


# Factory function
def get_order_service(session: Session) -> OrderService:
    return OrderService(session)