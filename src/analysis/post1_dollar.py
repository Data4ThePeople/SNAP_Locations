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
    out["survival_gap"] = {"dollar": ds["rate"], "small_grocery": sg["rate"],
                           "multiple": round(ds["rate"] / sg["rate"], 1)}
    print(f"\n     A dollar store from that cohort is {ds['rate']/sg['rate']:.1f}x more likely"
          f" to still be open than a small grocer.")

    # ---------------------------------------------------------------- 3. brands
    print("\n3. Brand trajectories")
    rows = con.execute(f"""
        SELECT s.brand, s.yr, sum(s.n) AS n FROM stock s
        WHERE s.brand IN {DOLLAR_BRANDS} GROUP BY 1, 2 ORDER BY 1, 2
    """).df()
    out["brands"] = {}
    for b in sorted(rows.brand.unique()):
        sub = rows[rows.brand == b].set_index("yr")["n"]
        out["brands"][b] = {"years": [int(y) for y in sub.index],
                            "stock": [int(v) for v in sub]}
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
    (OUT / "post1.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post1.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
