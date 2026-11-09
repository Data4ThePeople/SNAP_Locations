"""Export the map payload: one row per store, with a 21-bit snapshot mask.

Rather than shipping per-year datasets, each store is written once carrying a
bitmask where bit i means "authorized on snapshot date i". Bits 0-19 are Dec 31
of 2006-2025, from the historical file. Bit 20 is the newest live-feed snapshot
(src/fetch_live.py, src/load_live.py), labeled with its own date. The slider then
becomes a bit test, so every filter runs client-side with no server.

Nothing is written unless the mask reproduces snapshot() counts for all 20
historical years and the live_store count for the live snapshot.
"""
import csv
import json
from datetime import date

import numpy as np
import pandas as pd

from config import DATA, ROOT, connect
from snapshot import snapshot

GROUPS_CSV = DATA / "brand_groups.csv"

HIST_YEARS = list(range(2006, 2026))
# The live snapshot sits in the 2026 slot. Its label carries the real date, so
# the slider never presents it as a year-end.
LIVE_YEAR = 2026
YEARS = HIST_YEARS + [LIVE_YEAR]
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
        FOR y IN generate_series({HIST_YEARS[0]}, {HIST_YEARS[-1]})
    ], (a, b) -> a | b) AS INTEGER)) AS year_mask
FROM dim_store d
JOIN fact_spell f USING (record_id)
WHERE NOT f.date_anomaly AND d.mappable
GROUP BY ALL
ORDER BY d.record_id
"""

# Stores authorized on the live snapshot date that the map can place, after the
# two live-only groups the historical file never carried (see load_live.py).
LIVE_SQL = """
SELECT record_id, lon AS longitude, lat AS latitude, format, ownership, brand,
       store_name, state, in_hist
FROM live_store
WHERE excluded IS NULL AND mappable
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
    live = con.execute(LIVE_SQL).df()
    snap_date = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    live_label = f"{snap_date:%b} {snap_date.day}, {snap_date.year}"
    live_bit = 1 << (len(YEARS) - 1)

    # Historical stores on the live date: set the bit on their existing row.
    on_live = df["record_id"].isin(live.loc[live["in_hist"], "record_id"])
    df.loc[on_live, "year_mask"] = df.loc[on_live, "year_mask"] | live_bit
    missing = set(live.loc[live["in_hist"], "record_id"]) - set(df["record_id"])
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} live stores with a historical "
                         "Record_ID have no mappable historical row.")
    # Live-only stores: new rows carrying only the live bit.
    extra = live.loc[~live["in_hist"]].drop(columns="in_hist").copy()
    extra["year_mask"] = live_bit
    df = (pd.concat([df, extra[df.columns]], ignore_index=True)
            .query("year_mask != 0").reset_index(drop=True))
    print(f"  {len(df):,} stores with at least one active snapshot "
          f"({len(extra):,} only in the {live_label} live feed)")

    # --- assertions: the mask must reproduce the pipeline's own snapshots ----
    print(f"\nVerifying masks against snapshot() for all {len(HIST_YEARS)} years:")
    masks = df["year_mask"].to_numpy(dtype=np.uint32)
    per_year = {}
    for i, yr in enumerate(HIST_YEARS):
        from_mask = int(((masks >> i) & 1).sum())
        snap = snapshot(date(yr, 12, 31), con=con)
        direct = int(snap["mappable"].sum())
        per_year[yr] = from_mask
        flag = "OK" if from_mask == direct else "MISMATCH"
        if yr % 5 == 1 or yr in (HIST_YEARS[0], HIST_YEARS[-1]):
            print(f"  {yr}  mask {from_mask:>9,}   snapshot {direct:>9,}   {flag}")
        if from_mask != direct:
            raise SystemExit(
                f"ABORT: year {yr} mask count {from_mask:,} != snapshot {direct:,}. "
                "Nothing written."
            )
    print(f"  all {len(HIST_YEARS)} years match")
    from_mask = int(((masks >> (len(YEARS) - 1)) & 1).sum())
    flag = "OK" if from_mask == len(live) else "MISMATCH"
    print(f"  {live_label}  mask {from_mask:>9,}   live_store {len(live):>9,}   {flag}")
    if from_mask != len(live):
        raise SystemExit("ABORT: live snapshot mask does not match live_store. Nothing written.")
    per_year[LIVE_YEAR] = from_mask

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
    format_by_year = np.zeros((len(formats), len(YEARS)), dtype=np.int64)
    group_by_year = np.zeros((n_groups, len(YEARS)), dtype=np.int64)
    unb_by_year = {"independent": [], "unknown": []}
    for i in range(len(YEARS)):
        live = ((masks >> i) & 1).astype(bool)
        brand_by_year[:, i] = np.bincount(brand_id[live], minlength=n_brands)
        format_by_year[:, i] = np.bincount(format_id[live], minlength=len(formats))
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

    # The page used to hardcode these in its copy, and both drifted: the loading
    # line was 38 stores out and the "never appear" figure was stale by a third.
    # Publishing them here means the copy is generated from the same pass that
    # builds the payload and cannot disagree with it.
    mappable = int(con.execute(
        "SELECT count(*) FROM dim_store WHERE mappable").fetchone()[0])
    never = mappable - len(df)

    meta = {
        "count": len(df),
        "mappable": mappable,
        "excluded_shortlived_count": never,
        "excluded_shortlived_pct": round(100 * never / mappable, 1),
        "years": YEARS,
        # Display label per slider step: the year for Dec 31 snapshots, the full
        # date for the live one.
        "labels": [str(y) for y in HIST_YEARS] + [live_label],
        "live": {"date": str(snap_date), "label": live_label,
                 "only_in_live": len(extra)},
        "formats": formats,
        "format_by_year": format_by_year.tolist(),
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
            "semantics": "A store is included for year Y if authorized on Dec 31 of Y. "
                         f"The last step is the live feed on {live_label}.",
            "excluded_shortlived": "Stores that opened and closed between Dec 31sts never appear.",
            "excluded_geocode": "Stores without coordinates are excluded.",
            "source": "USDA SNAP Retailer Locator Historical Data 2005-2025; "
                      f"USDA SNAP retailer locator live feed, {live_label}",
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
