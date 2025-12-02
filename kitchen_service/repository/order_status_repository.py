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

    def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> Optional[OrderStatus]:
        """
        Aggiorna lo stato in etcd in modo atomico, ma solo se è diverso da quello attuale.

        - Restituisce l'oggetto OrderStatus aggiornato se la modifica avviene con successo.
        - Restituisce None se l'ordine non esiste o se lo stato è già quello desiderato.
        """
        key = self._get_key(order_id)
        
        while True:
            value, metadata = self.etcd.get(key)
            if value is None:
                # Ordine non trovato, nessuna azione possibile.
                return None

            current_status = OrderStatus.model_validate_json(value)
            
            # Se lo stato è già corretto, nessuna azione necessaria.
            if current_status.status == new_status:
                return None

            # Se siamo qui, lo stato deve essere aggiornato.
            mod_revision = metadata.mod_revision
            current_status.status = new_status
            
            success, _ = self.etcd.transaction(
                compare=[self.etcd.transactions.mod(key) == mod_revision],
                success=[self.etcd.transactions.put(key, current_status.model_dump_json())],
                failure=[]
            )

            if success:
                # Successo! Restituisci l'oggetto aggiornato.
                return current_status
    
    def get_all_by_kitchen(self, kitchen_id: uuid.UUID) -> list:
        """Recupera tutti gli ordini per una specifica cucina."""
        print(f"🔍 Cercando ordini per kitchen_id: {kitchen_id}")
        orders = []
        try:
            # Usa il prefix per ottenere tutti gli order_status
            prefix_results = list(self.etcd.get_prefix("order_status/"))
            print(f"📊 Trovati {len(prefix_results)} ordini totali in etcd")
            
            for value, metadata in prefix_results:
                if value:
                    try:
                        order_status = OrderStatus.model_validate_json(value)
                        print(f"   - Ordine {order_status.order_id}: kitchen_id={order_status.kitchen_id}, status={order_status.status}")
                        
                        # Salta ordini senza kitchen_id (ordini vecchi o incompleti)
                        if order_status.kitchen_id is None:
                            print(f"   ⚠️ Ordine {order_status.order_id} non ha kitchen_id, ignorato")
                            continue
                        
                        if str(order_status.kitchen_id) == str(kitchen_id):
                            # Usa mode='json' per serializzare correttamente gli enum come stringhe
                            order_dict = order_status.model_dump(mode='json')
                            orders.append(order_dict)
                            print(f"   ✅ Aggiunto ordine {order_status.order_id}")
                    except Exception as e:
                        print(f"   ❌ Errore parsing ordine: {e}")
                        continue
            
            print(f"✅ Totale ordini per kitchen {kitchen_id}: {len(orders)}")
            
            # Ordina gli ordini per created_at (dal più vecchio al più recente)
            orders.sort(key=lambda x: x.get('created_at', ''))
            print(f"📅 Ordini ordinati per tempo di arrivo")
        except Exception as e:
            print(f"❌ Errore get_all_by_kitchen: {e}")
            # Ritorna lista vuota invece di crashare
            return []
        
        return orders