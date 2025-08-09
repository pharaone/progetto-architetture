import uuid
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

class StatusEnum(str, Enum):
    """Stati possibili di un ordine."""
    RECEIVED = "received"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderStatus(BaseModel):
    """
    Modello separato per tracciare lo stato di un ordine in una cucina.
    """
    order_id: uuid.UUID # Per collegarlo al modello Order
    kitchen_id: uuid.UUID # Per sapere quale cucina lo sta gestendo
    status: StatusEnum = StatusEnum.RECEIVED
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
