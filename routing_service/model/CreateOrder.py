import uuid
from pydantic import BaseModel, Field

class CreateOrder(BaseModel):
    """
    Payload atteso dal client del microservizio MENU:
    - user_region: quartiere utente
    - order_id: UUID
    - dish_id: UUID
    """
    user_region: str = Field(..., description="Quartiere in cui si trova l'utente")
    order_id: uuid.UUID
    dish_id: uuid.UUID
