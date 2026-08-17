"""Post 6 — the other format that endures.

Posts 1-5 landed on one mechanism: in thin markets, the formats with the lowest
fixed cost per site are what remain. Post 5 named dollar stores as that format.
That is incomplete. Fuel-forward convenience chains satisfy the same condition,
persist at the same rate, and have something dollar stores do not: a fuel margin
that roughly doubled after 2020 and stayed there (fuel_margin.py, which pulls
EIA weekly prices and two companies' 10-Ks).

The finding this post turns on is that "convenience store" is not one thing. Cut
the format by operator scale and the pieces move in opposite directions:

    fuel-forward chains        78.7% of a 2008-12 cohort still active in 2025
    dollar stores              78.2%   <- the post-1 benchmark, for scale
    other convenience chains   33.1%
    fuel-branded single sites  20.6%
    unbranded convenience      13.5%

USDA's own store-type field cannot show this, because all four convenience rows
above collapse into one category. That is the reason the format reads as stable
in aggregate while its composition turns over completely.

Segments, cut on evidence already in dim_store rather than on judgement:

  fuel-forward chains   a named, listed set of operators that run fueling
                        positions at essentially all US sites. This IS a curated
                        list and is printed in the output so it can be audited.
                        7-Eleven is deliberately excluded: it is the largest
                        convenience brand in the data by a wide margin and is
                        mixed on fuel, so including it would let one brand carry
                        a claim about fuel economics.
  other conv. chains    any other recognised brand (brands.csv; 4+ locations is
                        the floor for a brand to exist at all).
  fuel-branded          the name carries an oil brand (SHELL, BP, EXXON...) and
                        nothing else. classify.py deliberately calls these
                        ownership=unknown: a canopy brand is a fuel supply
                        agreement, not ownership, so these are overwhelmingly
                        single-site dealers.
  unbranded             no recognised brand at all.

Two guards on the language, per the rules this series runs under:

  1. Authorizations are not storefronts. Chain-census ratios license "stores"
     for the chains: Murphy USA and Casey's both publish store counts in their
     10-Ks and both appear in this data, so the ratio is checkable here rather
     than asserted. It is NOT checkable for single sites, and stock growth in
     the single-site segments is therefore ambiguous between more stores and
     wider SNAP take-up among stores that already existed.
  2. No uncertain independent claims. The unbranded segment is mostly small
     independent operators, so nothing is said about it until its authorization
     trend is tested against Census County Business Patterns establishment
     counts. CBP counts establishments whether or not they take EBT, which
     separates "left the program" from "closed" the way it did in post 2.
"""
import io
import json
import statistics
import urllib.request
import zipfile

from analysis import panel
from config import DATA, ROOT

OUT = ROOT / "reports" / "data"
CBP_CACHE = DATA / "raw" / "cbp_convenience.json"

COHORT = (2008, 2012)   # first authorized in this window
COHORT_END = 2025       # still active on 31 December of this year

FUEL_FORWARD = ("Casey's", "Murphy USA", "Murphy Express", "Circle K", "Speedway",
                "QuikTrip", "Sheetz", "Wawa", "Maverik", "Kwik Trip", "RaceTrac",
                "Love's Travel Stops", "Pilot", "Pilot Flying J", "Cumberland Farms",
                "Holiday Stationstores", "Kum & Go", "Stripes", "Allsup's",
                "Royal Farms", "Rutter's", "Thorntons", "Yesway", "GetGo")

OIL_BRANDS = ("SHELL", "BP", "CITGO", "SUNOCO", "MOBIL", "EXXON", "CHEVRON", "TEXACO",
              "ARCO", "MARATHON", "VALERO", "CONOCO", "SINCLAIR", "GULF", "PHILLIPS 66")

# NAICS for convenience retail. Convenience stores WITH fuel and WITHOUT are
# separate codes in every vintage, so both are always needed.
#
# The 2022 NAICS revision renumbered them to 445131 and 457110, but the CBP
# county files do NOT follow that on the schedule the vintage year implies: the
# 2022 and 2023 files still publish 445120 and 447110. Rather than track which
# file switched when, accept both code sets — they are disjoint, so a file can
# only match one of them and a union cannot double-count. Rollup codes like
# "4451//" and "44512/" are excluded by requiring an exact 6-digit match, which
# matters because a rollup would double-count its own children.
NAICS_CODES = ("445120", "447110", "445131", "457110")
CBP_YEARS = [2012, 2016, 2019, 2021, 2022, 2023]

# Named for who owns and runs the store, because that is what the split measures.
# An oil brand on the canopy is a fuel supply contract, not an owner — a "Shell"
# station is almost never owned by Shell — so those sit with the single sites.
# An earlier version broke them out separately; the distinction was real (20.6%
# survival against 13.5%) but too fine to carry its own row, and having two
# segments with "fuel" in the name made the table unreadable.
ORDER = ["chains that sell fuel", "dollar stores", "other chains",
         "single-owner stores"]
CONV_SEGMENTS = [s for s in ORDER if s != "dollar stores"]

FAILURES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def lit(s):
    """SQL string literal. Casey's and Love's both contain apostrophes."""
    return "'" + s.replace("'", "''") + "'"


def segment_case(alias="p"):
    """CASE assigning each panel row to exactly one segment, or NULL if neither
    a dollar store nor a convenience store. Order matters: the first matching
    branch wins, so fuel-forward is tested before the generic branded case."""
    ff = ",".join(lit(b) for b in FUEL_FORWARD)
    oil = "|".join(OIL_BRANDS)
    return f"""CASE
      WHEN {alias}.format = 'Dollar Store' THEN 'dollar stores'
      WHEN {alias}.format <> 'Convenience Store' THEN NULL
      WHEN {alias}.brand IN ({ff}) THEN 'chains that sell fuel'
      WHEN {alias}.brand IS NOT NULL THEN 'other chains'
      ELSE 'single-owner stores' END"""


ACTIVE = """JOIN fact_spell f ON NOT f.date_anomaly
                 AND f.auth_date <= make_date({y},12,31)
                 AND (f.end_date IS NULL OR f.end_date >= make_date({y},12,31))"""


def cohort_survival(con):
    """Share of each segment's entry cohort still active at COHORT_END.

    Cohort survival rather than a stock ratio, because a stock ratio confuses
    persistence with expansion: a segment can hold its count while replacing its
    entire base. This asks whether the same stores are still there — which is
    the question "does this format endure" actually means.
    """
    lo, hi = COHORT
    return con.execute(f"""
        WITH c AS (
            SELECT p.record_id, {segment_case()} AS seg FROM panel p
            WHERE year(p.first_auth) BETWEEN {lo} AND {hi}),
        alive AS (
            SELECT DISTINCT record_id FROM fact_spell
            WHERE NOT date_anomaly
              AND auth_date <= make_date({COHORT_END},12,31)
              AND (end_date IS NULL OR end_date >= make_date({COHORT_END},12,31)))
        SELECT c.seg, count(*) AS cohort,
               count(*) FILTER (WHERE a.record_id IS NOT NULL) AS survived
        FROM c LEFT JOIN alive a USING (record_id)
        WHERE c.seg IS NOT NULL GROUP BY 1
    """).df()


def stock_by_segment(con):
    return con.execute(f"""
        SELECT y.yr, {segment_case()} AS seg, count(DISTINCT f.record_id) AS n
        FROM generate_series({panel.FIRST_YEAR},{panel.LAST_YEAR}) AS y(yr)
        JOIN fact_spell f ON NOT f.date_anomaly
                         AND f.auth_date <= make_date(y.yr,12,31)
                         AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
        JOIN panel p ON p.record_id = f.record_id
        WHERE {segment_case()} IS NOT NULL
        GROUP BY 1,2 ORDER BY 2,1
    """).df()


def active_count(con, year, where):
    return int(con.execute(f"""
        SELECT count(DISTINCT f.record_id)
        FROM fact_spell f JOIN panel p ON p.record_id = f.record_id
        WHERE NOT f.date_anomaly
          AND f.auth_date <= make_date({year},12,31)
          AND (f.end_date IS NULL OR f.end_date >= make_date({year},12,31))
          AND ({where})""").fetchone()[0])


def cbp_year(year):
    yy = f"{year % 100:02d}"
    url = f"https://www2.census.gov/programs-surveys/cbp/datasets/{year}/cbp{yy}co.zip"
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            blob = r.read()
    except Exception as e:
        print(f"    {year}: {type(e).__name__} — skipped")
        return None
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            text = io.TextIOWrapper(fh, encoding="latin-1")
            header = [h.strip().strip('"') for h in next(text).split(",")]
            idx = {h: i for i, h in enumerate(header)}
            c_small = idx.get("n1_4", idx.get("n<5"))
            c_naics, c_est = idx["naics"], idx["est"]
            tot = small = 0
            found = set()
            for line in text:
                f = line.rstrip("\n").split(",")
                if len(f) <= max(c_naics, c_est, c_small):
                    continue
                code = f[c_naics].strip().strip('"')
                if code not in NAICS_CODES:
                    continue
                found.add(code)
                try:
                    tot += int(f[c_est] or 0)
                    small += int(f[c_small] or 0)
                except ValueError:
                    continue
    return {"establishments": tot, "under_5_emp": small, "naics": sorted(found)}


def cbp():
    if CBP_CACHE.exists():
        return {int(k): v for k, v in json.loads(CBP_CACHE.read_text()).items()}
    print("  downloading CBP county files (no API key needed)")
    out = {}
    for y in CBP_YEARS:
        r = cbp_year(y)
        if r:
            out[y] = r
            print(f"    {y}: {r['establishments']:,} establishments "
                  f"({r['under_5_emp']:,} under 5 employees)  NAICS {'+'.join(r['naics'])}")
    CBP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    CBP_CACHE.write_text(json.dumps(out))
    return out


def main():
    con = panel.build()
    out = {"fuel_forward_brands": list(FUEL_FORWARD), "cohort": list(COHORT),
           "cohort_end": COHORT_END}

    print("1. Segments partition the convenience format exactly")
    tot = dict(con.execute(f"""
        SELECT {segment_case()} AS seg, count(*) FROM panel p
        WHERE {segment_case()} IS NOT NULL GROUP BY 1""").fetchall())
    conv_total = int(con.execute(
        "SELECT count(*) FROM panel WHERE format='Convenience Store'").fetchone()[0])
    for k in ORDER:
        print(f"     {k:28} {int(tot.get(k,0)):>8,}")
    conv_sum = sum(int(tot.get(k, 0)) for k in CONV_SEGMENTS)
    check("the four convenience segments sum to the format total",
          conv_sum == conv_total, f"{conv_sum:,} vs {conv_total:,}")
    out["totals"] = {k: int(tot.get(k, 0)) for k in ORDER}
    out["convenience_total"] = conv_total

    print(f"\n2. Cohort survival: first authorized {COHORT[0]}-{COHORT[1]}, "
          f"still active {COHORT_END}")
    cs = cohort_survival(con)
    cs["rate"] = (100 * cs["survived"] / cs["cohort"]).round(1)
    cs = cs.set_index("seg").reindex(ORDER)
    for seg, r in cs.iterrows():
        print(f"     {seg:28} {r['rate']:>5.1f}%   ({int(r['survived']):>6,} of "
              f"{int(r['cohort']):>6,})")
    out["survival"] = [{"segment": s, "cohort": int(r["cohort"]),
                        "survived": int(r["survived"]), "rate": float(r["rate"])}
                       for s, r in cs.iterrows()]
    ff_r = float(cs.loc["chains that sell fuel", "rate"])
    do_r = float(cs.loc["dollar stores", "rate"])
    oc_r = float(cs.loc["other chains", "rate"])
    un_r = float(cs.loc["single-owner stores", "rate"])
    out["survival_gap_pp"] = round(ff_r - do_r, 1)
    check("chains that sell fuel persist at the dollar-store rate (within 3pp)",
          abs(ff_r - do_r) <= 3, f"{ff_r}% vs {do_r}%")
    check("scale, not fuel, orders survival",
          ff_r > oc_r > un_r, f"{ff_r} > {oc_r} > {un_r}")
    check("chains persist at more than 4x the single-owner rate",
          ff_r > 4 * un_r, f"{ff_r}% vs {un_r}%")

    print("\n3. Stock 2006 to 2025")
    st = stock_by_segment(con)
    piv = st.pivot(index="yr", columns="seg", values="n").fillna(0).astype(int)
    piv = piv.reindex(columns=ORDER)
    out["stock"] = {"years": [int(y) for y in piv.index],
                    "series": {c: [int(v) for v in piv[c]] for c in piv.columns}}
    ch = {}
    print(f"     {'segment':28} {'2006':>8} {'2025':>8} {'multiple':>9}")
    for c in piv.columns:
        a, b = int(piv[c].iloc[0]), int(piv[c].iloc[-1])
        ch[c] = {"y2006": a, "y2025": b, "multiple": round(b / a, 2) if a else None}
        print(f"     {c:28} {a:>8,} {b:>8,} {ch[c]['multiple']:>8.2f}x")
    out["stock_change"] = ch
    check("chains that sell fuel more than tripled",
          ch["chains that sell fuel"]["multiple"] >= 3,
          f"{ch['chains that sell fuel']['multiple']}x")
    check("single-owner stores grew least of any segment",
          ch["single-owner stores"]["multiple"] == min(
              v["multiple"] for v in ch.values()),
          f"{ch['single-owner stores']['multiple']}x")

    print("\n4. The composition shift inside one USDA category")
    y0, y1 = panel.FIRST_YEAR, panel.LAST_YEAR
    shares = {}
    for y in (y0, 2015, y1):
        row = piv.loc[y, CONV_SEGMENTS]
        shares[y] = {k: round(100 * int(row[k]) / int(row.sum()), 1) for k in CONV_SEGMENTS}
        print(f"     {y}  " + "  ".join(f"{k.split()[0]} {v}%" for k, v in shares[y].items()))
    out["shares"] = shares
    check("chains' share of the convenience format rose",
          shares[y1]["chains that sell fuel"] > shares[y0]["chains that sell fuel"],
          f"{shares[y0]['chains that sell fuel']}% -> {shares[y1]['chains that sell fuel']}%")

    print("\n4b. How fast the named chains grew")
    # Median year-over-year change, not the start-to-end multiple.
    #
    # Two different things look identical in an authorization file: a chain that
    # opens stores adds them a few at a time, and a chain that decides to start
    # taking EBT adds its whole estate in one year. Wawa put 40% of nineteen
    # years of growth into 2010 alone; Murphy USA put 48% into 2022. A multiple
    # reads those as explosive expansion, which they are not.
    #
    # The median discards them by construction — one outlier year cannot move it
    # — so what is left is the rate in a typical year. Years growing off a base
    # under 50 stores are skipped, because a percentage off a base that small is
    # noise rather than a growth rate.
    # Restricted to the fuel chains, because that is the segment this section is
    # about. 7-Eleven is the largest convenience brand in the file but is NOT on
    # that list — it is mixed on fuel — so including it here contradicted the
    # section it illustrated.
    ff_list = ",".join(lit(b) for b in FUEL_FORWARD)
    series = con.execute(f"""
        SELECT y.yr, p.brand, count(DISTINCT f.record_id) AS n
        FROM generate_series({panel.FIRST_YEAR},{panel.LAST_YEAR}) AS y(yr)
        JOIN fact_spell f ON NOT f.date_anomaly
                         AND f.auth_date <= make_date(y.yr,12,31)
                         AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
        JOIN panel p ON p.record_id = f.record_id
        WHERE p.format = 'Convenience Store' AND p.brand IN ({ff_list})
        GROUP BY 1, 2""").df()

    brands = []
    for b in series.brand.unique():
        s = (series[series.brand == b].set_index("yr")["n"]
             .reindex(range(panel.FIRST_YEAR, panel.LAST_YEAR + 1), fill_value=0))
        if s.iloc[-1] < 500:
            continue
        g = [s.iloc[k] / s.iloc[k - 1] - 1 for k in range(1, len(s)) if s.iloc[k - 1] >= 50]
        # A chain needs most of the window at a countable size for its median to
        # be comparable with the rest. Murphy USA has only eight such years — its
        # stores existed from the 1990s but did not take EBT until 2009 — so a
        # rate from that window is not the same measurement as Circle K's.
        if len(g) < 12:
            continue
        step = s.diff().fillna(0)
        rise = max(int(s.iloc[-1] - s.iloc[0]), 1)
        brands.append({
            "brand": b, "y0": int(s.iloc[0]), "y1": int(s.iloc[-1]),
            "median_growth": round(100 * statistics.median(g), 1),
            "years_counted": len(g),
            # Kept for the limits note, not shown in the piece.
            "biggest_jump_share": round(100 * step.max() / rise, 1),
            "jump_year": int(step.idxmax())})
    brands.sort(key=lambda r: -r["y1"])
    out["brand_growth"] = {"brands": brands}
    print(f"     {'brand':<22} {'2025':>7} {'median yr':>10} {'yrs':>5}")
    for r in brands[:10]:
        print(f"     {r['brand']:<22} {r['y1']:>7,} {r['median_growth']:>9.1f}% "
              f"{r['years_counted']:>5}")
    check("every named chain grew in a typical year",
          all(r["median_growth"] > 0 for r in brands),
          f"slowest {min(r['median_growth'] for r in brands)}%")

    print("\n5. Chain census: do authorizations equal stores for these operators?")
    # Store counts as each company reports them in its own FY2025 10-K.
    cens = []
    for brands, label, reported in ((("Casey's",), "Casey's", 2907),
                                    (("Murphy USA", "Murphy Express"), "Murphy USA", 1649)):
        w = "p.brand IN (" + ",".join(lit(b) for b in brands) + ")"
        n = active_count(con, 2025, w)
        cens.append({"chain": label, "authorized": n, "reported": reported,
                     "ratio": round(n / reported, 2)})
        print(f"     {label:12} {n:>6,} authorized vs {reported:>6,} reported "
              f"= {n/reported:.2f}")
    out["census"] = cens
    check("at least one fuel chain's authorizations approximate its store count",
          any(0.85 <= c["ratio"] <= 1.15 for c in cens),
          ", ".join(f"{c['chain']} {c['ratio']}" for c in cens))

    print("\n6. Is the unbranded trend closure, or program churn? (CBP)")
    c = cbp()
    if c:
        yrs = sorted(c)
        # A NAICS code that stops matching returns 0 rather than an error, which
        # would silently read as a 100% collapse. CBP counts roughly 120-135k
        # convenience establishments nationally, so anything outside a wide band
        # around that is an extraction failure, not a finding.
        bad = [y for y in yrs if not 80_000 < c[y]["establishments"] < 200_000]
        check("every CBP year returned a plausible establishment count", not bad,
              f"implausible years: {[(y, c[y]['establishments']) for y in bad]}"
              if bad else f"{len(yrs)} years in 80k-200k")
        if bad:
            yrs = [y for y in yrs if y not in bad]
        unb = "p.format='Convenience Store' AND p.brand IS NULL"
        snap_unb = {y: active_count(con, y, unb) for y in yrs}
        print(f"     {'yr':>6} | {'CBP estabs':>11} {'<5 emp':>9} | {'SNAP unbranded':>15}")
        for y in yrs:
            print(f"     {y:>6} | {c[y]['establishments']:>11,} {c[y]['under_5_emp']:>9,} |"
                  f" {snap_unb[y]:>15,}")
        b0, b1 = yrs[0], yrs[-1]
        pct = lambda a, z: round(100 * (z / a - 1), 1) if a else 0.0
        cb = {"years": yrs, "cbp": {y: c[y] for y in yrs}, "snap_unbranded": snap_unb,
              "base_year": b0, "last_year": b1,
              "cbp_pct": pct(c[b0]["establishments"], c[b1]["establishments"]),
              "cbp_under5_pct": pct(c[b0]["under_5_emp"], c[b1]["under_5_emp"]),
              "snap_pct": pct(snap_unb[b0], snap_unb[b1])}
        print(f"\n     {b0} to {b1}:  CBP establishments {cb['cbp_pct']:+.1f}%,"
              f"  under-5-employee {cb['cbp_under5_pct']:+.1f}%,"
              f"  SNAP unbranded {cb['snap_pct']:+.1f}%")
        if cb["cbp_pct"] > 0 and cb["snap_pct"] > -20:
            cb["verdict"] = "sector_stable_stores_churn"
            print("     -> Establishments GREW while authorizations were flat-to-slightly-down.")
            print("        The unbranded sector is not disappearing. Its low cohort survival is")
            print("        therefore turnover — stores changing hands, names and registrations —")
            print("        not closure. Never write that these stores 'closed' or 'were lost'.")
        elif cb["snap_pct"] > 0 and cb["cbp_pct"] <= 0:
            cb["verdict"] = "authorization_take_up"
            print("     -> Authorizations rose while establishments did not. The unbranded")
            print("        count is rising because more existing stores took EBT, not because")
            print("        more stores exist. Do NOT read its growth as store growth.")
        elif cb["cbp_under5_pct"] > -10 and cb["snap_pct"] < -20:
            cb["verdict"] = "left_program"
            print("     -> Establishments held up while authorizations fell: mostly stores")
            print("        LEAVING SNAP. Say 'left the program', never 'closed'.")
        elif cb["cbp_under5_pct"] < -20:
            cb["verdict"] = "closed"
            print("     -> Both fell: real attrition of small convenience businesses.")
        else:
            cb["verdict"] = "mixed"
            print("     -> Both moved; part attrition, part program churn.")
        out["cbp"] = cb

    print("\n7. Thin markets: the pharmacy-loss ZIPs from post 5")
    p5 = OUT / "post5.json"
    if p5.exists():
        d5 = json.loads(p5.read_text())
        out["post5"] = {k: d5[k] for k in
                        ("groups", "presence", "density", "arc", "arc_change", "total_loss")}
        pr = {r["label"]: r for r in d5["presence"]}
        cv = pr["convenience store"]
        print(f"     convenience present in {cv['lost_pct']}% of pharmacy-loss ZIPs"
              f" vs {cv['kept_pct']}% of controls")
        for seg_name, w in (("chains that sell fuel",
                             "p.brand IN (" + ",".join(lit(b) for b in FUEL_FORWARD) + ")"),
                            ("dollar stores", "p.format='Dollar Store'")):
            n = active_count(con, 2025, w)
            print(f"     {seg_name:22} {n:>7,} active nationally in 2025")

    fm = OUT / "fuel_margin.json"
    if fm.exists():
        out["fuel_margin"] = json.loads(fm.read_text())
        m = out["fuel_margin"]
        print("\n8. Margin evidence (fuel_margin.py)")
        for name, cc in m["companies"].items():
            print(f"     {name:26} {cc['pre_mean']} -> {cc['post_mean']} cpg "
                  f"({cc['pct']:+.0f}%)")
        print(f"     EIA gross spread {m['macro']['delta_cpg']:+.1f} cpg "
              f"({m['macro']['pct']:+.0f}%), macro/micro ratio {m['macro_micro_ratio']}")
        check("margin evidence corroborated across macro and micro",
              m["verdict"] == "margin_expanded_and_persisted", m["verdict"])
    else:
        check("fuel_margin.json exists — run analysis.fuel_margin first", False)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post6.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT / 'post6.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("all checks passed")


if __name__ == "__main__":
    main()
