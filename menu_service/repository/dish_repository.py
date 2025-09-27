import uuid
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from menu_service.model.dish import Dish


class DishRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Dish]:
        return self.session.execute(select(Dish)).scalars().all()

    def get_by_id(self, dish_id: uuid.UUID) -> Optional[Dish]:
        return self.session.execute(
            select(Dish).where(Dish.id == dish_id)
        ).scalar_one_or_none()

    def add(self, dish: Dish) -> Dish:
        self.session.add(dish)
        self.session.commit()
        self.session.refresh(dish)
        return dish

    def update(self, dish_id: uuid.UUID, **kwargs) -> Optional[Dish]:
        self.session.execute(
            update(Dish)
            .where(Dish.id == dish_id)
            .values(**kwargs)
        )
        self.session.commit()
        return self.get_by_id(dish_id)

    def delete(self, dish_id: uuid.UUID) -> bool:
        result = self.session.execute(
            delete(Dish).where(Dish.id == dish_id)
        )
        self.session.commit()
        return result.rowcount > 0
