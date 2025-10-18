from fastapi import Depends

from repository.order_repository import OrderRepository
from repository.user_repository import UserRepository
from service.menu_service import MenuService
from config.dependecies_repository import get_dish_repository, get_order_repository, get_user_repository
from repository.dish_repository import DishRepository
from service.order_service import OrderService
from service.user_service import UserService


def get_menu_service(
        dish_repository: DishRepository = Depends(
            get_dish_repository),
):
    return MenuService(dish_repository)

def get_order_service(
        order_repository: OrderRepository = Depends(
            get_order_repository),
        user_repository: UserRepository = Depends(
            get_user_repository
        )
):
    return OrderService(order_repository, user_repository)

def get_user_service(
        user_repository: UserRepository = Depends(
            get_user_repository),
):
    return UserService(user_repository)