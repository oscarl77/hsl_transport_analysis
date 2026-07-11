import duckdb
import pytest

def test_database_batch_insertion():
    """Verify records are appended cleanly to DuckDB in-memory."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE tram_telemetry (
            route_id VARCHAR, vehicle_id VARCHAR,
            latitude DOUBLE, longitude DOUBLE, timestamp BIGINT
        );
    """)
    mock_batch = [
        {"route_id": "1001", "vehicle_id": "CAR_1", "lat": 60.1, "lon": 24.9, "ts": 1000}
    ]
    data_matrix = [[r['route_id'], r['vehicle_id'], r['lat'], r['lon'], r['ts']] for r in mock_batch]
    conn.executemany("""INSERT INTO tram_telemetry VALUES (?, ?, ?, ?, ?)""", data_matrix)
    count = conn.sql("SELECT COUNT(*) FROM tram_telemetry").fetchone()[0]
    assert count == 1, f"Expected 1 record, found {count}"