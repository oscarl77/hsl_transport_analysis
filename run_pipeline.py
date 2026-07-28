import logging
import sys
from pipeline import config
from paho.mqtt import client as mqtt_client

from pipeline.database import DatabaseManager
from pipeline.ingestor import BATCH_LIMIT, memory_buffer, parse_feed_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager(config.DATABASE_URL)

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Triggers on initial connection AND automatic reconnections.
    
    Subscribing inside on_connect guarantees subscriptions are automatically 
    renewed if the network socket drops and reconnects.
    """
    if reason_code == 0:
        logger.info("Successfully connected to MQTT Broker!")
        # Subscribe inside on_connect for self-healing subscriptions
        client.subscribe(config.TRAM_TOPIC)
        logger.info(f"Subscribed to topic: {config.TRAM_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker, reason code: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    """Triggers whenever the network socket drops unexpectedly."""
    if reason_code != 0:
        logger.warning(
            f"Unexpected MQTT disconnect (code {reason_code}). Paho will auto-reconnect..."
        )


def on_mqtt_message(client, userdata, msg):
    """Event handler triggered whenever an MQTT message arrives over the socket."""
    # Parse raw protobuf payload
    records = parse_feed_message(msg.payload)
    memory_buffer.extend(records)
    # Flush buffer using the single db_manager instance
    if len(memory_buffer) >= BATCH_LIMIT:
        db_manager.insert_batch(memory_buffer)
        logger.info(
            f"[PIPELINE STAGE] Committed {len(memory_buffer)} records to PostgreSQL."
        )
        memory_buffer.clear()


def start_pipeline():
    """Boots database management checks and starts the blocking MQTT network loop."""
    # Initialise database schema & run rolling retention pruning
    db_manager.initialise_db()
    db_manager.delete_old_telemetry(days=7)
    # Instantiate Paho Client using API Version 2
    client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        client_id="helsinki_tram_analytics_mvp",
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