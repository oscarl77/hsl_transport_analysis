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

ALLOWED_EVENTS = {"vp", "arr", "dep", "pas"}

def parse_hfp_json(payload_bytes: bytes) -> list[dict]:
    """Parses HFP JSON payloads into a unified list of event records.

    Includes event_type in each dictionary to allow downstream filtering.
    """
    if not payload_bytes:
        return []

    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        records = []

        payload_items = [data] if isinstance(data, dict) else data

        for item in payload_items:
            for event_key, body in item.items():
                if not isinstance(body, dict):
                    continue

                event_type = str(event_key).lower()
                if event_type not in ALLOWED_EVENTS:
                    continue

                lat = body.get("lat")
                lon = body.get("long")

                # Require valid position coordinates
                if lat is None or lon is None:
                    continue

                # Common base dictionary across all event types
                record = {
                    "route_id": str(body.get("desi", "Unknown")),
                    "vehicle_id": str(body.get("veh", "Unknown")),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "delay_seconds": body.get("dl"),
                    "timestamp": body.get("tst") or body.get("tsi"),
                }

                # Attach event-specific fields
                if event_type == "vp":
                    record["speed"] = body.get("spd")
                    record["heading"] = body.get("hdg")
                else:  # arr, dep, pas
                    record["event_type"] = event_type
                    record["stop_id"] = (
                        str(body.get("stop"))
                        if body.get("stop") is not None
                        else None
                    )

                records.append(record)

        return records

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"HFP JSON Parsing Exception: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected HFP Parsing Error: {e}", file=sys.stderr)
        return []