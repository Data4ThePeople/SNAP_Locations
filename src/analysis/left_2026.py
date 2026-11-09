"""Stores that left SNAP between Dec 31, 2025 and the live-feed snapshot date.

A store "left" if it was authorized on Dec 31, 2025 in the historical file and
its Record_ID is nowhere in the live feed, under any type. An exit whose
address reappears under a different authorization is counted separately as
"replaced at the same address" and kept off the map. The address test is the street line and 5-digit ZIP,
upper-cased, each run of punctuation or spaces collapsed to one space, ends
trimmed; a blank street never matches.

The same test is run on the historical file for each earlier year, Dec 31 of
the prior year to the same month and day, so 2026 is compared with years
measured the same way. Those years use the file on both ends; 2026 uses the
file on one end and the live feed on the other. That difference is a limit,
and DATASETS.md says so.

Writes reports/data/left_2026.json and reports/assets/left-snap-2026.png.

    python -m analysis.left_2026      (from src/)
"""
import json
from datetime import date

from analysis import figures, usmap
from config import ROOT, connect

OUT_JSON = ROOT / "reports" / "data" / "left_2026.json"
OUT_PNG = ROOT / "reports" / "assets" / "left-snap-2026.png"
BASE = date(2025, 12, 31)
BASELINE_YEARS = range(2019, 2026)

NORM = "trim(regexp_replace(upper({}), '[^A-Z0-9]+', ' ', 'g'))"
HIST_ADDR = NORM.format("coalesce(street_number,'') || ' ' || coalesce(street_name,'')")
# The historical file stores ZIP as a number, so 02657 arrives as 2657 (48,748
# stores, mostly New England and New Jersey). The live feed keeps all 5 digits.
HIST_ZIP = "lpad(left(trim(d.zip_code), 5), 5, '0')"


def active(d):
    return (f"(SELECT DISTINCT record_id FROM fact_spell WHERE auth_date <= DATE '{d}' "
            f"AND (end_date IS NULL OR end_date >= DATE '{d}'))")


def exits(con, a, b, live=False):
    """One row per store authorized and mappable on date `a` that is gone by
    date `b`, with a `replaced` flag from the same-address test.

    `live=True` reads date `b` from the live feed (live_store) instead of the
    historical file. Both arms use the same base, the same address and ZIP
    normalization, and the same rule that a newcomer is any store present on
    `b` that was not in the base. Returns a list of dicts with record_id,
    format, ownership, brand, state, longitude, latitude and replaced.
    """
    if live:
        B = "SELECT record_id FROM live_store"
        N = (f"SELECT {NORM.format('street')} AS addr, zip5 FROM live_store "
             "WHERE record_id NOT IN (SELECT record_id FROM A) "
             "AND store_type_live <> 'Restaurant Meals Program'")
    else:
        B = f"SELECT record_id FROM {active(b)}"
        N = (f"SELECT {HIST_ADDR} AS addr, {HIST_ZIP} AS zip5 "
             f"FROM dim_store d JOIN {active(b)} USING (record_id) "
             "WHERE record_id NOT IN (SELECT record_id FROM A)")
    cur = con.execute(f"""
        WITH A AS (SELECT d.record_id, d.format, d.ownership, d.brand, d.state,
                          d.longitude, d.latitude, {HIST_ADDR} AS addr, {HIST_ZIP} AS zip5
                   FROM dim_store d JOIN {active(a)} USING (record_id) WHERE d.mappable),
             N AS ({N})
        SELECT A.record_id, A.format, A.ownership, A.brand, A.state, A.longitude, A.latitude,
               EXISTS (SELECT 1 FROM N WHERE N.addr = A.addr AND N.zip5 = A.zip5
                       AND A.addr <> '') AS replaced
        FROM A WHERE record_id NOT IN ({B})""")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def base(con, a):
    """Stores authorized and mappable on date `a`: record_id, format, ownership, brand, state."""
    cur = con.execute(f"""SELECT d.record_id, d.format, d.ownership, d.brand, d.state
                          FROM dim_store d JOIN {active(a)} USING (record_id) WHERE d.mappable""")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def run():
    con = connect(read_only=True)
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    label = f"{snap:%B} {snap.day}, {snap.year}"

    from collections import Counter
    b0 = base(con, BASE)
    gone = exits(con, BASE, snap, live=True)
    nb = Counter(r["format"] for r in b0)
    nl = Counter(r["format"] for r in gone)
    nr = Counter(r["format"] for r in gone if r["replaced"])
    by_format = [{"format": f, "base": n, "left": nl[f], "replaced": nr[f]}
                 for f, n in sorted(nb.items(), key=lambda t: -t[1])]
    for r in by_format:
        r["left_not_replaced"] = r["left"] - r["replaced"]
        r["pct_left_not_replaced"] = round(100 * r["left_not_replaced"] / r["base"], 1)

    # Earlier years, same test, historical file on both ends.
    baseline = []
    for y in BASELINE_YEARS:
        a, b = date(y - 1, 12, 31), date(y, snap.month, snap.day)
        A = base(con, a)
        G = exits(con, a, b)
        cv = [g for g in G if g["format"] == "Convenience Store"]
        baseline.append({"year": y, "from": str(a), "to": str(b),
                         "conv_base": sum(r["format"] == "Convenience Store" for r in A),
                         "conv_left": len(cv), "conv_replaced": sum(g["replaced"] for g in cv),
                         "all_base": len(A), "all_left": len(G),
                         "all_replaced": sum(g["replaced"] for g in G)})
    for row in baseline:
        row["conv_left_not_replaced"] = row["conv_left"] - row["conv_replaced"]
        row["conv_pct"] = round(100 * row["conv_left_not_replaced"] / row["conv_base"], 1)

    pts = [(g["longitude"], g["latitude"], g["format"] == "Convenience Store")
           for g in gone if not g["replaced"]]
    ground = con.execute("""SELECT lon, lat FROM live_store
                            WHERE excluded IS NULL AND mappable""").fetchall()
    con.close()

    conv = next(r for r in by_format if r["format"] == "Convenience Store")
    tot = {k: sum(r[k] for r in by_format) for k in ("base", "left", "replaced", "left_not_replaced")}
    result = {"snapshot_date": str(snap), "base_date": str(BASE), "totals": tot,
              "by_format": by_format, "baseline_years": baseline}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT_JSON}")

    def lo48(rows):
        x0, y0, x1, y1 = usmap.LO48
        return [r for r in rows if x0 <= r[0] <= x1 and y0 <= r[1] <= y1]

    g48, p48 = lo48(ground), lo48(pts)
    result["shown_lower48"] = len(p48)
    OUT_JSON.write_text(json.dumps(result, indent=1))
    c48 = [p for p in p48 if p[2]]
    o48 = [p for p in p48 if not p[2]]
    xy = lambda rows: usmap.albers([r[0] for r in rows], [r[1] for r in rows])
    S = figures.S
    figures.map_pair_png(
        OUT_PNG,
        [{"title": "", "layers": [
            {"xy": xy(g48), "color": figures.MUTED, "size": 0.18, "alpha": 0.35},
            {"xy": xy(o48), "color": S[0], "size": 0.9, "alpha": 0.8},
            {"xy": xy(c48), "color": S[1], "size": 0.9, "alpha": 0.8},
        ], "keys": [
            {"label": f"{conv['left_not_replaced']:,} convenience stores", "color": S[1]},
            {"label": f"{tot['left_not_replaced'] - conv['left_not_replaced']:,} other stores", "color": S[0]},
            {"label": "still in SNAP", "color": figures.MUTED},
        ]}],
        width=8.0,
        title="Stores that left SNAP so far in 2026",
        subtitle=(f"authorized December 31, 2025, not on USDA's list {label}, "
                  "no new authorization at the same address"),
        note=(f"Counts are national; the map shows the lower 48 ({len(p48):,} of {tot['left_not_replaced']:,}). "
              f"Leaves out {tot['replaced']:,} exits where a different\nauthorization appeared at the same "
              "address. Source: USDA Food and Nutrition Administration, SNAP retailer historical data and live feed."),
    )
    print(f"wrote {OUT_PNG}")
    print(f"  convenience: {conv['base']:,} on Dec 31, {conv['left']:,} left, "
          f"{conv['replaced']:,} replaced, {conv['left_not_replaced']:,} not replaced "
          f"({conv['pct_left_not_replaced']}%)")
    for row in baseline:
        print(f"  {row['year']}: convenience not replaced {row['conv_left_not_replaced']:,} "
              f"of {row['conv_base']:,} ({row['conv_pct']}%)")
    return result


if __name__ == "__main__":
    run()
