"""Shared paths and constants for the SNAP retailer pipeline."""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"

DB_PATH = DATA / "snap.duckdb"
CSV_PATH = RAW / "hist.csv"
ZIP_PATH = RAW / "snap-retailer-locator-data2005-2025.zip"
BRANDS_CSV = DATA / "brands.csv"

SOURCE_URL = (
    "https://www.fns.usda.gov/sites/default/files/resource-files/"
    "snap-retailer-locator-data2005-2025.zip"
)
ZIP_MEMBER = "Historical SNAP Retailer Locator Data 2005-2025.csv"

# The archive covers retailers authorized at some point in the last 20 calendar
# years. Snapshots before this date are incomplete by construction: stores that
# opened and closed entirely before the window are absent from the file.
EARLIEST_SNAPSHOT = date(2006, 1, 1)

# The file's cutoff. Nothing authorized after this date exists in the data.
DATA_CUTOFF = date(2025, 12, 31)

# USDA uses 1930-01-01 as a sentinel for "authorization date unknown".
SENTINEL_AUTH_DATE = date(1930, 1, 1)


def connect(read_only: bool = False):
    """Open the project DuckDB database."""
    import duckdb

    DATA.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)
