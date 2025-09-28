from fastapi import FastAPI

from menu_service.api.routers import menu_router, order_router, user_router
from menu_service.config import settings
from menu_service.producers.kafka_producer import EventProducer

app = FastAPI()

app.include_router(menu_router.router)
app.include_router(order_router.router)
app.include_router(user_router.router)

app.state.event_producer = EventProducer(bootstrap_servers=settings.Settings.KAFKA_BROKERS)
app.state.event_producer.start()