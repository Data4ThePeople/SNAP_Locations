"""Post 3 — what Walmart's footprint covers.

Post 5 argued that thin markets only sustain formats with low fixed costs, which
is why dollar stores are what remains. Walmart is the counter-example: a very
high-fixed-cost format that nonetheless reaches into sparse country. This
measures how much population would lose superstore access without it.

Distances are straight-line great-circle from tract centroid to store. Road
distance typically runs 1.2-1.4x that, so a 20-mile drive standard sits nearer a
15-mile straight line. Results are reported across a ladder of radii rather than
resting on one threshold.
"""
import json

import numpy as np
from scipy.spatial import cKDTree

from analysis import census_tracts, panel
from config import ROOT

OUT = ROOT / "reports" / "data"
R_MI = 3958.7613          # earth radius, miles
RADII = [5, 10, 15, 20, 30]
FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    a = f"{actual:,}" if isinstance(actual, (int, np.integer)) else f"{actual}"
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {a} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def xyz(lat, lon):
    """Unit-sphere cartesian, so a KD-tree can answer great-circle queries."""
    la, lo = np.radians(lat), np.radians(lon)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


def chord(miles):
    """Chord length on the unit sphere for a given great-circle distance."""
    return 2 * np.sin(miles / (2 * R_MI))


def gc_miles(chord_len):
    return 2 * R_MI * np.arcsin(np.clip(chord_len / 2, 0, 1))


def main():
    print("1. Tract population")
    tr = census_tracts.load()
    geo = list(tr)
    tlat = np.array([tr[g]["lat"] for g in geo])
    tlon = np.array([tr[g]["lon"] for g in geo])
    tpop = np.array([tr[g]["pop"] for g in geo], dtype=np.int64)
    # Drop the handful of tracts with no residents; they cannot gain or lose access.
    keep = tpop > 0
    geo = [g for g, k in zip(geo, keep) if k]
    tlat, tlon, tpop = tlat[keep], tlon[keep], tpop[keep]
    T = xyz(tlat, tlon)
    total_pop = int(tpop.sum())
    print(f"   {len(geo):,} populated tracts, {total_pop:,} people")

    con = panel.build()
    out = {"total_pop": total_pop, "radii": RADII}

    print("\n2. Is Walmart's authorization a store census? (required before any claim)")
    rep = 4_606   # Walmart US supercenters + discount stores, company report FY2025
    n_wm = con.execute("""
        SELECT count(DISTINCT f.record_id) FROM fact_spell f JOIN panel p USING(record_id)
        WHERE p.brand='Walmart' AND p.format='Super Store' AND NOT f.date_anomaly
          AND f.end_date IS NULL""").fetchone()[0]
    out["census"] = {"authorized": int(n_wm), "reported": rep,
                     "ratio": round(n_wm / rep, 2)}
    print(f"   Walmart superstores authorized {n_wm:,} vs ~{rep:,} reported "
          f"(ratio {n_wm/rep:.2f})")

    print("\n3. Superstore locations, active 2025")
    def stores(where):
        r = con.execute(f"""
            SELECT p.longitude, p.latitude FROM panel p JOIN fact_spell f USING(record_id)
            WHERE {where} AND NOT f.date_anomaly
              AND f.auth_date <= DATE '2025-12-31'
              AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
            GROUP BY 1,2""").fetchall()
        a = np.array(r, dtype=float)
        return xyz(a[:, 1], a[:, 0]), len(a)

    SS = "p.format = 'Super Store'"
    all_xyz, n_all = stores(SS)
    nw_xyz, n_nw = stores(SS + " AND (p.brand IS NULL OR p.brand <> 'Walmart')")
    wm_xyz, n_wm_pts = stores(SS + " AND p.brand = 'Walmart'")
    print(f"   all superstores {n_all:,}   without Walmart {n_nw:,}   Walmart {n_wm_pts:,}")
    out["stores"] = {"all": n_all, "without_walmart": n_nw, "walmart": n_wm_pts}

    print("\n4. Population within reach of a superstore, with and against without Walmart")
    tree_all, tree_nw = cKDTree(all_xyz), cKDTree(nw_xyz)
    d_all = gc_miles(tree_all.query(T, k=1)[0])
    d_nw = gc_miles(tree_nw.query(T, k=1)[0])
    rows = []
    for r in RADII:
        with_wm = int(tpop[d_all <= r].sum())
        without = int(tpop[d_nw <= r].sum())
        rows.append({"radius": r, "with_walmart": with_wm, "without_walmart": without,
                     "depends_on_walmart": with_wm - without,
                     "with_pct": round(100 * with_wm / total_pop, 1),
                     "without_pct": round(100 * without / total_pop, 1)})
        print(f"   {r:>2} mi   with {with_wm/1e6:>6.1f}M ({100*with_wm/total_pop:>5.1f}%)"
              f"   without {without/1e6:>6.1f}M ({100*without/total_pop:>5.1f}%)"
              f"   difference {(with_wm-without)/1e6:>5.1f}M")
    out["access"] = rows
    # Coverage can only shrink when stores are removed.
    check("coverage never rises when Walmart is removed",
          int(all(x["without_walmart"] <= x["with_walmart"] for x in rows)), 1)

    print("\n5. Where the difference lands: tract density")
    r20 = 20
    only_wm = (d_all <= r20) & (d_nw > r20)
    dens_all = tpop / np.maximum(np.array([tr[g]["aland"] for g in geo]) / 2.59e6, 1e-6)
    print(f"   tracts that only reach a superstore because of Walmart: {int(only_wm.sum()):,}")
    print(f"   population {int(tpop[only_wm].sum()):,}")
    print(f"   median tract density  those tracts {np.median(dens_all[only_wm]):>8,.0f}"
          f"/sq mi   all tracts {np.median(dens_all):>8,.0f}/sq mi")
    out["density_20mi"] = {
        "tracts": int(only_wm.sum()), "pop": int(tpop[only_wm].sum()),
        "median_density": round(float(np.median(dens_all[only_wm])), 1),
        "median_density_all": round(float(np.median(dens_all)), 1)}

    print("\n6. Is the footprint really a grid? Nearest-neighbour spacing between stores")
    for label, pts in (("Walmart", wm_xyz), ("all other superstores", nw_xyz)):
        t = cKDTree(pts)
        dd = gc_miles(t.query(pts, k=2)[0][:, 1])
        out.setdefault("spacing", {})[label] = {
            "n": len(pts), "median": round(float(np.median(dd)), 1),
            "iqr": round(float(np.percentile(dd, 75) - np.percentile(dd, 25)), 1),
            "cv": round(float(np.std(dd) / np.mean(dd)), 2)}
        s = out["spacing"][label]
        print(f"   {label:22} n={len(pts):>6,}  median {s['median']:>5.1f} mi"
              f"  IQR {s['iqr']:>5.1f}  cv {s['cv']:.2f}")
    print("   a lower cv means more regular spacing — closer to a lattice than a cluster")

    print("\n7. Does Walmart reach the thin markets from post 5?")
    # The 976 ZIPs that lost their last chain pharmacy, mapped to their tracts is
    # not direct, so use the ZIP's store coordinates as the anchor instead.
    zl = con.execute("""
        WITH zf AS (
          SELECT y.yr, p.zip_code zip,
                 count(DISTINCT CASE WHEN p.brand IN ('Walgreens','CVS','Rite Aid','Duane Reade',
                   'Kinney Drugs','Discount Drug Mart','Eckerd','Longs Drugs','Osco Drug','Sav-On')
                   THEN p.record_id END) drug
          FROM generate_series(2021,2025) AS y(yr)
          JOIN fact_spell f ON NOT f.date_anomaly
               AND f.auth_date <= make_date(y.yr,12,31)
               AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr,12,31))
          JOIN panel p ON p.record_id=f.record_id
          WHERE p.zip_code IS NOT NULL AND length(p.zip_code)=5 GROUP BY 1,2),
        lost AS (SELECT a.zip FROM (SELECT zip FROM zf WHERE yr=2021 AND drug>0) a
                 LEFT JOIN (SELECT zip, drug FROM zf WHERE yr=2025) b USING(zip)
                 WHERE coalesce(b.drug,0)=0)
        SELECT avg(p.latitude), avg(p.longitude) FROM lost l
        JOIN panel p ON p.zip_code = l.zip
        GROUP BY l.zip HAVING count(*) > 0
    """).fetchall()
    zp = np.array([(a, b) for a, b in zl if a is not None and b is not None], dtype=float)
    Z = xyz(zp[:, 0], zp[:, 1])
    dz_all = gc_miles(cKDTree(all_xyz).query(Z, k=1)[0])
    dz_nw = gc_miles(cKDTree(nw_xyz).query(Z, k=1)[0])
    zrows = []
    for r in RADII:
        zrows.append({"radius": r,
                      "with_walmart": int((dz_all <= r).sum()),
                      "without_walmart": int((dz_nw <= r).sum()),
                      "base": len(Z)})
        print(f"   {r:>2} mi   {int((dz_all<=r).sum()):>4,} of {len(Z):,} pharmacy-loss ZIPs"
              f" reach a superstore; without Walmart {int((dz_nw<=r).sum()):>4,}")
    out["pharmacy_loss_zips"] = zrows

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post3.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post3.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
