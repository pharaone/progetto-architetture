# main.py
import logging
from contextlib import asynccontextmanager
import uuid
from typing import List
import uvicorn
from fastapi import FastAPI
from redis.cluster import ClusterNode

from settings import settings  # <- la nostra istanza pydantic
from repository.kitchen_repository import KitchenAvailabilityRepository
from repository.menu_repository import MenuRepository
from repository.order_repository import OrderRepository
from repository.order_status_repository import OrderStatusRepository
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.status_service import OrderStatusService
from service.order_service import OrderOrchestrationService
from producers.producers import EventProducer
from api.api import router as api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("kitchen.main")

def _cluster_nodes_from_settings():
    return [ClusterNode(h, p) for (h, p) in settings.redis_nodes()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: inizializzo repository e servizi...")
    # repositories
    app.state.kitchen_repo = KitchenAvailabilityRepository(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    app.state.order_repo = OrderRepository(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    app.state.order_status_repo = OrderStatusRepository(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    # menu repo con redis cluster nodes
    app.state.menu_repo = MenuRepository(redis_cluster_nodes=_cluster_nodes_from_settings())

    # event producer
    app.state.event_producer = EventProducer(bootstrap_servers=settings.KAFKA_BROKERS)
    await app.state.event_producer.start()
    logger.info("Producer Kafka avviato.")

    # servizi
    app.state.kitchen_service = KitchenService(kitchen_repo=app.state.kitchen_repo)
    app.state.menu_service = MenuService(menu_repo=app.state.menu_repo)
    app.state.status_service = OrderStatusService(status_repo=app.state.order_status_repo)
    app.state.orchestration_service = OrderOrchestrationService(
        order_repo=app.state.order_repo,
        kitchen_service=app.state.kitchen_service,
        menu_service=app.state.menu_service,
        status_service=app.state.status_service,
        event_producer=app.state.event_producer,
    )

    # config & id cucina
    app.state.internal_api_key = settings.INTERNAL_API_KEY
    app.state.kitchen_id = settings.KITCHEN_ID
    logger.info("Inizializzazione completata. Kitchen ID: %s", app.state.kitchen_id)

    try:
        yield
    finally:
        logger.info("Shutdown: arresto producer...")
        await app.state.event_producer.stop()
        logger.info("Producer fermato.")

app = FastAPI(title="Kitchen Service API", version="1.0.0", lifespan=lifespan)
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "kitchen_id": str(app.state.kitchen_id)}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, workers=settings.WORKERS, log_level="info")
