import uuid

from pydantic import BaseModel


class AcceptanceResponse(BaseModel):
    kitchen_id: uuid.UUID
    order_id: uuid.UUID
    can_handle: bool = True