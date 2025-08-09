import uuid
from pydantic import BaseModel, Field

# 1. Kitchen Availability
class KitchenAvailability(BaseModel):
    """
    Modello che rappresenta la disponibilità e il carico di una cucina.
    """
    kitchen_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    current_load: int = Field(default=0, ge=0)
    is_operational: bool = True
    max_load: int = Field(default=10, ge=0)  # Capacità massima della cucina
