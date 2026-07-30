import sys
import io
import json
from pathlib import Path
from datetime import datetime, timezone
from google.cloud import bigquery
import psycopg2
from psycopg2.extras import RealDictCursor

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from pipeline.config import DATABASE_URI, GCP_PROJECT_ID, BQ_DATASET, BQ_EVENTS_TABLE

def get_last_ingested_timestamp(bq_client: bigquery.Client) -> datetime:
    """Fetch maximum created_at timestamp from BigQuery to determine high-water mark."""
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_EVENTS_TABLE}"
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

def extract_and_load(
    bq_client: bigquery.Client, start_time: datetime, end_time: datetime
):
    """Streams rows from Postgres directly into BigQuery without building giant Python lists."""
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_EVENTS_TABLE}"

    # Use an in-memory text buffer (much cheaper than Python lists/dicts)
    buffer = io.StringIO()
    row_count = 0

    with psycopg2.connect(DATABASE_URI) as conn:
        # Server-side cursor prevents fetching 80k rows at once into Python RAM
        with conn.cursor(
            name="tram_events_cursor", cursor_factory=RealDictCursor
        ) as cur:
            cur.itersize = 10000  # Fetch 10k batch chunks from DB
            query = """
                SELECT id, route_id, vehicle_id, latitude, longitude,
                       event_type, stop_id, delay_seconds, timestamp, created_at
                FROM public.tram_stop_events
                WHERE created_at > %s AND created_at <= %s
                ORDER BY created_at ASC;
            """
            cur.execute(query, (start_time, end_time))

            for row in cur:
                rec = dict(row)
                rec["timestamp"] = str(rec["timestamp"])
                rec["created_at"] = str(rec["created_at"])

                # Write line directly to the string buffer
                buffer.write(json.dumps(rec) + "\n")
                row_count += 1

    if row_count == 0:
        print("No new records to ingest.")
        return

    # Reset buffer position to start before loading
    buffer.seek(0)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITIONS
        ],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    # Convert text string buffer into bytes stream for BigQuery
    file_obj = io.BytesIO(buffer.getvalue().encode("utf-8"))

    job = bq_client.load_table_from_file(
        file_obj, table_id, job_config=job_config
    )
    job.result()  # Wait for BigQuery load to complete
    print(f"Successfully loaded {row_count} rows into {table_id}.")


def run_pipeline():
    bq_client = bigquery.Client()
    execution_time = datetime.now(timezone.utc)

    start_time = get_last_ingested_timestamp(bq_client)
    print(f"Extracting records from {start_time} to {execution_time}...")

    extract_and_load(bq_client, start_time, execution_time)


if __name__ == "__main__":
    run_pipeline()