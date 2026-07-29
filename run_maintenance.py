import os
import logging
import psycopg2

from pipeline import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def reset_daily_tables(db_url: str) -> None:
    """Truncancates both telemetry and stop event tables, resetting ID sequences."""
    query = "TRUNCATE TABLE tram_telemetry, tram_stop_events RESTART IDENTITY:"

    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
        logger.info("Successfully truncated tram_telemetry, tram_stop_events tables.")
    except Exception as e:
        logger.error("Falised to truncate database tables: %s", e)
        raise

if __name__ == "__main__":
    db_url = config.DATABASE_URL
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set.")
        raise ValueError("DATABASE_URL missing.")
    logger.info("Starting scheduled maintenance task...")
    reset_daily_tables(db_url)
    logger.info("Maintenance complete. Exiting container.")