# ======================================================================
# --- 3. CODICE PER: messaging/consumers.py ---
# ======================================================================
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from pydantic import ValidationError

# Importiamo i modelli e il servizio orchestratore
from model.order import Order
from model.messaging_models import OrderRequest, StatusRequest
from service.order_service import OrderOrchestrationService # Il cervello

# Nomi dei topic che il servizio CUCINA ascolta
AVAILABILITY_REQUEST_TOPIC = "availability_requests" # Domande per la Fase 1
ORDER_ASSIGNMENT_TOPIC = "order_assignments"         # Messaggi per la Fase 2
ORDER_STATUS_REQUEST_TOPIC = "order_status_requests" # Domande per la Fase 3

class EventConsumer:
    """
    Ascolta i messaggi da Kafka e avvia la logica di business appropriata.
    """
    def __init__(self, bootstrap_servers: str, orchestrator: OrderOrchestrationService, group_id: str):
        self._consumer = AIOKafkaConsumer(
            AVAILABILITY_REQUEST_TOPIC,
            ORDER_ASSIGNMENT_TOPIC,
            ORDER_STATUS_REQUEST_TOPIC,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id=group_id,
            auto_offset_reset="latest"
        )
        self._orchestrator = orchestrator
        self._started = False

    async def start(self):
        if self._started: return
        try:
            await self._consumer.start()
            self._started = True
            print("✅ CONSUMER: Connesso a Kafka.")
        except KafkaConnectionError as e:
            raise KafkaConnectionError(f"❌ ERRORE CRITICO (Consumer): Impossibile connettersi a Kafka - {e}")

    async def stop(self):
        if self._started:
            await self._consumer.stop()
            print("🛑 CONSUMER: Disconnesso da Kafka.")

    async def listen(self):
        if not self._started: return
        print(f"🎧 CONSUMER: In ascolto sui topic...")
        
        async for msg in self._consumer:
            print(f"📬 CONSUMER: Messaggio ricevuto su topic '{msg.topic}'")
            try:
                # --- Logica di smistamento basata sul topic ---
                
                if msg.topic == AVAILABILITY_REQUEST_TOPIC:
                    # MIGLIORAMENTO: La validazione ora è nel blocco try
                    request = OrderRequest(**msg.value)
                    await self._orchestrator.check_availability_and_propose(request)
                
                elif msg.topic == ORDER_ASSIGNMENT_TOPIC:
                    order_data = Order(**msg.value)
                    await self._orchestrator.handle_newly_assigned_order(order_data)
                
                elif msg.topic == ORDER_STATUS_REQUEST_TOPIC:
                    request = StatusRequest(**msg.value)
                    await self._orchestrator.get_and_publish_status(request.order_id)

            # MIGLIORAMENTO: Ora cattura anche gli errori di validazione Pydantic
            except ValidationError as e:
                print(f"🔥 ERRORE di validazione del messaggio: {e}")
            except Exception as e:
                print(f"🔥 ERRORE durante l'elaborazione del messaggio dal topic {msg.topic}: {e}")