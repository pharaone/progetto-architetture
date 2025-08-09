# Dockerfile

# 1. Partiamo da un'immagine Python ufficiale, leggera e ottimizzata
FROM python:3.11-slim

# 2. Impostiamo la cartella di lavoro all'interno del container
WORKDIR /app

# 3. Copiamo prima il file dei requisiti. Questo è un trucco per velocizzare
#    le build future: se non cambi i requisiti, Docker userà la cache per questo strato.
COPY requirements.txt .

# 4. Installiamo tutte le dipendenze Python necessarie
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamo tutto il resto del codice del progetto nella cartella di lavoro
COPY . .

# 6. Comando che verrà eseguito quando il container parte per avviare il servizio
CMD ["python", "main.py"]