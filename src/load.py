"""Load the historical CSV into DuckDB as a store dimension + spell fact.

The source file is one row per *authorization spell*, not per store: 703,441
rows resolve to 661,456 distinct Record IDs, with 37,941 IDs carrying multiple
rows (up to 7) for lapses and reinstatements. Store name and store type never
vary within a Record ID, so the store dimension is well defined.
"""
from config import CSV_PATH, IN_US_SQL, SENTINEL_AUTH_DATE, connect

# One row per spell, typed and trimmed. The CSV pads many fields with spaces.
TYPED_SQL = """
CREATE OR REPLACE TABLE raw_hist AS
SELECT
    CAST(TRIM("Record ID") AS BIGINT)                    AS record_id,
    TRIM("Store Name")                                   AS store_name,
    TRIM("Store Type")                                   AS store_type_usda,
    TRIM("Street Number")                                AS street_number,
    TRIM("Street Name")                                  AS street_name,
    NULLIF(TRIM("Additional Address"), '')               AS additional_address,
    TRIM("City")                                         AS city,
    TRIM("State")                                        AS state,
    TRIM("Zip Code")                                     AS zip_code,
    NULLIF(TRIM("Zip4"), '')                             AS zip4,
    NULLIF(TRIM("County"), '')                           AS county,
    TRY_CAST(NULLIF(TRIM("Latitude"), '') AS DOUBLE)     AS latitude,
    TRY_CAST(NULLIF(TRIM("Longitude"), '') AS DOUBLE)    AS longitude,
    TRY_STRPTIME(TRIM("Authorization Date"), '%-m/%-d/%Y')::DATE AS auth_date,
    TRY_STRPTIME(NULLIF(TRIM("End Date"), ''), '%-m/%-d/%Y')::DATE AS end_date
-- The dialect is pinned: auto-detection infers escape = '\'' and then chokes on
-- addresses like "MOFFETT  SUITE 'S'".
FROM read_csv(
    ?,
    header = true,
    all_varchar = true,
    strict_mode = false,
    delim = ',',
    quote = '"',
    escape = '"'
)
"""

# Data-quality flags live on the spell, since they are properties of the dates.
SPELL_SQL = f"""
CREATE OR REPLACE TABLE fact_spell AS
SELECT
    record_id,
    auth_date,
    end_date,
    auth_date = DATE '{SENTINEL_AUTH_DATE}'              AS auth_date_unknown,
    end_date IS NOT NULL AND end_date < auth_date        AS date_anomaly
FROM raw_hist
"""

# Canonical attributes come from the most recent spell, so a store that moved or
# was re-registered carries its latest known address.
STORE_SQL = f"""
CREATE OR REPLACE TABLE dim_store AS
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY record_id
        ORDER BY auth_date DESC, end_date DESC NULLS FIRST
    ) AS rn
    FROM raw_hist
),
spells AS (
    SELECT
        record_id,
        COUNT(*)                                  AS n_spells,
        MIN(auth_date)                            AS first_auth_date,
        MAX(CASE WHEN end_date IS NULL THEN 1 ELSE 0 END) = 1 AS open_ended
    FROM raw_hist
    GROUP BY record_id
)
SELECT
    r.record_id,
    r.store_name,
    r.store_type_usda,
    r.street_number,
    r.street_name,
    r.additional_address,
    r.city,
    r.state,
    r.zip_code,
    r.zip4,
    r.county,
    r.latitude,
    r.longitude,
    s.n_spells,
    s.first_auth_date,
    s.open_ended,
    (r.latitude IS NULL OR r.longitude IS NULL
     OR r.latitude = 0 OR r.longitude = 0)        AS geocode_missing,
    -- Coordinates that land outside every US/territory box are wrong, not remote.
    (r.latitude IS NOT NULL AND r.longitude IS NOT NULL
     AND r.latitude <> 0 AND r.longitude <> 0
     AND NOT {IN_US_SQL.replace(chr(10), " ")})                             AS geocode_offshore,
    -- Classification columns; populated by classify.py.
    CAST(NULL AS VARCHAR)                         AS format,
    CAST(NULL AS VARCHAR)                         AS ownership,
    CAST(NULL AS VARCHAR)                         AS brand,
    CAST(NULL AS BOOLEAN)                         AS is_dollar_store,
    CAST(NULL AS VARCHAR)                         AS name_norm
FROM ranked r
JOIN spells s USING (record_id)
WHERE r.rn = 1
"""


def load() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing {CSV_PATH} — run `python src/fetch.py` first.")

    con = connect()
    print(f"Reading {CSV_PATH}")
    con.execute(TYPED_SQL, [str(CSV_PATH)])
    con.execute(SPELL_SQL)
    con.execute(STORE_SQL)

    rows = con.execute("SELECT count(*) FROM raw_hist").fetchone()[0]
    spells = con.execute("SELECT count(*) FROM fact_spell").fetchone()[0]
    stores = con.execute("SELECT count(*) FROM dim_store").fetchone()[0]
    print(f"  raw_hist   {rows:>9,} spells")
    print(f"  fact_spell {spells:>9,} spells")
    print(f"  dim_store  {stores:>9,} stores")

    flags = con.execute(
        """
        SELECT
            (SELECT count(*) FROM fact_spell WHERE auth_date_unknown),
            (SELECT count(*) FROM fact_spell WHERE date_anomaly),
            (SELECT count(*) FROM dim_store  WHERE geocode_missing),
            (SELECT count(*) FROM dim_store  WHERE geocode_offshore),
            (SELECT count(*) FROM raw_hist   WHERE auth_date IS NULL)
        """
    ).fetchone()
    print(f"\n  auth_date_unknown (1930 sentinel) {flags[0]:>7,}")
    print(f"  date_anomaly (end < auth)         {flags[1]:>7,}")
    print(f"  geocode_missing                   {flags[2]:>7,}")
    print(f"  geocode_offshore (bad coordinates) {flags[3]:>6,}")
    print(f"  unparseable auth_date             {flags[4]:>7,}")
    con.close()


if __name__ == "__main__":
    load()
