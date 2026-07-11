from google.transit import gtfs_realtime_pb2
import pytest
from pipeline.ingestor import extract_telemetry_from_feed

def test_extract_telemetry_from_feed_success():
    """Verify that the extraction function correctly parses a GTFS feed into telemetry records."""
    # Create a mock GTFS feed with one entity
    feed = gtfs_realtime_pb2.FeedMessage()
    
    entity = feed.entity.add()
    entity.id = "1"
    vehicle = entity.vehicle
    vehicle.trip.route_id = "1001"
    vehicle.vehicle.id = "CAR_1"
    vehicle.position.latitude = 60.142
    vehicle.position.longitude = 24.9
    vehicle.timestamp = 1000

    records = extract_telemetry_from_feed(feed)
    
    assert len(records) == 1, f"Expected 1 record, found {len(records)}"
    record = records[0]
    assert record['route_id'] == "1001"
    assert record['vehicle_id'] == "CAR_1"
    assert record['latitude'] == pytest.approx(60.142, abs=1e-3)
    assert record['longitude'] == pytest.approx(24.9, abs=1e-3)
    assert record['timestamp'] == 1000

def test_extract_telemetry_from_feed_missing_fields():
    """Verify that the extraction function handles missing fields gracefully."""
    feed = gtfs_realtime_pb2.FeedMessage()
    
    entity = feed.entity.add()
    entity.id = "2"
    vehicle = entity.vehicle
    # Missing route_id and vehicle_id
    vehicle.position.latitude = 60.289
    vehicle.position.longitude = 24.8
    vehicle.timestamp = 2000

    records = extract_telemetry_from_feed(feed)
    
    assert len(records) == 1, f"Expected 1 record, found {len(records)}"
    record = records[0]
    assert record['route_id'] == "Unknown"
    assert record['vehicle_id'] == "Unknown"
    assert record['latitude'] == pytest.approx(60.289, abs=1e-3)
    assert record['longitude'] == pytest.approx(24.8, abs=1e-3)
    assert record['timestamp'] == 2000