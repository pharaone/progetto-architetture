import requests
import uuid

data = {
    "name": "Margherita",
    "price": 10.5,
    "available_quantity": 20
}

headers = {
    "X-API-Key": "changeme123"
}

try:
    resp = requests.post("http://localhost:8001/api/menu/dishes", json=data, headers=headers)

    # --- INIZIO BLOCCO DI DEBUG ---
    print(f"Status Code: {resp.status_code}")
    print(f"Response Text: '{resp.text}'") # Le virgolette ci aiutano a vedere se è proprio vuoto

    # Controlliamo se la risposta è OK e non è vuota prima di provare a leggerla
    if resp.ok and resp.text:
        print("--- Risposta JSON ---")
        print(resp.json())
    else:
        print("--- La risposta non è un JSON valido o è vuota ---")
    # --- FINE BLOCCO DI DEBUG ---

except requests.exceptions.ConnectionError as e:
    print("ERRORE DI CONNESSIONE: Impossibile raggiungere il server.")
    print("Assicurati che il container del 'menu-service' sia in esecuzione e che la porta 8001 sia mappata correttamente.")