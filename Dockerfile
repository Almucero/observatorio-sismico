FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY producer ./producer
COPY consumer ./consumer
COPY api ./api
COPY scripts ./scripts
COPY frontend/public/datos/paises.geojson ./data/paises.geojson

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "producer.main"]
