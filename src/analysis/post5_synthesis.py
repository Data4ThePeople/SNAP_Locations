"""Post 5 — three forces, one destination.

Ties the series together on the ZIP codes that lost their last chain pharmacy
between 2021 and 2025. The tempting reading is substitution: pharmacies pushed
out, dollar stores moving in. This tests that against a control group of ZIPs
that kept their pharmacy, and it does not hold — which makes the real finding
more interesting and harder to act on.

Also tests the density hypothesis: that these are thin markets which cannot carry
a full grocery store, using 2020 census population by ZCTA.
"""
import json
import os
import pathlib
import urllib.request

from analysis import panel
from config import DATA, ROOT

OUT = ROOT / "reports" / "data"
POP_CACHE = DATA / "raw" / "zcta_pop.json"
DRUG = ("'Walgreens','CVS','Rite Aid','Duane Reade','Kinney Drugs','Discount Drug Mart',"
        "'Eckerd','Longs Drugs','Osco Drug','Sav-On'")
GROC = "('Supermarket','Super Store','Grocery (Large)','Grocery (Medium)','Grocery (Small)')"
FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def zcta_population():
    """2020 census population by ZCTA, cached. ZCTAs approximate ZIP codes."""
    if POP_CACHE.exists():
        return json.loads(POP_CACHE.read_text())
    key = ""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("CENSUS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    key = key or os.environ.get("CENSUS_API_KEY", "")
    if not key:
        print("  no CENSUS_API_KEY found — skipping the density test")
        return {}
    # ZCTA is not a supported geography on 2020/dec/pl (returns 400); the
    # decennial DHC file does carry it.
    url = ("https://api.census.gov/data/2020/dec/dhc?get=P1_001N"
           "&for=zip%20code%20tabulation%20area:*&key=" + key)
    print("  fetching ZCTA population from the Census API...")
    with urllib.request.urlopen(url, timeout=180) as r:
        rows = json.loads(r.read().decode())
    pop = {row[1]: int(row[0]) for row in rows[1:] if row[0] not in (None, "", "null")}
    POP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    POP_CACHE.write_text(json.dumps(pop))
    print(f"  cached {len(pop):,} ZCTAs to {POP_CACHE}")
    return pop


def main():
    con = panel.build()
    out = {}

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE zf AS
        SELECT y.yr, p.zip_code AS zip,
          count(DISTINCT CASE WHEN p.brand IN ({DRUG}) THEN p.record_id END) AS drug,
          count(DISTINCT CASE WHEN p.format='Dollar Store' THEN p.record_id END) AS dollar,
          count(DISTINCT CASE WHEN p.format='Convenience Store' THEN p.record_id END) AS conv,
          count(DISTINCT CASE WHEN p.format IN {GROC} THEN p.record_id END) AS groc
        FROM generate_series(2006,2025) AS y(yr)
        JOIN fact_spell f ON NOT f.date_anomaly
                         AND f.auth_date <= make_date(y.yr,12,31)
                         AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
        JOIN panel p ON p.record_id = f.record_id
        WHERE p.zip_code IS NOT NULL AND length(p.zip_code)=5
        GROUP BY 1,2
    """)
    # Treatment: lost the last chain pharmacy. Control: kept one. Without the
    # control every number below looks like substitution, because dollar stores
    # grew almost everywhere.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE grp AS
        SELECT a.zip, CASE WHEN coalesce(b.drug,0)=0 THEN 'lost' ELSE 'kept' END AS grp
        FROM (SELECT zip, drug FROM zf WHERE yr=2021 AND drug>0) a
        LEFT JOIN (SELECT zip, drug FROM zf WHERE yr=2025) b USING(zip)
    """)
    sizes = dict(con.execute("SELECT grp, count(*) FROM grp GROUP BY 1").fetchall())
    out["groups"] = {k: int(v) for k, v in sizes.items()}
    print(f"\n1. Groups: {sizes['lost']:,} ZIPs lost their last chain pharmacy, "
          f"{sizes['kept']:,} kept one")
    check("lost-pharmacy ZIPs", int(sizes["lost"]), 976, tol=5)

    print("\n2. What is there in 2025 — treatment against control")
    rows = []
    for label, where in (("dollar store", "z.dollar>0"),
                         ("convenience store", "z.conv>0"),
                         ("dollar or convenience", "(z.dollar>0 OR z.conv>0)"),
                         ("no grocery of any size", "z.groc=0")):
        r = dict((a, (b, c)) for a, b, c in con.execute(f"""
            SELECT g.grp, count(*) n, count(*) FILTER (WHERE {where}) k
            FROM grp g JOIN zf z ON z.zip=g.zip AND z.yr=2025 GROUP BY 1""").fetchall())
        rows.append({"label": label,
                     "lost_pct": round(100 * r["lost"][1] / r["lost"][0], 1),
                     "kept_pct": round(100 * r["kept"][1] / r["kept"][0], 1),
                     "lost_n": int(r["lost"][1]), "kept_n": int(r["kept"][1]),
                     "lost_base": int(r["lost"][0]), "kept_base": int(r["kept"][0])})
        print(f"     {label:24} lost {rows[-1]['lost_pct']:>5.1f}%   "
              f"kept {rows[-1]['kept_pct']:>5.1f}%")
    out["presence"] = rows
    nog = next(r for r in rows if r["label"] == "no grocery of any size")
    out["no_grocery_ratio"] = round(nog["lost_pct"] / nog["kept_pct"], 1)
    print(f"     -> pharmacy-loss ZIPs are {out['no_grocery_ratio']}x more likely to have"
          f" no grocery at all")

    print("\n3. Growth 2021-2025: did anyone move in?")
    g = {}
    for grp, n, d21, d25, c21, c25, upd, upc in con.execute("""
        SELECT g.grp, count(*),
               sum(a.dollar), sum(b.dollar), sum(a.conv), sum(b.conv),
               count(*) FILTER (WHERE b.dollar>a.dollar),
               count(*) FILTER (WHERE b.conv>a.conv)
        FROM grp g JOIN zf a ON a.zip=g.zip AND a.yr=2021
                   JOIN zf b ON b.zip=g.zip AND b.yr=2025
        GROUP BY 1""").fetchall():
        g[grp] = {"zips": int(n), "dollar_2021": int(d21), "dollar_2025": int(d25),
                  "conv_2021": int(c21), "conv_2025": int(c25),
                  "dollar_pct": round(100 * (d25 / d21 - 1), 1),
                  "conv_pct": round(100 * (c25 / c21 - 1), 1),
                  "zips_dollar_up": int(upd), "zips_conv_up": int(upc)}
        print(f"     {grp:5} dollar {d21:>6,} -> {d25:>6,} ({g[grp]['dollar_pct']:>+5.1f}%)"
              f"   convenience {c21:>6,} -> {c25:>6,} ({g[grp]['conv_pct']:>+5.1f}%)")
    out["growth"] = g
    print(f"     -> dollar growth was SLOWER where pharmacies left"
          f" ({g['lost']['dollar_pct']}% vs {g['kept']['dollar_pct']}%)")
    check("dollar growth slower in treatment than control",
          int(g["lost"]["dollar_pct"] < g["kept"]["dollar_pct"]), 1)

    print("\n4. Sequencing: the dollar stores were already there")
    r = con.execute("""
        SELECT count(*) FILTER (WHERE a.dollar>0),
               count(*) FILTER (WHERE a.dollar=0 AND b.dollar>0), count(*)
        FROM grp g JOIN zf a ON a.zip=g.zip AND a.yr=2021
                   JOIN zf b ON b.zip=g.zip AND b.yr=2025
        WHERE g.grp='lost'""").fetchone()
    out["sequencing"] = {"had_before": int(r[0]), "arrived_after": int(r[1]),
                         "base": int(r[2]),
                         "had_before_pct": round(100 * r[0] / r[2], 1),
                         "arrived_after_pct": round(100 * r[1] / r[2], 1)}
    s = out["sequencing"]
    print(f"     already had a dollar store in 2021: {s['had_before']:,} ({s['had_before_pct']}%)")
    print(f"     first dollar store arrived after:   {s['arrived_after']:,}"
          f" ({s['arrived_after_pct']}%)")

    print("\n5. The twenty-year arc in those same ZIP codes")
    arc = {"years": [], "drug": [], "dollar": [], "conv": [], "groc": []}
    for yr in range(2006, 2026):
        r = con.execute(f"""
            SELECT sum(z.drug), sum(z.dollar), sum(z.conv), sum(z.groc)
            FROM grp g JOIN zf z ON z.zip=g.zip AND z.yr={yr} WHERE g.grp='lost'
        """).fetchone()
        arc["years"].append(yr)
        for k, v in zip(("drug", "dollar", "conv", "groc"), r):
            arc[k].append(int(v or 0))
    out["arc"] = arc
    for i, yr in enumerate(arc["years"]):
        if yr in (2006, 2012, 2018, 2021, 2025):
            print(f"     {yr}  pharmacy {arc['drug'][i]:>5,}  dollar {arc['dollar'][i]:>6,}"
                  f"  convenience {arc['conv'][i]:>6,}  grocery {arc['groc'][i]:>6,}")
    out["arc_change"] = {
        "dollar_multiple": round(arc["dollar"][-1] / arc["dollar"][0], 1),
        "groc_pct": round(100 * (arc["groc"][-1] / arc["groc"][0] - 1), 1),
        "conv_pct": round(100 * (arc["conv"][-1] / arc["conv"][0] - 1), 1),
        "drug_peak": max(arc["drug"]),
        "drug_peak_year": arc["years"][arc["drug"].index(max(arc["drug"]))]}
    a = out["arc_change"]
    print(f"     -> dollar {a['dollar_multiple']}x, grocery {a['groc_pct']}%,"
          f" convenience {a['conv_pct']}%, pharmacy peak {a['drug_peak']:,}"
          f" ({a['drug_peak_year']}) to zero")

    print("\n6. Total loss")
    n = con.execute("""
        SELECT count(*) FROM grp g LEFT JOIN zf z ON z.zip=g.zip AND z.yr=2025
        WHERE g.grp='lost' AND z.zip IS NULL""").fetchone()[0]
    out["total_loss"] = {"no_snap_retail_at_all": int(n), "no_grocery": nog["lost_n"]}
    print(f"     {n} of the {sizes['lost']:,} have no SNAP-authorized retailer of any kind")
    print(f"     {nog['lost_n']} have no grocery of any size")

    # ---------------------------------------------------------------- density
    print("\n7. The density hypothesis: are these thin markets?")
    pop = zcta_population()
    if pop:
        con.execute("CREATE OR REPLACE TEMP TABLE zpop (zip VARCHAR, pop BIGINT)")
        con.executemany("INSERT INTO zpop VALUES (?, ?)", list(pop.items()))
        d = {}
        for grp, n, med, p25, share_small, share_tiny in con.execute("""
            SELECT g.grp, count(*), median(p.pop),
                   quantile_cont(p.pop, 0.25),
                   count(*) FILTER (WHERE p.pop < 10000)::DOUBLE / count(*),
                   count(*) FILTER (WHERE p.pop < 5000)::DOUBLE / count(*)
            FROM grp g JOIN zpop p ON p.zip = g.zip GROUP BY 1 ORDER BY 1""").fetchall():
            d[grp] = {"zips_matched": int(n), "median_pop": int(med),
                      "p25_pop": int(p25), "under_10k_pct": round(100 * share_small, 1),
                      "under_5k_pct": round(100 * share_tiny, 1)}
            print(f"     {grp:5} median ZIP population {int(med):>7,}"
                  f"   under 10k: {100*share_small:>5.1f}%   under 5k: {100*share_tiny:>5.1f}%")
        out["density"] = d
        # And the sharper version: among no-grocery ZIPs, how small are they?
        r = con.execute("""
            SELECT median(p.pop), count(*) FROM grp g
            JOIN zpop p ON p.zip=g.zip JOIN zf z ON z.zip=g.zip AND z.yr=2025
            WHERE g.grp='lost' AND z.groc=0""").fetchone()
        out["density"]["lost_no_grocery"] = {"median_pop": int(r[0] or 0), "n": int(r[1])}
        print(f"     of the pharmacy-loss ZIPs with no grocery at all (n={r[1]}),"
              f" median population is {int(r[0] or 0):,}")

    # The one-number summary of the whole run: how far the mix shifted toward
    # chains. Reported over ALL stores including the unclassified ones, which
    # makes it conservative — some unknowns are certainly chains, so the real
    # shift is at least this large.
    print("\nOwnership mix, first year against last")
    mix = {}
    for lbl, w in (("chain", "p.ownership = 'chain'"),
                   ("independent", "p.ownership = 'independent'"),
                   ("unknown", "p.ownership = 'unknown'"),
                   ("all", "TRUE")):
        a, b = (con.execute(f"""
            SELECT count(DISTINCT p.record_id) FROM panel p JOIN fact_spell s
            USING(record_id) WHERE {w} AND NOT s.date_anomaly
              AND s.auth_date <= make_date({y}, 12, 31)
              AND (s.end_date IS NULL OR s.end_date >= make_date({y}, 12, 31))
            """).fetchone()[0] for y in (2006, 2025))
        mix[lbl] = {"y2006": int(a), "y2025": int(b), "change": int(b - a)}
    for k in ("chain", "independent", "unknown"):
        mix[k]["share_2006"] = round(100 * mix[k]["y2006"] / mix["all"]["y2006"], 1)
        mix[k]["share_2025"] = round(100 * mix[k]["y2025"] / mix["all"]["y2025"], 1)
        print(f"   {k:<12} {mix[k]['y2006']:>8,} -> {mix[k]['y2025']:>8,}  "
              f"{mix[k]['share_2006']:>5}% -> {mix[k]['share_2025']:>5}%")
    out["ownership_mix"] = mix
    check("chains crossed from a minority of SNAP retailers to a majority",
          int(mix["chain"]["share_2006"] < 50 <= mix["chain"]["share_2025"]), 1)
    check("chains took more of the growth than independents",
          int(mix["chain"]["change"] > mix["independent"]["change"]), 1)

    out["series"] = {}
    for slug in ("post1", "post2", "post4"):
        p = OUT / f"{slug}.json"
        if p.exists():
            out["series"][slug] = json.loads(p.read_text())

    (OUT / "post5.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post5.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
