import uuid
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
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
    dish_id: Optional[uuid.UUID] = None  # ID del piatto da preparare (opzionale per retrocompatibilità)
    status: StatusEnum = StatusEnum.PENDING
    kitchen_id: Optional[uuid.UUID] = None  # Identifica quale cucina gestisce questo ordine (opzionale per retrocompatibilità)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Timestamp di creazione
