import sys
from paho.mqtt import client as mqtt_client
from google.transit import gtfs_realtime_pb2
from pipeline import config
from pipeline.database import initialise_db, insert_telemetry_batch

# In-memory accumulator for batched writes
BATCH_LIMIT = 50
memory_buffer = []

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"CONNECTED securely to Digitransit Broker: {config.MQTT_BROKER}")
        initialise_db()
        client.subscribe(config.TRAM_TOPIC)
        print(f"SUCCESS: Subscribed to active stream catch-all: {config.TRAM_TOPIC}")
    else:
        print(f"CRITICAL: Handshake rejected with reason code: {reason_code}")

def on_message(client, userdata, msg):
    """Triggers every time a tram pushed a new spatial status pocket

    Args:
        client (_type_): _description_
        userdata (_type_): _description_
        msg (_type_): _description_
    """
    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(msg.payload)
        for entity in feed.entity:
            if entity.HasField("vehicle"):
                vehicle_data = entity.vehicle

                # Extract telemetry data
                if vehicle_data.trip.HasField("route_id"):
                    route_id = vehicle_data.trip.route_id
                else:
                    route_id = "Unknown"
                lat = vehicle_data.position.latitude
                lon = vehicle_data.position.longitude
                timestamp = vehicle_data.timestamp
                if lat and lon:
                    # Append flat dictionary to memory buffer
                    memory_buffer.append({
                        'route_id': route_id,
                        'lat': lat,
                        'lon': lon,
                        'ts': timestamp
                    })
        
        # Once buffer hits the threshold, commit to DuckDB and flush
        if len(memory_buffer) >= BATCH_LIMIT:
            insert_telemetry_batch(memory_buffer)
            print(f"[PIPELINE STAGE] Committed {len(memory_buffer)} records onto local storage file.")
            memory_buffer.clear()
                    
    except Exception as e:
        print(f"Decoding Buffer Exception: {e}", file=sys.stderr)

def start_pipeline():
    """Initialises and activates the persistent background network loop"""
    client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        client_id="helsinki_tram_analytics_mvp",
    )
    client.username_pw_set(username=config.API_KEY, password="")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Initiating network link to {config.MQTT_BROKER}:{config.MQTT_PORT}...")
    client.connect(config.MQTT_BROKER, port=config.MQTT_PORT, keepalive=config.MQTT_KEEPALIVE)
    
    # Block process and loop continuously handling reconnections natively
    client.loop_forever()
    