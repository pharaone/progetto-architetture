import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from pydantic import BaseModel
# Importa modelli di dominio
from model.kitchen import KitchenAvailability
from model.menu import MenuItem # MenuItem serve ancora come modello di risposta!
from model.status import StatusEnum

# Tiping dei servizi (usati solo come hint nelle dipendenze)
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.status_service import OrderStatusService

router = APIRouter()


# -------------------------
# Dependency injection (INVARIATO)
# -------------------------
def get_kitchen_service(request: Request) -> KitchenService:
    return request.app.state.kitchen_service

def get_menu_service(request: Request) -> MenuService:
    return request.app.state.menu_service

def get_status_service(request: Request) -> OrderStatusService:
    return request.app.state.status_service

def get_kitchen_id(request: Request) -> uuid.UUID:
    return request.app.state.kitchen_id

async def verify_api_key(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
    """Verifica che la API key fornita nell'header sia valida."""
    if x_api_key != request.app.state.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid API Key"
        )

# -------------------------
# Pydantic models per request body (AGGIUNTO MenuItemCreate)
# -------------------------

# --- NUOVO MODELLO PER LA CREAZIONE ---
class MenuItemCreate(BaseModel):
    """Modello per la creazione di un nuovo piatto (dati richiesti dal client)."""
    dish_id: uuid.UUID
    name: str
    price: float
    available_quantity: int
# --- FINE NUOVO MODELLO ---

class QuantityUpdateRequest(BaseModel):
    available_quantity: int

class StatusUpdateRequest(BaseModel):
    status: StatusEnum

class MenuItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    available_quantity: Optional[int] = None

# -------------------------
# Endpoints (INVARIATO, TRANNE create_menu_item)
# -------------------------

# --- Kitchen Endpoints ---
@router.get("/kitchen", response_model=KitchenAvailability)
async def get_kitchen_status(
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    kitchen_service: KitchenService = Depends(get_kitchen_service)
):
    # ... (codice invariato)
    kitchen_state = await kitchen_service.get_by_id(kitchen_id)
    if not kitchen_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stato cucina non trovato.")
    return kitchen_state


@router.patch("/kitchen", dependencies=[Depends(verify_api_key)])
async def update_kitchen_status(
    is_operational: bool,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    kitchen_service: KitchenService = Depends(get_kitchen_service)
):
    # ... (codice invariato)
    success = await kitchen_service.set_operational_status(kitchen_id, is_operational)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impossibile aggiornare lo stato della cucina.")
    return {"message": "Stato cucina aggiornato con successo."}

# --- Menu Endpoints ---
@router.get("/menu/dishes/{dish_id}", response_model=MenuItem)
async def get_dish_detail(
    dish_id: uuid.UUID,
    menu_service: MenuService = Depends(get_menu_service)
):
    # ... (codice invariato)
    item = await menu_service.get_menu_item(dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    return item


# --- FUNZIONE MODIFICATA ---
@router.post("/menu/dishes", status_code=status.HTTP_201_CREATED, response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def create_menu_item(
    # 1. Usa il nuovo modello per i dati in ingresso
    dish_data: MenuItemCreate,
    menu_service: MenuService = Depends(get_menu_service)
):

    # 3. Crea l'oggetto MenuItem completo combinando l'ID e i dati ricevuti
    full_dish = MenuItem(
        dish_id=dish_data.dish_id,
        name=dish_data.name,
        price=dish_data.price,
        available_quantity=dish_data.available_quantity
    )

       # Aggiungi questo print per vedere cosa viene passato al servizio
    print(f"DEBUG API: Chiamando menu_service.create_menu_item con: {full_dish}")

    # 4. Passa l'oggetto completo al servizio per salvarlo
    success = await menu_service.create_menu_item(full_dish)

    # Aggiungi questo print per vedere cosa restituisce il servizio
    print(f"DEBUG API: menu_service.create_menu_item ha restituito: {success}")
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creazione piatto fallita. Potrebbe già esistere.")

    # 5. Restituisci l'oggetto completo con il nuovo ID
    return full_dish
# --- FINE FUNZIONE MODIFICata ---


@router.patch("/menu/dishes/{dish_id}/quantity", response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def update_dish_quantity(
    dish_id: uuid.UUID,
    request: QuantityUpdateRequest,
    menu_service: MenuService = Depends(get_menu_service)
):
    # ... (codice invariato)
    item = await menu_service.get_menu_item(dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    item.available_quantity = request.available_quantity
    await menu_service.update_menu_item(item)
    return item

@router.patch("/menu/dishes/{dish_id}", response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def update_menu_item_details(
    dish_id: uuid.UUID,
    request: MenuItemUpdateRequest,
    menu_service: MenuService = Depends(get_menu_service)
):
    # ... (codice invariato)
    item = await menu_service.get_menu_item(dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    
    update_data = request.model_dump(exclude_unset=True)
    updated_item = item.model_copy(update=update_data)

    await menu_service.update_menu_item(updated_item)
    return updated_item

@router.delete("/menu/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_menu_item(
    dish_id: uuid.UUID,
    menu_service: MenuService = Depends(get_menu_service)
):
    # ... (codice invariato)
    success = await menu_service.delete_menu_item(dish_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato o impossibile da eliminare.")
    return