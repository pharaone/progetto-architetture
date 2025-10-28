import uuid

from pydantic import BaseModel

from model.enum.order_status import OrderStatus


class OrderStatusMessage(BaseModel):
    order_id: uuid.UUID
    kitchen_id: uuid.UUID
    status: OrderStatus