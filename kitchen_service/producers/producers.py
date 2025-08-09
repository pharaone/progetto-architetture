# ======================================================================
# --- 2. CODICE PER: messaging/producers.py ---
# ======================================================================
import json
from model.status import OrderStatus
import uuid
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

# Nomi dei topic su cui il servizio CUCINA pubblica i messaggi
ACCEPTANCE_RESPONSE_TOPIC = "acceptance_responses"  # Risposte alla Fase 1
STATUS_UPDATE_TOPIC = "status_updates"              # Risposte alla Fase 3

class EventProducer:
    """
    Gestisce l'invio di messaggi (eventi) a Kafka.
    """
    def __init__(self, bootstrap_servers: str):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        self._started = False

    async def start(self):
        if self._started: return
        try:
            await self._producer.start()
            self._started = True
            print("✅ PRODUCER: Connesso a Kafka.")
        except KafkaConnectionError as e:
            raise KafkaConnectionError(f"❌ ERRORE CRITICO (Producer): Impossibile connettersi a Kafka - {e}")

    async def stop(self):
        if self._started:
            await self._producer.stop()
            print("🛑 PRODUCER: Disconnesso da Kafka.")

    async def publish_acceptance_response(self, kitchen_id: uuid.UUID, order_id: uuid.UUID, can_handle: bool):
        """Pubblica la risposta di 'candidatura' per un ordine (Fase 1)."""
        message = {"kitchen_id": kitchen_id, "order_id": order_id, "can_handle": can_handle}
        await self._producer.send_and_wait(ACCEPTANCE_RESPONSE_TOPIC, value=message)
        print(f"📬 PRODUCER (Fase 1): Candidatura per ordine {order_id} inviata: {'Sì' if can_handle else 'No'}")

    async def publish_status_update(self, status: OrderStatus):
        """Pubblica un aggiornamento di stato dell'ordine (Fase 3)."""
        # MODIFICA: Sostituito il metodo obsoleto .dict() con .model_dump()
        await self._producer.send_and_wait(STATUS_UPDATE_TOPIC, value=status.model_dump())
        print(f"📬 PRODUCER (Fase 3): Stato per ordine {status.order_id} inviato: {status.status.value}")
