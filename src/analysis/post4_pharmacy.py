"""Post 4 — the pharmacy collapse.

Drug stores sit in USDA's Combination Grocery/Other bucket alongside dollar
stores, and they moved in the opposite direction. The interesting part is the
timing: the decline has nothing to do with the 2016 stocking rule that shaped
the small-grocery story. It starts five years later and is driven by corporate
restructuring that was reported at the time — which makes it the most
externally checkable finding in the series.
"""
import json

from analysis import panel
from config import ROOT

OUT = ROOT / "reports" / "data"
DRUG_BRANDS = ["Walgreens", "CVS", "Rite Aid", "Duane Reade", "Kinney Drugs",
               "Discount Drug Mart", "Eckerd", "Longs Drugs", "Osco Drug", "Sav-On"]
FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def main():
    con = panel.build()
    out = {}
    years = list(range(2006, 2026))
    inlist = ",".join(f"'{b}'" for b in DRUG_BRANDS)

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE seg AS
        SELECT record_id, zip_code, state,
               CASE WHEN brand IN ({inlist}) THEN 'chain'
                    WHEN brand IS NULL
                     AND regexp_matches(name_norm, '(PHARMACY|DRUG|APOTHECARY|\\bRX\\b)')
                    THEN 'independent'
                    ELSE NULL END AS seg
        FROM panel
    """)

    def stock(where):
        return [con.execute(f"""
            SELECT count(DISTINCT f.record_id) FROM fact_spell f JOIN seg g USING(record_id)
            WHERE {where} AND NOT f.date_anomaly
              AND f.auth_date <= make_date({y},12,31)
              AND (f.end_date IS NULL OR f.end_date >= make_date({y},12,31))
        """).fetchone()[0] for y in years]

    # ------------------------------------------------------------ 1. the two eras
    print("\n1. Drug chains: a plateau, then a collapse")
    chain = stock("g.seg = 'chain'")
    peak = max(chain)
    peak_yr = years[chain.index(peak)]
    i21 = years.index(2021)
    out["chain"] = {"years": years, "stock": chain, "peak": peak, "peak_year": peak_yr,
                    "latest": chain[-1],
                    "peak_to_2021_pct": round(100 * (chain[i21] / peak - 1), 1),
                    "2021_to_latest_pct": round(100 * (chain[-1] / chain[i21] - 1), 1),
                    "total_pct": round(100 * (chain[-1] / peak - 1), 1)}
    c = out["chain"]
    print(f"     peak {peak:,} in {peak_yr}; 2025 {chain[-1]:,} ({c['total_pct']}%)")
    print(f"     peak -> 2021: {c['peak_to_2021_pct']:+.1f}% over 5 years  (the stocking rule bit in 2018)")
    print(f"     2021 -> 2025: {c['2021_to_latest_pct']:+.1f}% over 4 years")
    check("drug chain peak", peak, 20_341, tol=30)
    check("2025 drug chain stock", chain[-1], 14_828, tol=30)

    # ------------------------------------------------------------ 2. by brand
    print("\n2. By brand")
    out["brands"] = {}
    for b in DRUG_BRANDS:
        s = [int(con.execute("SELECT coalesce(sum(n),0) FROM stock WHERE yr=? AND brand=?",
                             [y, b]).fetchone()[0]) for y in years]
        if max(s) < 50:
            continue
        pk = max(s)
        out["brands"][b] = {"years": years, "stock": s, "peak": pk,
                            "peak_year": years[s.index(pk)], "latest": s[-1],
                            "pct": round(100 * (s[-1] / pk - 1), 1)}
        print(f"     {b:20} peak {pk:>6,} ({years[s.index(pk)]})  2025 {s[-1]:>6,}"
              f"  {out['brands'][b]['pct']:>+7.1f}%")
    check("Rite Aid all but gone by 2025", out["brands"]["Rite Aid"]["latest"], 2, tol=5)

    # ------------------------------------------------------------ 3. when they left
    print("\n3. Authorizations ending per year, drug chains")
    ends = {}
    for y in range(2019, 2026):
        rows = con.execute(f"""
            SELECT p.brand, count(*) n FROM panel p JOIN seg g USING(record_id)
            WHERE g.seg='chain' AND p.last_end IS NOT NULL AND year(p.last_end)={y}
            GROUP BY 1 ORDER BY 2 DESC
        """).fetchall()
        ends[y] = {b: int(n) for b, n in rows}
        tot = sum(ends[y].values())
        top = ", ".join(f"{b} {n:,}" for b, n in list(ends[y].items())[:3])
        print(f"     {y}  {tot:>6,}   {top}")
    out["endings"] = {str(k): v for k, v in ends.items()}

    # ------------------------------------------------------------ 4. independents
    # This dataset cannot measure independent pharmacies. A pharmacy only appears
    # if it is SNAP-authorized, which requires stocking staple foods, and most do
    # not — so the visible set is ~1.6% of the national population and half of it
    # is in New York. Reported as a coverage limit, not a trend.
    print("\n4. Independent pharmacies: what this data can and cannot see")
    indep = stock("g.seg = 'independent'")
    ny = [con.execute(f"""
        SELECT count(DISTINCT p.record_id) FROM panel p JOIN seg g USING(record_id)
        JOIN fact_spell f ON f.record_id=p.record_id AND NOT f.date_anomaly
        WHERE g.seg='independent' AND p.state='NY'
          AND f.auth_date <= make_date({y},12,31)
          AND (f.end_date IS NULL OR f.end_date >= make_date({y},12,31))
    """).fetchone()[0] for y in years]
    NATIONAL_INDEP = 19_500   # trade estimate of US independent community pharmacies
    out["independent"] = {
        "years": years, "stock": indep, "ny": ny,
        "latest": indep[-1], "latest_ny": ny[-1],
        "ny_share_latest": round(ny[-1] / indep[-1], 3),
        "ny_share_first": round(ny[0] / indep[0], 3),
        "national_estimate": NATIONAL_INDEP,
        "coverage": round(indep[-1] / NATIONAL_INDEP, 4),
        "ex_ny_first": indep[0] - ny[0], "ex_ny_latest": indep[-1] - ny[-1],
        "usable": False,
    }
    o = out["independent"]
    print(f"     visible in SNAP records: {o['latest']:,} of ~{NATIONAL_INDEP:,} nationally"
          f" ({100*o['coverage']:.1f}%)")
    print(f"     New York share: {100*o['ny_share_first']:.0f}% (2006) -> "
          f"{100*o['ny_share_latest']:.0f}% (2025)")
    print(f"     New York: {ny[0]:,} -> {ny[-1]:,}   everywhere else: "
          f"{o['ex_ny_first']:,} -> {o['ex_ny_latest']:,}")
    print("     New York rises while the rest falls, so any national trend line here")
    print("     averages two opposite movements. Not reported as a finding.")

    # ------------------------------------------------------------ 5. pharmacy deserts
    print("\n5. ZIP codes that lost their last SNAP-authorized chain drug store")
    def zips(y):
        return {r[0] for r in con.execute(f"""
            SELECT DISTINCT p.zip_code FROM panel p JOIN seg g USING(record_id)
            JOIN fact_spell f ON f.record_id = p.record_id AND NOT f.date_anomaly
            WHERE g.seg = 'chain' AND p.zip_code IS NOT NULL
              AND length(p.zip_code) = 5
              AND f.auth_date <= make_date({y},12,31)
              AND (f.end_date IS NULL OR f.end_date >= make_date({y},12,31))
        """).fetchall()}
    z21, z25 = zips(2021), zips(2025)
    lost = z21 - z25
    out["zips"] = {"y2021": len(z21), "y2025": len(z25), "lost": len(lost),
                   "gained": len(z25 - z21)}
    print(f"     ZIPs with a drug store: {len(z21):,} (2021) -> {len(z25):,} (2025)")
    print(f"     went to zero: {len(lost):,}   newly gained one: {len(z25-z21):,}")

    # ------------------------------------------------------------ 6. is authorization a census?
    print("\n6. Is authorization a store census for these chains?")
    # Only Walgreens is comparable. Rite Aid's count was falling so fast that its
    # 2024 authorizations (1,523) exceed the ~1,240 reported at its May 2025
    # filing — a date mismatch, not more stores than exist. CVS is excluded
    # because ~1,700 of its pharmacies sit inside Target stores.
    reported = {"Walgreens": (8_000, "company, Oct 2024, 'over 8,000' US stores")}
    out["census"] = []
    for b, (rep, src) in reported.items():
        n = out["brands"][b]["stock"][years.index(2024)]
        out["census"].append({"brand": b, "authorized_2024": n, "reported": rep,
                              "ratio": round(n / rep, 2), "source": src})
        print(f"     {b:12} 2024 authorized {n:>6,}  reported ~{rep:,}  ratio {n/rep:.2f}")
    print("     CVS excluded (~1,700 pharmacies inside Target stores carry Target's own")
    print("     authorization); Rite Aid excluded (count moving too fast to compare a point).")

    # ------------------------------------------------------------ 7. states
    print("\n7. States losing the most drug stores, 2021 to 2025")
    st = con.execute(f"""
        WITH a AS (SELECT p.state, count(DISTINCT p.record_id) n
                   FROM panel p JOIN seg g USING(record_id) JOIN fact_spell f
                     ON f.record_id=p.record_id AND NOT f.date_anomaly
                   WHERE g.seg = 'chain'
                     AND f.auth_date <= DATE '2021-12-31'
                     AND (f.end_date IS NULL OR f.end_date >= DATE '2021-12-31')
                   GROUP BY 1),
        b AS (SELECT p.state, count(DISTINCT p.record_id) n
              FROM panel p JOIN seg g USING(record_id) JOIN fact_spell f
                ON f.record_id=p.record_id AND NOT f.date_anomaly
              WHERE g.seg = 'chain'
                AND f.auth_date <= DATE '2025-12-31'
                AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
              GROUP BY 1)
        SELECT a.state, a.n AS then_n, coalesce(b.n,0) AS now_n,
               coalesce(b.n,0)-a.n AS delta,
               100.0*(coalesce(b.n,0)-a.n)/a.n AS pct
        FROM a LEFT JOIN b USING(state) WHERE a.n >= 150 ORDER BY pct
    """).df()
    out["states"] = [{"state": r.state, "then": int(r.then_n), "now": int(r.now_n),
                      "delta": int(r.delta), "pct": round(r.pct, 1)} for r in st.itertuples()]
    for r in out["states"][:6]:
        print(f"     {r['state']}  {r['then']:>5,} -> {r['now']:>5,}  {r['delta']:>+6,}"
              f"  {r['pct']:>+6.1f}%")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post4.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post4.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
