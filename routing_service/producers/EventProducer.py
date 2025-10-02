# routing_service/producers/EventProducer.py
import os
import json
import asyncio
from typing import Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

# legge la variabile d'ambiente se non viene passato bootstrap_servers al costruttore
DEFAULT_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

class EventProducer:
    """
    Producer con retry esponenziale all'avvio e cleanup sicuro.
    Usa `KAFKA_BOOTSTRAP` come default se non specificato.
    """
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or DEFAULT_BOOTSTRAP
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        self._started = False
        self._lock = asyncio.Lock()

    async def start(self, retries: int = 10, base_backoff: float = 1.0):
        """
        Avvia l'AIOKafkaProducer con retry esponenziale.
        - retries: numero massimo di tentativi
        - base_backoff: tempo base in secondi per il backoff esponenziale
        Lancia KafkaConnectionError se non riesce.
        """
        async with self._lock:
            if self._started:
                return
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    await self._producer.start()
                    self._started = True
                    print("✅ PRODUCER connesso a", self.bootstrap_servers)
                    return
                except KafkaConnectionError as e:
                    last_exc = e
                    # backoff esponenziale con cap a 10s
                    backoff = base_backoff * (2 ** (attempt - 1))
                    if backoff > 10:
                        backoff = 10
                    print(f"⚠️ Tentativo {attempt} fallito: impossibile connettersi a {self.bootstrap_servers}: {e} — retry in {backoff:.1f}s")
                    await asyncio.sleep(backoff)
            # se siamo qui, non siamo riusciti: puliamo e rilanciamo eccezione
            try:
                await self._producer.stop()
            except Exception:
                pass
            raise last_exc

    async def stop(self):
        async with self._lock:
            if not self._started:
                return
            try:
                await self._producer.stop()
            finally:
                self._started = False
                print("🛑 PRODUCER disconnesso")

    def _require_started(self):
        if not self._started:
            raise RuntimeError("Producer non avviato. Chiama start() prima di publish.")

    async def publish_disponibilita(self, order_request: dict):
        self._require_started()
        await self._producer.send_and_wait("disponibilita", value=order_request)
        print(f"📤 disponibilita → {order_request}")

    async def publish_conferma_ordine(self, order: dict):
        self._require_started()
        await self._producer.send_and_wait("conferma_ordine", value=order)
        print(f"📤 conferma_ordine → {order}")

    async def publish_order_status(self, status_payload: dict):
        self._require_started()
        await self._producer.send_and_wait("orderstatus", value=status_payload)
        print(f"📤 orderstatus → {status_payload}")
