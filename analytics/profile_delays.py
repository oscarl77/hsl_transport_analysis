import duckdb
import polars as pl
from pipeline import config

def run_live_profile():
    print(f"Connecting to live database storage at: {config.DB_PATH}")
    
    # Connect to the active file using a DuckDB read-only pointer
    # This ensures we don't block or lock the ingestion script's insert statements.
    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    
    try:
        # 2. Let DuckDB run the aggregation query.
        # .pl() tells DuckDB to instantly convert the result into a Polars DataFrame.
        df = conn.sql("""
            SELECT 
                route_id,
                COUNT(*) as total_pings,
                MIN(captured_at) as tracking_started,
                MAX(captured_at) as last_updated
            FROM tram_telemetry
            GROUP BY route_id
            ORDER BY total_pings DESC;
        """).pl()  # <-- The magic bridge string
        
        print("\n--- LIVE FLEET PROFILE SUMMARY ---")
        print(df)
        
    except Exception as e:
        print(f"Database query failed: {e}")
    finally:
        # Always close the connection pointer
        conn.close()

if __name__ == "__main__":
    try:
        run_live_profile()
    except Exception as e:
        print(f"Analytics execution failed: {e}")