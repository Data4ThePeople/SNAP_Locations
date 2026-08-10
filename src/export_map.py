"""Export the map payload: one row per store, with a 20-bit year mask.

Rather than shipping 20 per-year datasets, each store is written once carrying a
bitmask where bit i means "authorized on Dec 31 of 2006+i". The year slider then
becomes a bit test, so every filter runs client-side with no server.

Nothing is written unless the mask reproduces snapshot() counts for all 20 years.
"""
import json
import struct
from datetime import date

import numpy as np

from config import DATA, ROOT, connect
from snapshot import snapshot

YEARS = list(range(2006, 2026))
OUT_DIR = ROOT / "web" / "data"

# Ownership is a fixed 3-value domain; the map's color encoding depends on the
# order, so it is pinned here rather than discovered from the data.
OWNERSHIP = ["chain", "independent", "unknown"]

MASK_SQL = f"""
SELECT
    d.record_id,
    d.longitude,
    d.latitude,
    d.format,
    d.ownership,
    d.brand,
    d.store_name,
    d.state,
    bit_or(CAST(list_reduce([
        CASE WHEN f.auth_date <= make_date(y, 12, 31)
              AND (f.end_date IS NULL OR f.end_date >= make_date(y, 12, 31))
             THEN 1 << (y - {YEARS[0]}) ELSE 0 END
        FOR y IN generate_series({YEARS[0]}, {YEARS[-1]})
    ], (a, b) -> a | b) AS INTEGER)) AS year_mask
FROM dim_store d
JOIN fact_spell f USING (record_id)
WHERE NOT f.date_anomaly AND NOT d.geocode_missing
GROUP BY ALL
HAVING year_mask <> 0
ORDER BY d.record_id
"""


def export() -> None:
    con = connect(read_only=True)
    print("Building year masks...")
    df = con.execute(MASK_SQL).df()
    print(f"  {len(df):,} stores with at least one active year-end")

    # --- assertions: the mask must reproduce the pipeline's own snapshots ----
    print("\nVerifying masks against snapshot() for all 20 years:")
    masks = df["year_mask"].to_numpy(dtype=np.uint32)
    per_year = {}
    for i, yr in enumerate(YEARS):
        from_mask = int(((masks >> i) & 1).sum())
        snap = snapshot(date(yr, 12, 31), con=con)
        direct = int((~snap["geocode_missing"]).sum())
        per_year[yr] = from_mask
        flag = "OK" if from_mask == direct else "MISMATCH"
        if yr % 5 == 1 or yr in (YEARS[0], YEARS[-1]):
            print(f"  {yr}  mask {from_mask:>9,}   snapshot {direct:>9,}   {flag}")
        if from_mask != direct:
            raise SystemExit(
                f"ABORT: year {yr} mask count {from_mask:,} != snapshot {direct:,}. "
                "Nothing written."
            )
    print("  all 20 years match")

    # --- categorical domains -------------------------------------------------
    formats = sorted(df["format"].dropna().unique().tolist())
    # brand_id 0 is reserved for "no resolved brand".
    brand_counts = df["brand"].value_counts()
    brands = [None] + brand_counts.index.tolist()
    brand_index = {b: i for i, b in enumerate(brands)}
    fmt_index = {f: i for i, f in enumerate(formats)}
    own_index = {o: i for i, o in enumerate(OWNERSHIP)}

    # --- typed arrays --------------------------------------------------------
    position = np.empty(len(df) * 2, dtype=np.float32)
    position[0::2] = df["longitude"].to_numpy(dtype=np.float32)
    position[1::2] = df["latitude"].to_numpy(dtype=np.float32)
    format_id = df["format"].map(fmt_index).to_numpy(dtype=np.uint8)
    ownership_id = df["ownership"].map(own_index).to_numpy(dtype=np.uint8)
    brand_id = df["brand"].map(lambda b: brand_index.get(b, 0)).to_numpy(dtype=np.uint16)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bin_path = OUT_DIR / "points.bin"
    with open(bin_path, "wb") as fh:
        for arr in (position, format_id, ownership_id, brand_id, masks):
            fh.write(arr.tobytes())
    size_mb = bin_path.stat().st_size / 1e6
    print(f"\nwrote {bin_path} ({size_mb:.2f} MB)")

    # Per-brand counts for the checkbox list: total, and active in the latest year.
    latest_bit = 1 << (len(YEARS) - 1)
    latest = df[(masks & latest_bit) != 0]
    brand_latest = latest["brand"].value_counts()
    brand_meta = []
    for b in brands[1:]:
        row = df[df["brand"] == b].iloc[0]
        brand_meta.append({
            "name": b,
            "category": con.execute(
                "SELECT any_value(chain_category) FROM dim_store WHERE brand = ?", [b]
            ).fetchone()[0],
            "total": int(brand_counts[b]),
            "latest": int(brand_latest.get(b, 0)),
        })

    meta = {
        "count": len(df),
        "years": YEARS,
        "formats": formats,
        "ownership": OWNERSHIP,
        "brands": brand_meta,
        "per_year_totals": per_year,
        "unbranded": {
            "independent": int(((brand_id == 0) & (ownership_id == own_index["independent"])).sum()),
            "unknown": int(((brand_id == 0) & (ownership_id == own_index["unknown"])).sum()),
        },
        "notes": {
            "semantics": "A store is included for year Y if authorized on Dec 31 of Y.",
            "excluded_shortlived": "Stores that opened and closed between Dec 31sts never appear.",
            "excluded_geocode": "Stores without coordinates are excluded.",
            "source": "USDA SNAP Retailer Locator Historical Data 2005-2025",
        },
    }
    meta_path = OUT_DIR / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=1))
    print(f"wrote {meta_path}")
    print(f"  {len(formats)} formats, {len(brand_meta)} brands, {len(YEARS)} years")
    print(f"  unbranded: {meta['unbranded']['independent']:,} independent, "
          f"{meta['unbranded']['unknown']:,} unknown")
    con.close()


if __name__ == "__main__":
    export()
