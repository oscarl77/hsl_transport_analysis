from pipeline.config import POSTGRES_URI, GCP_PROJECT, BQ_DATASET, BQ_TABLE
from datetime import datetime, timezone
from google.cloud import bigquery
import psycopg2
from psycopg2.extras import RealDictCursor

def get_last_ingested_timestamp(bq_client: bigquery.Client) -> datetime:
    """Fetch maximum created_at timestamp from BigQuery to determine high-water mark."""
    table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    query = f"""
        SELECT COALESCE(MAX(created_at), '1970-01-01 00:00:00+00') as max_created_at
        FROM `{table_id}`
    """
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        for row in results:
            return row["max_created_at"]
    except Exception:
        # Fallback if table doesn't exist yet
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def extract_from_postgres(start_time: datetime, end_time: datetime) -> list[dict]:
    """Query PostgreSQL for new records between high-water mark and current execution time."""
    with psycopg2.connect(POSTGRES_URI) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT id, route_id, vehicle_id, latitude, longitude,
                       event_type, stop_id, delay_seconds, timestamp, created_at
                FROM public.tram_stop_events
                WHERE created_at > %s AND created_at <= %s
                ORDER BY created_at ASC;
            """
            cur.execute(query, (start_time, end_time))
            return [dict(row) for row in cur.fetchall()]


def load_to_bigquery(bq_client: bigquery.Client, records: list[dict]):
    """Appends extracted records directly to BigQuery using free batch load jobs."""
    if not records:
        print("No new records to ingest.")
        return

    table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITIONS
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    # Transform datetimes to strings for JSON serialization
    formatted_records = []
    for r in records:
        rec = dict(r)
        rec["timestamp"] = str(rec["timestamp"])
        rec["created_at"] = str(rec["created_at"])
        formatted_records.append(rec)

    job = bq_client.load_table_from_json(
        formatted_records, table_id, job_config=job_config
    )
    job.result()  # Wait for completion
    print(f"Successfully loaded {len(records)} rows into {table_id}.")


def run_pipeline():
    bq_client = bigquery.Client()
    execution_time = datetime.now(timezone.utc)

    start_time = get_last_ingested_timestamp(bq_client)
    print(f"Extracting records from {start_time} to {execution_time}...")

    records = extract_from_postgres(start_time, execution_time)
    print(f"Extracted {len(records)} records from PostgreSQL.")

    load_to_bigquery(bq_client, records)


if __name__ == "__main__":
    run_pipeline()