import uuid
from typing import Optional

from pydantic import BaseModel, Field

from model.enum.order_status import OrderStatus


class OrderStatusMessage(BaseModel):
    order_id: uuid.UUID
    kitchen_id: Optional[uuid.UUID] = None  # Opzionale per compatibilità
    status: OrderStatus  # Pydantic convertirà automaticamente la stringa in enum
    
    class Config:
        use_enum_values = False  # Mantieni come enum internamente