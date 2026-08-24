"""Post 3 — the size ladder, and the thing that substitutes for size.

The first three chapters each followed one small format. This one puts every
format on a single scale, which turns them from three observations into two
rules and a set of exceptions.

Rule one: survival runs with store size. Of the stores authorized in 2008-2012,
69% of super stores are still authorized and 4.6% of small groceries are, with
supermarkets, large and medium groceries falling in order in between. Nothing
about that ladder is subtle.

Rule two, and the reason the ladder exists: it is almost entirely an
INDEPENDENT ladder. Split each format by ownership and independents run
46/38/33/18/4 down the size order, while chains sit flat near the top wherever
we can measure them - 77.8% for a super store chain, 78.2% for a dollar store.
A small chain store survives about as well as a very large one. Chain-ness
substitutes for size.

That is why the two formats that broke the pattern in Days 2 and 3 broke it.
Dollar stores are small and 100% chain. The convenience stores that endure are
the fuel chains. Neither is an exception to the rule; both are the second rule
beating the first.

WHAT THIS DOES NOT SHOW. Being a chain is not sufficient on its own. The chain
small-grocery cell survives at 3.6%, no better than independents - but n=112,
far too few to carry a claim, so it is reported as a limit and nothing is built
on it. The plausible reading is that "chain" here spans a three-store local
operator and Dollar General alike, and only the second kind has the scale that
matters. This source cannot separate them, so the piece does not try.

Ownership is inferred from name patterns and is 'unknown' for 11-25% of each
format's cohort. Rates are computed over the classified stores only, and the
unknown share is published beside every one of them.

And the usual constraint: these are authorizations. A small grocer at 4.6% has
overwhelmingly LEFT THE PROGRAM; we cannot say from here that the building is
empty. The super store figure is the one place the two nearly coincide, because
for the big chains the authorization list is close to a store census.
"""
import json

from analysis import panel
from config import ROOT

OUT = ROOT / "reports" / "data"

# Ordered largest to smallest. This is USDA's own size gradient, and the order
# is the finding, so it is stated once here and never re-sorted downstream.
LADDER = ["Super Store", "Supermarket", "Grocery (Large)", "Grocery (Medium)",
          "Grocery (Small)"]
# The two formats that sit outside the size ladder and break it.
BREAKERS = ["Dollar Store", "Convenience Store"]
ALL_FMT = LADDER + BREAKERS

COHORT = ("f.auth_date BETWEEN DATE '2008-01-01' AND DATE '2012-12-31'")
ALIVE = ("s.auth_date <= DATE '2025-12-31' AND "
         "(s.end_date IS NULL OR s.end_date >= DATE '2025-12-31')")
MIN_N = 200          # below this a cell is reported but never leaned on
YEARS = [2006, 2010, 2015, 2020, 2025]

FAILURES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def main():
    con = panel.build()

    def survival(fmt, own=None):
        where = f"p.format = '{fmt}'" + (f" AND p.ownership = '{own}'" if own else "")
        n, alive = con.execute(f"""
            WITH c AS (
              SELECT DISTINCT p.record_id FROM panel p JOIN fact_spell f USING(record_id)
              WHERE {where} AND NOT f.date_anomaly AND {COHORT})
            SELECT count(*), count(*) FILTER (WHERE EXISTS (
              SELECT 1 FROM fact_spell s WHERE s.record_id = c.record_id
                AND NOT s.date_anomaly AND {ALIVE})) FROM c""").fetchone()
        return {"n": int(n), "alive": int(alive),
                "rate": round(100 * alive / n, 1) if n else None,
                "thin": n < MIN_N}

    print("1. Survival by format — the ladder")
    surv = {}
    for f in ALL_FMT:
        r = survival(f)
        own = dict(con.execute(f"""
            SELECT p.ownership, count(DISTINCT p.record_id) FROM panel p
            JOIN fact_spell f USING(record_id)
            WHERE p.format = '{f}' AND NOT f.date_anomaly AND {COHORT}
            GROUP BY 1""").fetchall())
        tot = sum(own.values())
        r["chain_share"] = round(100 * own.get("chain", 0) / tot, 1)
        r["unknown_share"] = round(100 * own.get("unknown", 0) / tot, 1)
        surv[f] = r
        print(f"   {f:<20} n={r['n']:>7,}  {r['rate']:>5}%  "
              f"chain {r['chain_share']:>5}%  unknown {r['unknown_share']:>5}%")

    print("\n2. The same split by ownership — is it size, or is it chains?")
    split = {}
    for f in ALL_FMT:
        split[f] = {o: survival(f, o) for o in ("chain", "independent")}
        c, i = split[f]["chain"], split[f]["independent"]
        note = "  (thin)" if c["thin"] or i["thin"] else ""
        print(f"   {f:<20} chain {str(c['rate']):>5}% (n={c['n']:>6,})   "
              f"independent {str(i['rate']):>5}% (n={i['n']:>6,}){note}")

    print("\n3. Growth, 2006 to 2025")
    growth = {}
    for f in ALL_FMT:
        stock = [con.execute(f"""
            SELECT count(DISTINCT p.record_id) FROM panel p JOIN fact_spell s
            USING(record_id) WHERE p.format = '{f}' AND NOT s.date_anomaly
              AND s.auth_date <= make_date({y}, 12, 31)
              AND (s.end_date IS NULL OR s.end_date >= make_date({y}, 12, 31))
            """).fetchone()[0] for y in YEARS]
        # Reported as percent change, not as a multiple. "1.00x" reads as up-100%
        # to plenty of readers when it means unchanged; "+0%" cannot be misread.
        # The multiple is kept for ordering comparisons in the checks below.
        growth[f] = {"years": YEARS, "stock": [int(x) for x in stock],
                     "first": int(stock[0]), "latest": int(stock[-1]),
                     "mult": round(stock[-1] / stock[0], 2) if stock[0] else None,
                     "pct": round(100 * (stock[-1] / stock[0] - 1)) if stock[0] else None}
        print(f"   {f:<20} {stock[0]:>7,} -> {stock[-1]:>7,}   {growth[f]['pct']:+}%")

    print("\n4. Growth by ownership — do chains grow faster as well as last longer?")
    growth_own = {}
    for f in ALL_FMT:
        growth_own[f] = {}
        for o in ("chain", "independent"):
            a, b = (con.execute(f"""
                SELECT count(DISTINCT p.record_id) FROM panel p JOIN fact_spell s
                USING(record_id) WHERE p.format = '{f}' AND p.ownership = '{o}'
                  AND NOT s.date_anomaly AND s.auth_date <= make_date({y}, 12, 31)
                  AND (s.end_date IS NULL OR s.end_date >= make_date({y}, 12, 31))
                """).fetchone()[0] for y in (YEARS[0], YEARS[-1]))
            growth_own[f][o] = {
                "first": int(a), "latest": int(b),
                "mult": round(b / a, 2) if a else None,
                "pct": round(100 * (b / a - 1)) if a else None,
                # A multiple off a tiny 2006 base is not a growth rate. The same
                # floor that governs survival cells governs these.
                "thin": a < MIN_N or b < MIN_N}
        c, i = growth_own[f]["chain"], growth_own[f]["independent"]
        cp = f"{c['pct']:+}%" if c["pct"] is not None else "--"
        ip = f"{i['pct']:+}%" if i["pct"] is not None else "--"
        print(f"   {f:<20} chain {cp:>7} (n={c['first']:>6,})   "
              f"independent {ip:>7} (n={i['first']:>6,})")

    print("\n5. Checks")
    # The ladder must actually be a ladder, or the whole piece is wrong.
    rates = [surv[f]["rate"] for f in LADDER]
    check("survival falls monotonically down the size ladder",
          all(a > b for a, b in zip(rates, rates[1:])),
          " > ".join(f"{r}%" for r in rates))
    # The claim is that chains are flat across sizes, not merely higher.
    big, small = split["Super Store"]["chain"], surv["Dollar Store"]
    check("a small chain store survives about as well as a very large one",
          abs(big["rate"] - small["rate"]) < 5,
          f"super store chain {big['rate']}% vs dollar store {small['rate']}%")
    # Independents must show the ladder too, else size is only a chain proxy.
    ind = [split[f]["independent"]["rate"] for f in LADDER]
    check("the ladder survives among independents alone",
          all(a > b for a, b in zip(ind, ind[1:])),
          " > ".join(f"{r}%" for r in ind))
    # Every rate we publish must rest on enough stores.
    thin = [f for f in ALL_FMT if surv[f]["thin"]]
    check("every headline format cell clears the sample floor", not thin,
          f"thin: {thin}" if thin else f"min n={min(surv[f]['n'] for f in ALL_FMT):,}")
    # The closing section rests on chains beating independents on BOTH measures.
    pairs = [f for f in ALL_FMT
             if not growth_own[f]["chain"]["thin"] and not growth_own[f]["independent"]["thin"]
             and not split[f]["chain"]["thin"] and not split[f]["independent"]["thin"]]
    check("chains outgrow independents in every format where both are measurable",
          all(growth_own[f]["chain"]["mult"] > growth_own[f]["independent"]["mult"]
              for f in pairs), ", ".join(pairs))
    check("chains also outlast independents in those same formats",
          all(split[f]["chain"]["rate"] > split[f]["independent"]["rate"] for f in pairs),
          ", ".join(pairs))
    # The dollar store's claim to the corner is the section's punchline.
    best_g = max(growth_own[f][o]["mult"] for f in ALL_FMT for o in ("chain", "independent")
                 if not growth_own[f][o]["thin"])
    best_s = max(split[f][o]["rate"] for f in ALL_FMT for o in ("chain", "independent")
                 if not split[f][o]["thin"])
    d_g, d_s = growth_own["Dollar Store"]["chain"]["mult"], split["Dollar Store"]["chain"]["rate"]
    check("the dollar store leads on growth and on survival at once",
          d_g == best_g and d_s == best_s,
          f"dollar {d_g}x/{d_s}%  best {best_g}x/{best_s}%")

    out = {"ladder": LADDER, "breakers": BREAKERS, "min_n": MIN_N,
           "cohort": "2008-2012", "survival": surv, "by_ownership": split,
           "growth": growth, "growth_by_ownership": growth_own,
           "thin_cells": [f"{f}/{o}" for f in ALL_FMT for o in ("chain", "independent")
                          if split[f][o]["thin"] and split[f][o]["n"] > 0]}
    # ------------------------------------------------- geography: growth by RUCC
    # Where each format's change landed, by USDA ERS Rural-Urban Continuum Code.
    # The finding this section exists to make checkable: big-format growth is
    # entirely a metro phenomenon, and the dollar store is the only format that
    # grows at full speed on every rung of the rural-urban ladder.
    from analysis import rucc as rucc_mod
    print("\n7. Geography: stock by Rural-Urban Continuum Code")
    lookup, rucc_pop = rucc_mod.load()
    RUCC_FMT = ("Super Store", "Supermarket", "Dollar Store",
                "Convenience Store", "Grocery (Small)")
    rows = con.execute(f"""
        SELECT y.yr, p.format, p.state, p.county, count(DISTINCT f.record_id) n
        FROM generate_series(2006, 2025) y(yr)
        JOIN fact_spell f ON f.auth_date <= make_date(y.yr,12,31)
          AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
          AND NOT f.date_anomaly
        JOIN panel p ON p.record_id = f.record_id
        WHERE p.format IN {RUCC_FMT}
        GROUP BY 1,2,3,4""").fetchall()
    from collections import defaultdict
    byrucc = {f: defaultdict(lambda: {str(y): 0 for y in (2006, 2012, 2025)})
              for f in RUCC_FMT}
    yearly = {f: {"metro": defaultdict(int), "nonmetro": defaultdict(int)}
              for f in RUCC_FMT}
    unmatched = defaultdict(int)
    for yr, fmt, st, cty, n in rows:
        code = lookup(st, cty)
        if code is None:
            if yr == 2025:
                unmatched[fmt] += n
            continue
        yearly[fmt]["metro" if code <= 3 else "nonmetro"][yr] += n
        if yr in (2006, 2012, 2025):
            byrucc[fmt][code][str(yr)] += n
    matched25 = sum(v[2025] for f in RUCC_FMT
                    for v in (yearly[f]["metro"], yearly[f]["nonmetro"]))
    un25 = sum(unmatched.values())
    check("at least 99% of 2025-active stores carry a RUCC code",
          un25 / (matched25 + un25) < 0.01,
          f"{un25:,} unmatched of {matched25 + un25:,}")
    out["rucc"] = {
        "population_2020": rucc_pop,
        "pop_metro": sum(v for k, v in rucc_pop.items() if k <= 3),
        "pop_nonmetro": sum(v for k, v in rucc_pop.items() if k >= 4),
        "unmatched_2025": int(un25),
        "formats": {}}
    for f in RUCC_FMT:
        m = yearly[f]["metro"]; nm = yearly[f]["nonmetro"]
        nm_peak = max(nm, key=nm.get)
        out["rucc"]["formats"][f] = {
            "by_code": {str(k): byrucc[f][k] for k in range(1, 10)},
            "metro": {str(y): m[y] for y in range(2006, 2026)},
            "nonmetro": {str(y): nm[y] for y in range(2006, 2026)},
            "nonmetro_peak_year": int(nm_peak),
            "nonmetro_peak": int(nm[nm_peak])}
        print(f"     {f:20} metro {m[2006]:>7,} -> {m[2025]:>7,}   "
              f"nonmetro {nm[2006]:>7,} -> {nm[2025]:>7,}  (peak {nm[nm_peak]:,} in {nm_peak})")
    ru = out["rucc"]["formats"]
    check("dollar stores are the only format whose nonmetro count peaks in 2025",
          [f for f in RUCC_FMT if ru[f]["nonmetro_peak_year"] == 2025] == ["Dollar Store"],
          str({f: ru[f]["nonmetro_peak_year"] for f in RUCC_FMT}))
    check("big-format nonmetro counts fell while metro grew",
          all(ru[f]["nonmetro"]["2025"] < ru[f]["nonmetro"]["2006"]
              and ru[f]["metro"]["2025"] > ru[f]["metro"]["2006"]
              for f in ("Super Store", "Supermarket")), "")
    # The sharpest single-year nonmetro fall is 2020, and it is Kmart's
    # liquidation: count the nonmetro super stores active in 2019, gone by
    # end-2020, that carry the Kmart brand.
    km = con.execute("""
        WITH a AS (SELECT DISTINCT f.record_id FROM fact_spell f
                   WHERE NOT f.date_anomaly AND f.auth_date <= DATE '2019-12-31'
                     AND (f.end_date IS NULL OR f.end_date >= DATE '2019-12-31')),
        b AS (SELECT DISTINCT f.record_id FROM fact_spell f
              WHERE NOT f.date_anomaly AND f.auth_date <= DATE '2020-12-31'
                AND (f.end_date IS NULL OR f.end_date >= DATE '2020-12-31'))
        SELECT p.state, p.county, p.brand FROM a LEFT JOIN b USING(record_id)
        JOIN panel p USING(record_id)
        WHERE b.record_id IS NULL AND p.format='Super Store'""").fetchall()
    gone_nm = sum(1 for st, cty, b in km if (lookup(st, cty) or 0) >= 4)
    gone_km = sum(1 for st, cty, b in km
                  if (lookup(st, cty) or 0) >= 4 and b == "Kmart")
    out["rucc"]["kmart_2020"] = {"nonmetro_exits": gone_nm, "kmart": gone_km}
    print(f"     2020 nonmetro super-store exits: {gone_nm} ({gone_km} Kmart)")
    check("the 2020 nonmetro super-store drop is mostly Kmart",
          gone_km > 0.7 * gone_nm, f"{gone_km}/{gone_nm}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post3.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post3.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
