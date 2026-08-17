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
        growth[f] = {"years": YEARS, "stock": [int(x) for x in stock],
                     "first": int(stock[0]), "latest": int(stock[-1]),
                     "mult": round(stock[-1] / stock[0], 2) if stock[0] else None}
        print(f"   {f:<20} {stock[0]:>7,} -> {stock[-1]:>7,}   {growth[f]['mult']}x")

    print("\n4. Checks")
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

    out = {"ladder": LADDER, "breakers": BREAKERS, "min_n": MIN_N,
           "cohort": "2008-2012", "survival": surv, "by_ownership": split,
           "growth": growth,
           "thin_cells": [f"{f}/{o}" for f in ALL_FMT for o in ("chain", "independent")
                          if split[f][o]["thin"] and split[f][o]["n"] > 0]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post3.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post3.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
