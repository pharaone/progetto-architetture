import json
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from pydantic import ValidationError
import uuid

# Import dei modelli
from model.messaging_models import OrderRequest, OrderAssignment
from model.status import OrderStatus, StatusEnum

# Import dei servizi e producer
from service.kitchen_service import KitchenService
from service.status_service import OrderStatusService
from producers.producers import EventProducer

# Nomi dei topic Kafka
AVAILABILITY_REQUEST_TOPIC = "disponibilita"
ORDER_ASSIGNMENT_TOPIC = "conferma_ordine"
STATUS_TOPIC = "status"
# CONSIGLIO: Aggiungi un topic separato per le risposte per evitare loop
#STATUS_RESPONSE_TOPIC = "status_responses"


class EventConsumer:
    """
    Consumer robusto e resiliente che ascolta i messaggi da Kafka,
    gestisce la creazione dello stato iniziale degli ordini e si riconnette
    automaticamente in caso di errori.
    """
    def __init__(self, bootstrap_servers: str, kitchen_service_instance: KitchenService, status_service: OrderStatusService, group_id: str, producer: EventProducer):
        self._consumer = AIOKafkaConsumer(
            AVAILABILITY_REQUEST_TOPIC,
            ORDER_ASSIGNMENT_TOPIC,
            STATUS_TOPIC,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id=group_id,
            auto_offset_reset="latest",
            retry_backoff_ms=1000
        )
        self._kitchen_service = kitchen_service_instance
        self._status_service = status_service
        self._producer = producer
        self._started = False

    async def start(self):
        if self._started:
            return
        try:
            await self._consumer.start()
            self._started = True
            print("✅ CONSUMER: Connesso a Kafka.")
        except KafkaConnectionError as e:
            raise KafkaConnectionError(
                f"❌ ERRORE CRITICO (Consumer): Impossibile connettersi a Kafka - {e}"
            )

    async def stop(self):
        if self._started:
            await self._consumer.stop()
            print("🛑 CONSUMER: Disconnesso da Kafka.")

    async def listen(self):
        if not self._started:
            return
        print("🎧 CONSUMER: Avvio del loop di ascolto principale...")

        while True:
            try:
                print("🏁 CONSUMER: In attesa di nuovi messaggi...")
                async for msg in self._consumer:
                    print(f"📬 CONSUMER: Messaggio ricevuto su topic '{msg.topic}'")
                    try:
                        # --- Logica di smistamento basata sul topic ---
                        if msg.topic == AVAILABILITY_REQUEST_TOPIC:
                            request = OrderRequest(**msg.value)
                            print(f"➡️ Richiesta disponibilità ricevuta: {request}")
                            await self._kitchen_service.handle_availability_request(request)

                        elif msg.topic == ORDER_ASSIGNMENT_TOPIC:
                            order_assignment = OrderAssignment(**msg.value)
                            print(f"➡️ Assegnazione ordine ricevuta: {order_assignment}")

                            print(f"🔧 Creazione dello stato iniziale 'pending' per l'ordine {order_assignment.order_id}...")
                            initial_status = OrderStatus(
                                order_id=order_assignment.order_id,
                                status=StatusEnum.PENDING,
                                kitchen_id=order_assignment.kitchen_id
                            )
                            await self._status_service.save(initial_status)
                            print(f"✅ Stato iniziale per ordine {order_assignment.order_id} salvato in etcd.")
                            
                            await self._kitchen_service.handle_order_assignment(order_assignment)

                        # --- INIZIO BLOCCO LOGICA CORRETTA PER STATUS_UPDATES ---
                        elif msg.topic == STATUS_TOPIC:
                            # 1. Estrai l'ID dell'ordine (comune a entrambi i casi)
                            order_id = uuid.UUID(msg.value["order_id"])

                            # 2. Controlla se il messaggio è una RICHIESTA DI AGGIORNAMENTO o una QUERY
                            if "status" in msg.value:
                                # --- CASO B: Richiesta di Aggiornamento Stato ---
                                # Il messaggio contiene sia 'order_id' che 'status'
                                print(f"➡️ Richiesta di aggiornamento stato per ordine {order_id}...")
                                
                                # Convalida e converte la stringa dello stato in un Enum
                                new_status_enum = StatusEnum(msg.value["status"])
                                
                                # Chiama il servizio di aggiornamento. La logica "pubblica solo se diverso"
                                # è già gestita internamente dal repository.
                                await self._status_service.update_status(order_id, new_status_enum)
                            
                            else:
                                # --- CASO A: Query Stato ---
                                # Il messaggio contiene solo 'order_id'
                                print(f"➡️ Query stato per ordine {order_id}...")
                                
                                # Cerca lo stato corrente in etcd
                                order_status_obj = await self._status_service.get_by_id(order_id)
                                
                                if order_status_obj:
                                    # Pubblica la risposta. Per evitare loop, la risposta dovrebbe
                                    # andare su un topic dedicato come "status_responses".
                                    # Per ora, riutilizziamo la funzione esistente, ma la soluzione
                                    # ideale è avere un topic di risposta separato.
                                    print(f"✅ Trovato stato: {order_status_obj.status.value}. Invio risposta...")
                                    await self._producer.publish_status_update(order_status_obj)
                                else:
                                    print(f"⚠️ Nessuno stato trovato per la query sull'ordine {order_id}.")
                        # --- FINE BLOCCO LOGICA CORRETTA ---

                    except (ValidationError, KeyError, ValueError) as e:
                        print(f"🔥 ERRORE di formato o dati mancanti nel messaggio: {e}")
                    except Exception as e:
                        print(f"🔥 ERRORE durante l'elaborazione del messaggio: {e}")

            except asyncio.CancelledError:
                print("CONSUMER: Task di ascolto annullato.")
                break
            except Exception as e:
                print(f"🔥 ERRORE CRITICO nel loop del consumer: {e}. Riprovo tra 5 secondi...")
                await asyncio.sleep(5)