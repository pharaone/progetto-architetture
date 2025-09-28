import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Order(BaseModel):

    order_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    kitchen_id: Optional[uuid.UUID] = None
    customer_id: uuid.UUID
    dish_id: uuid.UUID
    delivery_address: str
    user_neighborhood: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))