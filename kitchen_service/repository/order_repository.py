import uuid
from typing import Dict, Optional
from model.order import Order

class OrderRepository:
    def __init__(self):
        # CORREZIONE: La chiave è uuid.UUID.
        self._orders: Dict[uuid.UUID, Order] = {}

    def save(self, order: Order) -> None:
        """Salva un ordine."""
        self._orders[order.order_id] = order

    def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        """Recupera un ordine."""
        return self._orders.get(order_id)