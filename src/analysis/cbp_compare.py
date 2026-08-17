"""The decisive test for post 2: did small grocers close, or leave the program?

SNAP records cannot separate the two — an ended authorization looks the same
either way. Census County Business Patterns counts *establishments* regardless of
whether they accept EBT, so comparing the two series answers it:

  if establishments held steady while authorizations halved -> they left SNAP
  if both fell together                                     -> they closed

CBP county files download from the Census FTP without an API key. Establishment
counts are not suppressed (only employment and payroll are), so the size-class
columns are usable.

NAICS 445110 is "Supermarkets and Other Grocery (except Convenience) Stores",
renamed but substantively unchanged in the 2022 NAICS revision. Convenience
stores are excluded from it in both vintages, which is what makes the comparison
clean.
"""
import io
import json
import urllib.request
import zipfile

from analysis import panel
from config import DATA, ROOT

OUT = ROOT / "reports" / "data"
CACHE = DATA / "raw" / "cbp_grocery.json"
YEARS = [2012, 2014, 2016, 2018, 2019, 2021, 2022, 2023]
FAILURES = []


def check(name, actual, expected, tol=0):
    ok = abs(actual - expected) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,})")
    if not ok:
        FAILURES.append(name)


def fetch_year(year):
    """National establishment counts for NAICS 445110 by employment size class."""
    yy = f"{year % 100:02d}"
    url = f"https://www2.census.gov/programs-surveys/cbp/datasets/{year}/cbp{yy}co.zip"
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            blob = r.read()
    except Exception as e:
        print(f"    {year}: {type(e).__name__} — skipped")
        return None
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="latin-1")
            header = [h.strip().strip('"') for h in next(text).split(",")]
            idx = {h: i for i, h in enumerate(header)}
            # The under-5 column is n1_4 in older vintages and n<5 in newer ones.
            c_small = idx.get("n1_4", idx.get("n<5"))
            c_naics, c_est, c_59 = idx["naics"], idx["est"], idx["n5_9"]
            tot = small = mid = 0
            for line in text:
                f = line.rstrip("\n").split(",")
                if len(f) <= max(c_naics, c_est, c_59, c_small):
                    continue
                if f[c_naics].strip().strip('"') != "445110":
                    continue
                try:
                    tot += int(f[c_est] or 0)
                    small += int(f[c_small] or 0)
                    mid += int(f[c_59] or 0)
                except ValueError:
                    continue
    return {"establishments": tot, "under_5_emp": small, "emp_5_9": mid,
            "under_10_emp": small + mid}


def cbp():
    if CACHE.exists():
        return {int(k): v for k, v in json.loads(CACHE.read_text()).items()}
    print("  downloading CBP county files (no API key needed)")
    out = {}
    for y in YEARS:
        r = fetch_year(y)
        if r:
            out[y] = r
            print(f"    {y}: {r['establishments']:,} establishments, "
                  f"{r['under_10_emp']:,} with under 10 employees")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out))
    return out


def main():
    print("1. Census County Business Patterns, NAICS 445110")
    c = cbp()
    if not c:
        raise SystemExit("no CBP data retrieved")
    yrs = sorted(c)
    # Sanity: CBP counts roughly 60-70k grocery establishments nationally.
    check("2012 establishments in a plausible range",
          int(50_000 < c[2012]["establishments"] < 90_000), 1)

    print("\n2. SNAP authorizations for comparison")
    con = panel.build()
    snap = {}
    for y in yrs:
        row = con.execute(f"""
            SELECT
              sum(CASE WHEN format='Grocery (Small)' THEN n ELSE 0 END),
              sum(CASE WHEN format IN ('Grocery (Small)','Grocery (Medium)') THEN n ELSE 0 END),
              sum(CASE WHEN format IN ('Grocery (Small)','Grocery (Medium)',
                    'Grocery (Large)','Supermarket','Super Store') THEN n ELSE 0 END)
            FROM stock WHERE yr = {y}""").fetchone()
        snap[y] = {"small": int(row[0] or 0), "small_mid": int(row[1] or 0),
                   "all_grocery": int(row[2] or 0)}

    print(f"\n{'yr':>6} | {'CBP 445110':>11} {'<5 emp':>8} {'<10 emp':>8} |"
          f" {'SNAP small':>10} {'SNAP s+m':>9} {'SNAP all':>9}")
    print("  " + "-" * 76)
    for y in yrs:
        print(f"{y:>6} | {c[y]['establishments']:>11,} {c[y]['under_5_emp']:>8,}"
              f" {c[y]['under_10_emp']:>8,} | {snap[y]['small']:>10,}"
              f" {snap[y]['small_mid']:>9,} {snap[y]['all_grocery']:>9,}")

    base, last = yrs[0], yrs[-1]
    def pct(a, b):
        return 100 * (b / a - 1) if a else 0.0
    res = {
        "years": yrs,
        "cbp": {y: c[y] for y in yrs},
        "snap": {y: snap[y] for y in yrs},
        "base_year": base, "last_year": last,
        "cbp_total_pct": round(pct(c[base]["establishments"], c[last]["establishments"]), 1),
        "cbp_under5_pct": round(pct(c[base]["under_5_emp"], c[last]["under_5_emp"]), 1),
        "cbp_under10_pct": round(pct(c[base]["under_10_emp"], c[last]["under_10_emp"]), 1),
        "snap_small_pct": round(pct(snap[base]["small"], snap[last]["small"]), 1),
        "snap_small_mid_pct": round(pct(snap[base]["small_mid"], snap[last]["small_mid"]), 1),
        "snap_all_pct": round(pct(snap[base]["all_grocery"], snap[last]["all_grocery"]), 1),
    }

    print(f"\n3. Change from {base} to {last}")
    print(f"   CBP grocery establishments, all sizes  {res['cbp_total_pct']:>+7.1f}%")
    print(f"   CBP grocery, under 5 employees         {res['cbp_under5_pct']:>+7.1f}%")
    print(f"   CBP grocery, under 10 employees        {res['cbp_under10_pct']:>+7.1f}%")
    print(f"   SNAP Grocery (Small)                   {res['snap_small_pct']:>+7.1f}%")
    print(f"   SNAP Grocery (Small + Medium)          {res['snap_small_mid_pct']:>+7.1f}%")
    print(f"   SNAP all grocery formats               {res['snap_all_pct']:>+7.1f}%")

    gap = res["snap_small_pct"] - res["cbp_under5_pct"]
    res["gap_pp"] = round(gap, 1)
    print(f"\n4. Verdict")
    print(f"   The SNAP small-grocery series fell {abs(gap):.0f} percentage points more than the")
    print(f"   census count of the smallest grocery establishments over the same period.")
    if res["cbp_under5_pct"] > -10 and res["snap_small_pct"] < -30:
        res["verdict"] = "left_program"
        print("   -> Establishments held up while authorizations collapsed: the dominant")
        print("      mechanism is stores LEAVING SNAP, not stores closing.")
    elif res["cbp_under5_pct"] < -25:
        res["verdict"] = "closed"
        print("   -> Both series fell substantially: real attrition of small grocery")
        print("      businesses, not merely program exit.")
    else:
        res["verdict"] = "mixed"
        print("   -> Both moved; the decline is part real attrition, part program exit.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cbp.json").write_text(json.dumps(res, indent=1))
    print(f"\nwrote {OUT / 'cbp.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))


if __name__ == "__main__":
    main()
