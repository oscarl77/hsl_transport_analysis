import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URI = os.getenv(
    "DATABASE_URI", 
    "postgresql://postgres:password@localhost:5432/transit_db" # Fallback for local dev
)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET_RAW = os.getenv("BQ_DATASET_RAW_NAME")
BQ_EVENTS_TABLE = os.getenv("BQ_EVENTS_TABLE_NAME")


# Digitransit MQTT Settings
MQTT_BROKER = "mqtt.hsl.fi"
MQTT_PORT = 1883  # Standard TCP unencrypted port
MQTT_KEEPALIVE = 30  # Recommended interval under 1 minute

# API Credentials
API_KEY = os.getenv("DIGITRANSIT_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL: DIGITRANSIT_API_KEY is not set in your .env file!")

HFP_TOPICS = [
    "/hfp/v2/journey/ongoing/vp/tram/#",
    "/hfp/v2/journey/ongoing/arr/tram/#",
    "/hfp/v2/journey/ongoing/dep/tram/#",
    "/hfp/v2/journey/ongoing/pas/tram/#",
]