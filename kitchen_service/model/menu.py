import uuid
from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    """
    Rappresenta un singolo piatto (item) nel menù.
    """
    dish_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    price: float = Field(gt=0)
    available_quantity: int
