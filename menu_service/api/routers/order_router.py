import uuid

from fastapi import APIRouter, Depends

from config.dependecies_services import get_order_service
from service.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["menu"])

@router.post("/new_order")
async def new_order(
    dish_id: uuid.UUID,
    user_id: int,
    order_service: OrderService = Depends(get_order_service)
):
    return order_service.new_order(dish_id, user_id)

@router.post("/get_order_status")
async def get_order_status(
    order_id: uuid.UUID,
    user_id: uuid.UUID,
    order_service: OrderService = Depends(get_order_service)
):
    return order_service.get_order_status(order_id, user_id)

@router.post("/get_order_status")
async def get_my_orders(
    user_id: uuid.UUID,
    order_service: OrderService = Depends(get_order_service)
):
    return order_service.get_my_orders(user_id)

