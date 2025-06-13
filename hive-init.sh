#!/bin/bash
# Wait for PostgreSQL to be ready
while ! nc -z postgres 5432; do
  sleep 1
done

# Initialize Hive schema
/opt/hive/bin/schematool -dbType postgres -initSchema

# Start metastore
exec /opt/hive/bin/start-metastore