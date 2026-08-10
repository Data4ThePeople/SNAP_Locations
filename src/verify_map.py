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
    print(f"\n1. Binary layout ({n:,} stores)")
    check("file size in bytes", len(buf), n * 19)

    position = np.frombuffer(buf, np.float32, n * 2, 0)
    format_id = np.frombuffer(buf, np.uint8, n, n * 8)
    ownership_id = np.frombuffer(buf, np.uint8, n, n * 9)
    brand_id = np.frombuffer(buf, np.uint16, n, n * 10)
    year_mask = np.frombuffer(buf, np.uint32, n, n * 12)
    group_id = np.frombuffer(buf, np.uint8, n, n * 16)
    group_from = np.frombuffer(buf, np.uint8, n, n * 17)
    group_until = np.frombuffer(buf, np.uint8, n, n * 18)

    lon, lat = position[0::2], position[1::2]
    # Every point must land somewhere SNAP or NAP operates. The source geocodes
    # 38 Guam stores into Jerusalem and the Philippines, a "China, Texas" Dollar
    # General into Tibet, and a California Big Lots into Venezuela.
    boxes = [(-125.1, -66.8, 24.3, 49.5), (-179.9, -129.0, 51.0, 71.5),
             (-160.5, -154.6, 18.8, 22.4), (-68.0, -64.5, 17.6, 18.6),
             (144.5, 146.2, 13.2, 20.6), (-171.2, -169.3, -14.6, -13.9)]
    inside = np.zeros(len(lon), dtype=bool)
    for w, e, s, nth in boxes:
        inside |= (lon >= w) & (lon <= e) & (lat >= s) & (lat <= nth)
    check("points outside every US/territory box", int((~inside).sum()), 0)
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
        WHERE d.brand IN ('Kroger','Giant Eagle') AND NOT d.geocode_missing AND NOT d.geocode_offshore AND NOT f.date_anomaly
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
            WHERE d.format = ? AND NOT d.geocode_missing AND NOT d.geocode_offshore AND NOT f.date_anomaly
              AND f.auth_date <= DATE '2025-12-31'
              AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
        """, [fmt]).fetchone()[0]
        check(fmt, int((active25 & (format_id == i)).sum()), dbn)
    print("\n7. Per-year panel counts reconcile to the year total")
    for yr in (2006, 2015, years[-1]):
        i = yr - years[0]
        tot = (sum(b["by_year"][i] for b in meta["brands"])
               + meta["unbranded"]["independent_by_year"][i]
               + meta["unbranded"]["unknown_by_year"][i])
        check(f"{yr} brands + unbranded", tot, meta["per_year_totals"][str(yr)])
    # A group's per-year count must equal what the binary says for that year.
    gnames0 = [g["name"] for g in meta["groups"]]
    gi = gnames0.index("Kroger")
    i25 = 2025 - years[0]
    live = (year_mask & bit25) != 0
    got = int((live & (group_id == gi + 1)
               & (group_from <= i25) & (group_until >= i25)).sum())
    check("Kroger group by_year[2025]", meta["groups"][gi]["by_year"][i25], got)

    print("\n8. Parent-company groups")
    gnames = [g["name"] for g in meta["groups"]]
    check("group ids within domain", int(group_id.max()), len(gnames))
    kro = gnames.index("Kroger") + 1
    yi = lambda y: y - years[0]

    # Rebuild each group's 2025 membership straight from the database, applying
    # the same state/format/year rules, and compare against the binary.
    for gname in ("Kroger", "Albertsons Companies", "Ahold Delhaize"):
        gidx = gnames.index(gname) + 1
        want = set()
        for m in meta["groups"][gidx - 1]["members"]:
            if not (m["from"] <= 2025 <= m["until"]):
                continue
            sql = """
                SELECT DISTINCT d.record_id FROM dim_store d JOIN fact_spell f USING(record_id)
                WHERE d.brand = ? AND NOT d.geocode_missing AND NOT d.geocode_offshore AND NOT f.date_anomaly
                  AND f.auth_date <= DATE '2025-12-31'
                  AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
            """
            params = [m["brand"]]
            if m["states"]:
                sql += f" AND d.state IN ({','.join('?' * len(m['states']))})"
                params += m["states"]
            if m["formats"]:
                sql += f" AND d.format IN ({','.join('?' * len(m['formats']))})"
                params += m["formats"]
            want |= {r[0] for r in con.execute(sql, params).fetchall()}
        got = int((((group_id == gidx) & (group_from <= yi(2025))
                    & (group_until >= yi(2025))) & ((year_mask & bit25) != 0)).sum())
        check(f"{gname} group, 2025", got, len(want))

    # Time-varying membership: Harris Teeter joins in 2014, so 2013 must exclude it.
    ht = [b["name"] for b in meta["brands"]].index("Harris Teeter") + 1
    bit13 = np.uint32(1 << yi(2013))
    ht_in_13 = int(((brand_id == ht) & (group_id == kro)
                    & (group_from <= yi(2013)) & (group_until >= yi(2013))
                    & ((year_mask & bit13) != 0)).sum())
    check("Harris Teeter counted as Kroger in 2013", ht_in_13, 0)
    ht_in_14 = int(((brand_id == ht) & (group_id == kro)
                    & (group_from <= yi(2014)) & (group_until >= yi(2014))
                    & ((year_mask & np.uint32(1 << yi(2014))) != 0)).sum())
    check("Harris Teeter counted as Kroger in 2014", ht_in_14 > 0, True)

    # The convenience division leaves after 2017.
    tk = [b["name"] for b in meta["brands"]].index("Turkey Hill") + 1
    for yr, want in ((2017, True), (2018, False)):
        n_in = int(((brand_id == tk) & (group_id == kro)
                    & (group_from <= yi(yr)) & (group_until >= yi(yr))
                    & ((year_mask & np.uint32(1 << yi(yr))) != 0)).sum())
        check(f"Turkey Hill in Kroger group in {yr}", n_in > 0, want)

    # Shared banner split by state/format: Tom Thumb is Kroger in FL/AL and
    # Albertsons in TX.
    tt = [b["name"] for b in meta["brands"]].index("Tom Thumb") + 1
    alb = gnames.index("Albertsons Companies") + 1
    check("Tom Thumb split across two parents",
          len(set(group_id[brand_id == tt].tolist()) & {kro, alb}), 2)

    con.close()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        sys.exit(1)
    print("Map payload verified.")


if __name__ == "__main__":
    main()
