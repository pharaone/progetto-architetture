# 🧪 Test di Integrazione End-to-End

Test completi che verificano il funzionamento dell'intero sistema attraverso le API.

## 📋 Prerequisiti

### 1. Servizi in esecuzione:
```bash
# Vai nella cartella del kitchen service
cd kitchen_service

# Avvia tutti i servizi
docker-compose up -d

# Verifica che siano running
docker-compose ps

# Devono essere "Up":
# - etcd
# - redis-node-1, redis-node-2, redis-node-3
# - redis-cluster-init (completed)
# - kitchen-service-1 (porta 8001)
# - kitchen-service-2 (porta 8002)
# - kitchen-service-3 (porta 8003)
```

### 2. Dipendenze Python:
```bash
pip install requests
```

### 3. Verifica servizi online:
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## 🚀 Esecuzione Test

### 1️⃣ Test Kitchen Service (RACCOMANDATO - Funziona ora!)
```bash
cd tests
python3 integration_test_kitchen.py
```

**✅ TUTTI I 14 TEST PASSATI!**

**Cosa testa:**
- ✅ Health check delle cucine
- ✅ API stato cucina (current_load, max_load, is_operational)
- ✅ Menu CRUD completo (Create, Read, List, Restock, Delete)
- ✅ **Isolamento cucine**: Verifica che Kitchen 1 e Kitchen 2 abbiano menu separati
- ✅ Toggle stato operativo
- ✅ Lista ordini

### 2️⃣ Test Gestione Carico (Verifica bug fix)
```bash
cd tests
python3 test_load_management.py
```

**Cosa testa:**
- ✅ Carico cucina prima e dopo completamento ordine
- ✅ **Verifica che COMPLETED decrementi il load** (il bug che hai segnalato!)
- ✅ Analisi ordini per stato
- ✅ Transizioni di stato

### 3️⃣ Test Avanzati (Scenari complessi)
```bash
cd tests
python3 integration_test_advanced.py
```

**Cosa testa:**
- ✅ Menu CRUD completo
- ✅ Isolamento tra cucine
- ✅ Ciclo vita ordine (tutte le transizioni)
- ✅ **Completamento diretto**: PENDING → COMPLETED
- ✅ Ordini multipli simultanei + gestione carico

### 4️⃣ Test Base (Richiede Menu Service)
```bash
cd tests
python3 integration_test.py
```

**Nota:** Richiede che il menu service sia in esecuzione sulla porta 8000

**Cosa testa:**
- ✅ Integrazione completa menu service + kitchen service
- ✅ Creazione utente
- ✅ Creazione ordine end-to-end
- ✅ Flusso completo: creazione → assegnazione → completamento

## 🛠️ Utility

### Crea dati di test:
```bash
cd tests
python3 create_test_data.py
```

**Opzioni:**
1. Crea piatti in Kitchen 1 (5 piatti)
2. Crea piatti in Kitchen 2 (3 piatti)
3. Crea in entrambe le cucine
4. Mostra solo stato attuale

**Output esempio:**
```
🍽️  Creazione piatti di esempio in Kitchen 1...

✅ Spaghetti Carbonara - €12.50 (10 disponibili)
✅ Pizza Margherita - €8.00 (15 disponibili)
✅ Lasagna - €14.00 (8 disponibili)
✅ Risotto ai Funghi - €13.50 (12 disponibili)
✅ Tiramisù - €6.00 (20 disponibili)

Creati 5/5 piatti

━━━ Kitchen 1 ━━━
  Kitchen ID: 11111111-1111-1111-1111-111111111111
  Operational: ✅ True
  Load: 0/10
  Piatti nel menu: 5
  Ordini attivi: 0
  Ordini totali: 2
```

## 📊 Output Atteso

### Test Passato:
```
================================================================================
🎉 TUTTI I TEST PASSATI CON SUCCESSO!
================================================================================

Test passati: 10/10
```

### Test Fallito:
```
================================================================================
❌ ALCUNI TEST SONO FALLITI
================================================================================

Test passati: 8/10

Test falliti:
  ❌ Load Decrement: Carico non decrementato
  ❌ Menu CRUD: Status 500
```

## 🔍 Debug

### Se i test falliscono:

1. **Verifica che i servizi siano tutti running:**
   ```bash
   docker-compose ps
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   curl http://localhost:8000/health
   ```

2. **Controlla i log dei servizi:**
   ```bash
   docker-compose logs -f kitchen-service-1
   docker-compose logs -f menu-service
   ```

3. **Verifica i database:**
   ```bash
   # etcd
   etcdctl get --prefix "" --keys-only
   
   # Redis
   redis-cli -h localhost -p 7000 --scan --pattern "menu_*"
   ```

4. **Pulisci i database prima di re-testare:**
   ```bash
   cd kitchen_service/scripts
   ./clean_etcd.sh
   ./clean_redis.sh
   ```

## 🧪 Test Personalizzati

### Modifica le configurazioni:

Edita i file per cambiare:
- URL dei servizi
- API Key
- Timeout
- Dati di test

```python
# In integration_test.py o integration_test_advanced.py
MENU_SERVICE_URL = "http://localhost:8000"
KITCHEN_SERVICE_1_URL = "http://localhost:8001/api"
API_KEY = "changeme123"
```

## 📈 Metriche

I test verificano:
- ⏱️ **Performance**: Tempi di risposta delle API
- 🔒 **Isolamento**: Separazione tra cucine
- 📊 **Consistenza**: Carico cucina e stati ordini
- 🔄 **Idempotenza**: Aggiornamenti multipli stesso stato
- 🚦 **Transizioni**: Tutti i possibili cambi di stato

## 🎯 Utilizzo in CI/CD

```bash
# Esegui i test e cattura exit code
python3 tests/integration_test.py
if [ $? -eq 0 ]; then
  echo "✅ Integration tests passed"
else
  echo "❌ Integration tests failed"
  exit 1
fi
```

## 📝 Note

- I test creano e puliscono automaticamente i dati di test
- Ogni test è isolato e non dovrebbe interferire con gli altri
- I test attendono alcuni secondi per la propagazione asincrona (Kafka, etcd)
- Se un test fallisce, controlla sempre i log dei servizi per il dettaglio dell'errore

