"""Verify web/data/points.bin by decoding it exactly as web/app.js does.

There is no JS runtime here, so this reproduces the browser's byte offsets and
filter logic in NumPy and checks the results against the database. If this
passes, the front end is reading the right bytes and filtering on them the way
the pipeline intends.
"""
import json
import sys

import numpy as np

from config import ROOT, connect

OUT_DIR = ROOT / "web" / "data"
FAILURES = []


def check(name, actual, expected):
    ok = actual == expected
    a = f"{actual:,}" if isinstance(actual, (int, np.integer)) else actual
    e = f"{expected:,}" if isinstance(expected, (int, np.integer)) else expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {a} (expected {e})")
    if not ok:
        FAILURES.append(name)


def main():
    meta = json.loads((OUT_DIR / "meta.json").read_text())
    buf = (OUT_DIR / "points.bin").read_bytes()
    n = meta["count"]

    # Same offsets as app.js.
    expected_bytes = n * 16
    print(f"\n1. Binary layout ({n:,} stores)")
    check("file size in bytes", len(buf), expected_bytes)

    position = np.frombuffer(buf, np.float32, n * 2, 0)
    format_id = np.frombuffer(buf, np.uint8, n, n * 8)
    ownership_id = np.frombuffer(buf, np.uint8, n, n * 9)
    brand_id = np.frombuffer(buf, np.uint16, n, n * 10)
    year_mask = np.frombuffer(buf, np.uint32, n, n * 12)

    lon, lat = position[0::2], position[1::2]
    check("all longitudes in [-180,180]", bool(np.all((lon >= -180) & (lon <= 180))), True)
    check("all latitudes in [-90,90]", bool(np.all((lat >= -90) & (lat <= 90))), True)
    check("format ids within domain", int(format_id.max()), len(meta["formats"]) - 1)
    check("ownership ids within domain", int(ownership_id.max()), len(meta["ownership"]) - 1)
    check("brand ids within domain", int(brand_id.max()), len(meta["brands"]))

    print("\n2. Year masks reproduce per-year totals")
    years = meta["years"]
    for yr in (years[0], 2012, 2019, years[-1]):
        bit = np.uint32(1 << (yr - years[0]))
        check(f"{yr}", int(((year_mask & bit) != 0).sum()), meta["per_year_totals"][str(yr)])

    print("\n3. Unbranded buckets (the two synthetic filter entries)")
    own = {o: i for i, o in enumerate(meta["ownership"])}
    check("independent unbranded", int(((brand_id == 0) & (ownership_id == own["independent"])).sum()),
          meta["unbranded"]["independent"])
    check("unknown unbranded", int(((brand_id == 0) & (ownership_id == own["unknown"])).sum()),
          meta["unbranded"]["unknown"])
    check("no chain-owned store lacks a brand",
          int(((brand_id == 0) & (ownership_id == own["chain"])).sum()), 0)

    print("\n4. Brand filter — the driving use case (2025, Kroger + Giant Eagle only)")
    names = [b["name"] for b in meta["brands"]]
    bit25 = np.uint32(1 << (2025 - years[0]))
    ids = [names.index(b) + 1 for b in ("Kroger", "Giant Eagle")]
    sel = np.isin(brand_id, ids) & ((year_mask & bit25) != 0)
    con = connect(read_only=True)
    db = con.execute("""
        SELECT count(DISTINCT d.record_id) FROM dim_store d JOIN fact_spell f USING(record_id)
        WHERE d.brand IN ('Kroger','Giant Eagle') AND NOT d.geocode_missing AND NOT f.date_anomaly
          AND f.auth_date <= DATE '2025-12-31'
          AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
    """).fetchone()[0]
    check("Kroger + Giant Eagle active 2025", int(sel.sum()), db)

    print("\n5. Conservation — per-format counts sum to the all-on total")
    active25 = (year_mask & bit25) != 0
    parts = sum(int((active25 & (format_id == i)).sum()) for i in range(len(meta["formats"])))
    check("sum over 18 formats", parts, int(active25.sum()))

    print("\n6. Format labels agree with the database (2025)")
    for fmt in ("Supermarket", "Grocery (Large)", "Dollar Store"):
        i = meta["formats"].index(fmt)
        dbn = con.execute("""
            SELECT count(DISTINCT d.record_id) FROM dim_store d JOIN fact_spell f USING(record_id)
            WHERE d.format = ? AND NOT d.geocode_missing AND NOT f.date_anomaly
              AND f.auth_date <= DATE '2025-12-31'
              AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
        """, [fmt]).fetchone()[0]
        check(fmt, int((active25 & (format_id == i)).sum()), dbn)
    con.close()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        sys.exit(1)
    print("Map payload verified.")


if __name__ == "__main__":
    main()
