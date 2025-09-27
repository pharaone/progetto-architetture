import uuid
from sqlalchemy import Column, String, Float, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)