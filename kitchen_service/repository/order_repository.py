# cartella: repository/order_repository.py

import uuid
import etcd3
from typing import Optional
from model.order import Order # Assumendo che il tuo modello sia in model/order.py

class OrderRepository:
    def __init__(self, kitchen_id: uuid.UUID, host: str = 'localhost', port: int = 2379):
        """
        Inizializza il repository con una connessione a etcd.
        """
        try:
            self.etcd = etcd3.client(host=host, port=port)
            self.etcd.status()
            self.kitchen_id = str(kitchen_id)
            print(f"✅ REPOSITORY: Connesso a etcd per kitchen {self.kitchen_id}")
        except Exception as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a etcd. Dettagli: {e}")
            raise

    def _get_key(self, order_id: uuid.UUID) -> str:
        """Helper per generare la chiave etcd per un ordine."""
        return f"{self.kitchen_id}/order/{str(order_id)}"

    def save(self, order: Order) -> None:
        """
        Salva un ordine in etcd, serializzando il modello.
        """
        key = self._get_key(order.order_id)
        # Usa .model_dump_json() per serializzare il Pydantic model in JSON
        self.etcd.put(key, order.model_dump_json())

    def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        """
        Recupera un ordine da etcd e lo deserializza.
        """
        key = self._get_key(order_id)
        value, _ = self.etcd.get(key)
        
        if value is None:
            return None
        
        # Usa .model_validate_json() per deserializzare il JSON in un Pydantic model
        return Order.model_validate_json(value)