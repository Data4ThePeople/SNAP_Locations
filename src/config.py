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

# Boxes covering everywhere SNAP or NAP actually operates. A point outside all
# of them is a geocoding failure, not a location: the file puts 38 Guam stores
# in Jerusalem, France and the Philippines, a Dollar General in "China, Texas"
# in Tibet, and a Big Lots in Santa Margarita, California in Venezuela.
IN_US_SQL = """(
   (longitude BETWEEN -125.1 AND -66.8  AND latitude BETWEEN  24.3 AND 49.5)
OR (longitude BETWEEN -179.9 AND -129.0 AND latitude BETWEEN  51.0 AND 71.5)
OR (longitude BETWEEN -160.5 AND -154.6 AND latitude BETWEEN  18.8 AND 22.4)
OR (longitude BETWEEN  -68.0 AND  -64.5 AND latitude BETWEEN  17.6 AND 18.6)
OR (longitude BETWEEN  144.5 AND  146.2 AND latitude BETWEEN  13.2 AND 20.6)
OR (longitude BETWEEN -171.2 AND -169.3 AND latitude BETWEEN -14.6 AND -13.9)
)"""


def connect(read_only: bool = False):
    """Open the project DuckDB database."""
    import duckdb

    DATA.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)
