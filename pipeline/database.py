import psycopg2
from psycopg2.extras import execute_values
from pipeline.config import DATABASE_URL

def initialise_db():
    """Establishes the target file and ensures the telemetry table structure exists."""
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tram_telemetry (
                    id SERIAL PRIMARY KEY,
                    route_id VARCHAR(50),
                    vehicle_id VARCHAR(50),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    timestamp BIGINT
                );
            """)

def insert_telemetry_batch(records):
    """Inserts a collection of parsed position dictionaries into the storage file.
    
    Accepts a list of dicts: [{'route_id': 'X', 'lat': 0.0, 'lon': 0.0, 'ts': 1234}]
    """
    if not records:
        return
    # Convert the list of Python dicts directly into a DuckDB internal relation
    # and append it in a single highly-optimized transactional block
    values = [
    (
        r.get("route_id"),
        r.get("vehicle_id"),
        r.get("latitude"),
        r.get("longitude"),
        r.get("timestamp")
    )
    for r in records
    ]
    query = """
        INSERT INTO tram_telemetry (route_id, vehicle_id, latitude, longitude, timestamp)
        VALUES %s;
    """
    # Using context managers ('with') automatically commits transactions and closes connections/cursors
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            execute_values(cursor, query, values)