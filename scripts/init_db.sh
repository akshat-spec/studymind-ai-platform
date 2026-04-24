#!/bin/bash
set -e

echo "Waiting for postgres to be ready..."
until docker-compose exec -T postgres pg_isready -U postgres; do
  sleep 1
done

echo "Running alembic migrations..."
docker-compose exec -T backend alembic upgrade head

echo "Database initialization complete!"
