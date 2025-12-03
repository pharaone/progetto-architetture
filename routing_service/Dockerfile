FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# requirements della cartella routing_service
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# ⚠️ COPIA *questa* cartella DENTRO /app/routing_service così il pacchetto esiste
COPY . /app/routing_service

# opzionale ma utile per import
ENV PYTHONPATH=/app

# env di runtime
ENV PORT=7777 \
    KAFKA_BOOTSTRAP=kafka:9092 \
    MENU_SERVICE_URL=http://menu-service:8081 \

EXPOSE 7777

# avvia puntando al package routing_service
CMD ["uvicorn", "routing_service.main:app", "--host", "0.0.0.0", "--port", "7777", "--workers", "1"]

