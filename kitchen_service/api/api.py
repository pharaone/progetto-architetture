import uuid
from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from pydantic import BaseModel, Field, conint, confloat

# Importa modelli di dominio
from model.kitchen import KitchenAvailability
from model.menu import MenuItem
from model.messaging_models import OrderRequest
from model.order import Order
from model.status import OrderStatus, StatusEnum

# Tiping dei servizi (usati solo come hint nelle dipendenze)
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.order_service import OrderOrchestrationService
from service.status_service import OrderStatusService

router = APIRouter()


# -------------------------
# Dependency injection
# -------------------------
def get_kitchen_service(request: Request) -> KitchenService:
    return request.app.state.kitchen_service

def get_menu_service(request: Request) -> MenuService:
    return request.app.state.menu_service

def get_orchestrator(request: Request) -> OrderOrchestrationService:
    return request.app.state.orchestration_service

def get_status_service(request: Request) -> OrderStatusService:
    return request.app.state.status_service

def get_kitchen_id(request: Request) -> uuid.UUID:
    return request.app.state.kitchen_id

async def verify_api_key(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
    """Verifica che la API key fornita nell'header sia valida."""
    # use constant-time comparison if you later move to hmac.compare_digest
    if x_api_key != request.app.state.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid API Key"
        )

# -------------------------
# Pydantic models per request body
# -------------------------
class QuantityUpdateRequest(BaseModel):
    available_quantity: int

class StatusUpdateRequest(BaseModel):
    status: StatusEnum

class MenuItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    available_quantity: Optional[int] = None

# -------------------------
# Endpoints (usano @router.*)
# -------------------------

# --- Kitchen Endpoints ---
@router.get("/kitchen", response_model=KitchenAvailability)
async def get_kitchen_status(
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    kitchen_service: KitchenService = Depends(get_kitchen_service)
):
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
    success = await kitchen_service.set_operational_status(kitchen_id, is_operational)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impossibile aggiornare lo stato della cucina.")
    return {"message": "Stato cucina aggiornato con successo."}

# --- Menu Endpoints ---
@router.get("/menu/dishes", response_model=List[MenuItem])
async def get_all_dishes(
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    menu = await menu_service.get_menu(kitchen_id)
    return menu.items if menu and menu.items else []

@router.get("/menu/dishes/{dish_id}", response_model=MenuItem)
async def get_dish_detail(
    dish_id: uuid.UUID,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    item = await menu_service.get_menu_item(kitchen_id, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    return item

@router.post("/menu/dishes", status_code=status.HTTP_201_CREATED, response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def create_menu_item(
    dish: MenuItem,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    success = await menu_service.create_menu_item(kitchen_id, dish)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creazione piatto fallita.")
    return dish

@router.patch("/menu/dishes/{dish_id}/quantity", response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def update_dish_quantity(
    dish_id: uuid.UUID,
    request: QuantityUpdateRequest,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    item = await menu_service.get_menu_item(kitchen_id, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    item.available_quantity = request.available_quantity
    await menu_service.update_menu_item(kitchen_id, item)
    return item

@router.patch("/menu/dishes/{dish_id}", response_model=MenuItem, dependencies=[Depends(verify_api_key)])
async def update_menu_item_details(
    dish_id: uuid.UUID,
    request: MenuItemUpdateRequest,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    item = await menu_service.get_menu_item(kitchen_id, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    
    update_data = request.model_dump(exclude_unset=True)
    # Nota: qui potresti aggiungere autorizzazione field-level, es. bloccare "price" ai ruoli non consentiti.
    updated_item = item.model_copy(update=update_data)

    await menu_service.update_menu_item(kitchen_id, updated_item)
    return updated_item

@router.delete("/menu/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_menu_item(
    dish_id: uuid.UUID,
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    menu_service: MenuService = Depends(get_menu_service)
):
    success = await menu_service.delete_menu_item(kitchen_id, dish_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato o impossibile da eliminare.")
    return

# --- Orders Endpoints ---
@router.get("/orders", response_model=List[OrderStatus])
async def get_active_orders(
    kitchen_id: uuid.UUID = Depends(get_kitchen_id),
    status_service: OrderStatusService = Depends(get_status_service)
):
    return await status_service.get_all_active_orders_by_kitchen(kitchen_id)

@router.get("/orders/{order_id}", response_model=Order)
async def get_order_detail(
    order_id: uuid.UUID, 
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    order = await orchestrator.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine non trovato.")
    return order

@router.post("/user/orders", status_code=status.HTTP_201_CREATED, response_model=Order)
async def create_user_order(
    order_request: OrderRequest, 
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    """Endpoint pubblico per un cliente finale per effettuare un ordine."""
    saved_order = await orchestrator.create_order_from_user(order_request)
    if not saved_order:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="La creazione dell'ordine è fallita.")
    return saved_order

@router.post("/orders", status_code=status.HTTP_201_CREATED, response_model=Order, dependencies=[Depends(verify_api_key)])
async def create_order_internal(
    order: Order, 
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    """Endpoint interno per registrare un ordine già assegnato a questa cucina."""
    success = await orchestrator.handle_newly_assigned_order(order)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creazione ordine fallita.")
    return order

@router.post("/orders/proposals", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_api_key)])
async def propose_order(
    request: OrderRequest, 
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    """Endpoint interno per candidare la cucina a un ordine."""
    await orchestrator.check_availability_and_propose(request)
    return {"message": "Richiesta di candidatura inviata con successo."}

@router.patch("/orders/{order_id}/status", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_api_key)])
async def update_order_status(
    order_id: uuid.UUID,
    request: StatusUpdateRequest,
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    """Endpoint interno per aggiornare lo stato di un ordine."""
    success = await orchestrator.handle_order_status_update(order_id, request.status)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine non trovato o aggiornamento fallito.")
    return {"message": "Richiesta di aggiornamento stato accettata."}
