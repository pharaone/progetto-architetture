FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ================= Copia codice =================
COPY . .

# ================= Porta =================
EXPOSE 9999

# ================= Comando di avvio =================
CMD ["uvicorn", "menu_service.main:app", "--host", "0.0.0.0", "--port", "9999", "--reload"]
