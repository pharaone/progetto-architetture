from fastapi import FastAPI

from menu_service.api import menu_router, order_router, user_router

app = FastAPI()

app.include_router(menu_router.router)
app.include_router(order_router.router)
app.include_router(user_router.router)