from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from model.order import Order


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Order]:
        return self.session.execute(select(Order)).scalars().all()

    def get_by_id(self, order_id) -> Optional[Order]:
        return self.session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()

    def add(self, order: Order) -> Order:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def update(self, order_id, **kwargs) -> Optional[Order]:
        self.session.execute(update(Order).where(Order.id == order_id).values(**kwargs))
        self.session.commit()
        return self.get_by_id(order_id)

    def delete(self, order_id) -> bool:
        result = self.session.execute(delete(Order).where(Order.id == order_id))
        self.session.commit()
        return result.rowcount > 0
