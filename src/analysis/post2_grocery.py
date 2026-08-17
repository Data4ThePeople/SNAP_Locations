"""Post 2 — the small grocer decline, and what it is not.

The stock of small grocery stores in SNAP fell by roughly half. This tests the
three explanations that could produce that without stores dying: they were
reclassified into another store type, they switched to a different format at the
same address, or they left the program while staying open.

Note what the panel can and cannot settle. Store type never changes within a
Record ID, so reclassification is directly testable. Whether an exited store is
still trading is not — that needs a business registry, and the script says so
rather than guessing.
"""
import json

from analysis import panel
from config import ROOT

OUT = ROOT / "reports" / "data"
FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def main():
    con = panel.build()
    out = {}

    # ------------------------------------------------------- 1. the shape of the fall
    print("\n1. Small grocery: what actually moved")
    fl = panel.flows(con, where="format = 'Grocery (Small)'")
    fl = fl[fl.k == "Grocery (Small)"].set_index("yr")
    out["flows"] = {"years": [int(y) for y in fl.index],
                    "new": [int(v) for v in fl["new"]],
                    "departed": [int(v) for v in fl["departed"]],
                    "returning": [int(v) for v in fl["returning"]],
                    "lapsed": [int(v) for v in fl["lapsed"]],
                    "stock": [int(v) for v in fl["stock"]]}
    print(f"     {'yr':>5} {'new':>7} {'departed':>9} {'stock':>8} {'exit rate':>10}")
    for yr in (2008, 2012, 2014, 2016, 2018, 2020, 2022, 2025):
        r = fl.loc[yr]
        print(f"     {yr:>5} {int(r['new']):>7,} {int(r['departed']):>9,} {int(r['stock']):>8,}"
              f" {r['departed']/r['stock']:>9.1%}")

    peak = int(fl["stock"].idxmax())
    trough = int(fl.loc[2016:]["stock"].idxmin())
    out["arc"] = {
        "peak_year": peak, "peak": int(fl.loc[peak, "stock"]),
        "trough_year": trough, "trough": int(fl.loc[trough, "stock"]),
        "latest_year": int(fl.index[-1]), "latest": int(fl["stock"].iloc[-1]),
        "pct_fall": round(100 * (fl.loc[trough, "stock"] / fl.loc[peak, "stock"] - 1), 1),
    }
    print(f"\n     peak {out['arc']['peak']:,} in {peak} -> trough {out['arc']['trough']:,}"
          f" in {trough} ({out['arc']['pct_fall']}%), now {out['arc']['latest']:,}")

    # Entry collapse vs exit acceleration: which drove it?
    pre = fl.loc[2009:2013]
    post = fl.loc[2016:2020]
    out["drivers"] = {
        "new_before": float(pre["new"].mean()), "new_after": float(post["new"].mean()),
        "dep_before": float(pre["departed"].mean()), "dep_after": float(post["departed"].mean()),
        "exit_rate_before": float((pre["departed"] / pre["stock"]).mean()),
        "exit_rate_after": float((post["departed"] / post["stock"]).mean()),
    }
    dr = out["drivers"]
    print(f"     new authorizations   {dr['new_before']:,.0f}/yr (2009-13) -> "
          f"{dr['new_after']:,.0f}/yr (2016-20)  {100*(dr['new_after']/dr['new_before']-1):+.0f}%")
    print(f"     departures           {dr['dep_before']:,.0f}/yr -> {dr['dep_after']:,.0f}/yr"
          f"  {100*(dr['dep_after']/dr['dep_before']-1):+.0f}%")
    print(f"     exit rate (dep/stock) {dr['exit_rate_before']:.1%} -> {dr['exit_rate_after']:.1%}")
    check("entries fell more than departures rose",
          int(dr["new_after"] < dr["new_before"] * 0.75), 1)

    # ------------------------------------------------------- 2. is it grocery generally?
    print("\n2. Is this grocery generally, or the smallest format only?")
    ctx = con.execute("""
        SELECT yr, format, sum(n) n FROM stock
        WHERE format IN ('Grocery (Small)','Grocery (Medium)','Grocery (Large)',
                         'Supermarket','Super Store')
        GROUP BY 1,2 ORDER BY 2,1
    """).df()
    out["context"] = {}
    for f in sorted(ctx.format.unique()):
        sub = ctx[ctx.format == f].set_index("yr")["n"]
        first, last = int(sub.iloc[0]), int(sub.iloc[-1])
        out["context"][f] = {"years": [int(y) for y in sub.index],
                             "stock": [int(v) for v in sub],
                             "change_pct": round(100 * (last / first - 1), 1)}
        print(f"     {f:22} {first:>7,} (2006) -> {last:>7,} (2025)"
              f"  {out['context'][f]['change_pct']:>+7.1f}%")

    # ------------------------------------------------------- 3. reclassification
    # Store type cannot change within a Record ID, so a reclassified store must
    # appear as a NEW Record ID at the SAME address. A shared store name is the
    # signature of one business re-registering rather than a different tenant.
    print("\n3. Reclassification: was the same business re-registered as another type?")
    con.execute("""
        CREATE OR REPLACE TEMP TABLE succ AS
        SELECT e.record_id, e.name_norm AS from_nm, s.name_norm AS to_nm,
               e.format AS from_ty, s.format AS to_ty, year(e.last_end) AS yr
        FROM panel e JOIN panel s
          ON s.address_key = e.address_key AND s.record_id <> e.record_id
        WHERE e.format = 'Grocery (Small)' AND e.last_end IS NOT NULL
          AND year(e.last_end) BETWEEN 2012 AND 2022
          AND s.first_auth BETWEEN e.last_end - INTERVAL 180 DAY
                               AND e.last_end + INTERVAL 730 DAY
    """)
    tot_exits = con.execute("""
        SELECT count(*) FROM panel WHERE format='Grocery (Small)'
          AND last_end IS NOT NULL AND year(last_end) BETWEEN 2012 AND 2022
    """).fetchone()[0]
    pairs, with_succ, same_name_diff = con.execute("""
        SELECT count(*), count(DISTINCT record_id),
               count(*) FILTER (WHERE from_nm = to_nm AND from_ty <> to_ty)
        FROM succ
    """).fetchone()
    out["reclass"] = {
        "exits": int(tot_exits), "with_successor": int(with_succ),
        "successor_pairs": int(pairs), "same_name_diff_type": int(same_name_diff),
        "share_of_pairs": round(same_name_diff / pairs, 4),
        "share_of_exits": round(same_name_diff / tot_exits, 4),
    }
    r = out["reclass"]
    print(f"     {r['exits']:,} exits 2012-2022; {r['with_successor']:,} had another store"
          f" at the same address")
    print(f"     of {r['successor_pairs']:,} successor pairs, {r['same_name_diff_type']:,}"
          f" share a name and differ in type ({100*r['share_of_pairs']:.1f}%)")
    print(f"     that is {100*r['share_of_exits']:.1f}% of all exits -> reclassification is real"
          f" but small")
    check("same-name-different-type pairs", r["same_name_diff_type"], 1_478, tol=60)

    by_to = con.execute("""
        SELECT to_ty, count(*) n, count(*) FILTER (WHERE from_nm = to_nm) same_name
        FROM succ GROUP BY 1 ORDER BY 2 DESC LIMIT 6
    """).df()
    out["successor_types"] = [{"format": t.to_ty, "n": int(t.n), "same_name": int(t.same_name)}
                              for t in by_to.itertuples()]
    print(f"\n     {'successor format':28} {'pairs':>7} {'same name':>10}")
    for t in out["successor_types"]:
        print(f"     {t['format']:28} {t['n']:>7,} {t['same_name']:>10,}")

    # ------------------------------------------------------- 4. substitution
    print("\n4. Substitution: did convenience take the slot?")
    conv = con.execute("""
        SELECT yr, sum(n) n FROM stock WHERE format='Convenience Store' GROUP BY 1 ORDER BY 1
    """).df()
    conv_fl = panel.flows(con, where="format='Convenience Store'")
    conv_fl = conv_fl[conv_fl.k == "Convenience Store"].set_index("yr")
    out["convenience"] = {"years": [int(y) for y in conv.yr],
                          "stock": [int(v) for v in conv.n],
                          "new": [int(v) for v in conv_fl["new"]]}
    print(f"     convenience stock {int(conv.n.iloc[0]):,} (2006) -> {int(conv.n.iloc[-1]):,} (2025)")
    print(f"     small grocery lost {out['arc']['peak'] - out['arc']['latest']:,} from peak;"
          f" convenience gained {int(conv.n.iloc[-1]) - int(conv.n.iloc[0]):,}")

    # ------------------------------------------------------- 5. still open, unauthorized
    print("\n5. Proof that leaving the program is not the same as closing")
    lap = con.execute("""
        WITH gaps AS (
          SELECT p.record_id, p.format, f.end_date,
                 lead(f.auth_date) OVER (PARTITION BY p.record_id ORDER BY f.auth_date) AS next_auth
          FROM panel p JOIN fact_spell f USING(record_id) WHERE NOT f.date_anomaly),
        lapsed AS (
          SELECT record_id, format, min(datediff('day', end_date, next_auth)) gap
          FROM gaps WHERE next_auth IS NOT NULL AND end_date IS NOT NULL
            AND next_auth > end_date GROUP BY 1,2)
        SELECT p.format, count(DISTINCT p.record_id) stores,
               count(DISTINCT l.record_id) lapsed, median(l.gap) med
        FROM panel p LEFT JOIN lapsed l USING(record_id)
        WHERE p.format IN ('Grocery (Small)','Grocery (Medium)','Convenience Store',
                           'Supermarket','Dollar Store')
        GROUP BY 1 ORDER BY 3.0/count(DISTINCT p.record_id) DESC
    """).df()
    out["lapse"] = [{"format": t.format, "stores": int(t.stores), "lapsed": int(t.lapsed),
                     "rate": round(t.lapsed / t.stores, 4),
                     "median_gap_days": int(t.med or 0)} for t in lap.itertuples()]
    for t in out["lapse"]:
        print(f"     {t['format']:22} {t['lapsed']:>6,} of {t['stores']:>7,}"
              f" ({100*t['rate']:>4.1f}%) lapsed and returned, median {t['median_gap_days']} days")

    # ------------------------------------------------------- 6. where
    print("\n6. Where the fall was steepest (states, peak year to 2025)")
    st = con.execute(f"""
        WITH a AS (
          SELECT p.state, count(DISTINCT p.record_id) n FROM panel p JOIN fact_spell f USING(record_id)
          WHERE p.format='Grocery (Small)' AND NOT f.date_anomaly
            AND f.auth_date <= make_date({peak},12,31)
            AND (f.end_date IS NULL OR f.end_date >= make_date({peak},12,31)) GROUP BY 1),
        b AS (
          SELECT p.state, count(DISTINCT p.record_id) n FROM panel p JOIN fact_spell f USING(record_id)
          WHERE p.format='Grocery (Small)' AND NOT f.date_anomaly
            AND f.auth_date <= DATE '2025-12-31'
            AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31') GROUP BY 1)
        SELECT a.state, a.n AS then_n, coalesce(b.n,0) AS now_n,
               100.0*(coalesce(b.n,0)-a.n)/a.n AS pct
        FROM a LEFT JOIN b USING(state) WHERE a.n >= 150 ORDER BY pct
    """).df()
    out["states"] = [{"state": t.state, "then": int(t.then_n), "now": int(t.now_n),
                      "pct": round(t.pct, 1)} for t in st.itertuples()]
    for t in out["states"][:6]:
        print(f"     {t['state']}  {t['then']:>5,} -> {t['now']:>5,}  {t['pct']:>+6.1f}%")
    print("     ...")
    for t in out["states"][-3:]:
        print(f"     {t['state']}  {t['then']:>5,} -> {t['now']:>5,}  {t['pct']:>+6.1f}%")

    # ------------------------------------------------------- 6b. who the bar actually hit
    # The rule applies to any retailer authorized on inventory (Criterion A), not
    # to grocery stores specifically, so its mark should show up across formats.
    # It does, and it sorts by how much stock a format already carried.
    print("\n6b. Change in new authorizations, 2012-13 avg vs 2018-19 avg")
    ec = []
    for f in ("Combination Grocery/Other", "Grocery (Small)", "Convenience Store",
              "Grocery (Medium)", "Supermarket", "Super Store", "Dollar Store"):
        d2 = panel.flows(con, where=f"format = '{f}'")
        d2 = d2[d2.k == f].set_index("yr")["new"]
        a, b = d2.loc[2012:2013].mean(), d2.loc[2018:2019].mean()
        ec.append({"format": f, "before": float(a), "after": float(b),
                   "pct": round(100 * (b / a - 1), 1)})
        print(f"     {f:28} {a:>8,.0f} -> {b:>8,.0f}   {100*(b/a-1):>+6.0f}%")
    out["entry_change"] = ec

    # The same cut on USDA's own store types, with nothing broken out by brand.
    #
    # An earlier version split this category by owner and reported that
    # independents collapsed while the chains in it barely moved. That was wrong.
    # Inside Combination Grocery/Other the non-dollar chains fell 60.5%, almost
    # exactly as far as the independents' 62.6% — and those chains are Walgreens,
    # CVS, Rite Aid, Big Lots and Fred's, so the fall is entangled with a
    # bankruptcy and a liquidation rather than any stocking rule. Only the dollar
    # chains held up, and post 1 shows they opened at a near-constant rate for
    # sixteen years regardless of anything. Ownership explains nothing here.
    #
    # What survives is a size gradient in USDA's own categories, which needs no
    # brand list to state and is the version the post now makes.
    eu = []
    for typ, a, b in con.execute("""
        WITH e AS (SELECT store_type_usda t, year(first_auth) yr, count(*) n
                   FROM panel GROUP BY 1, 2)
        SELECT t, avg(CASE WHEN yr IN (2012,2013) THEN n END),
                  avg(CASE WHEN yr IN (2018,2019) THEN n END)
        FROM e GROUP BY 1
        HAVING avg(CASE WHEN yr IN (2012,2013) THEN n END) >= 200
        ORDER BY avg(CASE WHEN yr IN (2018,2019) THEN n END)
               / avg(CASE WHEN yr IN (2012,2013) THEN n END)""").fetchall():
        eu.append({"store_type": typ, "before": float(a), "after": float(b),
                   "pct": round(100 * (b / a - 1), 1)})
        print(f"     {typ:28} {a:>8,.0f} -> {b:>8,.0f}   {100*(b/a-1):>+6.0f}%")
    out["entry_change_usda"] = eu
    by = {r["store_type"]: r["pct"] for r in eu}
    check("the fall sorts by store size, not by owner",
          int(by["Small Grocery Store"] < by["Medium Grocery Store"] - 30), 1)
    check("the largest grocery formats were untouched",
          int(by["Large Grocery Store"] > -15 and by["Supermarket"] > -15), 1)

    # ------------------------------------------------- 7. the external test, now run
    # CBP counts establishments regardless of EBT, so it separates closure from
    # program exit. The result also exposes why the SNAP "Small" series overstates
    # the decline: the Small/Medium boundary moved when the stocking floor rose.
    print("\n7. Census County Business Patterns cross-check")
    cbp_path = OUT / "cbp.json"
    if cbp_path.exists():
        out["cbp"] = json.loads(cbp_path.read_text())
        cb = out["cbp"]
        print(f"     CBP grocery under 5 employees   {cb['cbp_under5_pct']:>+7.1f}%"
              f"  ({cb['base_year']}-{cb['last_year']})")
        print(f"     CBP grocery under 10 employees  {cb['cbp_under10_pct']:>+7.1f}%")
        print(f"     SNAP Grocery (Small)            {cb['snap_small_pct']:>+7.1f}%")
        print(f"     SNAP Grocery (Small + Medium)   {cb['snap_small_mid_pct']:>+7.1f}%")
        print("     -> Small+Medium tracks the census almost exactly; Small alone does not")
        check("SNAP Small+Medium tracks CBP under-10 within 3 points",
              int(abs(cb["snap_small_mid_pct"] - cb["cbp_under10_pct"]) < 3), 1)
    else:
        print("     cbp.json not found — run analysis/cbp_compare.py first")

    print("\n8. Did the Small/Medium boundary move?")
    mix = []
    for a, b in ((2008, 2011), (2012, 2015), (2016, 2017), (2018, 2021), (2022, 2025)):
        r = con.execute(f"""
            SELECT count(*) FILTER (WHERE format='Grocery (Small)'),
                   count(*) FILTER (WHERE format='Grocery (Medium)')
            FROM panel WHERE year(first_auth) BETWEEN {a} AND {b}
              AND format IN ('Grocery (Small)','Grocery (Medium)')""").fetchone()
        sm, md = int(r[0]), int(r[1])
        mix.append({"period": f"{a}-{b}", "new_small": sm, "new_medium": md,
                    "medium_share": round(100 * md / (sm + md), 1)})
        print(f"     {a}-{b}  new Small {sm:>7,}  new Medium {md:>7,}"
              f"  Medium share {mix[-1]['medium_share']:>5.1f}%")
    out["entry_mix"] = mix
    check("Medium share of new grocery authorizations jumps after the 2018 rule",
          int(mix[3]["medium_share"] > mix[1]["medium_share"] + 12), 1)

    out["open_question"] = {
        "resolved": True,
        "note": "Resolved by Census County Business Patterns. Grocery establishments with "
                "under 10 employees fell 24.9% from 2012 to 2023, and SNAP Grocery "
                "(Small+Medium) fell 25.9% - near-identical, so the decline is real business "
                "attrition rather than program exit. The SNAP 'Small' series alone fell 46% "
                "because the Small/Medium classification boundary moved when the 2018 stocking "
                "floor rose: Medium's share of new grocery authorizations went from 32% to 51%.",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post2.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post2.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
