from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from model.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[User]:
        return self.session.execute(select(User)).scalars().all()

    def get_by_id(self, user_id) -> Optional[User]:
        return self.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user_id, **kwargs) -> Optional[User]:
        self.session.execute(update(User).where(User.id == user_id).values(**kwargs))
        self.session.commit()
        return self.get_by_id(user_id)

    def delete(self, user_id) -> bool:
        result = self.session.execute(delete(User).where(User.id == user_id))
        self.session.commit()
        return result.rowcount > 0

