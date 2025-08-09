# cartella: repository/order_status_repository.py

import etcd3
import uuid
from typing import Optional
from model.status import OrderStatus, StatusEnum

class OrderStatusRepository:
    def __init__(self, host: str = 'localhost', port: int = 2379):
        try:
            self.etcd = etcd3.client(host=host, port=port)
            self.etcd.status()
            print("✅ REPOSITORY: Connesso a etcd.")
        except Exception as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a etcd. Dettagli: {e}")
            raise

    def _get_key(self, order_id: uuid.UUID) -> str:
        return f"order_status/{str(order_id)}"

    def save(self, order_status: OrderStatus) -> None:
        key = self._get_key(order_status.order_id)
        # CORREZIONE: Usa .model_dump_json() invece di .json()
        self.etcd.put(key, order_status.model_dump_json())

    def get_by_id(self, order_id: uuid.UUID) -> Optional[OrderStatus]:
        key = self._get_key(order_id)
        value, _ = self.etcd.get(key)
        
        if value is None:
            return None
        
        # CORREZIONE: Usa .model_validate_json() invece di .parse_raw()
        return OrderStatus.model_validate_json(value)

    def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        key = self._get_key(order_id)
        
        while True:
            value, metadata = self.etcd.get(key)
            if value is None:
                return False

            # CORREZIONE: Usa .model_validate_json()
            current_status = OrderStatus.model_validate_json(value)
            mod_revision = metadata.mod_revision

            current_status.status = new_status

            # CORREZIONE: Usa .model_dump_json()
            success, _ = self.etcd.transaction(
                compare=[self.etcd.transactions.mod(key) == mod_revision],
                success=[self.etcd.transactions.put(key, current_status.model_dump_json())],
                failure=[]
            )

            if success:
                return True