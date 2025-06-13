#!/bin/bash
# Wait for PostgreSQL to be ready
while ! nc -z postgres 5432; do
  sleep 1
done

# Initialize Superset
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@admin.com \
  --password admin

superset db upgrade
superset init

# Start the server
exec superset run -p 8088 --host=0.0.0.0