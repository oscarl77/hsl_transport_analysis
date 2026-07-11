import duckdb
from pipeline import config

def initialise_db():
    """Establishes the target file and ensures the telemetry table structure exists."""
    conn = duckdb.connect(str(config.DB_PATH))
    
    # Generate the columnar time-series table structure
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tram_telemetry (
            route_id VARCHAR,
            vehicle_id VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            timestamp BIGINT,
        );
    """)
    conn.close()
    print(f"Database initialized cleanly at: {config.DB_PATH}")

def insert_telemetry_batch(records):
    """Inserts a collection of parsed position dictionaries into the storage file.
    
    Accepts a list of dicts: [{'route_id': 'X', 'lat': 0.0, 'lon': 0.0, 'ts': 1234}]
    """
    if not records:
        return
        
    conn = duckdb.connect(str(config.DB_PATH))
    
    # Convert the list of Python dicts directly into a DuckDB internal relation
    # and append it in a single highly-optimized transactional block
    try:
        # Transform our array of dictionaries into a clean matrix of raw positional values
        data_matrix = [[r['route_id'], r['vehicle_id'], r['latitude'], r['longitude'], r['timestamp']] for r in records]
        
        # Using executemany tells the engine to map the 5 placeholders 
        # to each individual array entry across the entire collection sequentially.
        conn.executemany("""
            INSERT INTO tram_telemetry (route_id, vehicle_id, latitude, longitude, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, data_matrix)
    except Exception as e:
        print(f"Database Write Failure: {e}")
    finally:
        conn.close()