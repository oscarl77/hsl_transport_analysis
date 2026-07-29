import logging
import sys
import uuid
from pipeline import config
from paho.mqtt import client as mqtt_client

from pipeline.database import DatabaseManager
from pipeline.mqtt_ingestor import BATCH_LIMIT, memory_buffer, parse_hfp_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager(config.DATABASE_URL)

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Triggers on initial connection AND automatic reconnections.
    
    Subscribing inside on_connect guarantees subscriptions are automatically 
    renewed if the network socket drops and reconnects.
    """
    if reason_code == 0:
        logger.info("Connected to HSL MQTT broker successfully.")
        for topic in config.HFP_TOPICS:
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    """Triggers whenever the network socket drops unexpectedly."""
    if reason_code != 0:
        logger.warning(
            f"Unexpected MQTT disconnect (code {reason_code}). Paho will auto-reconnect..."
        )


def on_mqtt_message(client, userdata, msg):
    """Processes incoming HSL HFP MQTT messages and routes them to PostgreSQL."""
    try:
        # Parse raw payload bytes into structured dictionaries
        records = parse_hfp_json(msg.payload)
        if not records:
            return

        # Separate VP (position updates) from Stop Events (ARR, DEP, PAS)
        vp_records = [r for r in records if r["event_type"] == "vp"]
        stop_records = [
            r for r in records if r["event_type"] in ("arr", "dep", "pas")
        ]

        # Process position pings via memory buffer to batch database writes
        if vp_records:
            memory_buffer.extend(vp_records)
            if len(memory_buffer) >= BATCH_LIMIT:
                db_manager.insert_telemetry_batch(memory_buffer)
                memory_buffer.clear()

        # Insert stop lifecycle events immediately
        if stop_records:
            db_manager.insert_stop_events(stop_records)
            logger.info(
                f"[HFP MILESTONE] Logged {len(stop_records)} stop event(s) to database."
            )

    except Exception as e:
        logger.error(
            f"Error processing MQTT message on topic {msg.topic}: {e}"
        )


def start_pipeline():
    """Boots database management checks and starts the blocking MQTT network loop."""
    # Initialise database schema & run rolling retention pruning
    db_manager.initialise_db()
    # Instantiate Paho Client using API Version 2
    unique_client_id = f"hsl_tram_pipeline_{uuid.uuid4().hex[:8]}"
    client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        client_id=unique_client_id,
        clean_session=True
    )
    # Configure auth if API key is provided
    if config.API_KEY:
        client.username_pw_set(username=config.API_KEY, password="")
    # Bind callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_mqtt_message
    # Reconnection behavior: Exponential backoff (1s up to 2m max delay)
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    logger.info(f"Initiating network link to {config.MQTT_BROKER}:{config.MQTT_PORT}...")
    try:
        client.connect(
            config.MQTT_BROKER,
            port=config.MQTT_PORT,
            keepalive=config.MQTT_KEEPALIVE,
        )
        # Blocking call: Handles network IO, reconnects, and dispatches callbacks
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Stopping pipeline worker cleanly...")
        client.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    start_pipeline()