# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema necesarias para paquetes binarios como psycopg/ijson
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Flask escucha en 5000 por defecto
EXPOSE 5000

# Variables por defecto; se pueden sobrescribir via docker compose o `docker run`
ENV FLASK_APP=Sitio_web.app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000

CMD ["python", "main.py"]
