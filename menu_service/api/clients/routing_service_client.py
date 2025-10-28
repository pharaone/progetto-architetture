import uuid

import requests

from config.dependecies_configuration import get_settings

BASE_URL = get_settings().ROUTING_SERVICE_URL


def start_order(user_region: str, order_id: uuid.UUID, dish_id: uuid.UUID):
    url = f"{BASE_URL}/routing/create-order"
    payload = {
        "user_region": user_region,
        "order_id": str(order_id),
        "dish_id": str(dish_id),
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Ordine creato con successo!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nella richiesta: {e}")
        return None
