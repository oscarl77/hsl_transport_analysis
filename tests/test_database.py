from unittest.mock import MagicMock, patch
import pytest
from pipeline.database import DatabaseManager


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_database_batch_insertion(mock_execute_values, mock_connect):
    """Verify insert_batch formats records and executes bulk insert correctly."""
    # Arrange: Set up mock database connection & cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock psycopg2.connect to return mock connection handle
    mock_connect.return_value = mock_conn
    mock_conn.closed = 0
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # Initialize manager with dummy URL
    manager = DatabaseManager("postgresql://mock:mock@localhost/mock_db")
    # Mock payload matching keys from process_feed_message (lat, lon, ts)
    mock_batch = [
        {
            "route_id": "1001",
            "vehicle_id": "CAR_1",
            "latitude": 60.1,
            "longitude": 24.9,
            "timestamp": 1720720800,
        }
    ]
    # Act: Call method on class instance
    manager.insert_batch(mock_batch)
    # Assert: Verify execute_values parameters
    mock_execute_values.assert_called_once()
    call_args = mock_execute_values.call_args[0]
    passed_cursor = call_args[0]
    passed_query = call_args[1]
    passed_values = call_args[2]
    assert passed_cursor == mock_cursor
    assert "INSERT INTO tram_telemetry" in passed_query
    assert passed_values == [
        ("1001", "CAR_1", 60.1, 24.9, 1720720800)
    ]


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_insert_telemetry_batch_empty(mock_execute_values, mock_connect):
    """Verify empty batches exit early without executing queries."""
    manager = DatabaseManager("postgresql://mock:mock@localhost/mock_db")
    # Reset mock after manager.__init__() call
    mock_execute_values.reset_mock()
    manager.insert_batch([])
    # Should exit before running execute_values
    mock_execute_values.assert_not_called()