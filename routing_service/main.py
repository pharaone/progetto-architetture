import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI

from routing_service.api.RouterController import router
from routing_service.api.RouterController import (
    get_event_producer,
    get_kitchen_service,
    get_menu_service,
)
from routing_service.consumers.EventConsumers import EventConsumers

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = await get_event_producer()
    kitchen_service = get_kitchen_service()
    menu_service = await get_menu_service(kitchen_service, producer)

    consumers = EventConsumers(
        menu_service=menu_service,
        producer=producer,
        bootstrap_servers=KAFKA_BOOTSTRAP,
    )
    await consumers.start()
    task: Optional[asyncio.Task] = asyncio.create_task(consumers.run())
    try:
        yield
    finally:
        try:
            await consumers.stop()
        except Exception:
            pass
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        try:
            await producer.stop()
        except Exception:
            pass

def create_app() -> FastAPI:
    app = FastAPI(title="Routing Service", version="1.0.0", lifespan=lifespan)
    app.include_router(router)

    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "ok"}

    @app.get("/", tags=["meta"])
    async def root():
        return {"service": "routing-service", "status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("routing_service.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
