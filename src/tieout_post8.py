"""Tie out every number and label on the post 8 charts.

Recomputed in pandas from data/raw/hist.csv and the live snapshot gzip, not
from fact_spell, live_store or analysis.left_2026, then compared with
reports/data/post8.json. As in tieout_live.py, `mappable`, `format`,
`ownership` and `brand` come from dim_store, because recomputing them would mean
re-running the classifier. Writes TIEOUT_POST8.md; exits non-zero on a mismatch.

    python src/tieout_post8.py
"""
import gzip
import json
import re
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

from config import CSV_PATH, ROOT, connect
from fetch_live import LIVE_DIR

ROWS = []
CONV = "Convenience Store"

WORDS = [
    ("Splits chart: \"limit states had a SNAP soda or candy purchase restriction in effect in 2026\"",
     "Chrisinger and White, Health Affairs Scholar 4(10) qxag275, Oct 2026: ten states implemented during Jan 2025 to Jun 2026; IA, NE, WV blocked Jun 22, 2026",
     "supported; AR and MT targeted mid-2026 starts are unconfirmed and sit in the comparison group (DATASETS.md)"),
    ("Splits chart: \"New York City\"", "historical file County field: New York, Kings, Queens, Bronx, Richmond", "matches"),
    ("Every chart: \"left SNAP\" (never \"closed\")", "Authorization records; memory rule and DATASETS.md", "supported"),
    ("Every rate subtitle: \"% of ... authorized on December 31 of the year before\"",
     "Base in DATASETS.md exit test; recomputed above", "supported"),
    ("Trend and new-store titles: \"between January 1 and November 5\"",
     "Exit window Dec 31 to Nov 5 in DATASETS.md; live feed refresh date", "supported"),
    ("Trend and new-store marker: \"live list\" at 2026",
     "DATASETS.md: 2026 reads Nov 5 from the live feed, earlier years from the file", "supported"),
    ("Map title: \"Convenience stores that left SNAP so far in 2026\"",
     "Exit test, Dec 31, 2025 to Nov 5, 2026", "supported"),
    ("Map subtitle: \"no new authorization at the same address\"", "Address test in DATASETS.md", "supported"),
    ("Map note: \"Count includes Alaska, Hawaii and the territories; the map shows the lower 48\"",
     "Shown count recomputed above", "supported"),
    ("Trend subtitle: \"excludes exits replaced at the same address\"", "Exit test in DATASETS.md", "supported"),
    ("State chart title: \"highest share\"; first row \"All states and territories\"",
     "Ranked by 2026 rate; base includes territories", "supported"),
    ("New-store subtitle: \"still authorized November 5\"; \"2026 includes 1,671 stores with older IDs (5.5% without them)\"",
     "DATASETS.md post 8 breakdowns; recomputed above", "supported"),
    ("Map key: \"still in SNAP\" (convenience stores on the Nov 5 list)",
     "Ground layer: live_store convenience rows on the map", "supported"),
    ("Ownership rows: Chain, Independent, Owner unknown",
     "dim_store ownership; DATASETS.md curated brands (independent = name on 4 or fewer stores)", "supported"),
    ("Legend: \"2019–2025 average\"", "Simple mean of seven yearly rates, DATASETS.md post 8 breakdowns", "supported"),
    ("State chart: \"states with 500 or more\"", "Threshold recomputed above", "supported"),
    ("Store-type chart: \"types with 1,000 or more\"", "Threshold recomputed above", "supported"),
    ("Chain chart: \"Largest convenience chains\" (1,000 or more stores on Dec 31, 2025)",
     "Recomputed above; threshold not printed on the chart", "partly supported"),
    ("Map source line: USDA Food and Nutrition Administration, historical data and live feed",
     "DATASETS.md credit lines", "supported"),
]


def tie(item, built, recomputed):
    ROWS.append((item, built, recomputed, "match" if built == recomputed else "MISMATCH"))


def norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s).upper()).strip() if isinstance(s, str) else ""


def r1(x):
    return float(Decimal(x).quantize(Decimal("0.1"), ROUND_HALF_UP))


def pct(n, d):
    return r1(Decimal(100 * n) / Decimal(d)) if d else None


def main():
    built = json.loads((ROOT / "reports/data/post8.json").read_text())
    snap = date.fromisoformat(built["snapshot_date"])

    h = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8-sig")
    h["rid"] = h["Record ID"].astype("int64")
    h["auth"] = pd.to_datetime(h["Authorization Date"].str.strip(), format="%m/%d/%Y", errors="coerce")
    h["end"] = pd.to_datetime(h["End Date"].str.strip().replace("", None), format="%m/%d/%Y", errors="coerce")
    h["addr"] = (h["Street Number"].fillna("") + " " + h["Street Name"].fillna("")).map(norm)
    h["zip5"] = h["Zip Code"].fillna("").str.strip().str[:5].str.zfill(5)
    st = h.drop_duplicates("rid").set_index("rid")["State"].str.strip()
    cty = h.drop_duplicates("rid").set_index("rid")["County"].fillna("").str.strip().str.upper()

    with gzip.open(LIVE_DIR / f"snap-live-{snap}.csv.gz", "rt", encoding="utf-8") as fh:
        lv = pd.read_csv(fh, dtype=str)
    lv["rid"] = lv["Record_ID"].astype("int64")
    lv["addr"] = lv["Store_Street_Address"].map(norm)
    lv["zip5"] = lv["Zip_Code"].fillna("").str[:5]

    con = connect(read_only=True)
    ds = con.execute("SELECT record_id rid, mappable, format, ownership, brand FROM dim_store").df().set_index("rid")
    con.close()
    mappable = set(ds.index[ds["mappable"]])
    hist_ids = set(h["rid"])
    rmp = lv["Store_Type"].eq("Restaurant Meals Program")

    def active(d):
        d = pd.Timestamp(d)
        return set(h.loc[(h["auth"] <= d) & (h["end"].isna() | (h["end"] >= d)), "rid"])

    # Per year: base frame (mappable, active Dec 31 prior) with a `gone` flag
    # meaning left and not replaced at the same address.
    frames, newconv = {}, {}
    for y in range(2019, 2027):
        a, b = date(y - 1, 12, 31), date(y, snap.month, snap.day)
        A_ids = active(a) & mappable
        A = h[h["rid"].isin(A_ids)].drop_duplicates("rid").set_index("rid")
        if y == 2026:
            B_ids = set(lv["rid"])
            N = lv[~lv["rid"].isin(A_ids) & ~rmp]
        else:
            B_ids = active(b)
            N = h[h["rid"].isin(B_ids - A_ids)]
        keys = set(zip(N["addr"], N["zip5"]))
        left = ~A.index.isin(B_ids)
        rep = pd.Series([x != "" and (x, z) in keys for x, z in zip(A["addr"], A["zip5"])], index=A.index)
        f = pd.DataFrame({"gone": left & ~rep, "left_any": left, "rep_left": left & rep, "format": A.index.map(ds["format"]),
                          "own": A.index.map(ds["ownership"]), "brand": A.index.map(ds["brand"]),
                          "state": A.index.map(st), "county": A.index.map(cty)}, index=A.index)
        frames[y] = f
        if y < 2026:
            n = len((B_ids - active(a)) & set(ds.index[ds["mappable"] & ds["format"].eq(CONV)]))
            newconv[y] = (n, n)
    # 2026 new convenience: on the map (no RMP, no live-only markets), not
    # authorized Dec 31, 2025, convenience by historical format or by live
    # type with the dollar-name rule.
    from brands import normalize, resolve
    prior = active(date(2025, 12, 31))
    kept = lv[~rmp & ~(lv["Store_Type"].eq("Farmers and Markets") & ~lv["rid"].isin(hist_ids))]
    kept = kept[~kept["rid"].isin(prior)]
    m_hist = kept[kept["rid"].isin(hist_ids)]
    m_hist = m_hist[m_hist["rid"].isin(mappable) & m_hist["rid"].map(ds["format"]).eq(CONV)]
    lo = kept[~kept["rid"].isin(hist_ids) & kept["Store_Type"].eq(CONV)]
    lo = lo[[resolve(normalize(n or ""), s, CONV)[1] != "dollar"
             for n, s in zip(lo["Store_Name"].fillna(""), lo["State"])]]
    max_id = max(hist_ids)
    newconv[2026] = (len(m_hist) + len(lo), len(m_hist) + int((lo["rid"] > max_id).sum()))

    def rate(y, mask):
        f = frames[y][mask(frames[y])]
        return {"base": len(f), "left": int(f["gone"].sum()), "pct": pct(int(f["gone"].sum()), len(f))}

    def earlier(mask):
        # Mean of unrounded yearly rates.
        vals = []
        for y in range(2019, 2026):
            f = frames[y][mask(frames[y])]
            vals.append(100 * f["gone"].sum() / len(f))
        return r1(sum(vals) / 7)

    conv = lambda f: f["format"].eq(CONV)
    other = lambda f: ~f["format"].eq(CONV)
    t = built["trend"]
    for y in range(2019, 2027):
        tie(f"Convenience {y}: base, left, %", t["convenience"][str(y)], rate(y, conv))
        tie(f"All other stores {y}: %", t["all_other"][str(y)]["pct"], rate(y, other)["pct"])
        nb = rate(y, conv)["base"]
        b = built["new_convenience"][str(y)]
        tie(f"New convenience {y}: count, %", (b["new"], b["pct"]), (newconv[y][0], pct(newconv[y][0], nb)))
    tie("New convenience 2026 without older IDs: count, %",
        (built["new_convenience"]["2026"]["new_excl_old_ids"], built["new_convenience"]["2026"]["pct_excl_old_ids"]),
        (newconv[2026][1], pct(newconv[2026][1], rate(2026, conv)["base"])))
    tie("Convenience 2019–2025 average", t["conv_earlier_mean"], earlier(conv))
    any_vals = []
    for y in range(2019, 2027):
        f = frames[y][conv(frames[y])]
        la, rp = int(f["left_any"].sum()), int(f["rep_left"].sum())
        b = t["convenience_before_address_test"][str(y)]
        tie(f"Convenience {y} before address test: left, %, replaced, replaced share",
            (b["left_any"], b["pct_any"], b["replaced"], b["replaced_share_pct"]),
            (la, pct(la, len(f)), rp, pct(rp, la)))
        if y < 2026:
            any_vals.append(100 * la / len(f))
    tie("Convenience before address test, 2019–2025 average", t["conv_any_earlier_mean"], r1(sum(any_vals) / 7))
    tie("All other 2019–2025 average", t["other_earlier_mean"], earlier(other))

    for k, v in built["ownership"].items():
        m = lambda f, k=k: f["format"].eq(CONV) & f["own"].eq(k)
        tie(f"Ownership {k}: 2026", v["y2026"], rate(2026, m))
        tie(f"Ownership {k}: 2019–2025 average", v["earlier_mean"], earlier(m))

    f26 = frames[2026]
    big = f26[f26["format"].eq(CONV)]["brand"].value_counts()
    tie("Chains with 1,000+ convenience stores", [c["brand"] for c in built["chains"]],
        [b for b, n in big.items() if n >= 1000])
    for c in built["chains"]:
        m = lambda f, b=c["brand"]: f["format"].eq(CONV) & f["brand"].eq(b)
        tie(f"{c['brand']}: 2025 %, 2026 %", (c["y2025"]["pct"], c["y2026"]["pct"]),
            (rate(2025, m)["pct"], rate(2026, m)["pct"]))

    sc = f26[f26["format"].eq(CONV)]["state"].value_counts()
    states = [s for s, n in sc.items() if n >= 500]
    def exact(s):
        r = rate(2026, lambda f, s=s: f["format"].eq(CONV) & f["state"].eq(s))
        return (-r["left"] / r["base"], s)
    ranked = sorted(states, key=exact)
    tie("Top 15 states by 2026 rate", [s["state"] for s in built["states"][:15]], ranked[:15])
    for s in built["states"][:15]:
        m = lambda f, s=s["state"]: f["format"].eq(CONV) & f["state"].eq(s)
        tie(f"{s['state']}: 2026 %, average %", (s["y2026"]["pct"], s["earlier_mean"]),
            (rate(2026, m)["pct"], earlier(m)))

    fc = f26["format"].value_counts()
    for fm in built["formats"]:
        m = lambda f, x=fm["format"]: f["format"].eq(x)
        tie(f"{fm['format']}: 2026 %, average %", (fm["y2026"]["pct"], fm["earlier_mean"]),
            (rate(2026, m)["pct"], earlier(m)))
    tie("Store types with 1,000+", sorted(x["format"] for x in built["formats"]),
        sorted(x for x, n in fc.items() if n >= 1000))

    g = h[h["rid"].isin(frames[2026].index[frames[2026]["gone"] & frames[2026]["format"].eq(CONV)])]
    g = g.drop_duplicates("rid")
    lon, lat = g["Longitude"].astype(float), g["Latitude"].astype(float)
    from analysis.usmap import LO48
    x0, y0, x1, y1 = LO48
    tie("Map: convenience exits shown in lower 48", built["map_conv_shown_lower48"],
        int((lon.between(x0, x1) & lat.between(y0, y1)).sum()))

    cv = h[h["rid"].map(ds["format"]).eq(CONV) & h["end"].dt.month.ge(10)]
    cv = cv[cv["end"].dt.year.between(2022, 2025)]
    q4 = cv.groupby(cv["end"].dt.year)["rid"].nunique()
    q = built["q4_check"]
    tie("Q4 convenience stores with end dates, 2022–2025", q["conv_end_dates_oct_dec"],
        {str(k): int(v) for k, v in q4.items()})
    short = round(sum(int(q4[y]) for y in (2022, 2023, 2024)) / 3) - int(q4[2025])
    c26 = rate(2026, conv)
    tie("Q4 shortfall and adjusted 2026 rate", (q["shortfall_2025"], q["conv_pct_2026_if_shortfall_moved_to_2025"]),
        (short, pct(c26["left"] - short, c26["base"] - short)))

    # Restriction states (Chrisinger & White 2026, ten states) and NYC.
    R = set("IN ID OK LA TX FL UT IA NE WV".split()); T = set("PR VI GU AS MP".split())
    boro = {"NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"}
    sp = built["splits"]
    for key, m in (("restricted", lambda f: f["format"].eq(CONV) & f["state"].isin(R)),
                   ("other_states", lambda f: f["format"].eq(CONV) & ~f["state"].isin(R | T)),
                   ("nyc", lambda f: f["format"].eq(CONV) & f["state"].eq("NY") & f["county"].isin(boro)),
                   ("rest_of_ny", lambda f: f["format"].eq(CONV) & f["state"].eq("NY") & ~f["county"].isin(boro))):
        vals = [100 * frames[y][m(frames[y])]["gone"].mean() for y in range(2019, 2027)]
        tie(f"Split {key}: 2026, average, rise in points",
            (sp[key]["y2026"], sp[key]["earlier_mean"], sp[key]["rise_points"]),
            (rate(2026, m), r1(sum(vals[:7]) / 7), r1(vals[7] - sum(vals[:7]) / 7)))
    tie("Restriction states list", sp["restricted_states"], sorted(R))

    # Gap above the 2019-2025 rate, from the raw frames.
    from decimal import Decimal, ROUND_HALF_UP
    whole = lambda x: int(Decimal(x).quantize(Decimal("1"), ROUND_HALF_UP))
    def gap(left, base, rates):
        m, hi = sum(rates) / len(rates), max(rates)
        return (left - whole(base * m), left - whole(base * hi))
    cf = {y: frames[y][conv(frames[y])] for y in range(2019, 2027)}
    nr = [cf[y]["gone"].sum() / len(cf[y]) for y in range(2019, 2026)]
    an = [cf[y]["left_any"].sum() / len(cf[y]) for y in range(2019, 2026)]
    L, B, LA = int(cf[2026]["gone"].sum()), len(cf[2026]), int(cf[2026]["left_any"].sum())
    G = built["gap"]
    for key, rec in (("not_replaced", gap(L, B, nr)), ("before_address_test", gap(LA, B, an)),
                     ("not_replaced_lag_adjusted", gap(L - short, B - short, nr))):
        tie(f"Gap {key}: vs average, vs highest year",
            (G[key]["gap_vs_mean"], G[key]["gap_vs_highest_year"]), rec)

    # ---- Beats 2-5 (post8_beats.json) ----
    bj = json.loads((ROOT / "reports/data/post8_beats.json").read_text())
    con = connect(read_only=True)
    lmap = con.execute("SELECT record_id rid, mappable, excluded, format, ownership FROM live_store").df().set_index("rid")
    con.close()
    hc = h.drop_duplicates("rid").set_index("rid")
    def U(d):
        return active(d) & mappable
    lv_keep = lv[lv["rid"].isin(lmap.index[lmap["excluded"].isna() & lmap["mappable"]])]
    for y in range(2019, 2027):
        a = len(U(date(y - 1, 12, 31)))
        b = len(lv_keep) if y == 2026 else len(U(date(y, snap.month, snap.day)))
        tie(f"Net change {y}: Dec 31, Nov 5, net", (bj["net"][str(y)]["dec31"], bj["net"][str(y)]["nov5"],
            bj["net"][str(y)]["net"]), (a, b, b - a))
    boro = {"NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"}
    def grp(state, county, fm, own):
        if fm == CONV: return "Independent convenience" if own == "independent" else "Other convenience"
        if str(fm).startswith("Grocery"): return "Grocery, any size"
        return "All other stores"
    A26 = sorted(U(date(2025, 12, 31)))
    # Exits by year and group; waterfall from the 2019-2025 average.
    from decimal import Decimal as _D, ROUND_HALF_UP as _H
    G4 = ["Independent convenience", "Other convenience", "Grocery, any size", "All other stores"]
    def g4(f):
        return [grp(None, None, fm, ow) for fm, ow in zip(f["format"], f["own"])]
    byg = {}
    for y in range(2019, 2027):
        f = frames[y]
        e = bj["exits"][str(y)]
        tie(f"Exits {y}: left, left before address test, base",
            (e["left"], e["left_any"], e["base"]), (int(f["gone"].sum()), int(f["left_any"].sum()), len(f)))
        byg[y] = pd.Series(g4(f[f["gone"]])).value_counts()
    wh = lambda x: int(_D(x).quantize(_D("1"), _H))
    avg = {g: wh(sum(int(byg[y].get(g, 0)) for y in range(2019, 2026)) / 7) for g in G4}
    wf = bj["waterfall"]
    tie("Exit waterfall start and end", (wf["start"], wf["end"]), (sum(avg.values()), int(frames[2026]["gone"].sum())))
    for s in wf["steps"]:
        g = s["group"]
        tie(f"Exit waterfall {g}: average, 2026, change", (s["avg_2019_2025"], s["y2026"], s["change"]),
            (avg[g], int(byg[2026].get(g, 0)), int(byg[2026].get(g, 0)) - avg[g]))
    # Entries and the exit-to-entry ratio.
    lv_addr = lv.set_index("rid")
    max_id = max(hist_ids)
    for y in range(2019, 2027):
        a, b = date(y - 1, 12, 31), date(y, snap.month, snap.day)
        Aall = active(a)
        A = hc.loc[sorted(Aall & mappable)]
        if y == 2026:
            Bids = set(lv["rid"])
            N = lv_keep[~lv_keep["rid"].isin(Aall)]
            Naddr = list(zip(N["addr"], N["zip5"]))
            old = (~N["rid"].isin(hist_ids) & (N["rid"] <= max_id)).values
        else:
            Bids = active(b)
            nid = sorted((Bids - Aall) & mappable)
            N = hc.loc[nid]
            Naddr = list(zip(N["addr"], N["zip5"]))
            old = np.zeros(len(N), bool)
        X = A[~A.index.isin(Bids)]
        xk = set(zip(X["addr"], X["zip5"]))
        rep = np.array([ad != "" and (ad, z) in xk for ad, z in Naddr])
        e = bj["entries"][str(y)]
        left, left_any = int(frames[y]["gone"].sum()), int(frames[y]["left_any"].sum())
        new_addr = len(N) - int(rep.sum())
        r2 = lambda x: float(_D(x).quantize(_D("0.01"), _H))
        tie(f"Entries {y}: all, at exit address, ratio, ratio before address test",
            (e["all"], e["at_exit_address"], e["ratio"], e["ratio_any"]),
            (len(N), int(rep.sum()), r2(left / new_addr), r2(left_any / len(N))))
        if y == 2026:
            tie("Entries 2026: older-ID live-only, ratio without them",
                (e["old_id_live_only"], e["ratio_excl_old_ids"]),
                (int(old.sum()), r2(left / (new_addr - int((old & ~rep).sum())))))
    SM = "Grocery (Small)"
    for key, m in (("independent_convenience", lambda f: f["format"].eq(CONV) & f["own"].eq("independent")),
                   ("chain_convenience", lambda f: f["format"].eq(CONV) & f["own"].eq("chain")),
                   ("nyc_small", lambda f: f["format"].isin([CONV, SM]) & f["state"].eq("NY") & f["county"].isin(boro)),
                   ("us_small_outside_nyc", lambda f: f["format"].isin([CONV, SM]) &
                    ~(f["state"].eq("NY") & f["county"].isin(boro)))):
        for y in range(2019, 2027):
            tie(f"Rate {key} {y}", bj["rates"][key][str(y)], rate(y, m))
    # Counties with shapely (the build uses matplotlib paths).
    import io, zipfile as _zf, shapefile as _shp
    from shapely.geometry import shape as _shape
    from shapely import STRtree, points as _points
    z = _zf.ZipFile(ROOT / "data/raw/cb_2024_us_county_500k.zip")
    gt = lambda e: io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith(e))))
    rd = _shp.Reader(shp=gt(".shp"), dbf=gt(".dbf"), shx=gt(".shx"))
    flds = [f[0] for f in rd.fields[1:]]
    recs = [dict(zip(flds, r)) for r in rd.records()]
    keepc = [i for i, r in enumerate(recs) if r["STATEFP"] not in {"60", "66", "69", "72", "78"}]
    geoms = [_shape(rd.shape(i).__geo_interface__) for i in keepc]
    tree = STRtree(geoms)
    def county_counts(lon, lat):
        pi, gi = tree.query(_points(np.asarray(lon, float), np.asarray(lat, float)), predicate="within")
        return pd.Series(gi).drop_duplicates().size and pd.Series(pi).groupby(gi).nunique()

    ca = county_counts(hc.loc[A26, "Longitude"].astype(float), hc.loc[A26, "Latitude"].astype(float))
    cbn = county_counts(lv_keep["Longitude"].astype(float), lv_keep["Latitude"].astype(float))
    geo = [recs[i]["GEOID"] for i in keepc]
    rows = pd.DataFrame({"geoid": geo, "dec31": [int(ca.get(i, 0)) for i in range(len(geo))],
                         "nov5": [int(cbn.get(i, 0)) for i in range(len(geo))]})
    pick = lambda q: sorted(rows.query(q)["geoid"])
    tie("Counties newly at zero", sorted(r["geoid"] for r in bj["counties_newly_zero"]), pick("dec31 > 0 and nov5 == 0"))
    tie("Counties down to one", sorted(r["geoid"] for r in bj["counties_down_to_one"]), pick("dec31 >= 2 and nov5 == 1"))
    tie("Counties halved (to 2+)", sorted(r["geoid"] for r in bj["counties_halved"]),
        pick("dec31 >= 2 and nov5 > 1 and nov5 <= dec31 / 2"))
    cs = bj["counties_summary"]
    tie("Counties with 0 and 1 store, Dec 31 and Nov 5", (cs["zero_dec31"], cs["zero_nov5"], cs["one_dec31"], cs["one_nov5"]),
        (int((rows.dec31 == 0).sum()), int((rows.nov5 == 0).sum()), int((rows.dec31 == 1).sum()), int((rows.nov5 == 1).sum())))
    for r in bj["counties_newly_zero"] + bj["counties_down_to_one"] + bj["counties_halved"]:
        x = rows[rows.geoid == r["geoid"]].iloc[0]
        tie(f"County {r['name']}: Dec 31, Nov 5", (r["dec31"], r["nov5"]), (int(x.dec31), int(x.nov5)))
    # Places: exits of convenience + small grocery by county field, NYC as one place.
    f26 = frames[2026]
    pf = f26[f26["format"].isin([CONV, SM])]
    plc = [("New York City" if s == "NY" and c in boro else f"{c.title()} County, {s}")
           for s, c in zip(pf["state"], pf["county"])]
    pf = pf.assign(place=plc)
    left = pf[pf["gone"]]["place"].value_counts()
    basep = pf["place"].value_counts()
    top = sorted(left.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    tie("Places top 10 (place, left, base, %)",
        [(r["place"], r["left"], r["base"], r["pct"]) for r in bj["places"]["top"]],
        [(k, int(n), int(basep[k]), pct(int(n), int(basep[k]))) for k, n in top])
    nyc = bj["places"]["top"][0]
    tie("NYC share of US exits and of US stores (conv + small grocery)",
        (nyc["share_of_us_left"], nyc["share_of_us_base"]),
        (pct(int(left["New York City"]), int(pf["gone"].sum())), pct(int(basep["New York City"]), len(pf))))
    for fm in (CONV, SM):
        q = pf[pf["format"].eq(fm) & pf["gone"]]
        tie(f"NYC share of US {fm} exits", bj["places"]["nyc_by_type"][fm]["share_pct"],
            pct(int((q["place"] == "New York City").sum()), len(q)))
    tie("NYC map: convenience and small groceries that left", bj["nyc_map"]["left_conv_small"],
        rate(2026, lambda f: f["format"].isin([CONV, SM]) & f["state"].eq("NY") & f["county"].isin(boro))["left"])

    fmt = lambda v: f"{v:,}" if isinstance(v, int) else str(v)
    lines = ["# Tie-out, post 8", "",
             f"Recomputed by `src/tieout_post8.py` from `data/raw/hist.csv` and "
             f"`data/raw/live/snap-live-{snap}.csv.gz`. `mappable`, `format`, `ownership` and `brand` "
             "are read from `dim_store`.", "",
             "| Item | Built | Recomputed | Result |", "|---|---|---|---|"]
    lines += [f"| {i} | {fmt(b)} | {fmt(r)} | {s} |" for i, b, r, s in ROWS]
    lines += ["", "## Words", "", "| Text on the output | Source | Verdict |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in WORDS]
    (ROOT / "TIEOUT_POST8.md").write_text("\n".join(lines) + "\n")
    bad = [r for r in ROWS if r[3] != "match"]
    for r in bad:
        print(f"  MISMATCH {r[0]}: built {r[1]}, recomputed {r[2]}")
    print(f"\n{len(ROWS) - len(bad)} of {len(ROWS)} match. Wrote TIEOUT_POST8.md")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
