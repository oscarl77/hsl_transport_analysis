import logging
import paho.mqtt.client as mqtt
from pipeline import config
from paho.mqtt import client as mqtt_client

from pipeline.database import DatabaseManager
from pipeline.ingestor import BATCH_LIMIT, memory_buffer, process_feed_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager(config.DATABASE_URL)

def on_mqtt_message(client, userdata, msg):
    """Event handler triggered whenever an MQTT message arrives over the socket."""
    # Parse raw protobuf payload
    records = process_feed_message(msg.payload)
    memory_buffer.extend(records)

    # Flush buffer using the single db_manager instance
    if len(memory_buffer) >= BATCH_LIMIT:
        db_manager.insert_batch(memory_buffer)
        print(
            f"[PIPELINE STAGE] Committed {len(memory_buffer)} records to PostgreSQL."
        )
        memory_buffer.clear()

def start_pipeline():
    # Initialize DB table schema on startup
    db_manager.initialise_db()

    client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        client_id="helsinki_tram_analytics_mvp",
    )
    client.username_pw_set(username=config.API_KEY, password="")
    client.on_message = on_mqtt_message

    print(
        f"Initiating network link to {config.MQTT_BROKER}:{config.MQTT_PORT}..."
    )
    client.connect(
        config.MQTT_BROKER,
        port=config.MQTT_PORT,
        keepalive=config.MQTT_KEEPALIVE,
    )
    client.loop_forever()


def parse_payload(payload_bytes):
    """Helper to deserialize incoming byte payloads."""
    # Add your JSON decoding or payload parsing logic here
    pass


if __name__ == "__main__":
    # Ensure database table schema is initialized on boot
    db_manager.initialise_db()
    # Configure MQTT Client
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    logger.info(f"Connecting to MQTT Broker at {config.MQTT_BROKER}:{config.MQTT_PORT}...")
    client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
    # Subscribe to transit telemetry topic
    client.subscribe(config.MQTT_TOPIC)
    logger.info(f"Subscribed to topic: {config.MQTT_TOPIC}. Starting network loop...")
    # Blocking call: Keeps the container process alive & listens for incoming messages
    client.loop_forever()