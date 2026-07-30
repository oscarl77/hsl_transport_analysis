#!/bin/bash
# Exit immediately if any command returns a non-zero exit code
set -e

echo "==> Step 1: Ingesting data from PostgreSQL to BigQuery..."
python ingestion/load_tram_events.py

echo "==> Step 2: Running dbt transformations..."
cd dbt_transforms
dbt run --profiles-dir .

echo "==> Step 3: Truncating source table in PostgreSQL..."
cd ..
python ingestion/truncate_postgres_source.py

echo "==> Warehouse sync executed successfully!"