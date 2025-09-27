

class UserService:
    def new_user(self, email: str, password: str):
        pass

    def get_user(self, email: str, password: str):
        pass


def get_user_service():
    return UserService()