import uuid

from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import declarative_base

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(300), unique=True, nullable=False)
    password = Column(String, nullable=False)
    region = Column(String(300), nullable=False)