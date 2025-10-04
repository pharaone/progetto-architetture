import logging
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import uuid
from settings import settings

# Import delle tue classi specifiche
from repository.kitchen_repository import KitchenAvailabilityRepository
from repository.menu_repository import MenuRepository
from repository.order_status_repository import OrderStatusRepository
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.status_service import OrderStatusService
from producers.producers import EventProducer
from consumers.consumers import EventConsumer
from api.api import router as api_router
from redis.cluster import ClusterNode
from model.status import OrderStatus # Import corretto già presente

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("kitchen.main")

def _cluster_nodes_from_settings():
    return [ClusterNode(h, p) for (h, p) in settings.get_redis_nodes()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Inizializzazione delle dipendenze...")

    app.state.internal_api_key = settings.INTERNAL_API_KEY

    # --- 1. Creazione dei componenti base (Repository e Producer) ---
    app.state.kitchen_repo = KitchenAvailabilityRepository(kitchen_id=settings.KITCHEN_ID, host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    app.state.order_status_repo = OrderStatusRepository(host=settings.ETCD_HOST, port=settings.ETCD_PORT)
    app.state.menu_repo = MenuRepository(redis_cluster_nodes=_cluster_nodes_from_settings())
    app.state.event_producer = EventProducer(bootstrap_servers=settings.KAFKA_BROKERS)
    
    # --- 2. Creazione dei Servizi (che dipendono dai componenti base) ---
    app.state.menu_service = MenuService(menu_repo=app.state.menu_repo)

    app.state.status_service = OrderStatusService(
        status_repo=app.state.order_status_repo,
        kitchen_repo=app.state.kitchen_repo,
        producer=app.state.event_producer
    )
    
    
    app.state.kitchen_service = KitchenService(
        kitchen_repo=app.state.kitchen_repo,
        menu_service=app.state.menu_service,
        producer=app.state.event_producer,
        status_service=app.state.status_service
    )
    

    # --- 3. Creazione del Consumer (che dipende dai Servizi) ---
    app.state.event_consumer = EventConsumer(
        bootstrap_servers=settings.KAFKA_BROKERS,
        kitchen_service_instance=app.state.kitchen_service,
        status_service=app.state.status_service,
        producer=app.state.event_producer,
        group_id=f"kitchen_service_{settings.KITCHEN_ID}"
    )
    
    # --- 4. Avvio delle connessioni e dei processi in background ---
    await app.state.event_producer.start()
    await app.state.event_consumer.start()
    
    logger.info("Avvio del Consumer Kafka in background...")
    app.state.consumer_task = asyncio.create_task(
        app.state.event_consumer.listen()
    )
    logger.info("Consumer Kafka task avviato con successo.")

    # Eseguiamo i test di invio dopo l'avvio
    logger.info("Invio messaggi di startup a Kafka...")
    await app.state.event_producer.publish_acceptance_response(
        kitchen_id=settings.KITCHEN_ID,
        order_id=str(uuid.uuid4()),
        can_handle=True
    )

    # --- INIZIO BLOCCO CORRETTO ---
    # 1. Creiamo un oggetto OrderStatus, come si aspetta la funzione
    startup_status_update = OrderStatus(
        order_id=uuid.uuid4(),
        status="pending",
        kitchen_id=settings.KITCHEN_ID
    )
    # 2. E passiamo l'oggetto singolo alla funzione
    await app.state.event_producer.publish_status_update(startup_status_update)
    # --- FINE BLOCCO CORRETTO ---
    
    logger.info("Messaggi di startup inviati con successo.")

    yield # L'applicazione è in esecuzione

    # --- 5. Shutdown ---
    logger.info("Shutdown: avvio procedura di arresto...")
    
    if hasattr(app.state, 'consumer_task') and not app.state.consumer_task.done():
        logger.info("Arresto del consumer task...")
        app.state.consumer_task.cancel()
        try:
            await app.state.consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task annullato correttamente.")

    await app.state.event_consumer.stop()
    await app.state.event_producer.stop()
    
    logger.info("Procedura di shutdown completata.")


app = FastAPI(title="Kitchen Service API", version="1.0.0", lifespan=lifespan)
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["health"])
async def health():
    # Accediamo direttamente alla configurazione
    return {"status": "ok", "kitchen_id": str(settings.KITCHEN_ID)}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, workers=settings.WORKERS, log_level="info")