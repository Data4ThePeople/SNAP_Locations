"""Post 8: stores that left SNAP in 2026, with convenience stores drilled into.

Every rate here is the same measure: of the stores authorized and mappable on
Dec 31 of the year before, the share whose authorization was gone by Nov 5 and
whose address did not get a new authorization (the test in
left_2026.exits). 2026 reads Nov 5 from USDA's live feed; 2019 to 2025 read it
from the historical file. "Earlier years" means the simple mean of the seven
yearly rates, 2019 to 2025.

New authorizations are stores present on Nov 5 that were not authorized on the
Dec 31 before (returns under an old ID count, as they do in every year). In
2026, 2,273 live-only stores carry IDs below the historical file's highest, so
some may be older authorizations the file never carried; the JSON records the
count with and without them.

Writes reports/data/post8.json and PNGs in reports/post8/images/.

    python -m analysis.post8_left2026      (from src/)
"""
import json
from collections import Counter
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from analysis import figures, usmap
from analysis.left_2026 import active, base, exits
from config import ROOT, connect

OUT = ROOT / "reports" / "data" / "post8.json"
IMG = ROOT / "reports" / "post8" / "images"
YEARS = list(range(2019, 2027))
CONV = "Convenience Store"
STATES = dict(zip(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
    "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU".split(),
    ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
     "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
     "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
     "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
     "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
     "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah",
     "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "Puerto Rico",
     "Virgin Islands", "Guam"]))
# States whose SNAP soda/candy purchase restriction was in effect at some point
# between Jan 1 and Nov 5, 2026: the ten in Chrisinger and White, Health Affairs
# Scholar 4(10), qxag275 (Oct 2026). Iowa, Nebraska and West Virginia were
# blocked by a court on June 22, 2026. Arkansas (target Jul 1) and Montana
# (target Sep 30) are left in the comparison group because their start could
# not be confirmed. Territories are left out of both groups.
RESTRICTED = {"IN", "ID", "OK", "LA", "TX", "FL", "UT", "IA", "NE", "WV"}
TERRITORIES = {"PR", "VI", "GU", "AS", "MP"}
NYC_COUNTIES = {"NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"}
OWN = [("chain", "Chain"), ("independent", "Independent"), ("unknown", "Owner unknown")]


def pct(n, d):
    """Percent to one decimal, rounding halves up (6.35 -> 6.4), so a reader
    redoing the division by hand gets the same figure."""
    if not d:
        return None
    return float((Decimal(100 * n) / Decimal(d)).quantize(Decimal("0.1"), ROUND_HALF_UP))


def main():
    con = connect(read_only=True)
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    label = f"{snap:%B} {snap.day}"
    max_hist_id = con.execute("SELECT max(record_id) FROM dim_store").fetchone()[0]

    years = {}
    for y in YEARS:
        a, b = date(y - 1, 12, 31), date(y, snap.month, snap.day)
        A = base(con, a)
        G_all = exits(con, a, b, live=(y == 2026))
        G = [g for g in G_all if not g["replaced"]]
        # New convenience authorizations, a to b.
        if y == 2026:
            new = con.execute(f"""
                SELECT count(*), count(*) FILTER (WHERE in_hist OR record_id > {max_hist_id})
                FROM live_store WHERE excluded IS NULL AND mappable AND format = '{CONV}'
                  AND record_id NOT IN {active(a)}""").fetchone()
        else:
            n = con.execute(f"""
                SELECT count(*) FROM dim_store d JOIN {active(b)} USING (record_id)
                WHERE d.mappable AND d.format = '{CONV}' AND record_id NOT IN {active(a)}""").fetchone()[0]
            new = (n, n)
        years[y] = {"A": A, "G": G, "G_all": G_all, "new": new}
    con.close()

    def rate(y, keep):
        A = [r for r in years[y]["A"] if keep(r)]
        G = [r for r in years[y]["G"] if keep(r)]
        return {"base": len(A), "left": len(G), "pct": pct(len(G), len(A))}

    def exact(s, y):
        return 100 * s[y]["left"] / s[y]["base"]

    def series(keep):
        return {y: rate(y, keep) for y in YEARS}

    def earlier(s):
        # Mean of the unrounded yearly rates, then rounded once.
        m = sum(exact(s, y) for y in YEARS[:-1]) / (len(YEARS) - 1)
        return float(Decimal(m).quantize(Decimal("0.1"), ROUND_HALF_UP))

    out = {"snapshot_date": str(snap), "years": YEARS,
           "measure": "left SNAP Dec 31 of prior year to Nov 5, not replaced at same address"}

    conv = series(lambda r: r["format"] == CONV)
    other = series(lambda r: r["format"] != CONV)
    # The same exits before the address test, and the share the test removed.
    # Both are disclosed because the replaced share fell in 2026.
    conv_all = {}
    for y in YEARS:
        G = [g for g in years[y]["G_all"] if g["format"] == CONV]
        rep = sum(g["replaced"] for g in G)
        conv_all[y] = {"left_any": len(G), "pct_any": pct(len(G), conv[y]["base"]),
                       "replaced": rep, "replaced_share_pct": pct(rep, len(G))}
    out["trend"] = {"convenience_before_address_test": conv_all,
                    "conv_any_earlier_mean": float(Decimal(sum(100 * conv_all[y]["left_any"] / conv[y]["base"]
                                                   for y in YEARS[:-1]) / 7).quantize(Decimal("0.1"), ROUND_HALF_UP)),
                    "convenience": conv, "all_other": other,
                    "conv_earlier_mean": earlier(conv), "other_earlier_mean": earlier(other)}

    own = {}
    for k, _ in OWN:
        s = series(lambda r, k=k: r["format"] == CONV and r["ownership"] == k)
        own[k] = {"by_year": s, "earlier_mean": earlier(s), "y2026": s[2026]}
    out["ownership"] = own

    b26 = Counter(r["brand"] for r in years[2026]["A"] if r["format"] == CONV and r["brand"])
    chains = [b for b, n in b26.most_common() if n >= 1000]
    out["chains"] = []
    for b in chains:
        s = series(lambda r, b=b: r["format"] == CONV and r["brand"] == b)
        out["chains"].append({"brand": b, "y2025": s[2025], "y2026": s[2026], "earlier_mean": earlier(s)})

    st26 = Counter(r["state"] for r in years[2026]["A"] if r["format"] == CONV)
    states = []
    for st, n in st26.items():
        if n < 500:
            continue
        s = series(lambda r, st=st: r["format"] == CONV and r["state"] == st)
        states.append({"state": st, "y2026": s[2026], "earlier_mean": earlier(s)})
    states.sort(key=lambda d: (-d["y2026"]["left"] / d["y2026"]["base"], d["state"]))
    out["states"] = states
    out["states_min_base"] = 500

    # Restriction states vs the rest, and New York City vs the rest of NY.
    # NYC uses the historical file's county field (the five boroughs).
    con = connect(read_only=True)
    nyc_ids = {r[0] for r in con.execute(
        "SELECT record_id FROM dim_store WHERE state = 'NY' AND upper(trim(county)) IN ('"
        + "','".join(sorted(NYC_COUNTIES)) + "')").fetchall()}
    con.close()
    groups = {
        "restricted": lambda r: r["format"] == CONV and r["state"] in RESTRICTED,
        "other_states": lambda r: (r["format"] == CONV and r["state"] not in RESTRICTED
                                   and r["state"] not in TERRITORIES),
        "nyc": lambda r: r["format"] == CONV and r["state"] == "NY" and r["record_id"] in nyc_ids,
        "rest_of_ny": lambda r: r["format"] == CONV and r["state"] == "NY" and r["record_id"] not in nyc_ids,
    }
    out["splits"] = {}
    for k, keep in groups.items():
        s = series(keep)
        out["splits"][k] = {"by_year": s, "earlier_mean": earlier(s), "y2026": s[2026],
                            "rise_points": float(Decimal(exact(s, 2026) - sum(exact(s, y) for y in YEARS[:-1]) / 7)
                                                   .quantize(Decimal("0.1"), ROUND_HALF_UP))}
    out["splits"]["restricted_states"] = sorted(RESTRICTED)

    fm = Counter(r["format"] for r in years[2026]["A"])
    formats = []
    for f, n in fm.items():
        if n < 1000:
            continue
        s = series(lambda r, f=f: r["format"] == f)
        formats.append({"format": f, "y2026": s[2026], "earlier_mean": earlier(s)})
    formats.sort(key=lambda d: (-d["y2026"]["left"] / d["y2026"]["base"], d["format"]))
    out["formats"] = formats

    new = {}
    for y in YEARS:
        allnew, strict = years[y]["new"]
        nb = conv[y]["base"]
        new[y] = {"new": allnew, "new_excl_old_ids": strict, "base": nb,
                  "pct": pct(allnew, nb), "pct_excl_old_ids": pct(strict, nb)}
    out["new_convenience"] = new

    # Recording-lag check: convenience end dates in Oct-Dec of each year. A
    # short fourth quarter in 2025 would mean some exits that happened in 2025
    # are counted in 2026, because the base date reads them as still authorized.
    con = connect(read_only=True)
    q4 = dict(con.execute(f"""
        SELECT year(end_date), count(DISTINCT record_id) FROM fact_spell f JOIN dim_store d USING (record_id)
        WHERE d.format = '{CONV}' AND NOT f.date_anomaly AND month(end_date) >= 10
          AND year(end_date) BETWEEN 2022 AND 2025 GROUP BY 1""").fetchall())
    con.close()
    prior = round(sum(q4[y] for y in (2022, 2023, 2024)) / 3)
    short = prior - q4[2025]
    out["q4_check"] = {"conv_end_dates_oct_dec": {str(k): v for k, v in sorted(q4.items())},
                       "mean_2022_2024": prior, "shortfall_2025": short,
                       "unit": "stores (distinct Record_ID) with a convenience end date Oct 1 to Dec 31",
                       "conv_pct_2026_if_shortfall_moved_to_2025":
                           pct(conv[2026]["left"] - short, conv[2026]["base"] - short)}

    # Gap: 2026 convenience exits above what the earlier years' rate would
    # give on the 2026 base. Expected = 2026 base x the mean of the seven
    # unrounded 2019-2025 rates; "highest year" uses the single highest rate.
    def gap(left, base, rates):
        mean, hi = sum(rates) / len(rates) / 100, max(rates) / 100
        whole = lambda x: int(Decimal(x).quantize(Decimal("1"), ROUND_HALF_UP))
        return {"left": left, "base": base,
                "expected_at_mean": whole(base * mean), "gap_vs_mean": left - whole(base * mean),
                "expected_at_highest_year": whole(base * hi), "gap_vs_highest_year": left - whole(base * hi)}
    early = YEARS[:-1]
    c26 = conv[2026]
    out["gap"] = {
        "method": "2026 exits minus 2026 base x 2019-2025 rate (mean of unrounded yearly rates, or highest year)",
        "not_replaced": gap(c26["left"], c26["base"], [exact(conv, y) for y in early]),
        "before_address_test": gap(conv_all[2026]["left_any"], c26["base"],
                                   [100 * conv_all[y]["left_any"] / conv[y]["base"] for y in early]),
        "not_replaced_lag_adjusted": gap(c26["left"] - short, c26["base"] - short,
                                         [exact(conv, y) for y in early]),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT}")
    charts(out, years, label)
    return out


def charts(out, years, label):
    IMG.mkdir(parents=True, exist_ok=True)
    S = figures.S
    tr = out["trend"]
    c26, o26 = tr["convenience"][2026], tr["all_other"][2026]

    # 1. Map: convenience stores only.
    x0, y0, x1, y1 = usmap.LO48
    in48 = lambda lo, la: x0 <= lo <= x1 and y0 <= la <= y1
    from config import connect
    con = connect(read_only=True)
    ground = [r for r in con.execute(f"""SELECT lon, lat FROM live_store WHERE excluded IS NULL
                AND mappable AND format = '{CONV}'""").fetchall() if in48(*r)]
    con.close()
    pts = [(g["longitude"], g["latitude"]) for g in years[2026]["G"]
           if g["format"] == CONV and in48(g["longitude"], g["latitude"])]
    out["map_conv_shown_lower48"] = len(pts)
    xy = lambda rows: usmap.albers([r[0] for r in rows], [r[1] for r in rows])
    figures.map_pair_png(
        IMG / "post8-map-convenience.png",
        [{"title": "", "layers": [
            {"xy": xy(ground), "color": figures.MUTED, "size": 0.2, "alpha": 0.35},
            {"xy": xy(pts), "color": S[1], "size": 1.0, "alpha": 0.85},
        ], "keys": [
            {"label": f"{c26['left']:,} left SNAP", "color": S[1]},
            {"label": "still in SNAP", "color": figures.MUTED},
        ]}],
        width=8.0,
        title="Convenience stores that left SNAP so far in 2026",
        subtitle=(f"authorized December 31, 2025, not on USDA's list {label}, 2026, "
                  "no new authorization at the same address"),
        note=(f"Count includes Alaska, Hawaii and the territories; the map shows the lower 48 ({len(pts):,} of {c26['left']:,}). "
              "Source: USDA Food and Nutrition Administration, SNAP retailer historical data and live feed."),
    )

    # 2. Trend, convenience vs every other format.
    figures.line_png(
        IMG / "post8-trend.png", YEARS,
        [{"name": "Convenience stores", "values": [tr["convenience"][y]["pct"] for y in YEARS], "slot": 2},
         {"name": "All other stores", "values": [tr["all_other"][y]["pct"] for y in YEARS], "slot": 1}],
        title="Share of SNAP stores that left between January 1 and " + label,
        subtitle="% of stores authorized on December 31 of the year before;\nexcludes exits replaced at the same address",
        annotate=[{"year": 2026, "text": "live list"}],
    )

    # 3. Ownership.
    figures.dotrows_png(
        IMG / "post8-ownership.png", [n for _, n in OWN],
        [{"name": "2019–2025 average", "values": [out["ownership"][k]["earlier_mean"] for k, _ in OWN], "slot": 1},
         {"name": "2026", "values": [out["ownership"][k]["y2026"]["pct"] for k, _ in OWN], "slot": 2}],
        title=f"Convenience stores that left SNAP by {label}, by owner",
        subtitle="% of each group authorized on December 31 of the year before",
        signed=False, x_zero=True,
    )

    # 4. Largest chains.
    ch = out["chains"]
    figures.dotrows_png(
        IMG / "post8-chains.png", [c["brand"] for c in ch],
        [{"name": "2025", "values": [c["y2025"]["pct"] for c in ch], "slot": 1},
         {"name": "2026", "values": [c["y2026"]["pct"] for c in ch], "slot": 2}],
        title=f"Largest convenience chains: stores that left SNAP by {label}",
        subtitle="% of each chain's stores authorized on December 31 of the year before",
        signed=False, x_zero=True,
    )

    # 5. States, top 15 by 2026 rate, plus the US.
    st = out["states"][:15]
    figures.dotrows_png(
        IMG / "post8-states.png", ["All states and territories"] + [STATES.get(s["state"], s["state"]) for s in st],
        [{"name": "2019–2025 average", "values": [tr["conv_earlier_mean"]] + [s["earlier_mean"] for s in st], "slot": 1},
         {"name": "2026", "values": [c26["pct"]] + [s["y2026"]["pct"] for s in st], "slot": 2}],
        title=f"States with the highest share of convenience stores leaving SNAP by {label}, 2026",
        subtitle="% of convenience stores authorized on December 31 of the year before; states with 500 or more",
        divider_after=1, signed=False, x_zero=True,
    )

    # 6. New convenience authorizations.
    nw = out["new_convenience"]
    figures.line_png(
        IMG / "post8-new.png", YEARS,
        [{"name": "New convenience stores", "values": [nw[y]["pct"] for y in YEARS], "slot": 1}],
        title=f"New convenience stores authorized between January 1 and {label}",
        subtitle=(f"% of convenience stores authorized on December 31 of the year before; still authorized {label}.\n"
                  f"2026 includes {nw[2026]['new'] - nw[2026]['new_excl_old_ids']:,} stores with older IDs "
                  f"({nw[2026]['pct_excl_old_ids']}% without them)"),
        annotate=[{"year": 2026, "text": "live list"}],
    )

    # 7. Formats.
    fm = out["formats"]
    figures.dotrows_png(
        IMG / "post8-formats.png", [f["format"] for f in fm],
        [{"name": "2019–2025 average", "values": [f["earlier_mean"] for f in fm], "slot": 1},
         {"name": "2026", "values": [f["y2026"]["pct"] for f in fm], "slot": 2}],
        title=f"Stores that left SNAP by {label}, by store type",
        subtitle="% of each type authorized on December 31 of the year before; types with 1,000 or more",
        signed=False, x_zero=True,
    )
    # 8. Restriction states and New York City.
    sp = out["splits"]
    keys = [("restricted", "States with soda or candy limits"), ("other_states", "Other states and DC"),
            ("nyc", "New York City"), ("rest_of_ny", "Rest of New York State")]
    figures.dotrows_png(
        IMG / "post8-splits.png", [n for _, n in keys],
        [{"name": "2019–2025 average", "values": [sp[k]["earlier_mean"] for k, _ in keys], "slot": 1},
         {"name": "2026", "values": [sp[k]["y2026"]["pct"] for k, _ in keys], "slot": 2}],
        title=f"Convenience stores that left SNAP by {label}: limit states and New York City",
        subtitle=("% of convenience stores authorized on December 31 of the year before; limit states had a SNAP\n"
                  "soda or candy restriction in effect in 2026 (see methods). Shows where exits rose, not why."),
        divider_after=2, signed=False, x_zero=True,
    )
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote charts to {IMG}")


if __name__ == "__main__":
    main()
