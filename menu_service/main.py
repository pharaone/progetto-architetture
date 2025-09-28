from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
import asyncio

from menu_service.api.routers import menu_router, order_router, user_router
from menu_service.config.dependecies_services import get_order_service
from menu_service.consumers.kafka_consumer import EventConsumer
from menu_service.service.order_service import OrderService

consumer: EventConsumer | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer
    order_service: OrderService = get_order_service()
    consumer = EventConsumer(order_service=order_service)
    await consumer.start()
    task = asyncio.create_task(consumer.listen())
    yield
    await consumer.stop()
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Router
app.include_router(menu_router.router)
app.include_router(order_router.router)
app.include_router(user_router.router)

if __name__ == "__main__":
    uvicorn.run("menu_service.main:app", host="0.0.0.0", port=8000, reload=True)