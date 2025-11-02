from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
import asyncio

from api.routers import menu_router, order_router, user_router
from config.settings import Settings
from db.session_manager import SessionManager
from repository.order_repository import OrderRepository
from repository.user_repository import UserRepository
from consumers.kafka_consumer import EventConsumer
from service.order_service import OrderService

consumer: EventConsumer | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer
    
    # Crea manualmente le dipendenze (non possiamo usare Depends fuori dalle route)
    settings = Settings()
    session_manager = SessionManager(settings)
    db_session = session_manager.session_local()
    
    try:
        # Crea i repository e il service
        order_repo = OrderRepository(db_session)
        user_repo = UserRepository(db_session)
        order_service = OrderService(order_repo, user_repo)
        
        # Avvia il consumer
        consumer = EventConsumer(order_service=order_service)
        await consumer.start()
        task = asyncio.create_task(consumer.listen())
        
        yield
        
        # Cleanup
        await consumer.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Comportamento atteso
    finally:
        db_session.close()

app = FastAPI(lifespan=lifespan)

# Router
app.include_router(menu_router.router)
app.include_router(order_router.router)
app.include_router(user_router.router)

if __name__ == "__main__":
    uvicorn.run("menu_service.main:app", host="0.0.0.0", port=8000, reload=True)