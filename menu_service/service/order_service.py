import uuid

from consumers.message.order_status_message import OrderStatusMessage
from model.enum.order_status import OrderStatus
from model.order import Order
from producers.kafka_producer import EventProducer
from repository.order_repository import OrderRepository

from api.clients.routing_service_client import start_order
from repository.user_repository import UserRepository


class OrderService:
    def __init__(self, order_repo : OrderRepository,
                 user_repo : UserRepository):
        self.order_repo = order_repo
        self.user_repo = user_repo

    def new_order(self, dish_id: uuid.UUID, user_id: uuid.UUID) -> Order:
        """Create a new order for a user."""
        order = Order(dish_id=dish_id, user_id=user_id, status=OrderStatus.PENDING.value)
        order = self.order_repo.add(order)
        user = self.user_repo.get_by_id(user_id)
        start_order(user.region,order.id, user_id)
        return order

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

    def assign_order(self, order_id: uuid.UUID, kitchen_id: uuid.UUID) -> Order:
        order = self.order_repo.get_by_id(order_id)
        order.kitchen_id = kitchen_id
        return self.order_repo.update(order)

    def update_order_status(self, order_status_message: OrderStatusMessage):
        order = self.order_repo.get_by_id(order_status_message.order_id)
        order.status = order_status_message.status
        return self.order_repo.update(order)
