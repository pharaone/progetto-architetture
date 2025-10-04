import uuid
import json
from typing import Optional
import etcd3
from model.kitchen import KitchenAvailability

class KitchenAvailabilityRepository:
    """
    Repository per la disponibilità di UNA SPECIFICA cucina, che usa etcd come backend.
    Tutte le operazioni implicite (get, update) utilizzano il kitchen_id fornito nell'init.
    """
    
    _KEY_PREFIX = '/kitchens/availability/'

    def __init__(self, kitchen_id: uuid.UUID, host: str = 'localhost', port: int = 2379):
        """
        Inizializza il repository con una connessione a etcd e associa l'istanza a un
        singolo kitchen_id.
        """
        try:
            self.kitchen_id = kitchen_id  # L'ID della singola cucina gestita da questa istanza
            self.etcd = etcd3.client(host=host, port=port)
            self.etcd.status() 
            print("✅ REPOSITORY: Connesso a etcd.")
        except Exception as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a etcd. Dettagli: {e}")
            raise
        if self.get_by_id() is None:
            print(f"Nessun dato trovato per la cucina {self.kitchen_id}, inizializzo con valori di default...")
            self.save(KitchenAvailability(
                kitchen_id=self.kitchen_id,
                current_load=0,
                max_load=10,
                is_operational=True
            ))
            # 3. Salva l'oggetto
            print(f"✅ Dati iniziali salvati per la cucina {self.kitchen_id}.")

    def _get_key(self, kitchen_id: uuid.UUID) -> str:
        """Helper per generare la chiave etcd per una cucina (richiede un ID esplicito)."""
        return f"{self._KEY_PREFIX}{str(kitchen_id)}"
    
    def save(self, availability: KitchenAvailability) -> None:
        """
        Salva lo stato completo della cucina unica su etcd.
        """
        key = self._get_key(self.kitchen_id)
        self.etcd.put(key, availability.model_dump_json())

    def update_fields(self, current_load: Optional[int] = None,
                      max_load: Optional[int] = None,
                      is_operational: Optional[bool] = None) -> bool:
        """
        Aggiorna uno o più campi della cucina associata in modo atomico.
        Non richiede il kitchen_id come argomento, usa self.kitchen_id.
        """
        key = self._get_key(self.kitchen_id)
        
        # Loop per gestire i tentativi in caso di fallimento della transazione (ottimistic locking)
        while True:
            # 1. READ: Recupera l'oggetto e la sua revisione
            value, metadata = self.etcd.get(key)
            if value is None:
                return False  # La cucina non esiste

            # Deserializza per ottenere l'oggetto Python
            existing_availability = KitchenAvailability.model_validate_json(value)
            mod_revision = metadata.mod_revision

            # 2. MODIFY: Aggiorna l'oggetto Python in memoria
            if current_load is not None:
                existing_availability.current_load = current_load
            if max_load is not None:
                existing_availability.max_load = max_load
            if is_operational is not None:
                existing_availability.is_operational = is_operational
            
            # 3. WRITE ATOMICO: Tentativo di salvare solo se la revisione non è cambiata
            # Condizione: la revisione del dato sulla chiave deve essere ancora la stessa
            compare_condition = self.etcd.transactions.mod(key) == mod_revision
            
            # Operazione di successo: salva il nuovo valore serializzato
            success_operation = self.etcd.transactions.put(key, existing_availability.model_dump_json())
            
            # Esegue la transazione.
            success, _ = self.etcd.transaction(
                compare=[compare_condition],
                success=[success_operation],
                failure=[]
            )
            
            if success:
                # Se la transazione è andata a buon fine, usciamo dal loop
                return True
            # Se fallisce, riprova (ottimistic locking)

    def get_by_id(self) -> Optional[KitchenAvailability]:
        """
        Recupera lo stato della cucina associata a questa istanza da etcd.
        Non richiede il kitchen_id come argomento.
        """
        key = self._get_key(self.kitchen_id)
        print(f"🔍 DEBUG: Sto cercando la chiave '{key}' in etcd.")
        value, _ = self.etcd.get(key)
        
        if value is None:
            return None
        
        # Usa .model_validate_json() per deserializzare il JSON in un Pydantic model
        return KitchenAvailability.model_validate_json(value)