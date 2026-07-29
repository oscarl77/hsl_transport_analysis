from pathlib import Path
import functools

SQL_DIR = Path(__file__).resolve().parent / "sql"

@functools.lru_cache(maxsize=32)
def load_sql(filename: str) -> str:
    """Reads and caches SQL query files from the sql/ directory."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    return file_path.read_text()