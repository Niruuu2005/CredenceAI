FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./alembic.ini
COPY scripts/docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh
ENV PYTHONPATH=/app/src

EXPOSE 8000

ENV APP_ENV=production
ENV MOCK_SERVICES=false
ENV CELERY_ALWAYS_EAGER=false
ENV RATE_LIMIT_ENABLED=true

CMD ["./docker-entrypoint.sh"]
