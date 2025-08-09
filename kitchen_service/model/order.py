import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Order(BaseModel):
    """
    Modello che contiene i dati primari di un ordine,
    con la regola di un solo piatto per ordine.
    """
    order_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    kitchen_id: uuid.UUID
    customer_id: uuid.UUID
    dish_id: uuid.UUID
    delivery_address: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
