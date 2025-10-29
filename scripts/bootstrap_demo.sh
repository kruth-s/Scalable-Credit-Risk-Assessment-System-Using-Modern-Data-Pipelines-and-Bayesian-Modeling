#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.dev.yml"

echo "Starting docker-compose..."
docker-compose -f "$COMPOSE_FILE" up -d

echo "Waiting for Postgres to be ready..."
MAX_TRIES=30
TRIES=0
until docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U kruth >/dev/null 2>&1; do
  TRIES=$((TRIES+1))
  if [ $TRIES -ge $MAX_TRIES ]; then
    echo "Postgres not ready after waiting" >&2
    exit 1
  fi
  sleep 2
done

echo "Loading DB schema..."
docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U kruth -d credit_risk -f - < storage/init_db.sql

echo "Creating Kafka topic 'credit_behavior' (if not exists)..."
docker-compose -f "$COMPOSE_FILE" exec -T kafka kafka-topics --create --if-not-exists --topic credit_behavior --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1 || true

echo "Bootstrap complete."
