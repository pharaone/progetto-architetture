import json
import asyncio
from aiokafka import AIOKafkaConsumer

from routing_service.producers.EventProducer import EventProducer
from routing_service.service.MenuRoutingService import MenuRoutingService

class EventConsumer:
    """
    Consumer:
      - accettazione → passa a MenuRoutingService.on_acceptance(...)
      - status       → se RISPOSTA (ha 'status'): salva su service e inoltra su 'orderstatus'
                       se RICHIESTA (senza 'status'): la ignora (la deve gestire la kitchen)
    """
    def __init__(self,
                 menu_service: MenuRoutingService,
                 producer: EventProducer,
                 bootstrap_servers: str = "localhost:9092"):

        self._menu = menu_service
        self._producer = producer

        self.acceptance_consumer = AIOKafkaConsumer(
            "accettazione",
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="routing-accettazione",
            auto_offset_reset="latest",
        )
        self.status_consumer = AIOKafkaConsumer(
            "status",
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="routing-status",
            auto_offset_reset="latest",
        )
        self._started = False

    async def start(self):
        if self._started:
            return
        await self.acceptance_consumer.start()
        await self.status_consumer.start()
        self._started = True
        print("CONSUMERS connessi")

    async def stop(self):
        if not self._started:
            return
        await self.acceptance_consumer.stop()
        await self.status_consumer.stop()
        self._started = False
        print("CONSUMERS disconnessi")

    async def run(self):
        async def _acc_loop():
            async for msg in self.acceptance_consumer:
                try:
                    await self._menu.on_acceptance(msg.value)
                except Exception as e:
                    print(f" errore on_acceptance: {e}")

        async def _status_loop():
            async for msg in self.status_consumer:
                payload = msg.value  # dict
                try:
                    if "status" in payload:
                        # RISPOSTA/aggiornamento da kitchen → salva e inoltra a MENU
                        self._menu.save_status(payload["order_id"], payload["status"])
                        await self._producer.publish_order_status(payload)
                    else:
                        # RICHIESTA: ignorata dal routing (è per la kitchen)
                        pass
                except Exception as e:
                    print(f" errore status handling: {e}")

        await asyncio.gather(_acc_loop(), _status_loop())
