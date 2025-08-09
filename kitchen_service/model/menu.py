import uuid
from typing import List
from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    """
    Rappresenta un singolo piatto (item) nel menù.
    """
    dish_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    price: float = Field(gt=0)
    available_quantity: int

class Menu(BaseModel):
    """
    Rappresenta il menù completo di una specifica cucina.
    Contiene una lista di `MenuItem`.
    """
    kitchen_id: uuid.UUID # A quale cucina appartiene questo menù
    items: List[MenuItem]