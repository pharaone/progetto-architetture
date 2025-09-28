import uuid

from pydantic import BaseModel


class OrderRequest(BaseModel):
    order_id: uuid.UUID
    dish_id: uuid.UUI