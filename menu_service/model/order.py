import uuid

from sqlalchemy import Column, UUID, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Enum as SQLEnum

from db.base import Base
from model.enum.order_status import OrderStatus


class Order(Base):

    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    kitchen_id = Column(UUID(as_uuid=True))
    status = Column(String, nullable=False)

    dish_id = Column(UUID(as_uuid=True), ForeignKey("dishes.id"), nullable=False)
    dish = relationship("Dish", backref="orders")

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="orders")