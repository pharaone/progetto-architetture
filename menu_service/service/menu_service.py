import uuid


class MenuService:
    def __init__(self):
        pass

    def get_menu(self, menu_id):
        pass


    def new_dish(self, name: str, price: float, description: str):
        pass

    def get_dish(self, order_id: uuid.UUID, user_id: uuid.UUID):
        pass


def get_menu_service():
    return MenuService()