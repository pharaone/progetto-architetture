import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from routing_service.model.StatusEnum import StatusEnum


class OrderStatus(BaseModel):
    order_id: uuid.UUID
    kitchen_id: uuid.UUID
    status: StatusEnum
