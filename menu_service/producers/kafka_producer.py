import json
import uuid

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