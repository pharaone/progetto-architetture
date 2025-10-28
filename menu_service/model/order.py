import uuid

from sqlalchemy import Column, UUID, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from menu_service.db.base import Base
from menu_service.model.enum.order_status import OrderStatus


class Order(Base):

    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    kitchen_id = Column(UUID(as_uuid=True))
    status = Column(String, default=OrderStatus.SUBMITTED)

    dish_id = Column(UUID(as_uuid=True), ForeignKey("dishes.id"), nullable=False)
    dish = relationship("Dish", backref="orders")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="orders")