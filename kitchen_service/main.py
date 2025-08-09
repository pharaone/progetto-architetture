# file: main.py

import asyncio
import uvicorn
# 1. Importiamo i componenti chiave già istanziati nel file dell'API.
#    Questo è fondamentale per garantire che sia l'API sia il Consumer
#    usino le STESSE istanze dei servizi e dei repository.
from api.api import app, orchestration_service, event_producer

# 2. Importiamo la classe del nostro consumatore di eventi.
from consumers.consumers import EventConsumer

# 3. Definiamo le costanti di configurazione in un unico posto.
KAFKA_BROKERS = "localhost:9092"
KITCHEN_GROUP_ID = "kitchen-service-group-1"
API_HOST = "0.0.0.0"
API_PORT = 8000

async def main():
    """
    Funzione principale asincrona che avvia, orchestra e gestisce
    il ciclo di vita di tutti i componenti del microservizio.
    """
    print("🚀 Avvio del Microservizio Cucina...")

    # 1. Istanziamo il consumer, "iniettando" l'orchestratore
    #    che abbiamo importato dal modulo API.
    consumer = EventConsumer(
        bootstrap_servers=KAFKA_BROKERS,
        orchestrator=orchestration_service,
        group_id=KITCHEN_GROUP_ID
    )

    # 2. Prepariamo la configurazione per il server web Uvicorn.
    config = uvicorn.Config(app, host=API_HOST, port=API_PORT, log_level="info")
    server = uvicorn.Server(config)

    # 3. Usiamo un blocco try...finally per garantire uno spegnimento pulito.
    try:
        # 4. Avviamo i componenti di messaging (producer e consumer).
        #    È importante avviarli prima di iniziare ad ascoltare.
        await event_producer.start()
        await consumer.start()

        # 5. Creiamo due "task" concorrenti: uno per il server API
        #    e uno per il loop di ascolto del consumer Kafka.
        api_task = asyncio.create_task(server.serve())
        consumer_task = asyncio.create_task(consumer.listen())

        # 6. `asyncio.gather` li esegue in parallelo. Il programma rimarrà
        #    in questa riga finché uno dei due task non terminerà o non verrà interrotto.
        await asyncio.gather(api_task, consumer_task)

    except Exception as e:
        print(f"🔥 ERRORE CRITICO durante l'esecuzione: {e}")
    finally:
        # 7. Quando usciamo dal programma (es. con Ctrl+C), questa sezione
        #    garantisce che le connessioni vengano chiuse correttamente.
        print("\n🛑 Spegnimento dei servizi...")
        await consumer.stop()
        await event_producer.stop()
        print("✅ Microservizio Cucina fermato correttamente.")

if __name__ == "__main__":
    try:
        # Eseguiamo la nostra funzione principale asincrona.
        asyncio.run(main())
    except KeyboardInterrupt:
        # Gestisce l'interruzione manuale (Ctrl+C) in modo pulito.
        print("\n🚦 Rilevato arresto manuale...")