# Menu Service Frontend

Un'interfaccia web moderna e responsive per gestire il Menu Service, che permette di utilizzare tutti i router disponibili del servizio.

## 🚀 Caratteristiche

- **Gestione Menu**: Visualizza tutti i piatti disponibili e aggiungi nuovi piatti
- **Gestione Utenti**: Registrazione, login e conferma utenti
- **Gestione Ordini**: Crea nuovi ordini, controlla lo stato e visualizza i tuoi ordini
- **Design Moderno**: Interfaccia responsive con effetti glassmorphism
- **Notifiche**: Sistema di notifiche per feedback immediato

## 📁 Struttura File

```
frontend/
├── index.html          # Pagina principale
├── styles.css          # Stili CSS
├── script.js           # Logica JavaScript
└── README.md           # Documentazione
```

## 🛠️ Come Utilizzare

### 1. Avvia il Menu Service

Prima di utilizzare il frontend, assicurati che il Menu Service sia in esecuzione:

```bash
cd progetto-architetture/menu_service
python main.py
```

Il servizio sarà disponibile su `http://localhost:8000`

### 2. Apri il Frontend

Apri il file `index.html` nel tuo browser preferito. Puoi:

- Aprire direttamente il file dal file system
- Utilizzare un server HTTP locale (es. Live Server in VS Code)
- Servire i file tramite un web server

### 3. Utilizzo delle Funzionalità

#### 🍽️ Gestione Menu
- **Visualizza Menu**: I piatti vengono caricati automaticamente
- **Aggiungi Piatto**: Clicca su "Aggiungi Piatto" per aprire il form
- **Informazioni Piatto**: Ogni piatto mostra nome, prezzo, descrizione e ID

#### 👥 Gestione Utenti
- **Registrazione**: Inserisci email, password e regione
- **Login**: Accedi con email e password
- **Conferma**: Conferma un utente esistente

#### 📦 Gestione Ordini
- **Nuovo Ordine**: Inserisci ID piatto e ID utente
- **Stato Ordine**: Controlla lo stato di un ordine specifico
- **I Miei Ordini**: Visualizza tutti gli ordini di un utente

## 🔧 Configurazione

### URL del Servizio

Se il Menu Service è in esecuzione su una porta diversa, modifica la variabile `API_BASE_URL` in `script.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Cambia porta se necessario
```

### CORS

Se riscontri problemi di CORS, assicurati che il Menu Service abbia le configurazioni CORS appropriate per permettere le richieste dal frontend.

## 🎨 Design

Il frontend utilizza un design moderno con:

- **Glassmorphism**: Effetti di vetro smerigliato
- **Gradienti**: Sfondo con gradienti colorati
- **Responsive**: Adattabile a tutti i dispositivi
- **Animazioni**: Transizioni fluide e hover effects
- **Notifiche**: Sistema di notifiche elegante

## 📱 Responsive Design

L'interfaccia si adatta automaticamente a:

- **Desktop**: Layout a griglia ottimizzato
- **Tablet**: Layout adattivo con colonne ridotte
- **Mobile**: Layout a singola colonna

## 🔍 Debugging

### Console del Browser

Apri gli strumenti di sviluppo del browser (F12) per:

- Visualizzare errori JavaScript
- Monitorare le richieste di rete
- Debug delle chiamate API

### Log del Servizio

Controlla i log del Menu Service per eventuali errori lato server.

## 🚨 Risoluzione Problemi

### Errore di Connessione
- Verifica che il Menu Service sia in esecuzione
- Controlla che la porta 8000 sia libera
- Verifica l'URL in `script.js`

### CORS Errors
- Aggiungi configurazioni CORS al Menu Service
- Utilizza un server HTTP locale per servire il frontend

### Errori di Formato
- Assicurati di utilizzare UUID validi per ID
- Verifica il formato dei dati inseriti nei form

## 📝 Note

- Gli ID devono essere in formato UUID valido
- Le password sono case-sensitive
- I prezzi devono essere numerici con decimali
- Le descrizioni supportano testo multi-riga

## 🔄 Aggiornamenti

Per aggiornare il frontend:

1. Modifica i file HTML/CSS/JS
2. Ricarica la pagina nel browser
3. Le modifiche saranno immediatamente visibili

---

**Sviluppato per il progetto architetture software** 🏗️
