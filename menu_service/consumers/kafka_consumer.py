import json
import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from fastapi import Depends
from pydantic import ValidationError

from config.dependecies_configuration import get_settings
from config.settings import Settings
from consumers.message.order_status_message import OrderStatusMessage
from service.order_service import OrderService

logger = logging.getLogger(__name__)

ORDER_STATUS_TOPIC = "order_status_topic"


class EventConsumer:
    """
    Ascolta i messaggi da Kafka e avvia la logica di business appropriata.
    """

    def __init__(self, order_service: OrderService):
        self._consumer = AIOKafkaConsumer(
            ORDER_STATUS_TOPIC,
            bootstrap_servers=get_settings().KAFKA_BROKERS,
            group_id=get_settings().GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=False,  # commit manuale
        )
        self._started = False
        self._order_service = order_service

    async def start(self):
        if self._started:
            return
        try:
            await self._consumer.start()
            self._started = True
            logger.info("✅ CONSUMER: Connesso a Kafka.")
        except KafkaConnectionError as e:
            logger.error(f"❌ Errore critico: impossibile connettersi a Kafka - {e}")
            raise

    async def stop(self):
        if self._started:
            await self._consumer.stop()
            logger.info("🛑 CONSUMER: Disconnesso da Kafka.")
            self._started = False

    async def listen(self):
        if not self._started:
            return
        logger.info("🎧 CONSUMER: In ascolto su topic...")

        async for msg in self._consumer:
            logger.info(f"📬 Messaggio ricevuto su topic '{msg.topic}'")
            try:
                if msg.topic == ORDER_STATUS_TOPIC:
                    request = OrderStatusMessage(**msg.value)
                    self._order_service.update_order_status(request)

                await self._consumer.commit()

            except ValidationError as e:
                logger.error(f"🔥 Errore di validazione: {e}")
                # TODO: inviare a DLQ
            except Exception as e:
                logger.exception(f"🔥 Errore durante l'elaborazione: {e}")
                # TODO: inviare a DLQ
