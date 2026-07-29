import time
import psycopg2
import logging
from psycopg2.extras import execute_values


logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self._connect()
    
    def initialise_db(self):
        """Creates schema and composite indexes for HSL HFP telemetry and stop events."""
        create_schema_query = """
        -- 1. High-frequency vehicle position updates (HFP: VP)
        CREATE TABLE IF NOT EXISTS tram_telemetry (
            id SERIAL PRIMARY KEY,
            route_id VARCHAR(50),
            vehicle_id VARCHAR(50) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            delay_seconds INTEGER,              -- Schedule offset in seconds (+ ahead, - behind)
            speed DOUBLE PRECISION,             -- Speed in m/s
            heading INTEGER,                    -- Heading in degrees (0-360)
            timestamp BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Index for fast DISTINCT ON (vehicle_id) queries on the map dashboard
        CREATE INDEX IF NOT EXISTS idx_vehicle_ts 
        ON tram_telemetry (vehicle_id, timestamp DESC);


        -- 2. Low-frequency stop lifecycle milestones (HFP: ARR, DEP, PAS)
        CREATE TABLE IF NOT EXISTS tram_stop_events (
            id SERIAL PRIMARY KEY,
            route_id VARCHAR(50),
            vehicle_id VARCHAR(50) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            event_type VARCHAR(10) NOT NULL,    -- 'arr', 'dep', or 'pas'
            stop_id VARCHAR(50),                -- Stop ID (nullable for edge-case pass events)
            delay_seconds INTEGER,              -- Schedule delay recorded at milestone
            timestamp BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Index for querying recent stop events and dwell/delay performance
        CREATE INDEX IF NOT EXISTS idx_stop_event_type 
        ON tram_stop_events (stop_id, event_type, timestamp DESC);
        """

        for attempt in range(2):
            try:
                if not self.conn or self.conn.closed != 0:
                    self._connect()

                with self.conn.cursor() as cursor:
                    cursor.execute(create_schema_query)
                self.conn.commit()
                logger.info("HSL HFP database schemas and indexes initialized successfully.")
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.error(f"Failed to initialize schema: {e}. Retrying connection...")
                self._connect()
            except Exception as e:
                if self.conn:
                    self.conn.rollback()
                logger.error(f"Error initializing schema: {e}")
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

    def insert_telemetry_batch(self, records: list[dict]) -> None:
        """Inserts a batch of high-frequency vehicle position (VP) records into tram_telemetry."""
        if not records:
            return

        insert_query = """
            INSERT INTO tram_telemetry (
                route_id, vehicle_id, latitude, longitude, delay_seconds, speed, heading, timestamp
            ) VALUES %s;
        """

        # Format records into tuples matching column order
        data_tuples = [
            (
                r.get("route_id"),
                r["vehicle_id"],
                r["latitude"],
                r["longitude"],
                r.get("delay_seconds"),
                r.get("speed"),
                r.get("heading"),
                r["timestamp"],
            )
            for r in records
        ]

        self._execute_batch_write(
            insert_query, data_tuples, "tram_telemetry", len(records)
        )

    def insert_stop_events(self, records: list[dict]) -> None:
        """Inserts stop lifecycle events (ARR, DEP, PAS) into tram_stop_events."""
        if not records:
            return

        insert_query = """
            INSERT INTO tram_stop_events (
                route_id, vehicle_id, latitude, longitude, event_type, stop_id, delay_seconds, timestamp
            ) VALUES %s;
        """

        data_tuples = [
            (
                r.get("route_id"),
                r["vehicle_id"],
                r["latitude"],
                r["longitude"],
                r["event_type"],
                r.get("stop_id"),
                r.get("delay_seconds"),
                r["timestamp"],
            )
            for r in records
        ]

        self._execute_batch_write(
            insert_query, data_tuples, "tram_stop_events", len(records)
        )

    def _execute_batch_write(
        self, query: str, data_tuples: list[tuple], table_name: str, count: int
    ) -> None:
        """Helper method to handle batch insertion, connection retries, and transactions."""
        for attempt in range(2):
            try:
                if not self.conn or self.conn.closed != 0:
                    self._connect()

                with self.conn.cursor() as cursor:
                    execute_values(cursor, query, data_tuples)
                self.conn.commit()
                logger.info(f"Successfully inserted {count} records into {table_name}.")
                return

            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.error(
                    f"Connection lost during write to {table_name}: {e}. Retrying..."
                )
                self._connect()
            except Exception as e:
                if self.conn:
                    self.conn.rollback()
                logger.error(f"Error executing batch write to {table_name}: {e}")
                raise e
                
