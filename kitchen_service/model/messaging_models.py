# ======================================================================
# --- 1. File: model/messaging_models.py ---
# ======================================================================
import uuid
from pydantic import BaseModel

class OrderRequest(BaseModel):
    """
    Modello per il messaggio di richiesta disponibilità (Fase 1).
    Inviato dal Dispatcher a tutte le cucine.
    """
    order_id: uuid.UUID
    dish_id: uuid.UUID

class StatusRequest(BaseModel):
    """
    Modello per il messaggio di richiesta stato (Fase 3).
    Inviato da un client esterno (es. app utente) per sapere lo stato di un ordine.
    """
    order_id: uuid.UUID