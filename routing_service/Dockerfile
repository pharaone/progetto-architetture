FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl ca-certificates netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements della cartella routing_service
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# ⚠️ COPIA *questa* cartella DENTRO /app/routing_service così il pacchetto esiste
COPY . /app/routing_service

# opzionale ma utile per import
ENV PYTHONPATH=/app

# env di runtime
ENV PORT=8080 \
    KAFKA_BOOTSTRAP=kafka:9092 \
    MENU_SERVICE_URL=http://menu-service:8081 \
    TOPIC_DISPONIBILITA=disponibilita \
    TOPIC_CONFERMA=conferma_ordine \
    TOPIC_STATUS=status \
    TOPIC_ORDERSTATUS=orderstatus

EXPOSE 8080

# avvia puntando al package routing_service
CMD ["uvicorn", "routing_service.main:app", "--host", "0.0.0.0", "--port", "7777", "--workers", "1"]

