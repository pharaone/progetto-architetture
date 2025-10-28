import uuid
from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    """
    Rappresenta un singolo piatto (item) nel menù.
    """
    dish_id: uuid.UUID 
    name: str
    price: float = Field(gt=0)
    available_quantity: int
