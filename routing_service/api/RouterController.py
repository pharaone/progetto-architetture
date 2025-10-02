import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from routing_service.model.CreateOrder import CreateOrder
from routing_service.model.KitchenLocation import KitchenLocation
from routing_service.model.Order import Order
from routing_service.producers.EventProducer import EventProducer
from routing_service.service.KitchenRoutingService import KitchenRoutingService
from routing_service.service.MenuRoutingService import MenuRoutingService

router = APIRouter(prefix="/routing", tags=["routing"])

# ---------------------------------------------------------
# Singletons semplici (lazy) per service/producer
# ---------------------------------------------------------
_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

_kitchen_svc_singleton: Optional[KitchenRoutingService] = None
_producer_singleton: Optional[EventProducer] = None
_menu_svc_singleton: Optional[MenuRoutingService] = None


async def get_event_producer() -> EventProducer:
    """Istanzia e avvia il producer alla prima richiesta (idempotente)."""
    global _producer_singleton
    if _producer_singleton is None:
        _producer_singleton = EventProducer(bootstrap_servers=_KAFKA_BOOTSTRAP)
    await _producer_singleton.start()
    return _producer_singleton


def get_kitchen_service() -> KitchenRoutingService:
    global _kitchen_svc_singleton
    if _kitchen_svc_singleton is None:
        _kitchen_svc_singleton = KitchenRoutingService()
    return _kitchen_svc_singleton


async def get_menu_service(
    kitchen_svc: KitchenRoutingService = Depends(get_kitchen_service),
    producer: EventProducer = Depends(get_event_producer),
) -> MenuRoutingService:
    """Istanzia il MenuRoutingService una volta sola, collegato a kitchen_svc + producer."""
    global _menu_svc_singleton
    if _menu_svc_singleton is None:
        window_ms = int(os.getenv("WINDOW_MS", "1500"))  # ← configurabile da env
        _menu_svc_singleton = MenuRoutingService(kitchen_svc, producer, window_ms=window_ms)
    return _menu_svc_singleton


# ---------------------------------------------------------
# ORDINI (ingresso dal microservizio di menu)
# ---------------------------------------------------------

@router.post("/create-order")
async def create_order_minimal(
    body: CreateOrder,
    menu_service: MenuRoutingService = Depends(get_menu_service),
):
    """
    Endpoint COMPATIBILE col client del servizio MENU.
    Riceve: user_region, order_id, dish_id.
    Mappa user_region -> user_neighborhood e avvia il flusso di routing.
    """
    await menu_service.on_new_order({
        "order_id": str(body.order_id),
        "dish_id": str(body.dish_id),
        "user_neighborhood": body.user_region,  # mapping compat
        # campi opzionali (customer_id, delivery_address) gestiti con default nel service
    })
    return {"ok": True, "order_id": str(body.order_id)}


@router.post("/orders")
async def submit_order(
    order: Order,
    menu_service: MenuRoutingService = Depends(get_menu_service),
):
    """
    Variante “completa” (se vuoi ricevere l'Order pieno via API).
    Effetti:
      - salva traccia ordine,
      - pubblica su 'disponibilita' {order_id, dish_id}.
    """
    await menu_service.on_new_order(order.model_dump())
    return {"ok": True, "order_id": str(order.order_id)}


@router.get("/assignment/{order_id}")
async def assignment(
    order_id: uuid.UUID,
    menu_service: MenuRoutingService = Depends(get_menu_service),
):
    """
    PULL per sapere a quale cucina è stato assegnato un ordine:
      - unknown | pending | decided (+ kitchen_id)
    """
    return menu_service.get_assignment(order_id)


@router.get("/orders/{order_id}/status")
async def get_order_status(
    order_id: uuid.UUID,
    menu_service: MenuRoutingService = Depends(get_menu_service),
):
    """
    Ritorna l’ultimo stato noto (cache aggiornata dal consumer che legge 'status').
    Non invia richieste su Kafka.
    """
    status = menu_service.get_order_status(order_id)
    if not status:
        return {"order_id": str(order_id), "status": None}
    return status


@router.post("/orders/{order_id}/status/request")
async def request_order_status(
    order_id: uuid.UUID,
    producer: EventProducer = Depends(get_event_producer),
):
    """
    Chiede lo stato su Kafka: pubblica su 'status' {'order_id': ...}.
    La risposta (es. {'order_id','status'}) arriverà su 'status'
    e il tuo consumer aggiornerà la cache nel MenuRoutingService.
    """
    await producer.publish_status_request({"order_id": str(order_id)})
    return {"ok": True, "requested_order_id": str(order_id)}


# ---------------------------------------------------------
# CUCINE: posizione (serve al routing per le distanze)
# ---------------------------------------------------------

@router.post("/kitchens/{kitchen_id}/location")
async def set_kitchen_location(
    kitchen_id: uuid.UUID,
    body: KitchenLocation,
    kitchen_service: KitchenRoutingService = Depends(get_kitchen_service),
):
    """Associa la cucina a un quartiere (nodo del grafo)."""
    if body.kitchen_id != kitchen_id:
        raise HTTPException(status_code=400, detail="kitchen_id nel path e nel body non coincidono.")
    kitchen_service.set_kitchen_location(kitchen_id, body.neighborhood)
    return {"ok": True}


@router.get("/graph")
def get_graph(
    kitchen_service: KitchenRoutingService = Depends(get_kitchen_service),
):
    """Snapshot del grafo mock (quartieri + archi) e mappa cucine."""
    return JSONResponse(content=kitchen_service.get_graph_snapshot())

