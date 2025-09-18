# Dockerfile (migliorato)
FROM python:3.11-slim

# impostazioni base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# install deps - copia solo requirements per sfruttare la cache
COPY requirements.txt /app/requirements.txt

# upgrade pip e install (no-cache-dir già usato)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# copia il resto del codice
COPY . /app

# crea utente non-root e usa il suo home
RUN groupadd -r app && useradd -r -g app app \
 && chown -R app:app /app

USER app

# porta esplicita (documentativa)
EXPOSE 8000

# healthcheck (facoltativo): verifica l'endpoint /health dell'app
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- --timeout=2 http://localhost:8000/health || exit 1

# comando raccomandato: uvicorn (consente gestione segnali e workers)
# Nota: in dev puoi lasciare --reload (ma non usarlo in produzione)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
