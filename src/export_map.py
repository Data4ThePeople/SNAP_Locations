"""Export the map payload: one row per store, with a 20-bit year mask.

Rather than shipping 20 per-year datasets, each store is written once carrying a
bitmask where bit i means "authorized on Dec 31 of 2006+i". The year slider then
becomes a bit test, so every filter runs client-side with no server.

Nothing is written unless the mask reproduces snapshot() counts for all 20 years.
"""
import csv
import json
from datetime import date

import numpy as np

from config import DATA, ROOT, connect
from snapshot import snapshot

GROUPS_CSV = DATA / "brand_groups.csv"

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
WHERE NOT f.date_anomaly AND NOT d.geocode_missing AND NOT d.geocode_offshore
GROUP BY ALL
HAVING year_mask <> 0
ORDER BY d.record_id
"""


def load_group_rules(known_brands):
    """Read the curated parent-company rules, validating every brand name."""
    if not GROUPS_CSV.exists():
        return [], []
    with open(GROUPS_CSV, newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    rules, names, unknown = [], [], []
    for r in csv.DictReader(lines):
        brand = (r.get("brand") or "").strip()
        group = (r.get("group") or "").strip()
        if not brand or not group:
            continue
        if brand not in known_brands:
            unknown.append((group, brand))
            continue
        if group not in names:
            names.append(group)
        rules.append({
            "group": group,
            "brand": brand,
            "states": [s for s in (r.get("states") or "").split("|") if s],
            "formats": [f for f in (r.get("formats") or "").split("|") if f],
            "from": int(r["from_year"]) if (r.get("from_year") or "").strip() else YEARS[0],
            "until": int(r["until_year"]) if (r.get("until_year") or "").strip() else YEARS[-1],
        })
    if unknown:
        raise SystemExit(
            "ABORT: brand_groups.csv references brands that do not exist in "
            "data/brands.csv:\n  " + "\n  ".join(f"{g}: {b!r}" for g, b in unknown)
        )
    return rules, names


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
        direct = int((~snap["geocode_missing"] & ~snap["geocode_offshore"]).sum())
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

    # --- parent-company groups ----------------------------------------------
    # Resolved here rather than in the browser because membership is qualified
    # by state and format, not just brand name: "Tom Thumb" is Kroger's Florida
    # convenience chain and Albertsons' Texas supermarket.
    rules, group_names = load_group_rules(set(brands[1:]))
    group_id = np.zeros(len(df), dtype=np.uint8)
    group_from = np.zeros(len(df), dtype=np.uint8)
    group_until = np.full(len(df), len(YEARS) - 1, dtype=np.uint8)
    print(f"\nResolving {len(rules)} group rules across {len(group_names)} groups:")
    for rule in rules:
        sel = (df["brand"] == rule["brand"]).to_numpy()
        if rule["states"]:
            sel &= df["state"].isin(rule["states"]).to_numpy()
        if rule["formats"]:
            sel &= df["format"].isin(rule["formats"]).to_numpy()
        sel &= group_id == 0          # first matching rule wins
        group_id[sel] = group_names.index(rule["group"]) + 1
        group_from[sel] = rule["from"] - YEARS[0]
        group_until[sel] = rule["until"] - YEARS[0]
    for i, g in enumerate(group_names, start=1):
        n = int((group_id == i).sum())
        print(f"  {g:24} {n:>7,} stores")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bin_path = OUT_DIR / "points.bin"
    with open(bin_path, "wb") as fh:
        for arr in (position, format_id, ownership_id, brand_id, masks,
                    group_id, group_from, group_until):
            fh.write(arr.tobytes())
    size_mb = bin_path.stat().st_size / 1e6
    print(f"\nwrote {bin_path} ({size_mb:.2f} MB)")

    # Per-year counts for every row in the retailer panel. Without these the
    # panel shows all-time totals next to a year-filtered map, which reads as a
    # mismatch — 311,131 independents beside 88,229 on screen.
    latest_bit = 1 << (len(YEARS) - 1)
    n_brands = len(brands)
    n_groups = len(group_names) + 1
    brand_by_year = np.zeros((n_brands, len(YEARS)), dtype=np.int64)
    group_by_year = np.zeros((n_groups, len(YEARS)), dtype=np.int64)
    unb_by_year = {"independent": [], "unknown": []}
    for i in range(len(YEARS)):
        live = ((masks >> i) & 1).astype(bool)
        brand_by_year[:, i] = np.bincount(brand_id[live], minlength=n_brands)
        in_window = live & (group_from <= i) & (group_until >= i)
        group_by_year[:, i] = np.bincount(group_id[in_window], minlength=n_groups)
        nob = live & (brand_id == 0)
        for key in ("independent", "unknown"):
            unb_by_year[key].append(int((nob & (ownership_id == own_index[key])).sum()))

    categories = dict(con.execute(
        "SELECT brand, any_value(chain_category) FROM dim_store "
        "WHERE brand IS NOT NULL GROUP BY brand").fetchall())
    brand_meta = []
    for bi, b in enumerate(brands[1:], start=1):
        brand_meta.append({
            "name": b,
            "category": categories.get(b),
            "total": int(brand_counts[b]),
            "latest": int(brand_by_year[bi, -1]),
            "by_year": brand_by_year[bi].tolist(),
        })

    group_meta = []
    for i, g in enumerate(group_names, start=1):
        members = [r for r in rules if r["group"] == g]
        group_meta.append({
            "name": g,
            "total": int((group_id == i).sum()),
            "latest": int(group_by_year[i, -1]),
            "by_year": group_by_year[i].tolist(),
            "members": [
                {"brand": r["brand"], "from": r["from"], "until": r["until"],
                 "states": r["states"], "formats": r["formats"]}
                for r in members
            ],
        })

    meta = {
        "count": len(df),
        "years": YEARS,
        "formats": formats,
        "ownership": OWNERSHIP,
        "brands": brand_meta,
        "groups": group_meta,
        "per_year_totals": per_year,
        "unbranded": {
            "independent": int(((brand_id == 0) & (ownership_id == own_index["independent"])).sum()),
            "unknown": int(((brand_id == 0) & (ownership_id == own_index["unknown"])).sum()),
            "independent_by_year": unb_by_year["independent"],
            "unknown_by_year": unb_by_year["unknown"],
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
