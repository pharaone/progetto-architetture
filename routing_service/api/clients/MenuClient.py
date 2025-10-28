# routing_service/client/menu_client.py
import os
import uuid
import requests
from typing import Optional, Dict, Any


class MenuClient:
    """
    Client HTTP per parlare col microservizio MENU.
    Serve per notificare quale cucina è stata assegnata ad un ordine.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 5.0) -> None:
        self.base_url = base_url or os.getenv("MENU_SERVICE_URL", "http://localhost:8081")
        self.timeout_s = timeout_s

    def notify_assignment(
        self,
        order_id: uuid.UUID,
        kitchen_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Notifica al MENU che l'ordine `order_id` è stato assegnato alla `kitchen_id`.
        """
        url = f"{self.base_url}/menu/order_assigned"
        payload = {
            "order_id": str(order_id),
            "kitchen_id": str(kitchen_id),
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout_s)
            resp.raise_for_status()
            return resp.json() if resp.content else {"ok": True}
        except requests.RequestException as e:
            return {"ok": False, "error": f"request_failed: {e}", "payload": payload}
