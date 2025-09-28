import asyncio

from fastapi import FastAPI, Depends

from menu_service.api.routers import menu_router, order_router, user_router
from menu_service.config import settings
from menu_service.config.dependecies_configuration import get_settings
from menu_service.config.dependecies_services import get_order_service
from menu_service.consumers.kafka_consumer import EventConsumer
from menu_service.producers.kafka_producer import EventProducer
from menu_service.service.order_service import OrderService

app = FastAPI()

app.include_router(menu_router.router)
app.include_router(order_router.router)
app.include_router(user_router.router)

order_service: OrderService = Depends(get_order_service)
consumer = EventConsumer(
    order_service=order_service
)

@app.on_event("startup")
async def startup_event():
    await consumer.start()
    asyncio.create_task(consumer.listen())

@app.on_event("shutdown")
async def shutdown_event():
    await consumer.stop()
