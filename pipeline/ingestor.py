import sys
from google.transit import gtfs_realtime_pb2

# In-memory accumulator for batched writes
BATCH_LIMIT = 50
memory_buffer = []

def parse_feed_message(payload_bytes: bytes) -> list[dict]:
    """Parses GTFS-RT protobuf payload bytes into structured record dicts."""
    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(payload_bytes)

        records = []
        for entity in feed.entity:
            if entity.HasField("vehicle"):
                v = entity.vehicle
                lat = v.position.latitude if v.HasField("position") else None
                lon = v.position.longitude if v.HasField("position") else None

                if lat and lon:
                    records.append({
                        "route_id": (
                            v.trip.route_id
                            if v.trip.HasField("route_id")
                            else "Unknown"
                        ),
                        "vehicle_id": (
                            v.vehicle.id
                            if v.HasField("vehicle") and v.vehicle.HasField("id")
                            else "Unknown"
                        ),
                        "latitude": lat,
                        "longitude": lon,
                        "timestamp": v.timestamp,
                    })
        return records
    except Exception as e:
        print(f"Protobuf Parsing Exception: {e}", file=sys.stderr)
        return []