import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "transit_analytics.db"

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/transit_db" # Fallback for local dev
)

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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