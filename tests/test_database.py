from unittest.mock import MagicMock, patch
import pytest
from pipeline.database import insert_telemetry_batch

@patch('pipeline.database.psycopg2.connect')
@patch('pipeline.database.execute_values')
def test_database_batch_insertion(mock_execute_values, mock_connect):
    """Verify insert_telemetry_batch formats records and executes bulk insert correctly."""
    #Arrange: Set up mock database connection & cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Make psycopg2.connect() return our mock connection context manager
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # Mock payload matching your production dictionary keys
    mock_batch = [
        {
            "route_id": "1001",
            "vehicle_id": "CAR_1",
            "latitude": 60.1,
            "longitude": 24.9,
            "timestamp": "2026-07-11T18:00:00Z",
        }
    ]
    # Act: Call production function
    insert_telemetry_batch(mock_batch)
    # Assert: Verify mock received expected parameters
    mock_execute_values.assert_called_once()
    # Extract args passed to execute_values(cursor, query, values)
    call_args = mock_execute_values.call_args[0]
    passed_cursor = call_args[0]
    passed_query = call_args[1]
    passed_values = call_args[2]
    # Check query structure and extracted data tuples
    assert passed_cursor == mock_cursor
    assert "INSERT INTO tram_telemetry" in passed_query
    assert passed_values == [
        ("1001", "CAR_1", 60.1, 24.9, "2026-07-11T18:00:00Z")
    ]


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_insert_telemetry_batch_empty(mock_execute_values, mock_connect):
    """Verify empty batches exit early without hitting the database."""
    insert_telemetry_batch([])
    # Should exit before connecting
    mock_connect.assert_not_called()
    mock_execute_values.assert_not_called()