import time
import psycopg2
import logging
from psycopg2.extras import execute_values
from pipeline.config import DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self._connect()
    
    def initialise_db(self):
        """Creates table schema and optimized composite indexes if they do not exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tram_telemetry (
            id SERIAL PRIMARY KEY,
            route_id VARCHAR(50),
            vehicle_id VARCHAR(50) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            timestamp BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Composite index targeting latest-position window queries
        CREATE INDEX IF NOT EXISTS idx_vehicle_ts 
        ON tram_telemetry (vehicle_id, timestamp DESC);
        """

        for attempt in range(2):
            try:
                # Reconnect handle if socket was broken
                if not self.conn or self.conn.closed != 0:
                    self._connect()

                with self.conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                self.conn.commit()
                logger.info("Database schema and indexes initialized successfully.")
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.error(f"Failed to initialize database schema: {e}. Retrying connection...")
                self._connect()
            except Exception as e:
                if self.conn:
                    self.conn.rollback()
                logger.error(f"Error during database schema initialization: {e}")
                raise e

    def _connect(self):
        """Establishes or restores the persistent database connection
        """
        attempt = 0
        backoff = 1.0 # Initial backoff in seconds

        while True:
            try:
                if self.conn and not self.conn.closed:
                    self.conn.close()
                self.conn = psycopg2.connect(self.db_url)
                logger.info("Database connection established successfully.")
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                attempt += 1
                logger.warning(f"Database connection failed (Attempt {attempt}). Retrying in {backoff:.1f} seconds...   Error: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)  # Exponential backoff with a cap at 30 seconds

    def insert_batch(self, records: list[dict]):
        """Inserts a batch of telemetry records into the database."""
        if not records:
            return

        values = [
            (
                r.get("route_id"),
                r.get("vehicle_id"),
                r.get("latitude"),
                r.get("longitude"),
                r.get("timestamp")
            )
            for r in records
        ]

        query = """
            INSERT INTO tram_telemetry (route_id, vehicle_id, latitude, longitude, timestamp)
            VALUES %s;
        """

        # Retry loop for write batch
        for _ in range(2):
            try:
                if not self.conn or self.conn.closed != 0:
                    self._connect()
                with self.conn.cursor() as cursor:
                    execute_values(cursor, query, values)
                self.conn.commit()
                return  # Successful insertion, exit the method
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.error(f"Write operation failed: {e}. Attempting to reconnect...")
                self._connect()
            except Exception as e:
                if self.conn:
                    self.conn.rollback()
                logger.error(f"Unexpected error during batch insert: {e}")
                raise e