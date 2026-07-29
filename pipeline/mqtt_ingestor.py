import json
import sys
from google.transit import gtfs_realtime_pb2

# In-memory accumulator for batched writes
BATCH_LIMIT = 50
memory_buffer = []

def parse_gtfs_realtime(payload_bytes: bytes) -> list[dict]:
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

ALLOWED_STOP_EVENTS = {"vp", "arr", "dep", "pas"}

def parse_hfp_json(payload_bytes: bytes) -> list[dict]:
    """Parses HFP JSON payloads specifically for ARR, DEP, and PAS stop events."""
    if not payload_bytes:
        return []

    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        records = []

        payload_items = [data] if isinstance(data, dict) else data

        for item in payload_items:
            for event_type, body in item.items():
                # Skip non-dictionary bodies or events outside our target set
                if not isinstance(body, dict) or event_type.lower() not in ALLOWED_STOP_EVENTS:
                    continue

                lat = body.get("lat")
                lon = body.get("long")

                # Require valid position coordinates
                if lat is not None and lon is not None:
                    records.append({
                        "route_id": str(body.get("desi", "Unknown")),
                        "vehicle_id": str(body.get("veh", "Unknown")),
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "timestamp": int(body.get("tsi", 0)),
                        "event_type": str(event_type).lower(),
                        "stop_id": str(body.get("stop")) if body.get("stop") else None,
                        "delay_seconds": body.get("dl"),  # Schedule delay (positive = late, negative = early)
                        "speed": body.get("spd"),  # Speed in m/s
                        "heading": body.get("hdg"),  # Heading in degrees
                    })

        return records

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"HFP JSON Parsing Exception: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected HFP Parsing Error: {e}", file=sys.stderr)
        return []