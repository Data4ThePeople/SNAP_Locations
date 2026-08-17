"""Tract population, SNAP receipt and vehicle access, for the distance work.

Three sources, one cache:

  - 2020 Centers of Population (tract level). These are population-WEIGHTED
    centroids, unlike the Gazetteer internal points used by census_tracts.
    The difference is not cosmetic: on the "no supermarket within a mile"
    measure the geographic centroid reports 51.5% of the country and the
    weighted one reports 45.7%. A geographic centroid puts a rural tract's
    whole population on an arbitrary point inside a polygon that may be
    hundreds of square miles; the weighted point puts it where people are.
    Block-group centres agree with weighted tracts to within a point
    (45.6% vs 45.7%), which is what licenses using tracts here.

  - ACS 5-year B22010: households that received SNAP in the past 12 months.
  - ACS 5-year B08201: households with no vehicle available.

Both ACS tables are 5-year estimates on 2020 tract boundaries, so they join
to the 2020 centres directly. They are estimates with sampling error, and are
used here only in aggregate across tens of thousands of tracts, never tract
by tract.

IMPORTANT: the ACS undercounts SNAP receipt. It finds 14.9 million households
against USDA's own administrative count of roughly 22 million — survey
respondents under-report benefits, which is long documented. So these counts
are usable for WHERE SNAP households are, and unusable as a national total.
Report shares (what fraction of SNAP households live far from a store), never
levels, and cite USDA for any headline count of participants.

The SNAP and vehicle counts are separate marginals. This module does NOT
cross them, and neither should callers: multiplying the two would assume the
two are independent, and they are not — SNAP households are markedly less
likely to own a car, so an independence estimate understates the overlap.
"""
import csv
import io
import json
import os
import urllib.request

from config import ROOT

CACHE = ROOT / "data" / "raw" / "tract_access.json"
CENPOP = ("https://www2.census.gov/geo/docs/reference/cenpop2020/tract/"
          "CenPop2020_Mean_TR.txt")
ACS = "https://api.census.gov/data/2022/acs/acs5"

# Census FIPS for the 50 states, DC and Puerto Rico. 03/07/14/43/52 were never
# assigned; the island areas (60/66/69/78) are outside the ACS sample.
STATES = [f"{n:02d}" for n in range(1, 57)
          if n not in (3, 7, 14, 43, 52)] + ["72"]


def _key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith(("CENSUS_API_KEY", "CENSUS_KEY")):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get("CENSUS_API_KEY") or os.environ.get("CENSUS_KEY")


def centers():
    """Population-weighted tract centroids, keyed by 11-digit GEOID."""
    print(f"  fetching {CENPOP.rsplit('/', 1)[1]}")
    with urllib.request.urlopen(CENPOP, timeout=300) as r:
        txt = r.read().decode("utf-8-sig")
    out = {}
    for row in csv.DictReader(io.StringIO(txt)):
        geoid = row["STATEFP"] + row["COUNTYFP"] + row["TRACTCE"]
        pop = int(row["POPULATION"])
        if pop > 0:
            out[geoid] = {"lat": float(row["LATITUDE"]),
                          "lon": float(row["LONGITUDE"]), "pop": pop}
    print(f"  centres of population: {len(out):,} populated tracts")
    return out


def acs(key, variables, label):
    """One ACS table across every state, keyed by tract GEOID."""
    out, missing = {}, []
    for st in STATES:
        url = (f"{ACS}?get={','.join(variables)}&for=tract:*&in=state:{st}"
               f"&key={key}")
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                rows = json.loads(r.read().decode())
        except Exception:
            missing.append(st)
            continue
        head = rows[0]
        gi = [head.index(x) for x in ("state", "county", "tract")]
        vi = [head.index(v) for v in variables]
        for row in rows[1:]:
            geoid = "".join(row[i] for i in gi)
            vals = [row[i] for i in vi]
            # ACS uses negative sentinels (-666666666) for suppressed cells.
            if any(v is None or v == "" or float(v) < 0 for v in vals):
                continue
            out[geoid] = [int(float(v)) for v in vals]
    print(f"  {label}: {len(out):,} tracts"
          + (f" ({len(missing)} states unavailable: {','.join(missing)})" if missing else ""))
    return out


def load():
    if CACHE.exists():
        d = json.loads(CACHE.read_text())
        print(f"  cached: {len(d):,} tracts from {CACHE.name}")
        return d
    key = _key()
    if not key:
        raise SystemExit("CENSUS_API_KEY not found in .env or environment")

    cen = centers()
    snap = acs(key, ["B22010_001E", "B22010_002E"], "SNAP receipt (B22010)")
    veh = acs(key, ["B08201_001E", "B08201_002E"], "vehicle access (B08201)")

    out = {}
    for g, c in cen.items():
        s, v = snap.get(g), veh.get(g)
        out[g] = {**c,
                  "hh": s[0] if s else None,
                  "hh_snap": s[1] if s else None,
                  "hh_nocar": v[1] if v else None}

    pop = sum(v["pop"] for v in out.values())
    n_snap = sum(v["hh_snap"] for v in out.values() if v["hh_snap"] is not None)
    n_car = sum(v["hh_nocar"] for v in out.values() if v["hh_nocar"] is not None)
    cov = sum(1 for v in out.values() if v["hh_snap"] is not None) / len(out)
    print(f"  joined: {len(out):,} tracts, {pop:,} people, "
          f"{n_snap:,} SNAP households, {n_car:,} car-free households")
    print(f"  ACS coverage: {100*cov:.1f}% of populated tracts")

    # 2020 census total was 331,449,281 including PR (3.29M).
    if not 325_000_000 < pop < 340_000_000:
        raise SystemExit(f"ABORT: tract population total {pop:,} is implausible")
    # ACS finds ~14.9M against USDA's ~22M administrative count; the gap is
    # survey under-reporting, not an error here. The guard is wide enough to
    # allow it and narrow enough to catch a broken join.
    if not 12_000_000 < n_snap < 26_000_000:
        raise SystemExit(f"ABORT: SNAP household total {n_snap:,} is implausible")
    if cov < 0.95:
        raise SystemExit(f"ABORT: ACS covers only {100*cov:.1f}% of tracts")

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out))
    print(f"  cached to {CACHE}")
    return out


if __name__ == "__main__":
    load()
