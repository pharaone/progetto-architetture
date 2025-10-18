import uuid

from fastapi import APIRouter, Depends, Form

from config.dependecies_services import get_menu_service
from service.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["menu"])

@router.post("/new_dish")
async def new_dish(
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    menu_service: MenuService = Depends(get_menu_service)
):
    return menu_service.new_dish(name, price, description)

@router.get("/get_dish")
async def get_dish(
    dish_id: uuid.UUID,
    menu_service: MenuService = Depends(get_menu_service)
):
    return menu_service.get_dish(dish_id)

@router.get("/get_menu")
async def get_menu(
    menu_service: MenuService = Depends(get_menu_service)
):
    return menu_service.get_menu()

