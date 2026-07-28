import io
import logging
import zipfile
import pandas as pd
import requests
from sqlalchemy import create_engine
from pipeline import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TAMPERE_GTFS_URL = "http://data.itsfactory.fi/journeys/files/gtfs/latest/gtfs_tampere.zip"

def fetch_and_load_gtfs_static():
    """Downloads Tampere GTFS static feed and loads stops/routes into PostgreSQL."""
    logger.info(f"Downloading GTFS Static package from {TAMPERE_GTFS_URL}...")
    
    headers = {}
    if config.API_KEY:
        headers["digitransit-subscription-key"] = config.API_KEY

    response = requests.get(TAMPERE_GTFS_URL, headers=headers)
    response.raise_for_status()

    # Unzip in memory
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        logger.info("Extracting stops.txt and routes.txt...")
        stops_df = pd.read_csv(z.open("stops.txt"))
        routes_df = pd.read_csv(z.open("routes.txt"))

    # Connect to database via SQLAlchemy engine
    engine = create_engine(config.DATABASE_URL)

    # Clean & write stops table
    stops_clean = stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()
    stops_clean.to_sql("gtfs_stops", engine, if_exists="replace", index=False)
    logger.info(f"Successfully loaded {len(stops_clean)} stops into 'gtfs_stops'.")

    # Clean & write routes table
    routes_clean = routes_df[["route_id", "route_short_name", "route_long_name"]].copy()
    routes_clean.to_sql("gtfs_routes", engine, if_exists="replace", index=False)
    logger.info(f"Successfully loaded {len(routes_clean)} routes into 'gtfs_routes'.")

if __name__ == "__main__":
    fetch_and_load_gtfs_static()