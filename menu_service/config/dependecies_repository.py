from fastapi import Depends
from sqlalchemy.orm import Session

from menu_service.config.dependecies_configuration import get_db
from menu_service.repository.dish_repository import DishRepository
from menu_service.repository.order_repository import OrderRepository
from menu_service.repository.user_repository import UserRepository


def get_dish_repository(db: Session = Depends(get_db)):
    return DishRepository(db)

def get_order_repository(db: Session = Depends(get_db)):
    return OrderRepository(db)

def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)