from unittest.mock import MagicMock, patch
import pytest

from pipeline.database import DatabaseManager


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_database_batch_insertion(mock_execute_values, mock_connect):
    """Verify telemetry batch insertion formats tuples and calls execute_values correctly."""
    # Arrange: Set up mock database connection & cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn
    mock_conn.closed = 0
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Initialize manager with dummy URL
    manager = DatabaseManager("postgresql://mock:mock@localhost/mock_db")

    mock_batch = [
        {
            "route_id": "1001",
            "vehicle_id": "CAR_1",
            "latitude": 60.1,
            "longitude": 24.9,
            "delay_seconds": 10,
            "speed": 5.5,
            "heading": 180,
            "timestamp": 1720720800,
        }
    ]
    # Act
    manager.insert_telemetry_batch(mock_batch)
    # Assert
    mock_execute_values.assert_called_once()
    call_args = mock_execute_values.call_args[0]
    passed_cursor = call_args[0]
    passed_query = call_args[1]
    passed_values = call_args[2]

    assert passed_cursor == mock_cursor
    assert "INSERT INTO tram_telemetry" in passed_query
    assert passed_values == [
        ("1001", "CAR_1", 60.1, 24.9, 10, 5.5, 180, 1720720800)
    ]


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_insert_stop_events(mock_execute_values, mock_connect):
    """Verify stop event insertion formats event metadata and calls execute_values correctly."""
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_connect.return_value = mock_conn
    mock_conn.closed = 0
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    manager = DatabaseManager("postgresql://mock:mock@localhost/mock_db")

    mock_stop_events = [
        {
            "route_id": "7",
            "vehicle_id": "1234",
            "latitude": 60.1,
            "longitude": 24.9,
            "event_type": "arr",
            "stop_id": "H1234",
            "delay_seconds": 30,
            "timestamp": 1720720850,
        }
    ]

    # Act
    manager.insert_stop_events(mock_stop_events)

    # Assert
    mock_execute_values.assert_called_once()
    call_args = mock_execute_values.call_args[0]
    passed_cursor = call_args[0]
    passed_query = call_args[1]
    passed_values = call_args[2]

    assert passed_cursor == mock_cursor
    assert "tram_stop_events" in passed_query
    assert passed_values == [
        ("7", "1234", 60.1, 24.9, "arr", "H1234", 30, 1720720850)
    ]


@patch("pipeline.database.psycopg2.connect")
@patch("pipeline.database.execute_values")
def test_insert_telemetry_batch_empty(mock_execute_values, mock_connect):
    """Verify empty batches exit early without executing queries."""
    manager = DatabaseManager("postgresql://mock:mock@localhost/mock_db")
    mock_execute_values.reset_mock()

    manager.insert_telemetry_batch([])

    # Should exit before running execute_values
    mock_execute_values.assert_not_called()