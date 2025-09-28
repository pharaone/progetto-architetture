import hashlib
from sqlalchemy.orm import Session

from menu_service.model.user import User
from menu_service.repository.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo : UserRepository):
        self.user_repo = user_repo

    def hash_password(self, password: str) -> str:
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def new_user(self, email: str, password: str) -> User:
        """Create a new user with hashed password."""
        existing_user = self.user_repo.get_all()
        if any(u.email == email for u in existing_user):
            raise ValueError("User with this email already exists")

        hashed_pw = self.hash_password(password)
        user = User(email=email, password=hashed_pw)
        return self.user_repo.add(user)

    def get_user(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        hashed_pw = self.hash_password(password)
        all_users = self.user_repo.get_all()
        for user in all_users:
            if user.email == email and user.password == hashed_pw:
                return user
        return None

    def confirm_user(self, email: str, password: str) -> bool:
        """Check if user exists with given credentials."""
        return self.get_user(email, password) is not None


# Factory function
def get_user_service(session: Session) -> UserService:
    return UserService(session)
