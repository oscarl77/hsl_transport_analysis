import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "transit_analytics.db"

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Digitransit MQTT Settings
MQTT_BROKER = "mqtt.digitransit.fi"
MQTT_PORT = 1883  # Standard TCP unencrypted port
MQTT_KEEPALIVE = 30  # Recommended interval under 1 minute

# API Credentials
API_KEY = os.getenv("DIGITRANSIT_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL: DIGITRANSIT_API_KEY is not set in your .env file!")

# Target Subscription: GTFS-RT Realtime Vehicle Positions (vp) for HSL Trams
# The '+' acts as an open wildcard for agency/direction tags.
# The '#' captures everything downstream from the TRAM category.
TRAM_TOPIC = "/gtfsrt/vp/tampere/+/+/TRAM/#"