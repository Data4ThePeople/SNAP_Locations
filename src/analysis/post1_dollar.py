"""Post 1 — the dollar store metronome.

The growth is well known. What the panel adds is the *mechanism*: a near-constant
rate of new authorizations sustained for sixteen years with almost no closures,
which is unlike anything else in the data. Every figure printed here is written
to reports/data/post1.json for the report to render.
"""
import json

from analysis import panel
from config import ROOT

OUT = ROOT / "reports" / "data"
GROCERY = "('Supermarket','Super Store','Grocery (Large)','Grocery (Medium)','Grocery (Small)')"
DOLLAR_BRANDS = ("Dollar General", "Dollar Tree", "Family Dollar", "99 Cents Only",
                 "Dollar Express", "Dollar Zone")

FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def main():
    con = panel.build()
    out = {}

    # ---------------------------------------------------------------- 1. the metronome
    print("\n1. Dollar Store flows — new authorizations vs closures")
    fl = panel.flows(con, where="format = 'Dollar Store'")
    fl = fl[fl.k == "Dollar Store"].set_index("yr")
    out["dollar_flows"] = {
        "years": [int(y) for y in fl.index],
        "new": [int(v) for v in fl["new"]],
        "departed": [int(v) for v in fl["departed"]],
        "stock": [int(v) for v in fl["stock"]],
    }
    print(f"     {'yr':>5} {'new':>7} {'closed':>7} {'stock':>8}")
    for yr in (2008, 2012, 2016, 2020, 2023, 2024, 2025):
        r = fl.loc[yr]
        print(f"     {yr:>5} {int(r['new']):>7,} {int(r['departed']):>7,} {int(r['stock']):>8,}")

    mid = fl.loc[2009:2023]
    out["metronome"] = {
        "mean_new": float(mid["new"].mean()),
        "sd_new": float(mid["new"].std()),
        "cv": float(mid["new"].std() / mid["new"].mean()),
        "mean_closed": float(mid["departed"].mean()),
    }
    print(f"\n     2009-2023 new authorizations: mean {mid['new'].mean():,.0f}"
          f"  sd {mid['new'].std():,.0f}  cv {out['metronome']['cv']:.2f}")
    print(f"     2009-2023 closures:           mean {mid['departed'].mean():,.0f}/yr")

    # Compare volatility against other formats — is the steadiness distinctive?
    print("\n2. Is that steadiness unusual? (coefficient of variation of new authorizations)")
    cvs = []
    for fmt in ("Dollar Store", "Convenience Store", "Supermarket", "Super Store",
                "Grocery (Small)", "Grocery (Medium)", "Combination Grocery/Other"):
        f2 = panel.flows(con, where=f"format = '{fmt}'")
        f2 = f2[f2.k == fmt].set_index("yr").loc[2009:2023]
        cv = f2["new"].std() / f2["new"].mean()
        churn = f2["departed"].sum() / f2["stock"].mean()
        cvs.append({"format": fmt, "cv": float(cv), "mean_new": float(f2["new"].mean()),
                    "churn": float(churn)})
        print(f"     {fmt:28} cv {cv:>5.2f}   mean new {f2['new'].mean():>7,.0f}"
              f"   closures/avg stock {churn:>5.2f}")
    out["volatility"] = sorted(cvs, key=lambda d: d["cv"])

    # The steady-opening framing does not survive contact with the data:
    # Supermarket entry is far steadier (cv 0.11 vs 0.39). What is distinctive is
    # that dollar stores almost never close, so cohort survival is the real test.
    print("\n2b. Survival: of stores first authorized 2008-2012, share still active in 2025")
    surv = con.execute("""
        SELECT format,
               count(*) AS cohort,
               count(*) FILTER (WHERE last_end IS NULL) AS still_open
        FROM panel
        WHERE year(first_auth) BETWEEN 2008 AND 2012
          AND format IN ('Dollar Store','Supermarket','Super Store','Convenience Store',
                         'Grocery (Small)','Grocery (Medium)','Grocery (Large)',
                         'Combination Grocery/Other')
        GROUP BY 1 HAVING count(*) >= 200 ORDER BY 3.0/count(*) DESC
    """).df()
    out["survival"] = [{"format": r.format, "cohort": int(r.cohort),
                        "still_open": int(r.still_open),
                        "rate": round(r.still_open / r.cohort, 3)}
                       for r in surv.itertuples()]
    for r in out["survival"]:
        print(f"     {r['format']:28} {r['still_open']:>6,} of {r['cohort']:>7,}"
              f"  {100*r['rate']:>5.1f}% still open")
    ds = next(r for r in out["survival"] if r["format"] == "Dollar Store")
    sg = next(r for r in out["survival"] if r["format"] == "Grocery (Small)")
    # From the unrounded counts: dividing the two already-rounded rates
    # (0.782/0.045) inflated this to 17.4x when the exact figure is 17.2x.
    exact = (ds["still_open"] / ds["cohort"]) / (sg["still_open"] / sg["cohort"])
    out["survival_gap"] = {"dollar": ds["rate"], "small_grocery": sg["rate"],
                           "multiple": round(exact, 1)}
    print(f"\n     A dollar store from that cohort is {exact:.1f}x more likely"
          f" to still be open than a small grocer.")

    # ---------------------------------------------------------------- 3. brands
    print("\n3. Brand trajectories")
    rows = con.execute(f"""
        SELECT s.brand, s.yr, sum(s.n) AS n FROM stock s
        WHERE s.brand IN {DOLLAR_BRANDS} GROUP BY 1, 2 ORDER BY 1, 2
    """).df()
    # Align every brand to the full year axis: a brand absent in a year has zero
    # stores, not a missing point, and ragged arrays break any shared x axis.
    all_years = list(range(panel.FIRST_YEAR, panel.LAST_YEAR + 1))
    out["brands"] = {}
    for b in sorted(rows.brand.unique()):
        sub = rows[rows.brand == b].set_index("yr")["n"].reindex(all_years, fill_value=0)
        out["brands"][b] = {"years": all_years, "stock": [int(v) for v in sub]}
    print(f"     {'brand':20}" + "".join(f"{y:>9}" for y in (2008, 2016, 2020, 2024, 2025)))
    for b, d in out["brands"].items():
        idx = dict(zip(d["years"], d["stock"]))
        print(f"     {b:20}" + "".join(f"{idx.get(y, 0):>9,}" for y in (2008, 2016, 2020, 2024, 2025)))

    # ---------------------------------------------------------------- 4. the 2024 break
    print("\n4. The 2024 closure spike — which brand?")
    spike = con.execute(f"""
        SELECT brand, count(*) n FROM panel
        WHERE format = 'Dollar Store' AND last_end IS NOT NULL AND year(last_end) = 2024
        GROUP BY 1 ORDER BY 2 DESC
    """).df()
    out["spike_2024"] = [{"brand": r.brand, "n": int(r.n)} for r in spike.itertuples()]
    for r in spike.itertuples():
        print(f"     {str(r.brand):22} {int(r.n):>6,}")
    fam = int(spike[spike.brand == "Family Dollar"].n.sum())
    check("2024 closures are Family Dollar dominated", fam, 1_000, tol=600)

    # ------------------------------------------------- 4b. what an ended authorization means
    # The dataset records authorizations, not storefronts, so an ending could be a
    # closure or a store dropping EBT. Two things bound that ambiguity, and they
    # point opposite ways for chains and independents.
    print("\n4b. Does an ended authorization mean a closed store?")
    print("     (a) chains: is SNAP authorization effectively a store census?")
    reported = {  # each company's own reported US store count
        "Dollar General": (20_942, "company report, Feb 2026"),
        "Dollar Tree": (9_000, "company release, 'surpassed 9,000'"),
        "Family Dollar": (7_600, "trade press, early 2025"),
    }
    census = []
    for b, (rep, src) in reported.items():
        n = con.execute("SELECT sum(n) FROM stock WHERE yr=2025 AND brand=?", [b]).fetchone()[0]
        census.append({"brand": b, "authorized": int(n or 0), "reported": rep,
                       "ratio": round((n or 0) / rep, 3), "source": src})
        print(f"         {b:16} authorized {int(n or 0):>7,}  reported {rep:>7,}"
              f"  ratio {(n or 0)/rep:.2f}")
    out["chain_census"] = census
    check("Dollar General authorizations match its own store count",
          census[0]["authorized"], census[0]["reported"], tol=400)

    # (b) A store that lapses and returns was demonstrably open while unauthorized.
    print("\n     (b) stores that lapsed and came back — open, but not authorized:")
    lap = con.execute("""
        WITH gaps AS (
          SELECT p.record_id, p.format, f.end_date,
                 lead(f.auth_date) OVER (PARTITION BY p.record_id ORDER BY f.auth_date) AS next_auth
          FROM panel p JOIN fact_spell f USING(record_id) WHERE NOT f.date_anomaly),
        lapsed AS (
          SELECT record_id, format, min(datediff('day', end_date, next_auth)) AS gap
          FROM gaps WHERE next_auth IS NOT NULL AND end_date IS NOT NULL
            AND next_auth > end_date GROUP BY 1, 2)
        SELECT p.format, count(DISTINCT p.record_id) stores,
               count(DISTINCT l.record_id) lapsed, median(l.gap) med_gap
        FROM panel p LEFT JOIN lapsed l USING(record_id)
        WHERE p.format IN ('Dollar Store','Supermarket','Super Store','Convenience Store',
                           'Grocery (Small)','Grocery (Medium)','Grocery (Large)')
        GROUP BY 1 ORDER BY 3.0 / count(DISTINCT p.record_id) DESC
    """).df()
    out["lapse"] = [{"format": r.format, "stores": int(r.stores), "lapsed": int(r.lapsed),
                     "rate": round(r.lapsed / r.stores, 4),
                     "median_gap_days": int(r.med_gap or 0)} for r in lap.itertuples()]
    for r in out["lapse"]:
        print(f"         {r['format']:28} {r['lapsed']:>6,} of {r['stores']:>7,}"
              f"  {100*r['rate']:>5.1f}%  median gap {r['median_gap_days']:>3} days")
    d_lap = next(r for r in out["lapse"] if r["format"] == "Dollar Store")
    g_lap = next(r for r in out["lapse"] if r["format"] == "Grocery (Small)")
    out["lapse_gap"] = {"dollar": d_lap["rate"], "small_grocery": g_lap["rate"],
                        "multiple": round(g_lap["rate"] / d_lap["rate"], 1)}
    print(f"\n         A small grocer is {g_lap['rate']/d_lap['rate']:.1f}x more likely than a"
          f" dollar store to have gone unauthorized and come back.")

    # ---------------------------------------------------------------- 5. dollar-only places
    print("\n5. Places with a dollar store but no grocery of any size")
    zips, counties = [], []
    for yr in range(2008, 2026, 2):
        r = con.execute(f"""
            WITH act AS (
              SELECT DISTINCT p.zip_code, p.state, p.county, p.format
              FROM panel p JOIN fact_spell f USING(record_id)
              WHERE NOT f.date_anomaly
                AND f.auth_date <= make_date({yr},12,31)
                AND (f.end_date IS NULL OR f.end_date >= make_date({yr},12,31))),
            z AS (SELECT zip_code,
                    bool_or(format='Dollar Store') d,
                    bool_or(format IN {GROCERY}) g
                  FROM act WHERE zip_code IS NOT NULL AND length(zip_code)=5 GROUP BY 1),
            c AS (SELECT state, county,
                    bool_or(format='Dollar Store') d,
                    bool_or(format IN {GROCERY}) g
                  FROM act WHERE county IS NOT NULL GROUP BY 1,2)
            SELECT (SELECT count(*) FROM z WHERE d),
                   (SELECT count(*) FROM z WHERE d AND NOT g),
                   (SELECT count(*) FROM c WHERE d),
                   (SELECT count(*) FROM c WHERE d AND NOT g)
        """).fetchone()
        zips.append({"yr": yr, "with_dollar": r[0], "dollar_only": r[1]})
        counties.append({"yr": yr, "with_dollar": r[2], "dollar_only": r[3]})
    out["dollar_only_zip"] = zips
    out["dollar_only_county"] = counties

    # How a ZIP code joins the dollar-only list matters more than that it did:
    # a grocery leaving and a dollar store arriving where no grocery ever was
    # are opposite stories. Split the 2008 -> 2024 walk into its movements, per
    # ZIP, checking "ever had a grocery" on every 31 December in the window so
    # a grocery that came and went mid-window still counts as a loss. Each ZIP
    # is attributed to one state across both years so the walk reconciles.
    walk = con.execute(f"""
        WITH zstate AS (SELECT zip_code, min(state) st FROM panel
                        WHERE zip_code IS NOT NULL AND length(zip_code)=5 GROUP BY 1),
        snap AS (
          SELECT y.yr, p.zip_code, bool_or(p.format='Dollar Store') d,
                 bool_or(p.format IN {GROCERY}) g
          FROM (VALUES (2008),(2024)) y(yr)
          JOIN fact_spell f ON f.auth_date <= make_date(y.yr,12,31)
            AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
            AND NOT f.date_anomaly
          JOIN panel p ON p.record_id = f.record_id
          WHERE p.zip_code IS NOT NULL AND length(p.zip_code)=5
          GROUP BY 1, 2),
        ever AS (
          SELECT p.zip_code, bool_or(p.format IN {GROCERY}) g_ever,
                 bool_or(p.format = 'Convenience Store') c_ever
          FROM panel p JOIN fact_spell f USING(record_id)
          JOIN generate_series(2008, 2024) y(yr)
            ON f.auth_date <= make_date(y.yr,12,31)
           AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
          WHERE NOT f.date_anomaly AND p.zip_code IS NOT NULL
            AND length(p.zip_code)=5
          GROUP BY 1),
        a AS (SELECT zip_code FROM snap WHERE yr=2008 AND d AND NOT g),
        b AS (SELECT zip_code FROM snap WHERE yr=2024 AND d AND NOT g)
        SELECT z.st,
          count(*) FILTER (WHERE a.zip_code IS NOT NULL) AS start08,
          count(*) FILTER (WHERE a.zip_code IS NOT NULL AND b.zip_code IS NULL) AS exited,
          count(*) FILTER (WHERE b.zip_code IS NOT NULL AND a.zip_code IS NULL
                             AND NOT e.g_ever) AS new_never,
          count(*) FILTER (WHERE b.zip_code IS NOT NULL AND a.zip_code IS NULL
                             AND NOT e.g_ever AND e.c_ever) AS new_never_conv,
          count(*) FILTER (WHERE b.zip_code IS NOT NULL AND a.zip_code IS NULL
                             AND e.g_ever) AS new_lost,
          count(*) FILTER (WHERE b.zip_code IS NOT NULL) AS end24
        FROM (SELECT zip_code FROM a UNION SELECT zip_code FROM b) u
        JOIN zstate z USING(zip_code)
        LEFT JOIN a USING(zip_code) LEFT JOIN b USING(zip_code)
        LEFT JOIN ever e USING(zip_code)
        GROUP BY 1""").fetchall()
    nat = [sum(r[i] for r in walk) for i in range(1, 7)]
    out["dollar_only_split"] = {
        "start": nat[0], "exited": nat[1], "new_never": nat[2],
        "new_never_conv": nat[3], "new_lost": nat[4], "end": nat[5],
        "joined": nat[2] + nat[4]}
    sp = out["dollar_only_split"]
    print(f"     walk: {sp['start']:,} in 2008, -{sp['exited']:,} left the list, "
          f"+{sp['new_never']:,} never had a grocery ({sp['new_never_conv']:,} had "
          f"convenience), +{sp['new_lost']:,} had one and lost it -> {sp['end']:,}")
    check("the national walk reconciles",
          int(sp["start"] - sp["exited"] + sp["joined"] == sp["end"]), 1)
    check("national endpoints match the trend line",
          int(sp["start"] == zips[0]["dollar_only"]
              and sp["end"] == zips[-1]["dollar_only"]), 1)
    # Deterministic tie-break (NC and AR both added 129): larger 2024 count,
    # then alphabetical, so the table cannot reshuffle between runs.
    top = sorted(walk, key=lambda r: (-(r[6] - r[1]), -r[6], r[0]))[:10]
    out["dollar_only_states"] = [
        {"state": st, "y2008": s8, "exited": ex, "new_never": nn,
         "new_lost": nl, "y2024": e24}
        for st, s8, ex, nn, _nc, nl, e24 in top]
    # The columns need unpacking. "Left the list" is nearly always a grocery
    # becoming authorized, not the dollar store going. "Never had a grocery"
    # arrivals are all NEW dollar stores by construction (a ZIP with a dollar
    # store and no grocery in 2008 would already be on the list). "Grocery left
    # SNAP" arrivals are mixed: some had the dollar store all along, most
    # gained one too. The post explains this, so the numbers live here.
    sub = con.execute(f"""
        WITH a AS (
          SELECT zip_code, bool_or(format='Dollar Store') d, bool_or(format IN {GROCERY}) g
          FROM (SELECT DISTINCT p.zip_code, p.format FROM panel p JOIN fact_spell f USING(record_id)
                WHERE NOT f.date_anomaly AND f.auth_date <= DATE '2008-12-31'
                  AND (f.end_date IS NULL OR f.end_date >= DATE '2008-12-31'))
          WHERE zip_code IS NOT NULL AND length(zip_code)=5 GROUP BY 1),
        b AS (
          SELECT zip_code, bool_or(format='Dollar Store') d, bool_or(format IN {GROCERY}) g
          FROM (SELECT DISTINCT p.zip_code, p.format FROM panel p JOIN fact_spell f USING(record_id)
                WHERE NOT f.date_anomaly AND f.auth_date <= DATE '2024-12-31'
                  AND (f.end_date IS NULL OR f.end_date >= DATE '2024-12-31'))
          WHERE zip_code IS NOT NULL AND length(zip_code)=5 GROUP BY 1),
        e AS (
          SELECT p.zip_code, bool_or(p.format IN {GROCERY}) g_ever
          FROM panel p JOIN fact_spell f USING(record_id)
          JOIN generate_series(2008,2024) y(yr) ON f.auth_date <= make_date(y.yr,12,31)
           AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
          WHERE NOT f.date_anomaly AND p.zip_code IS NOT NULL AND length(p.zip_code)=5
          GROUP BY 1)
        SELECT
          count(*) FILTER (WHERE a.d AND NOT a.g AND NOT coalesce(b.d AND NOT b.g, false)
                             AND coalesce(b.g, false)) AS exit_grocery_came,
          count(*) FILTER (WHERE a.d AND NOT a.g AND NOT coalesce(b.d AND NOT b.g, false)
                             AND NOT coalesce(b.g, false)) AS exit_dollar_gone,
          count(*) FILTER (WHERE b.d AND NOT b.g AND NOT coalesce(a.d AND NOT a.g, false)
                             AND e.g_ever AND coalesce(a.d, false)) AS lost_had_dollar,
          count(*) FILTER (WHERE b.d AND NOT b.g AND NOT coalesce(a.d AND NOT a.g, false)
                             AND e.g_ever AND NOT coalesce(a.d, false)) AS lost_new_dollar
        FROM a FULL JOIN b USING(zip_code) LEFT JOIN e USING(zip_code)""").fetchone()
    out["dollar_only_split"].update({
        "exit_grocery_came": int(sub[0]), "exit_dollar_gone": int(sub[1]),
        "lost_had_dollar": int(sub[2]), "lost_new_dollar": int(sub[3])})
    print(f"     exits: {sub[0]:,} grocery became authorized, {sub[1]:,} dollar store gone")
    print(f"     grocery-left arrivals: {sub[2]:,} already had a dollar store, "
          f"{sub[3]:,} gained one after 2008")
    check("exit reasons sum to the exits", int(sub[0] + sub[1] == sp["exited"]), 1)
    check("grocery-left arrival kinds sum", int(sub[2] + sub[3] == sp["new_lost"]), 1)

    # The post says these two things in prose, so they are checked here.
    lossy = [r["state"] for r in out["dollar_only_states"]
             if r["new_lost"] > r["new_never"]]
    check("Illinois is the only top-10 state where losses outnumber arrivals",
          int(lossy == ["IL"]), 1)
    check("Texas is on the top-10 list", int(any(
        r["state"] == "TX" for r in out["dollar_only_states"])), 1)
    print(f"     {'state':>6} {'2008':>6} {'left':>6} {'never':>7} {'lost':>6} {'2024':>6}")
    for r in out["dollar_only_states"]:
        print(f"     {r['state']:>6} {r['y2008']:>6,} {-r['exited']:>6,} "
              f"{r['new_never']:>+7,} {r['new_lost']:>+6,} {r['y2024']:>6,}")
        check(f"{r['state']} walk reconciles",
              int(r["y2008"] - r["exited"] + r["new_never"] + r["new_lost"]
                  == r["y2024"]), 1)
    print(f"     {'yr':>5} {'ZIPs w/ dollar':>15} {'no grocery':>11} {'share':>7}"
          f"   {'counties':>9} {'no grocery':>11}")
    for z, c in zip(zips, counties):
        print(f"     {z['yr']:>5} {z['with_dollar']:>15,} {z['dollar_only']:>11,}"
              f" {100*z['dollar_only']/max(z['with_dollar'],1):>6.1f}%"
              f"   {c['with_dollar']:>9,} {c['dollar_only']:>11,}")

    # ---------------------------------------------------------------- 6. scale context
    print("\n6. Dollar stores against the grocery formats they sit beside")
    ctx = con.execute("""
        SELECT yr, format, sum(n) n FROM stock
        WHERE format IN ('Dollar Store','Supermarket','Super Store',
                         'Grocery (Small)','Grocery (Medium)','Grocery (Large)')
        GROUP BY 1,2 ORDER BY 2,1
    """).df()
    out["context"] = {}
    for f in sorted(ctx.format.unique()):
        sub = ctx[ctx.format == f].set_index("yr")["n"]
        out["context"][f] = {"years": [int(y) for y in sub.index],
                             "stock": [int(v) for v in sub]}
    d25 = out["context"]["Dollar Store"]["stock"][-1]
    allg = sum(out["context"][f]["stock"][-1] for f in out["context"] if f != "Dollar Store")
    out["headline"] = {"dollar_2025": d25, "all_grocery_2025": allg,
                       "ratio": round(d25 / allg, 3)}
    print(f"     2025: {d25:,} dollar stores vs {allg:,} grocery of every size "
          f"({100*d25/allg:.0f}%)")

    OUT.mkdir(parents=True, exist_ok=True)
    # Who owns these formats. The post's answer to "why did dollar stores keep
    # their authorizations" rests on this, so it is measured rather than asserted:
    # a chain absorbs a fixed compliance cost, a single owner pays it alone.
    print("\n9. Ownership mix, the basis for the scale argument")
    mix = {}
    for fmt in ("Dollar Store", "Grocery (Small)", "Convenience Store"):
        rows = dict(con.execute(
            "SELECT ownership, count(*) FROM dim_store WHERE mappable AND format = ? "
            "GROUP BY 1", [fmt]).fetchall())
        tot = sum(rows.values())
        mix[fmt] = {"total": int(tot),
                    **{k: round(100 * v / tot, 1) for k, v in rows.items()}}
        # Chain share of the stores active at the end of 2025, not of every
        # store the file has ever seen. Chains gained share over the twenty
        # years, so the all-time figure (20% for convenience) understates
        # today's (35%) — and the post quotes it next to a 2025 store count.
        act = dict(con.execute(f"""
            SELECT p.ownership, count(DISTINCT f.record_id)
            FROM fact_spell f JOIN panel p USING(record_id)
            WHERE p.format = ? AND NOT f.date_anomaly
              AND f.auth_date <= DATE '2025-12-31'
              AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
            GROUP BY 1""", [fmt]).fetchall())
        mix[fmt]["chain_2025"] = round(100 * act.get("chain", 0) / sum(act.values()), 1)
        parts = "  ".join(f"{k} {100*v/tot:.0f}%"
                          for k, v in sorted(rows.items(), key=lambda r: -r[1]))
        print(f"     {fmt:<20} {tot:>8,}   {parts}")
    out["ownership_mix"] = mix
    check("every dollar store belongs to a chain",
          int(mix["Dollar Store"].get("chain", 0) == 100.0), 1)
    check("small grocers are overwhelmingly independent",
          int(mix["Grocery (Small)"].get("independent", 0) > 75), 1)
    check("convenience is majority independent, unlike dollar stores",
          int(mix["Convenience Store"].get("independent", 0) > 50), 1)

    (OUT / "post1.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post1.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
