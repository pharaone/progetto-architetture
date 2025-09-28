import uuid

from pydantic import BaseModel

from menu_service.model.enum.order_status import OrderStatus


class OrderStatusMessage(BaseModel):
    order_id: uuid.UUID
    status: OrderStatus