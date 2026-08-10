"""End-to-end verification of the SNAP retailer pipeline.

Every expected figure here was measured against the source file before the
pipeline was written, so these are real regression anchors rather than
assertions restating whatever the code happens to produce.
"""
import sys
from datetime import date

from config import connect
from snapshot import snapshot

FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol if isinstance(expected, (int, float)) else actual == expected
    status = "PASS" if ok else "FAIL"
    detail = f"{actual:,}" if isinstance(actual, int) else str(actual)
    exp = f"{expected:,}" if isinstance(expected, int) else str(expected)
    print(f"  [{status}] {name}: {detail} (expected {exp}{f' ±{tol}' if tol else ''})")
    if not ok:
        FAILURES.append(name)
    return ok


def main():
    con = connect(read_only=True)
    q = lambda s: con.execute(s).fetchone()[0]

    print("\n1. Grain")
    check("dim_store rows", q("SELECT count(*) FROM dim_store"), 661_456)
    check("fact_spell rows", q("SELECT count(*) FROM fact_spell"), 703_441)
    check("duplicate record_ids in dim_store",
          q("SELECT count(*) FROM (SELECT record_id FROM dim_store "
            "GROUP BY 1 HAVING count(*) > 1)"), 0)

    print("\n2. Snapshot anchor")
    # The archive's own "currently authorized" figure is the count of stores
    # with an open-ended spell. The as-of count on the cutoff is 29 higher
    # because those stores' authorizations end exactly on 2025-12-31, and a
    # spell is treated as covering its end date (same-day auth/end spells exist
    # in the data and would otherwise vanish entirely).
    open_ended = q("SELECT count(DISTINCT record_id) FROM fact_spell WHERE end_date IS NULL")
    check("stores with an open-ended spell", open_ended, 249_063)
    cur = snapshot(date(2025, 12, 31), con=con)
    check("snapshot(2025-12-31)", len(cur), 249_092)
    check("  ...of which end exactly on the cutoff", len(cur) - open_ended, 29)

    print("\n   format breakdown (current snapshot):")
    for k, n in cur.groupby("format").size().sort_values(ascending=False).items():
        print(f"     {k:28} {n:>8,}")

    print("\n3. USDA type totals preserved (no store lost to reclassification)")
    for usda, expected in [("Convenience Store", 117_045), ("Combination Grocery/Other", 58_546),
                           ("Super Store", 20_604), ("Supermarket", 19_538),
                           ("Medium Grocery Store", 11_508), ("Small Grocery Store", 7_989),
                           ("Large Grocery Store", 4_001), ("Farmers' Market", 3_464)]:
        n = int((cur["store_type_usda"] == usda).sum())
        # Open-ended vs as-of differ by the 29 cutoff-boundary stores.
        check(f"{usda} (USDA, untouched)", n, expected, tol=29)

    print("\n4. Time series (June 30 each year)")
    series = {}
    for yr in range(2006, 2026):
        series[yr] = len(snapshot(date(yr, 6, 30), con=con))
    for yr in (2006, 2010, 2015, 2020, 2025):
        print(f"     {yr}  {series[yr]:>9,}")
    check("2006 active", series[2006], 157_552, tol=60)
    check("2025 active", series[2025], 253_419, tol=60)
    gaps = [y for y in range(2007, 2026)
            if abs(series[y] - series[y - 1]) > 0.25 * series[y - 1]]
    check("years with >25% discontinuity", len(gaps), 0)

    print("\n5. Brand resolution (all three broke under naive normalization)")
    for pat, brand in [("7 ELEVEN", "7-Eleven"), ("DOLLARTREE", "Dollar Tree"),
                       ("WALMART", "Walmart")]:
        n = q(f"SELECT count(DISTINCT brand) FROM dim_store "
              f"WHERE name_norm LIKE '{pat}%' AND brand IS NOT NULL")
        check(f"{brand}: distinct brand values", n, 1)
    check("7-Eleven stores resolve to one brand",
          q("SELECT count(DISTINCT brand) FROM dim_store WHERE brand = '7-Eleven'"), 1)

    print("\n6. Dollar-store breakout")
    dollar = int(cur["is_dollar_store"].sum())
    check("active dollar stores", dollar, 37_362, tol=200)
    check("Dollar Store format == is_dollar_store",
          int((cur["format"] == "Dollar Store").sum()), dollar)
    combo_usda = int((cur["store_type_usda"] == "Combination Grocery/Other").sum())
    combo_fmt = int((cur["format"] == "Combination Grocery/Other").sum())
    print(f"     Combination Grocery/Other: {combo_usda:,} USDA -> {combo_fmt:,} after breakout")
    check("stores conserved across reclassification",
          combo_fmt + int(((cur["store_type_usda"] == "Combination Grocery/Other")
                           & cur["is_dollar_store"]).sum()), combo_usda)

    print("\n7. Data-quality flags")
    check("auth_date_unknown spells", q("SELECT count(*) FROM fact_spell WHERE auth_date_unknown"), 6_666)
    check("date_anomaly spells", q("SELECT count(*) FROM fact_spell WHERE date_anomaly"), 45)
    check("stores missing coordinates", q("SELECT count(*) FROM dim_store WHERE geocode_missing"), 4_542)
    # Coordinates that land outside every US/territory box: 38 Guam stores
    # geocoded to Jerusalem/France/the Philippines, a "China, Texas" Dollar
    # General placed in Tibet, and a California Big Lots in Venezuela.
    check("stores with off-world coordinates",
          q("SELECT count(*) FROM dim_store WHERE geocode_offshore"), 40)
    check("Guam stores among them",
          q("SELECT count(*) FROM dim_store WHERE geocode_offshore AND state = 'GU'"), 38)
    # Inside the US but in the wrong state: a Dime Box, Texas grocery placed in
    # Pennsylvania, a Manitowish Waters, Wisconsin market placed in Minnesota.
    check("stores whose coordinates land in another state",
          q("SELECT count(*) FROM dim_store WHERE state_mismatch"), 6)
    # Legitimate edge geography a bare bounding box would have caught.
    check("Adak / Montauk / Booker style edge cases spared",
          q("SELECT count(*) FROM dim_store WHERE state_mismatch AND ("
            "city ILIKE '%Montauk%' OR city ILIKE '%Booker%' OR city ILIKE '%Adak%' "
            "OR city ILIKE '%Big River%' OR city ILIKE '%Ewing%')"), 0)
    check("mappable stores", q("SELECT count(*) FROM dim_store WHERE mappable"), 656_868)
    check("unclassified stores (format IS NULL)", q("SELECT count(*) FROM dim_store WHERE format IS NULL"), 0)

    con.close()
    print("\n" + "=" * 62)
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
