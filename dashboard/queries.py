from pathlib import Path
import functools
import pandas as pd
from sqlalchemy import Engine

SQL_DIR = Path(__file__).resolve().parent / "sql"

@functools.lru_cache(maxsize=32)
def load_sql(filename: str) -> str:
    """Reads SQL string from the .sql file."""
    return (SQL_DIR / filename).read_text()


def fetch_latest_fleet_positions(engine: Engine) -> pd.DataFrame:
    """Loads the .sql file and EXECUTES it against PostgreSQL."""
    query_str = load_sql("get_latest_fleet_positions.sql")
    df = pd.read_sql(query_str, con=engine)
    
    return df