import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from routing_service.api.clients.MenuClient import MenuClient


@dataclass
class OrderState:
    """Stato interno di un ordine durante la finestra di decisione."""
    order: Dict[str, Any]
    candidates: Set[uuid.UUID] = field(default_factory=set)
    deadline_mono_s: float = 0.0  # tempo monotono in secondi
    decided: bool = False
    decided_kitchen_id: Optional[uuid.UUID] = None


class MenuRoutingService:
    """
    - on_new_order: salva ordine, pubblica 'disponibilita', programma decisione.
    - on_acceptance: aggiunge candidati se entro finestra.
    - _decide_when_ready: allo scadere sceglie la kitchen più vicina e pubblica 'conferma_ordine'.
    - cache status: get_order_status/save_status per il topic 'status' e API.
    """

    def __init__(
        self,
        kitchen_service,
        producer,
        menu_client: Optional[MenuClient] = None,
        window_ms: int = 1500,
    ) -> None:
        self._kitchen_service = kitchen_service
        self._producer = producer
        self._menu_client: Optional[MenuClient] = menu_client

        # finestra in secondi (configurabile)
        self._window_s: float = max(0.0, window_ms / 1000.0)

        # stato ordini + task
        self._orders: Dict[uuid.UUID, OrderState] = {}
        self._tasks: Dict[uuid.UUID, asyncio.Task] = {}

        # cache ultimi status
        self._status_cache: Dict[uuid.UUID, Dict[str, Any]] = {}

        # lock per race HTTP/consumer
        self._lock = asyncio.Lock()

    # ==================== HTTP: nuovo ordine ====================

    async def on_new_order(self, order: Dict[str, Any]) -> None:
        """
        Campi minimi richiesti:
          - order_id, dish_id, user_neighborhood (oppure user_region come alias)
        """
        oid = uuid.UUID(str(order["order_id"]))
        o_user_nb = order.get("user_neighborhood") or order.get("user_region") or ""

        safe_order = {
            "order_id": str(order["order_id"]),
            "dish_id": str(order["dish_id"]),
            "user_neighborhood": o_user_nb,
            "customer_id": str(order.get("customer_id")) if order.get("customer_id") else None,
            "delivery_address": order.get("delivery_address"),
        }

        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._window_s  # tempo monotono

        async with self._lock:
            self._orders[oid] = OrderState(
                order=safe_order,
                candidates=set(),
                deadline_mono_s=deadline,
                decided=False,
                decided_kitchen_id=None,
            )
            if oid not in self._tasks:
                self._tasks[oid] = asyncio.create_task(self._decide_when_ready(oid))

        # Kafka: richiede disponibilità
        await self._producer.publish_disponibilita({
            "order_id": safe_order["order_id"],
            "dish_id": safe_order["dish_id"],
        })
        print(f"[NEW_ORDER] oid={safe_order['order_id']} window_s={self._window_s:.3f}")

    # ==================== KAFKA: acceptance ====================

    async def on_acceptance(self, payload: Dict[str, Any]) -> None:
        """
        payload:
          - order_id: str
          - kitchen_id: str
          - can_handle: bool
        """
        if not payload or not payload.get("can_handle"):
            return
        try:
            oid = uuid.UUID(str(payload["order_id"]))
            kid = uuid.UUID(str(payload["kitchen_id"]))
        except Exception:
            return  # payload non valido

        loop = asyncio.get_running_loop()
        async with self._lock:
            state = self._orders.get(oid)
            if not state:
                print(f"[ACCEPT] oid={payload.get('order_id')} ignored (unknown)")
                return

            # se abbiamo già deciso, ignoriamo (comportamento atteso)
            if state.decided:
                print(f"[ACCEPT] oid={payload.get('order_id')} ignored (decided)")
                return

            state.candidates.add(kid)
            left = max(0.0, state.deadline_mono_s - loop.time())
            print(f"[ACCEPT] oid={payload.get('order_id')} +candidate={payload.get('kitchen_id')} time_left_s={left:.3f}")

    # ==================== API per controller ====================

    def get_assignment(self, order_id: uuid.UUID) -> Dict[str, Any]:
        oid = uuid.UUID(str(order_id))
        state = self._orders.get(oid)
        if not state:
            return {"state": "unknown"}
        if not state.decided:
            return {"state": "pending"}
        return {
            "state": "decided",
            "kitchen_id": str(state.decided_kitchen_id) if state.decided_kitchen_id else None,
        }

    def get_order_status(self, order_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        oid = uuid.UUID(str(order_id))
        return self._status_cache.get(oid)

    def save_status(self, order_id: str, status: Any) -> None:
        try:
            oid = uuid.UUID(str(order_id))
        except Exception:
            return
        self._status_cache[oid] = {"order_id": str(oid), "status": status}
        print(f"[STATUS] cached oid={oid} status={status}")

    # ==================== Decisione ====================

    async def _decide_when_ready(self, oid: uuid.UUID) -> None:
        loop = asyncio.get_running_loop()

        async with self._lock:
            state = self._orders.get(oid)
            if not state:
                return
            wait_s = max(0.0, state.deadline_mono_s - loop.time())

        print(f"[DECIDE] scheduling wait_s={wait_s:.3f} order_id={state.order['order_id']}")
        if wait_s > 0:
            await asyncio.sleep(wait_s)

        async with self._lock:
            state = self._orders.get(oid)
            if not state:
                self._tasks.pop(oid, None)
                return
            if state.decided:
                self._tasks.pop(oid, None)
                return

            best = self._choose_best(
                user_nb=state.order["user_neighborhood"],
                candidates=list(state.candidates),
            )

            if best is None:
                state.decided = True
                state.decided_kitchen_id = None
                self._tasks.pop(oid, None)
                print(f"[DECIDE] oid={state.order['order_id']} no candidates → none")
                return

            o = state.order
            msg = {
                "order_id": o["order_id"],
                "customer_id": o["customer_id"],
                "dish_id": o["dish_id"],
                "delivery_address": o["delivery_address"],
                "kitchen_id": str(best),
            }
            # publish conferma_ordine
            await self._producer.publish_conferma_ordine(msg)
            print(f"[KAFKA] conferma_ordine → {msg}")

            # HTTP opzionale verso MENU
            if self._menu_client is not None:
                try:
                    result = await loop.run_in_executor(
                        None,
                        self._menu_client.notify_assignment,
                        uuid.UUID(o["order_id"]),
                        best,
                    )
                    print(f"[HTTP] notify MENU result={result}")
                except Exception as e:
                    print(f"[HTTP] notify MENU error={e}")

            state.decided = True
            state.decided_kitchen_id = best
            self._tasks.pop(oid, None)

    def _choose_best(self, user_nb: str, candidates: List[uuid.UUID]) -> Optional[uuid.UUID]:
        """Seleziona la kitchen più vicina al quartiere dell'utente."""
        best: Optional[uuid.UUID] = None
        best_d = float("inf")
        for kid in candidates:
            nb = self._kitchen_service.resolve_kitchen_neighborhood(kid)
            if not nb:
                continue
            d = self._kitchen_service.shortest_distance(user_nb, nb)
            if d is not None and d < best_d:
                best, best_d = kid, d
        return best
