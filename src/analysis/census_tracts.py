"""Fetch and cache 2020 census tract population with centroid coordinates.

Two sources, joined on GEOID:
  - population from the Census API (2020 Decennial DHC, table P1), per state
  - centroid latitude/longitude and land area from the 2020 national tract
    Gazetteer file, which needs no key

A tract's population is not literally at its centroid, and rural tracts are
large, so any distance result built on this is an approximation. It is the right
resolution for a 10-30 mile question and the wrong one for anything finer.
"""
import io
import json
import os
import urllib.request
import zipfile

from config import DATA, ROOT

CACHE = DATA / "raw" / "tracts.json"
GAZ_URL = ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
           "2020_Gazetteer/2020_Gaz_tracts_national.zip")
# 50 states + DC + PR
FIPS = [f"{i:02d}" for i in range(1, 57)
        if f"{i:02d}" not in {"03", "07", "14", "43", "52"}] + ["72"]


def _key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("CENSUS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("CENSUS_API_KEY", "")


def gazetteer():
    """GEOID -> (lat, lon, land_area_sq_m) from the national tract Gazetteer."""
    print(f"  fetching {GAZ_URL.rsplit('/', 1)[1]}")
    with urllib.request.urlopen(GAZ_URL, timeout=300) as r:
        blob = r.read()
    out = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="latin-1")
            header = [h.strip() for h in next(text).rstrip("\n").split("\t")]
            idx = {h: i for i, h in enumerate(header)}
            geo = idx.get("GEOID")
            lat = idx.get("INTPTLAT")
            lon = idx.get("INTPTLONG") or idx.get("INTPTLONG ")
            aland = idx.get("ALAND")
            for line in text:
                f = line.rstrip("\n").split("\t")
                if len(f) <= max(geo, lat, lon):
                    continue
                try:
                    out[f[geo].strip()] = (float(f[lat]), float(f[lon]),
                                           float(f[aland]) if aland is not None else 0.0)
                except ValueError:
                    continue
    print(f"  gazetteer: {len(out):,} tracts")
    return out


def population(key):
    """GEOID -> 2020 population, looping states because tract needs a parent."""
    pop = {}
    for st in FIPS:
        url = (f"https://api.census.gov/data/2020/dec/dhc?get=P1_001N"
               f"&for=tract:*&in=state:{st}&in=county:*&key={key}")
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:
            print(f"    state {st}: {type(e).__name__} — skipped")
            continue
        for v, state, county, tract in rows[1:]:
            if v in (None, "", "null"):
                continue
            pop[f"{state}{county}{tract}"] = int(v)
    print(f"  population: {len(pop):,} tracts")
    return pop


def load():
    if CACHE.exists():
        d = json.loads(CACHE.read_text())
        print(f"  cached: {len(d):,} tracts from {CACHE.name}")
        return d
    key = _key()
    if not key:
        raise SystemExit("CENSUS_API_KEY not found in .env or environment")
    gaz = gazetteer()
    pop = population(key)
    merged = {g: {"lat": gaz[g][0], "lon": gaz[g][1], "aland": gaz[g][2], "pop": p}
              for g, p in pop.items() if g in gaz}
    total = sum(v["pop"] for v in merged.values())
    print(f"  joined: {len(merged):,} tracts, total population {total:,}")
    # 2020 census total was 331,449,281 including PR (3.29M).
    if not 325_000_000 < total < 340_000_000:
        raise SystemExit(f"ABORT: tract population total {total:,} is implausible")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(merged))
    print(f"  cached to {CACHE}")
    return merged


if __name__ == "__main__":
    d = load()
    print(f"\n  {len(d):,} tracts, {sum(v['pop'] for v in d.values()):,} people")
    g = next(iter(d.items()))
    print(f"  sample: {g[0]} -> {g[1]}")
