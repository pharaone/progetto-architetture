# Progetto Microservizi — Relazione Tecnica Completa

> **Servizi principali:** `menu_service`, `routing_service`, `kitchen_service`  
> **Infrastruttura:** Docker Compose esterno con Kafka + Zookeeper (root `docker-compose.yml`)  
> Ogni microservizio è contenuto in un proprio container e può essere eseguito indipendentemente.  
> Ogni **istanza di cucina** corrisponde a un container dedicato di `kitchen_service`, che rappresenta una cucina fisica distinta.

---

## Indice
1. [Analisi dei requisiti](#analisi-dei-requisiti)  
2. [Progettazione architetturale](#progettazione-architetturale)  
3. [Gestione dei dati e database](#gestione-dei-dati-e-database)  
4. [Piano di sviluppo](#piano-di-sviluppo)  
5. [Implementazione del PoC](#implementazione-del-poc)  
6. [Risultati dei test](#risultati-dei-test)  
7. [Guida al deployment e all’esecuzione](#guida-al-deployment-e-allesecuzione)  
8. [Evoluzioni future](#evoluzioni-future)

---

## Analisi dei requisiti

### Requisiti funzionali
- **Gestione menu:** CRUD piatti, esposizione del menu al frontend o ad altri servizi (`menu_service`).
- **Gestione ordini:** creazione, aggiornamento e monitoraggio dello stato ordine.
- **Instradamento ordini:** selezione automatica della migliore cucina in base alla distanza, disponibilità e carico.
- **Comunicazione asincrona:** scambio eventi tra microservizi tramite Kafka (order creation, acceptance, status update).
- **Stato ordine:** tracciamento dello stato ciclo vita (`PENDING`, `ASSIGNED`, `COOKING`, `COMPLETED`, ecc.).
- **API REST:** interfacce FastAPI per comunicazioni interne/esterne.

### Requisiti non funzionali
- **Scalabilità:** ogni servizio è eseguibile in container isolato e scalabile orizzontalmente.
- **Affidabilità:** messaggistica resiliente con Kafka e retry automatici.
- **Configurabilità:** parametri ambientali esterni (.env o variabili Docker).
- **Semplicità:** il PoC deve essere avviabile interamente via Docker Compose.
- **Osservabilità:** log strutturati, health-check endpoint e metriche base.

---

## Progettazione architetturale

### Panoramica generale
Il sistema è composto da tre microservizi principali che comunicano tramite eventi Kafka e API HTTP.

- **menu_service:**  
  Gestisce utenti, ordini e piatti. Espone API pubbliche e si interfaccia con il `routing_service` per assegnare ordini a una cucina.
- **routing_service:**  
  Coordina l'instradamento degli ordini. Riceve richieste da `menu_service`, consulta il grafo delle cucine e decide quale cucina assegnare.
- **kitchen_service:**  
  Rappresenta una singola cucina fisica. Ogni istanza del servizio gestisce il proprio menu, disponibilità e stati ordini.

### Infrastruttura e containerizzazione
- **Docker Compose principale (root):** gestisce i container Kafka e Zookeeper per la messaggistica.  
- **Container microservizi:** ciascun microservizio dispone di un proprio `Dockerfile` e può essere avviato come container indipendente.  
- **Multi-istanza `kitchen_service`:** ogni container rappresenta una cucina distinta, con un proprio `KITCHEN_ID` e porta dedicata.  

Esempio:
```bash
# Avvio di tre istanze di kitchen_service
docker run -d --name kitchen1 -e KITCHEN_ID=1 -p 8010:8000 kitchen_service
docker run -d --name kitchen2 -e KITCHEN_ID=2 -p 8011:8000 kitchen_service
docker run -d --name kitchen3 -e KITCHEN_ID=3 -p 8012:8000 kitchen_service
```

### Comunicazione
- **Eventi Kafka:** per ordini, accettazioni e aggiornamenti di stato.  
- **Chiamate REST interne:** `menu_service → routing_service`, `routing_service → kitchen_service`.  
- **Cache e configurazione:** Redis Cluster e etcd per stato e discovery.

### Motivazioni tecniche
- **FastAPI:** framework asincrono e performante per microservizi Python.  
- **Kafka:** messaggistica affidabile e disaccoppiata.  
- **Redis Cluster:** caching distribuito per ridurre latenza e migliorare disponibilità.  
- **etcd:** registro configurazioni e discovery.  
- **Containerizzazione:** isolamento e scalabilità orizzontale semplice.

---

## Gestione dei dati e database

### PostgreSQL — Database relazionale
- Utilizzato da `menu_service` per memorizzare **utenti, ordini e piatti**.  
- Gestito tramite ORM SQLAlchemy con repository dedicati.  
- Garantisce coerenza e integrità referenziale.

### etcd — Configurazione distribuita
- Utilizzato da `kitchen_service` per configurazioni runtime e service discovery.  
- Archivia parametri di rete e identificatori univoci di cucina (`KITCHEN_ID`).

### Redis Cluster — Cache e stato temporaneo
- Utilizzato per caching degli ordini, sincronizzazione e stato in tempo reale.  
- Ogni istanza Redis è containerizzata nel `docker-compose.yml` di `kitchen_service`.  
- Accesso configurato via `REDIS_CLUSTER_NODES` in `settings.py`.

| Componente | Tipo | Scopo | Microservizi |
|-------------|------|-------|---------------|
| PostgreSQL | Relazionale | Persistenza utenti, ordini, menu | `menu_service` |
| etcd | Key-Value store | Configurazione e discovery | `kitchen_service` |
| Redis Cluster | In-memory cache | Cache runtime e stato distribuito | `kitchen_service`, `routing_service` |

---

## Piano di sviluppo

1. **Fase 1 - Analisi congiunta e definizione dei componenti**  
   Il progetto è iniziato con una riunione di analisi condivisa tra i membri del team, durante la quale sono stati:
   - Individuati i tre microservizi principali: menu_service, routing_service e kitchen_service;
   - Assegnate le responsabilità di sviluppo a ciascun componente;
   - Definite le interazioni e le dipendenze principali tra i servizi.

   Questa fase ha permesso di stabilire una visione architetturale comune e di distribuire i compiti in modo chiaro.

2. **Fase 2 — Definizione della comunicazione e dei topic Kafka**

    Prima di iniziare lo sviluppo, il gruppo ha concentrato l’attenzione sulla comunicazione inter-servizi, definendo:
   - I topic Kafka da utilizzare per lo scambio asincrono di messaggi (order.requested, order.acceptance, order.status);  
   - La struttura standard dei messaggi JSON, con chiavi condivise (order_id, kitchen_id, status, ecc.);
   - La sequenza logica dei flussi (menu → routing → kitchen e ritorno via callback/eventi);
   - Le regole di business comuni, come la gestione dello stato ordine e i tempi di risposta delle cucine.

    Questo allineamento iniziale ha garantito la compatibilità e l’interoperabilità tra i microservizi sviluppati in parallelo.

3. **Fase 3 — Sviluppo indipendente dei microservizi**  
   Ogni sviluppatore ha realizzato in autonomia il proprio microservizio.

    Durante questa fase, ciascun servizio è stato testato in locale con mock dei producer e consumer Kafka.

4. **Fase 4 — Integrazione e test end-to-end**  
   Completato lo sviluppo individuale, i servizi sono stati integrati in un ambiente comune:  
   - Avvio dei tre microservizi in container separati con rete Docker condivisa;  
   - Utilizzo del docker-compose principale per gestire Kafka e Zookeeper;
   - Simulazione di più istanze di cucina, ciascuna in un container kitchen_service distinto;
   - Test funzionali dell’intero flusso (ordine → routing → cucina → assegnazione) tramite Postman e test automatici pytest.

   Questa fase ha confermato il corretto scambio di messaggi e la coerenza degli stati ordine.
4. **Fase 5 — Validazione finale e rifiniture**  
   L’ultima fase ha riguardato la stabilizzazione e rifinitura del PoC: 
   - Miglioramento dei log, gestione errori e cleanup del codice;  
   - Verifica delle dipendenze e ottimizzazione dei Dockerfile;
   - Redazione della documentazione tecnica e guida di deployment.

   Il risultato finale è un PoC completamente funzionante, modulare e facilmente estendibile.
---

## Implementazione del PoC

### menu_service
- **API pubbliche:** gestione ordini (`/orders`) e menu (`/menu`).  
- **Integrazione routing:** invio HTTP POST a `/routing/create-order`.  
- **Database:** repository SQLAlchemy per entità `Order`, `Dish`, `User`.

### routing_service
- **API interne:** `/routing/*`.  
- **Decisione assegnazione:** finestra decisionale (`MenuRoutingService`) e grafo (`KitchenRoutingService`).  
- **Eventi Kafka:** gestione accettazioni e stati tramite `EventProducer` e `EventConsumers`.

### kitchen_service
- **API locali:** per disponibilità, menu e stato ordini.  
- **Consumer Kafka:** ascolta richieste e pubblica accettazioni.  
- **Configurazione:** tramite `settings.py` con `KITCHEN_ID`, Redis, ecc.  
- **Test automatici:** suite `pytest` completa.

---

## Test
- **Da definire** 
---

## Guida al deployment e all’esecuzione

### 1. Avvio infrastruttura base
Nel root del progetto:
```bash
docker compose up -d
# Avvia Zookeeper e Kafka
```

### 2. Avvio Redis Cluster e etcd
```bash
cd kitchen_service
docker compose up -d
```

### 3. Avvio microservizi
```bash
# Routing service
cd routing_service
docker build -t routing_service .
docker run -d --network app-network -p 8080:8080 routing_service

# Menu service
cd ../menu_service
docker build -t menu_service .
docker run -d --network app-network -p 8001:8001 menu_service
```

### 4. Avvio istanze di kitchen_service
```bash
cd ../kitchen_service
docker build -t kitchen_service .

docker run -d --name kitchen1 --network app-network -e KITCHEN_ID=1 -p 8010:8000 kitchen_service
docker run -d --name kitchen2 --network app-network -e KITCHEN_ID=2 -p 8011:8000 kitchen_service
docker run -d --name kitchen3 --network app-network -e KITCHEN_ID=3 -p 8012:8000 kitchen_service
```
---

## Evoluzioni future

1. **Utilizzo API google maps** utilizzo di api per il calcolo delle cucine più vicine.
2.  **Routing dinamico:** calcolo pesi in tempo reale (traffico, carico).  
3.  **Scalabilità:** deployment Kubernetes, autoscaling e bilanciamento traffico.  
4.  **Sicurezza:** autenticazione JWT.

---

**Autori:** Stefano Imbalzano - Emanuele Antonio Faraone - Davide Vitale
