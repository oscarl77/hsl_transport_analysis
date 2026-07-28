import pytest
import json
from google.transit import gtfs_realtime_pb2
from pipeline.mqtt_ingestor import parse_gtfs_realtime, parse_hfp_json

def _create_base_feed() -> gtfs_realtime_pb2.FeedMessage:
    """Helper to initialize a valid base FeedMessage with required headers."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
    feed.header.timestamp = 1720720800
    return feed

def test_parse_feed_message_happy_path():
    """Verify valid GTFS-RT protobuf bytes are parsed into schema-aligned dicts."""
    # Arrange: Build a real GTFS protobuf message in memory
    feed = _create_base_feed()
    header = feed.header
    header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "entity_1"
    vehicle = entity.vehicle
    vehicle.trip.route_id = "10M"
    vehicle.vehicle.id = "TRAM_99"
    vehicle.position.latitude = 61.4978
    vehicle.position.longitude = 23.7610
    vehicle.timestamp = 1720720800
    # Serialize to raw bytes (mimicking the MQTT payload)
    payload_bytes = feed.SerializeToString()
    # Act: Run through the pure parsing function
    result = parse_gtfs_realtime(payload_bytes)
    # Assert: Verify the extracted structure
    assert len(result) == 1
    record = result[0]
    assert record["route_id"] == "10M"
    assert record["vehicle_id"] == "TRAM_99"
    assert record["latitude"] == pytest.approx(61.4978)
    assert record["longitude"] == pytest.approx(23.7610)
    assert record["timestamp"] == 1720720800


def test_parse_feed_message_missing_optional_fields():
    """Verify default fallbacks ('Unknown') when route or vehicle IDs are missing."""
    feed = _create_base_feed()
    entity = feed.entity.add()
    entity.id = "entity_2"
    # Intentionally leaving out trip.route_id and vehicle.id
    vehicle = entity.vehicle
    vehicle.position.latitude = 61.4978
    vehicle.position.longitude = 23.7610
    vehicle.timestamp = 1720720800
    payload_bytes = feed.SerializeToString()
    result = parse_gtfs_realtime(payload_bytes)
    assert len(result) == 1
    assert result[0]["route_id"] == "Unknown"
    assert result[0]["vehicle_id"] == "Unknown"


def test_parse_feed_message_filters_missing_gps():
    """Verify records missing latitude/longitude are skipped entirely."""
    feed = _create_base_feed()
    entity = feed.entity.add()
    entity.id = "entity_3"
    # Populating IDs but omitting GPS position configurations
    vehicle = entity.vehicle
    vehicle.trip.route_id = "10M"
    vehicle.timestamp = 1720720800
    payload_bytes = feed.SerializeToString()
    result = parse_gtfs_realtime(payload_bytes)
    # Should be dropped because lat/lon evaluate to 0.0 or None
    assert len(result) == 0


def test_parse_feed_message_corrupted_bytes():
    """Verify corrupted network packets return an empty list instead of crashing."""
    garbage_bytes = b"invalid_protobuf_data_stream_12345"
    # Act & Assert: Function should internally catch the exception and exit cleanly
    result = parse_gtfs_realtime(garbage_bytes)
    assert result == []


def test_parse_feed_message_empty_payload():
    """Verify empty byte triggers exit early without parsing."""
    assert parse_gtfs_realtime(b"") == []

def test_parse_hfp_json_arr_event_success():
    """Verify valid HFP ARR payload is parsed into normalised dictionary."""
    sample_hfp_payload = {
        "arr": {
            "desi": "3",
            "veh": 105,
            "lat": 61.498,
            "long": 23.761,
            "tsi": 1720720800,
            "stop": 1204
        }
    }
    payload_bytes = json.dumps(sample_hfp_payload).encode("utf-8")

    result = parse_hfp_json(payload_bytes)

    assert len(result) == 1
    record = result[0]
    assert record["route_id"] == "3"
    assert record["vehicle_id"] == "105"
    assert record["event_type"] == "arr"
    assert record["stop_id"] == "1204"


def test_parse_hfp_json_ignores_non_stop_events():
    """Verify events outside the stop lifecycle (e.g. VP) are dropped."""
    sample_vp_payload = {
        "VP": {
            "desi": "3",
            "veh": 105,
            "lat": 61.498,
            "long": 23.761,
            "tsi": 1720720800
        }
    }
    payload_bytes = json.dumps(sample_vp_payload).encode("utf-8")

    result = parse_hfp_json(payload_bytes)
    assert result == []


def test_parse_hfp_json_corrupted_bytes():
    """Verify malformed JSON fails gracefully without crashing."""
    invalid_bytes = b"not_valid_json_data"
    result = parse_hfp_json(invalid_bytes)
    assert result == []