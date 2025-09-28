import time
import asyncio
import uuid
from typing import Any, Dict, List, Optional

class MenuRoutingService:
    def __init__(self, kitchen_svc, producer, acceptance_window_ms: int = 1500):
        self._kitchen = kitchen_svc
        self._producer = producer
        self._window = acceptance_window_ms
        self._orders: Dict[uuid.UUID, Dict[str, Any]] = {}   # stato per ordine
        self._tasks: Dict[uuid.UUID, asyncio.Task] = {}      # decision task per ordine

    async def on_new_order(self, order: Dict[str, Any]) -> None:
        oid = uuid.UUID(str(order["order_id"]))
        now = time.time()
        self._orders[oid] = {
            "order": order,
            "candidates": [],              # list[UUID]
            "deadline": now + self._window / 1000.0,
            "decided": False,
            "decided_kitchen_id": None,
        }
        # 1) chiedo disponibilità
        await self._producer.publish_disponibilita({
            "order_id": str(order["order_id"]),
            "dish_id": str(order["dish_id"]),
        })
        # 2) programmo decisione a fine finestra (una sola volta)
        if oid not in self._tasks:
            self._tasks[oid] = asyncio.create_task(self._decide_when_ready(oid))

    async def on_acceptance(self, payload: Dict[str, Any]) -> None:
        # payload: {'order_id': str, 'kitchen_id': str, 'can_handle': bool}
        if not payload.get("can_handle"):
            return
        oid = uuid.UUID(str(payload["order_id"]))
        kid = uuid.UUID(str(payload["kitchen_id"]))

        state = self._orders.get(oid)
        if not state:
            return  # ordine sconosciuto o già garbage-collected
        if state["decided"]:
            return  # già deciso → ignoro accettazioni tardive

        state["candidates"].append(kid)
        # nessuna decisione qui: si decide in _decide_when_ready

    async def _decide_when_ready(self, oid: uuid.UUID) -> None:
        state = self._orders.get(oid)
        if not state:
            return
        # aspetta fino al deadline
        wait_s = max(0.0, state["deadline"] - time.time())
        await asyncio.sleep(wait_s)

        # ricontrolla lo stato (può essere stato eliminato)
        state = self._orders.get(oid)
        if not state or state["decided"]:
            return

        best = self._choose_best(
            user_nb=state["order"]["user_neighborhood"],
            candidates=state["candidates"],
        )
        if best is None:
            # nessuna cucina disponibile: qui potresti notificare/cancellare
            state["decided"] = True
            state["decided_kitchen_id"] = None
            return

        # pubblica UNA SOLA conferma alla fine della finestra
        o = state["order"]
        await self._producer.publish_conferma_ordine({
            "order_id": str(o["order_id"]),
            "customer_id": str(o["customer_id"]),
            "dish_id": str(o["dish_id"]),
            "delivery_address": o["delivery_address"],
            "kitchen_id": str(best),
        })

        state["decided"] = True
        state["decided_kitchen_id"] = best

        # opzionale: cleanup task e/o stato
        self._tasks.pop(oid, None)

    def _choose_best(self, user_nb: str, candidates: List[uuid.UUID]) -> Optional[uuid.UUID]:
        best, best_d = None, float("inf")
        for kid in candidates:
            nb = self._kitchen.resolve_kitchen_neighborhood(kid)
            if not nb:
                continue
            d = self._kitchen.shortest_distance(user_nb, nb)
            if d is not None and d < best_d:
                best, best_d = kid, d
        return best
