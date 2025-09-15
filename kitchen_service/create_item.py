import requests
import uuid

data = {
    "name": "Margherita",
    "price": 10.5,
    "available_quantity": 20  # aggiungi anche la quantità
}

headers = {
    "X-API-Key": "changeme123"
}

resp = requests.post("http://localhost:8001/api/menu/dishes", json=data, headers=headers)
print(resp.json())
