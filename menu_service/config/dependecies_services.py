from fastapi import Depends

from menu_service.repository.order_repository import OrderRepository
from menu_service.repository.user_repository import UserRepository
from menu_service.service.menu_service import MenuService
from menu_service.config.dependecies_repository import get_dish_repository, get_order_repository, get_user_repository
from menu_service.repository.dish_repository import DishRepository
from menu_service.service.order_service import OrderService
from menu_service.service.user_service import UserService


def get_menu_service(
        dish_repository: DishRepository = Depends(
            get_dish_repository),
):
    return MenuService(dish_repository)

def get_order_service(
        order_repository: OrderRepository = Depends(
            get_order_repository),
):
    return OrderService(order_repository)

def get_user_service(
        user_repository: UserRepository = Depends(
            get_user_repository),
):
    return UserService(user_repository)