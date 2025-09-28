import json
from aiokafka import AIOKafkaProducer

class EventProducer:
    """
    Producer minimale:
      - disponibilita      → richiesta disponibilità alle cucine
      - conferma_ordine    → ordine assegnato a una cucina
      - orderstatus        → inoltro degli aggiornamenti di stato verso il servizio menu
    """
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        self._started = False

    async def start(self):
        if self._started:
            return
        await self._producer.start()
        self._started = True
        print("✅ PRODUCER connesso")

    async def stop(self):
        if not self._started:
            return
        await self._producer.stop()
        self._started = False
        print("🛑 PRODUCER disconnesso")

    async def publish_disponibilita(self, order_request: dict):
        await self._producer.send_and_wait("disponibilita", value=order_request)
        print(f"📤 disponibilita → {order_request}")

    async def publish_conferma_ordine(self, order: dict):
        await self._producer.send_and_wait("conferma_ordine", value=order)
        print(f"📤 conferma_ordine → {order}")

    async def publish_order_status(self, status_payload: dict):
        """
        Inoltra gli aggiornamenti di stato verso il microservizio MENU sul topic 'orderstatus'.
        Esempio payload: {'order_id': '...', 'status': 'preparing'}
        """
        await self._producer.send_and_wait("orderstatus", value=status_payload)
        print(f"📤 orderstatus → {status_payload}")
