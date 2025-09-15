# cartella: repository/kitchen_repository.py
import uuid
from typing import Optional, List
import etcd3  # Importa la libreria etcd3 per la connessione
from model.kitchen import KitchenAvailability

class KitchenAvailabilityRepository:
    """
    Repository per la disponibilità delle cucine che usa etcd come backend.
    """
    
    _KEY_PREFIX = '/kitchens/availability/'

    def __init__(self, host: str = 'localhost', port: int = 2379):
        """
        Inizializza il repository con una connessione a etcd.
        """
        try:
            self.etcd = etcd3.client(host=host, port=port)
            self.etcd.status()  # Verifica la connessione
            print("✅ REPOSITORY: Connesso a etcd.")
        except Exception as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a etcd. Dettagli: {e}")
            raise

    def _get_key(self, kitchen_id: uuid.UUID) -> str:
        """Helper per generare la chiave etcd per una cucina."""
        return f"{self._KEY_PREFIX}{str(kitchen_id)}"

    def save(self, availability: KitchenAvailability) -> None:
        """
        Salva lo stato completo di una cucina su etcd, serializzando il modello.
        """
        key = self._get_key(availability.kitchen_id)
        # Usa .model_dump_json() per serializzare il Pydantic model in JSON
        self.etcd.put(key, availability.model_dump_json())

    def update_fields(self, kitchen_id: uuid.UUID, current_load: Optional[int] = None,
                      max_load: Optional[int] = None,
                      is_operational: Optional[bool] = None) -> bool:
        """
        Aggiorna uno o più campi di una cucina in modo atomico usando una transazione.
        """
        key = self._get_key(kitchen_id)
        
        # Loop per gestire i tentativi in caso di fallimento della transazione
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
            
            # Esegue la transazione. Successo o fallimento è gestito da etcd.
            success, _ = self.etcd.transaction(
                compare=[compare_condition],
                success=[success_operation],
                failure=[]
            )
            
            if success:
                # Se la transazione è andata a buon fine, usciamo dal loop
                return True
            # Se la transazione è fallita, un altro processo ha modificato il dato.
            # Il loop `while True` riproverà l'intera operazione.

    def get_by_id(self, kitchen_id: uuid.UUID) -> Optional[KitchenAvailability]:
        """
        Recupera lo stato di una cucina tramite il suo ID da etcd.
        """
        key = self._get_key(kitchen_id)
        value, _ = self.etcd.get(key)
        
        if value is None:
            return None
        
        # Usa .model_validate_json() per deserializzare il JSON in un Pydantic model
        return KitchenAvailability.model_validate_json(value)

    def get_all(self) -> List[KitchenAvailability]:
        """
        Recupera lo stato di tutte le cucine salvate sotto il prefisso.
        """
        availabilities = []
        # Usa get_prefix per trovare tutte le chiavi che iniziano con il nostro prefisso
        results = self.etcd.get_prefix(self._KEY_PREFIX)
        for value, _ in results:
            availabilities.append(
                KitchenAvailability.model_validate_json(value)
            )
        return availabilities