from fastapi import Depends
from sqlalchemy.orm import Session

from config.dependecies_configuration import get_db
from repository.dish_repository import DishRepository
from repository.order_repository import OrderRepository
from repository.user_repository import UserRepository


def get_dish_repository(db: Session = Depends(get_db)):
    return DishRepository(db)

def get_order_repository(db: Session = Depends(get_db)):
    return OrderRepository(db)

def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)