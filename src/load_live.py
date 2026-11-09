"""Load the newest live-feed snapshot into `live_store`, classified like dim_store.

One row per store in the snapshot. A store whose Record_ID is in the historical
file keeps that file's format, ownership, brand and coordinates, so a dot does
not move or change colour between Dec 31, 2025 and the live date. USDA's live
feed relabels about 1.5% of matched stores under a different coarse type; the
historical label wins, because it is the finer one.

A store that is only in the live feed is classified here, by the same rules:

  format     USDA's 8 live types are coarser than the 17 historical ones. The
             live type maps to the historical format where the two agree, and
             to a "not given" format where the live feed hides the size or the
             specialty. A dollar-store brand still becomes Dollar Store.
  ownership  brands.csv, as for every other store. An unresolved name counts as
             independent if 4 or fewer stores carry it, counting historical and
             live-only stores together. dim_store is never rewritten, so every
             historical label, and every number already published, stays put.
  mappable   coordinates present, inside the US windows, and not outside its
             own state's envelope (the same test load.py applies).

Two live-only groups are excluded from the map, because the historical file has
never carried them, and adding them for one date would read as growth:
  - Restaurant Meals Program locations
  - "Farmers and Markets" entities with no historical Record_ID

    python src/load_live.py
"""
import sys

import pandas as pd

from brands import normalize, resolve
from classify import (BANNER_CATEGORIES, CHAIN_CATEGORIES, DOLLAR_FORMAT,
                      INDEPENDENT_MAX_LOCATIONS, UNKNOWN_CATEGORIES)
from config import IN_US_SQL, connect
from fetch_live import LIVE_DIR
from load import STATE_BUFFER_DEG

# Live type -> display format, for live-only stores.
LIVE_FORMAT = {
    "Convenience Store": "Convenience Store",
    "Supermarket": "Supermarket",
    "Super Store": "Super Store",
    "Other": "Combination Grocery/Other",
    "Grocery Store": "Grocery (size not given)",
    "Specialty Store": "Specialty (type not given)",
    "Farmers and Markets": "Farmers' Market",
}
# Live type -> the historical USDA type brands.csv qualifiers are written in.
# Grocery and specialty have no single equivalent, so qualified rules skip them.
LIVE_TO_HIST_TYPE = {
    "Convenience Store": "Convenience Store",
    "Supermarket": "Supermarket",
    "Super Store": "Super Store",
    "Other": "Combination Grocery/Other",
    "Farmers and Markets": "Farmers' Market",
}
EXCLUDED_TYPES = {"Restaurant Meals Program": "restaurant meals program",
                  "Farmers and Markets": "farmers-market entity not in the historical file"}


def latest_snapshot():
    files = sorted(LIVE_DIR.glob("snap-live-*.csv.gz"))
    if not files:
        raise SystemExit("No live snapshot. Run src/fetch_live.py first.")
    return files[-1]


def load_live() -> None:
    path = latest_snapshot()
    snap_date = path.name[len("snap-live-"):-len(".csv.gz")]
    con = connect()
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _live AS
        SELECT CAST(Record_ID AS BIGINT) AS record_id, Store_Name AS store_name,
               Store_Type AS store_type_live, Store_Street_Address AS street,
               City AS city, State AS state, left(Zip_Code, 5) AS zip5,
               CAST(Longitude AS DOUBLE) AS longitude, CAST(Latitude AS DOUBLE) AS latitude
        FROM read_csv('{path}', all_varchar=true)
    """)
    n = con.execute("SELECT count(*), count(DISTINCT record_id) FROM _live").fetchone()
    if n[0] != n[1]:
        raise SystemExit(f"ABORT: {n[0] - n[1]} duplicate Record_IDs in {path.name}")

    live = con.execute("""
        SELECT l.*, d.record_id IS NOT NULL AS in_hist,
               d.format AS h_format, d.ownership AS h_ownership, d.brand AS h_brand,
               d.chain_category AS h_cat, d.longitude AS h_lon, d.latitude AS h_lat,
               d.mappable AS h_mappable
        FROM _live l LEFT JOIN dim_store d USING (record_id)
    """).df()
    hist_freq = dict(con.execute(
        "SELECT name_norm, count(*) FROM dim_store GROUP BY 1").fetchall())

    new = ~live["in_hist"]
    live["excluded"] = None
    for t, why in EXCLUDED_TYPES.items():
        live.loc[new & live["store_type_live"].eq(t), "excluded"] = why
    unknown_types = set(live.loc[new, "store_type_live"]) - set(LIVE_FORMAT) - set(EXCLUDED_TYPES)
    if unknown_types:
        raise SystemExit(f"ABORT: live store types with no format mapping: {sorted(unknown_types)}")

    # --- classify live-only stores -------------------------------------------
    nl = live.loc[new].copy()
    nl["name_norm"] = nl["store_name"].fillna("").map(normalize)
    res = [resolve(nn, st, LIVE_TO_HIST_TYPE.get(t))
           for nn, st, t in zip(nl["name_norm"], nl["state"], nl["store_type_live"])]
    nl["brand"] = [r[0] for r in res]
    nl["chain_category"] = [r[1] for r in res]
    live_counts = nl.loc[nl["excluded"].isna(), "name_norm"].value_counts()
    nl["name_freq"] = [hist_freq.get(nn, 0) + int(live_counts.get(nn, 0)) for nn in nl["name_norm"]]

    def ownership(cat, nn, freq):
        if cat in CHAIN_CATEGORIES:
            return "chain"
        if cat in BANNER_CATEGORIES:
            return "independent"
        if cat in UNKNOWN_CATEGORIES or not nn:
            return "unknown"
        return "independent" if freq <= INDEPENDENT_MAX_LOCATIONS else "unknown"

    nl["ownership"] = [ownership(c, nn, f) for c, nn, f in
                       zip(nl["chain_category"], nl["name_norm"], nl["name_freq"])]
    nl["format"] = nl["store_type_live"].map(LIVE_FORMAT)
    nl.loc[nl["chain_category"].eq("dollar"), "format"] = DOLLAR_FORMAT

    live["format"] = live["h_format"]
    live["ownership"] = live["h_ownership"]
    live["brand"] = live["h_brand"]
    live["chain_category"] = live["h_cat"]
    for col in ("format", "ownership", "brand", "chain_category"):
        live.loc[new, col] = nl[col]
    live["lon"] = live["h_lon"].where(live["in_hist"], live["longitude"])
    live["lat"] = live["h_lat"].where(live["in_hist"], live["latitude"])

    out = live[["record_id", "store_name", "store_type_live", "street", "city", "state",
                "zip5", "lon", "lat", "in_hist", "format", "ownership", "brand",
                "chain_category", "excluded", "h_mappable"]].copy()
    out.insert(0, "snapshot_date", pd.Timestamp(snap_date).date())
    con.register("_out", out)
    con.execute("CREATE OR REPLACE TABLE live_store AS SELECT * FROM _out")

    # --- mappable: historical stores keep dim_store's flag --------------------
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE _env AS
        SELECT state,
               quantile_cont(longitude, 0.001) w, quantile_cont(longitude, 0.999) e,
               quantile_cont(latitude , 0.001) s, quantile_cont(latitude , 0.999) n
        FROM dim_store
        WHERE NOT geocode_missing AND NOT geocode_offshore
        GROUP BY state HAVING count(*) >= 50;

        ALTER TABLE live_store ADD COLUMN mappable BOOLEAN;
        UPDATE live_store SET mappable = h_mappable WHERE in_hist;
        UPDATE live_store SET mappable =
            lon IS NOT NULL AND lat IS NOT NULL
            AND {IN_US_SQL.replace(chr(10), ' ').replace('longitude', 'lon').replace('latitude', 'lat')}
        WHERE NOT in_hist;
        UPDATE live_store l SET mappable = FALSE
        FROM _env own
        WHERE NOT l.in_hist AND l.mappable AND own.state = l.state
          AND (l.lon < own.w - {STATE_BUFFER_DEG} OR l.lon > own.e + {STATE_BUFFER_DEG}
            OR l.lat < own.s - {STATE_BUFFER_DEG} OR l.lat > own.n + {STATE_BUFFER_DEG})
          AND EXISTS (SELECT 1 FROM _env o WHERE o.state <> l.state
                      AND l.lon BETWEEN o.w AND o.e AND l.lat BETWEEN o.s AND o.n);
        ALTER TABLE live_store DROP COLUMN h_mappable;
    """)

    print(f"live_store from {path.name}: snapshot {snap_date}")
    for row in con.execute("""
        SELECT CASE WHEN in_hist THEN 'in historical file' ELSE 'live only' END,
               coalesce(excluded, 'kept'), mappable, count(*)
        FROM live_store GROUP BY ALL ORDER BY ALL""").fetchall():
        print(f"  {row[0]:20} {row[1]:48} mappable={row[2]!s:5} {row[3]:>8,}")
    con.close()


if __name__ == "__main__":
    load_live()
    sys.exit(0)
