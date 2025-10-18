import uuid

from fastapi import APIRouter, Form, Depends

from config.dependecies_services import get_menu_service, get_order_service
from service.menu_service import MenuService
from service.order_service import OrderService

router = APIRouter(prefix="/internal_router", tags=["internal_router"])

@router.post("/order_assigned")
async def order_assigned(
    order_id: uuid.UUID = Form(...),
    kitchen_id: uuid.UUID = Form(...),
    order_service: OrderService = Depends(get_order_service)
):
    return order_service.assign_order(order_id, kitchen_id)