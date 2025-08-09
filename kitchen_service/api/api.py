# cartella: api/main.py
import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from redis.cluster import ClusterNode
# Importa i tuoi modelli, servizi e repository
from model.menu import MenuItem
from model.status import OrderStatus, StatusEnum
from model.kitchen import KitchenAvailability
from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.order_service import OrderOrchestrationService
from repository.kitchen_repository import KitchenAvailabilityRepository
from repository.menu_repository import MenuRepository
from repository.order_status_repository import OrderStatusRepository
from repository.order_repository import OrderRepository
from producers.producers import EventProducer
from service.status_service import OrderStatusService

# ======================================================================
# --- Blocco di Inizializzazione e Dependency Injection ---
# ======================================================================

# In un'app reale, questi valori verrebbero da file di configurazione o variabili d'ambiente
KAFKA_BROKERS = "localhost:9092"
ETCD_HOST = "localhost"
ETCD_PORT = 2379

#Leggiamo il KITCHEN_ID da una variabile d'ambiente.
# Se non la trova, ne crea uno nuovo (utile per i test locali).
try:
    KITCHEN_ID = uuid.UUID(os.environ.get("KITCHEN_ID"))
    print(f"✅ ID Cucina caricato dall'ambiente: {KITCHEN_ID}")
except (ValueError, TypeError):
    KITCHEN_ID = uuid.uuid4()
    print(f"⚠️ ATTENZIONE: KITCHEN_ID non trovato. Generato un ID casuale: {KITCHEN_ID}")


# 1. Istanziamo i Repository (le connessioni ai database)
kitchen_repo = KitchenAvailabilityRepository() # In-memory per il PoC
# Quando esegui il codice dentro Docker (tra container)
redis_cluster_nodes = [
    ClusterNode("redis-node-1", 6379),
    ClusterNode("redis-node-2", 6379),
    ClusterNode("redis-node-3", 6379)
]

# Quando esegui il codice fuori Docker (dal tuo PC)
# redis_cluster_nodes = [
#     ClusterNode("localhost", 7000),
#     ClusterNode("localhost", 7001),
#     ClusterNode("localhost", 7002)
# ]
menu_repo = MenuRepository(redis_cluster_nodes=redis_cluster_nodes)
order_status_repo = OrderStatusRepository(host=ETCD_HOST, port=ETCD_PORT)
order_repo = OrderRepository() # In-memory per il PoC

# 2. Istanziamo il Producer Kafka
event_producer = EventProducer(bootstrap_servers=KAFKA_BROKERS)

# 3. Istanziamo i Servizi, iniettando le loro dipendenze
kitchen_service = KitchenService(kitchen_repo=kitchen_repo)
menu_service = MenuService(menu_repo=menu_repo)
status_service = OrderStatusService(status_repo=order_status_repo)
orchestration_service = OrderOrchestrationService(
    order_repo=order_repo,
    kitchen_service=kitchen_service,
    menu_service=menu_service,
    status_service=status_service,
    event_producer=event_producer
)

# Funzione "provider" per FastAPI per iniettare l'orchestratore
def get_orchestrator():
    return orchestration_service

# ======================================================================
# --- Applicazione FastAPI e Definizione degli Endpoint ---
# ======================================================================

app = FastAPI(
    title="Kitchen Service API",
    description="API per gestire le operazioni di una Ghost Kitchen."
)

# Modelli Pydantic per i corpi delle richieste API
class QuantityUpdateRequest(BaseModel):
    available_quantity: int

class StatusUpdateRequest(BaseModel):
    status: StatusEnum

# --- Endpoint per la Risorsa: Kitchen ---

@app.get("/kitchen", response_model=KitchenAvailability)
async def get_kitchen_status():
    """Recupera lo stato operativo attuale della cucina."""
    kitchen_state = await kitchen_repo.get_by_id(KITCHEN_ID)
    if not kitchen_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stato cucina non trovato.")
    return kitchen_state

@app.patch("/kitchen")
async def update_kitchen_status(is_operational: bool):
    """Aggiorna lo stato operativo della cucina (aperta/chiusa)."""
    success = await kitchen_service.set_operational_status(KITCHEN_ID, is_operational)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impossibile aggiornare lo stato della cucina.")
    return {"message": "Stato cucina aggiornato con successo."}

# --- Endpoint per la Risorsa: Menu / Inventory ---

@app.get("/menu/dishes", response_model=List[MenuItem])
async def get_all_dishes():
    """Recupera la lista di tutti i piatti del menu con la loro quantità."""
    # Nota: questo richiede un metodo get_all_items nel MenuRepository
    menu = await menu_repo.get_menu(KITCHEN_ID)
    if not menu:
        return []
    return list(menu.items.values())

@app.patch("/menu/dishes/{dish_id}/quantity", response_model=MenuItem)
async def update_dish_quantity(dish_id: uuid.UUID, request: QuantityUpdateRequest):
    """Imposta la quantità disponibile per un piatto specifico."""
    # Nota: questo richiede un metodo specifico nel MenuService/MenuRepository
    item = await menu_repo.get_menu_item(KITCHEN_ID, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    
    item.available_quantity = request.available_quantity
    await menu_repo.create_menu_item(KITCHEN_ID, item)
    return item

# --- Endpoint per la Risorsa: Orders ---

@app.get("/orders", response_model=List[OrderStatus])
async def get_active_orders():
    """Recupera la lista di tutti gli ordini attivi per questa cucina."""
    # Nota: questo richiede un metodo get_all nel OrderStatusRepository
    return await order_status_repo.get_all_by_kitchen(KITCHEN_ID)

@app.patch("/orders/{order_id}/status", status_code=status.HTTP_202_ACCEPTED)
async def update_order_status(
    order_id: uuid.UUID,
    request: StatusUpdateRequest,
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    """
    Endpoint principale per lo staff: aggiorna lo stato di un ordine
    (es. da 'in preparazione' a 'pronto').
    """
    success = await orchestrator.handle_order_status_update(
        order_id=order_id,
        kitchen_id=KITCHEN_ID,
        new_status=request.status
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine non trovato o aggiornamento fallito.")
    return {"message": "Richiesta di aggiornamento stato accettata."}