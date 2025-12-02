# 👨‍🍳 Kitchen Service Frontend

Frontend moderno per la gestione della cucina, con tema verde.

## 🚀 Avvio

Il frontend è una Single Page Application (SPA) statica. Puoi servirla in diversi modi:

### Opzione 1: Python HTTP Server
```bash
cd kitchen_service/frontend
python3 -m http.server 8080
```

Poi apri: http://localhost:8080

### Opzione 2: Node.js HTTP Server
```bash
cd kitchen_service/frontend
npx http-server -p 8080
```

### Opzione 3: Live Server (VS Code Extension)
Clicca destro su `index.html` → "Open with Live Server"

## 🎯 Funzionalità

### 📋 Sezione Ordini
- **Visualizzazione in tempo reale**: Gli ordini si aggiornano automaticamente ogni 10 secondi
- **Gestione stati**: 
  - ⏳ Pending → 👨‍🍳 Preparing
  - 👨‍🍳 Preparing → 🎉 Ready for Pickup
  - 🎉 Ready → ✨ Completed
- **Card moderne**: Design accattivante con colori per ogni stato

### 🍽️ Sezione Menu
- **Aggiungi piatti**: Form modale con validazione
- **Campi richiesti**:
  - Nome piatto
  - Prezzo (€)
  - Quantità disponibile

### 📊 Sezione Stato Cucina
- **Disponibilità**: Attiva/Disattiva la cucina
- **Carico attuale**: Numero di ordini in preparazione
- **Capacità massima**: Limite di ordini gestibili

## 🔧 Configurazione

Il file `script.js` contiene le configurazioni:

```javascript
const API_BASE_URL = 'http://localhost:8001/api';  // URL del Kitchen Service
const API_KEY = 'changeme123';                      // API Key per operazioni protette
const KITCHEN_ID = '11111111-1111-1111-1111-111111111111';  // ID della Kitchen 1
```

### ⚙️ Modificare per Kitchen 2 o 3

Per puntare a una cucina diversa, modifica in `script.js`:

**Kitchen 2**:
```javascript
const API_BASE_URL = 'http://localhost:8002/api';
const KITCHEN_ID = '22222222-2222-2222-2222-222222222222';
```

**Kitchen 3**:
```javascript
const API_BASE_URL = 'http://localhost:8003/api';
const KITCHEN_ID = '33333333-3333-3333-3333-333333333333';
```

## 🎨 Tema

Il frontend usa un **tema verde** ispirato alla natura e alla freschezza:

- **Colori primari**: `#10b981` (emerald-500), `#059669` (emerald-600)
- **Gradiente**: Linear gradient verde per header e buttons
- **Accenti**: Verde per stati positivi, rosso per errori

## 📡 Endpoint API Utilizzati

### GET `/api/orders`
Recupera tutti gli ordini assegnati alla cucina

### PATCH `/api/orders/{order_id}/status`
Aggiorna lo stato di un ordine
- **Headers**: `X-API-Key: changeme123`
- **Body**: `{ "status": "preparing" }`

### GET `/api/kitchen`
Recupera lo stato della cucina

### PATCH `/api/kitchen?is_operational={bool}`
Cambia lo stato operativo della cucina
- **Headers**: `X-API-Key: changeme123`

### POST `/api/menu/dishes`
Aggiungi un nuovo piatto al menu
- **Headers**: `X-API-Key: changeme123`, `Content-Type: application/json`
- **Body**: 
```json
{
  "dish_id": "uuid",
  "name": "string",
  "price": 12.50,
  "available_quantity": 10
}
```

## 🔐 Sicurezza

- L'API Key è hardcoded per semplicità (ambiente di sviluppo)
- In produzione, usare variabili d'ambiente o un sistema di autenticazione

## 🎯 Auto-Refresh

Gli ordini si aggiornano automaticamente ogni 30 secondi:
```javascript
setInterval(loadOrders, 30000);
```

Puoi modificare l'intervallo o disabilitarlo commentando questa riga.

## 📱 Responsive

Il frontend è completamente responsive e funziona su:
- 💻 Desktop
- 📱 Tablet
- 📞 Mobile

## 🐛 Troubleshooting

### Gli ordini non si caricano
- Verifica che il kitchen service sia in esecuzione su porta 8001
- Controlla la console del browser per errori CORS
- Verifica che l'API_BASE_URL sia corretto

### Errore 403 Forbidden
- Controlla che l'API_KEY sia corretta (`changeme123`)
- Verifica che corrisponda a `INTERNAL_API_KEY` in `settings.py`

### Modal non si apre
- Controlla la console per errori JavaScript
- Verifica che il file `script.js` sia caricato correttamente

## 🎨 Personalizzazione

### Cambiare il colore del tema
Modifica in `styles.css`:

```css
/* Cambia il colore primario */
background: linear-gradient(135deg, #10b981 0%, #059669 100%);

/* Cambia con il tuo colore preferito */
background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
```

### Modificare l'intervallo di auto-refresh
In `script.js`:
```javascript
// Da 10 secondi (10000ms) a 30 secondi (30000ms)
setInterval(loadOrders, 30000);
```

## 📚 Struttura File

```
frontend/
├── index.html      # Struttura HTML
├── styles.css      # Stili con tema verde
├── script.js       # Logica JavaScript
└── README.md       # Questa documentazione
```

## 🚀 Features

- ✅ Design moderno e pulito
- ✅ Tema verde accattivante
- ✅ Auto-refresh degli ordini
- ✅ Animazioni smooth
- ✅ Responsive design
- ✅ Notifiche real-time
- ✅ Modal per aggiungere piatti
- ✅ Gestione completa ordini
- ✅ Dashboard stato cucina

Buon lavoro in cucina! 👨‍🍳✨



