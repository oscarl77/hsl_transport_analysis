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
        {"route_id": "1001", "vehicle_id": "CAR_1", "latitude": 60.1, "longitude": 24.9, "timestamp": 1000}
    ]
    data_matrix = [[r['route_id'], r['vehicle_id'], r['latitude'], r['longitude'], r['timestamp']] for r in mock_batch]
    conn.executemany("""INSERT INTO tram_telemetry VALUES (?, ?, ?, ?, ?)""", data_matrix)
    count = conn.sql("SELECT COUNT(*) FROM tram_telemetry").fetchone()[0]
    assert count == 1, f"Expected 1 record, found {count}"