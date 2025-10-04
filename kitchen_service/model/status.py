import uuid
from enum import Enum
from pydantic import BaseModel, Field

class StatusEnum(str, Enum):
    """Stati possibili di un ordine."""
    PENDING = "pending"
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
    status: StatusEnum = StatusEnum.PENDING
