import uuid


class OrderService:
    def new_order(self, dish_id: uuid.UUID, user_id: uuid.UUID):
        pass

    def get_order_status(self, order_id: uuid.UUID, user_id: uuid.UUID):
        pass

    def get_my_orders(self, user_id: uuid.UUID):
        pass

def get_order_service():
    return OrderService()