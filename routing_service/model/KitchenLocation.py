import uuid

from pydantic import BaseModel

class KitchenLocation(BaseModel):
    kitchen_id: uuid.UUID
    neighborhood: str