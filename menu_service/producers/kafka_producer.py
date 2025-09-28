import json

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError


class EventProducer:
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
