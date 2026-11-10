"""Post 8, beats 2 to 5: net change, the waterfall, independent convenience
stores, New York City, and counties left with one store or fewer.

Universe. "Stores in SNAP" on a date is the map's universe: on a historical
date, stores authorized and mappable in the historical file; on November 5,
2026, the live feed's map layer (no Restaurant Meals Program sites, no
farmers-market entities the historical file never carried, mappable). Net
change is the count on November 5 minus the count on December 31 of the year
before, so it nets new authorizations against exits.

Waterfall groups are store types and do not overlap: independent
convenience stores; other convenience stores (chain or owner unknown); grocery
stores of any size (live-only grocery stores carry no size, so sizes are not
split); everything else.

Places: 2026 exits of convenience stores and small groceries (not replaced at
the same address) by the historical file's county field, with New York City's
five boroughs counted as one place.

Exit rates (independents, NYC trend) use the post's exit test: left and not
replaced at the same address (left_2026.exits).

Counties are assigned by coordinates with the 2024 Census cartographic county
boundaries (cb_2024_us_county_500k), not by USDA's county field, which has
errors (a Morrill, NE store listed in Sioux County). Territories are left out.
Each county row also carries the farmers-market entities on the November 5
list that the historical file never carried; they are outside the store count
but a shopper can use them.

Writes reports/data/post8_beats.json and PNGs in reports/post8/images/.

    python -m analysis.post8_beats      (from src/)
"""
import gzip
import json
import urllib.request
import zipfile
from collections import Counter
from datetime import date
from io import BytesIO

import numpy as np
import shapefile
from matplotlib.path import Path

from analysis import figures, usmap
from analysis.left_2026 import active, base, exits
from analysis.post8_left2026 import STATES, pct
from config import ROOT, connect

OUT = ROOT / "reports" / "data" / "post8_beats.json"
IMG = ROOT / "reports" / "post8" / "images"
LIVE_DIR = ROOT / "data" / "raw" / "live"
CTY_ZIP = ROOT / "data" / "raw" / "cb_2024_us_county_500k.zip"
CTY_URL = "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip"
YEARS = list(range(2019, 2027))
CONV, SMALL = "Convenience Store", "Grocery (Small)"
NYC_COUNTIES = {"NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"}
NYC_FIPS = {"36005", "36047", "36061", "36081", "36085"}
TERR_FIPS = {"60", "66", "69", "72", "78"}
GROUPS = ["Independent convenience", "Other convenience", "Grocery, any size", "All other stores"]


def group(r):
    if r["format"] == CONV:
        return GROUPS[0] if r["ownership"] == "independent" else GROUPS[1]
    if (r["format"] or "").startswith("Grocery"):
        return GROUPS[2]
    return GROUPS[3]


def place(state, county):
    """New York City as one place (five boroughs); every other county alone."""
    if state == "NY" and county in NYC_COUNTIES:
        return "New York City"
    return f"{county.title()} County, {state}"


def universe_hist(con, d):
    cur = con.execute(f"""SELECT record_id, format, ownership, state,
                                 upper(trim(coalesce(county, ''))) AS county,
                                 longitude AS lon, latitude AS lat
                          FROM dim_store JOIN {active(d)} USING (record_id) WHERE mappable""")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def universe_live(con, snap):
    with gzip.open(LIVE_DIR / f"snap-live-{snap}.csv.gz", "rt", encoding="utf-8") as fh:
        import csv
        live_cty = {int(r["Record_ID"]): (r["County"] or "").strip().upper() for r in csv.DictReader(fh)}
    cur = con.execute("""SELECT l.record_id, coalesce(d.format, l.format) AS format,
                                coalesce(d.ownership, l.ownership) AS ownership, l.state,
                                upper(trim(coalesce(d.county, ''))) AS county, l.lon, l.lat, l.in_hist
                         FROM live_store l LEFT JOIN dim_store d USING (record_id)
                         WHERE l.excluded IS NULL AND l.mappable""")
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    for r in rows:
        if not r["in_hist"]:
            r["county"] = live_cty.get(r["record_id"], "")
    return rows


def counties():
    """[(geoid, name, state_abbr, [Path, ...], bbox)] from the Census file."""
    if not CTY_ZIP.exists():
        req = urllib.request.Request(CTY_URL, headers={"User-Agent": "Data4ThePeople SNAP research"})
        with urllib.request.urlopen(req, timeout=300) as r:
            CTY_ZIP.write_bytes(r.read())
    z = zipfile.ZipFile(CTY_ZIP)
    get = lambda ext: BytesIO(z.read(next(n for n in z.namelist() if n.endswith(ext))))
    rd = shapefile.Reader(shp=get(".shp"), dbf=get(".dbf"), shx=get(".shx"))
    f = [x[0] for x in rd.fields[1:]]
    out = []
    for rec, shp in zip(rd.records(), rd.shapes()):
        rec = dict(zip(f, rec))
        if rec["STATEFP"] in TERR_FIPS:
            continue
        pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
        rings = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
        out.append((rec["GEOID"], rec["NAMELSAD"], rec["STUSPS"], rings, shp.bbox))
    return out


def assign(cty, lon, lat):
    """County index per point (-1 if none). Even-odd fill over all of a
    county's rings handles holes and islands."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    out = np.full(len(lon), -1)
    for i, (_, _, _, rings, (x0, y0, x1, y1)) in enumerate(cty):
        m = (out < 0) & (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
        if not m.any():
            continue
        idx = np.nonzero(m)[0]
        xy = np.c_[lon[idx], lat[idx]]
        inside = np.zeros(len(idx), bool)
        for ring in rings:
            inside ^= Path(ring).contains_points(xy)
        out[idx[inside]] = i
    return out


def main():
    con = connect(read_only=True)
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    label = f"{snap:%B} {snap.day}"
    out = {"snapshot_date": str(snap)}

    # Beat 2a: net change, Dec 31 to Nov 5, each year.
    net = {}
    for y in YEARS:
        a = universe_hist(con, date(y - 1, 12, 31))
        b = universe_live(con, snap) if y == 2026 else universe_hist(con, date(y, snap.month, snap.day))
        net[y] = {"dec31": len(a), "nov5": len(b), "net": len(b) - len(a),
                  "pct": pct(len(b) - len(a), len(a))}
        if y == 2026:
            A26, B26 = a, b
    out["net"] = net

    # Beat 2b: waterfall of the 2026 net change by group.
    ca, cb = Counter(map(group, A26)), Counter(map(group, B26))
    steps = sorted(({"group": g, "dec31": ca[g], "nov5": cb[g], "net": cb[g] - ca[g]} for g in GROUPS),
                   key=lambda s: s["net"])
    out["waterfall"] = {"start": len(A26), "end": len(B26), "steps": steps}

    # Beat 3 and 4: exit rates by year (not replaced at the same address).
    nyc_ids = {r[0] for r in con.execute(
        "SELECT record_id FROM dim_store WHERE state = 'NY' AND upper(trim(county)) IN ('"
        + "','".join(sorted(NYC_COUNTIES)) + "')").fetchall()}
    sel = {
        "independent_convenience": lambda r: r["format"] == CONV and r["ownership"] == "independent",
        "chain_convenience": lambda r: r["format"] == CONV and r["ownership"] == "chain",
        "nyc_small": lambda r: r["format"] in (CONV, SMALL) and r["record_id"] in nyc_ids,
        "us_small_outside_nyc": lambda r: r["format"] in (CONV, SMALL) and r["record_id"] not in nyc_ids,
    }
    rates = {k: {} for k in sel}
    for y in YEARS:
        A = base(con, date(y - 1, 12, 31))
        G = [g for g in exits(con, date(y - 1, 12, 31), date(y, snap.month, snap.day), live=(y == 2026))
             if not g["replaced"]]
        for k, keep in sel.items():
            n, m = sum(map(keep, A)), sum(map(keep, G))
            rates[k][y] = {"base": n, "left": m, "pct": pct(m, n)}
        if y == 2026:
            G26 = G
    out["rates"] = rates
    # Places with the most 2026 exits of convenience stores and small groceries.
    cmap = {r[0]: (r[1], (r[2] or "").strip().upper()) for r in
            con.execute("SELECT record_id, state, county FROM dim_store").fetchall()}
    F = (CONV, SMALL)
    PB = [r for r in base(con, date(2025, 12, 31)) if r["format"] in F]
    PE = [g for g in G26 if g["format"] in F]
    pb = Counter(place(*cmap[r["record_id"]]) for r in PB)
    pe = Counter(place(*cmap[g["record_id"]]) for g in PE)
    out["places"] = {
        "total_base": len(PB), "total_left": len(PE),
        "top": [{"place": k, "left": n, "base": pb[k], "pct": pct(n, pb[k]),
                 "share_of_us_left": pct(n, len(PE)), "share_of_us_base": pct(pb[k], len(PB))}
                for k, n in sorted(pe.items(), key=lambda kv: (-kv[1], kv[0]))[:10]],
        "nyc_by_type": {f: {"left": sum(1 for g in PE if g["format"] == f and place(*cmap[g["record_id"]]) == "New York City"),
                            "us_left": sum(1 for g in PE if g["format"] == f)} for f in F},
    }
    for v in out["places"]["nyc_by_type"].values():
        v["share_pct"] = pct(v["left"], v["us_left"])
    ground = con.execute("SELECT lon, lat FROM live_store WHERE excluded IS NULL AND mappable").fetchall()
    # Farmers-market entities the historical file never carried are outside the
    # store universe, but a shopper can still use one, so the county list notes them.
    markets = con.execute("""SELECT lon, lat FROM live_store
                             WHERE excluded = 'farmers-market entity not in the historical file'""").fetchall()
    con.close()

    # Beat 5: counties by coordinates.
    cty = counties()
    ia = assign(cty, [r["lon"] for r in A26], [r["lat"] for r in A26])
    ib = assign(cty, [r["lon"] for r in B26], [r["lat"] for r in B26])
    na, nb = Counter(ia[ia >= 0].tolist()), Counter(ib[ib >= 0].tolist())
    im = assign(cty, [m[0] for m in markets], [m[1] for m in markets])
    nm = Counter(im[im >= 0].tolist())
    rows = [{"geoid": g, "name": f"{n}, {STATES.get(s, s)}", "dec31": na[i], "nov5": nb[i],
             "market_entities_nov5": nm[i]}
            for i, (g, n, s, _, _) in enumerate(cty)]
    out["counties_unassigned"] = {"dec31": int((ia < 0).sum()), "nov5": int((ib < 0).sum())}
    out["counties_summary"] = {
        "counties": len(rows),
        "zero_dec31": sum(r["dec31"] == 0 for r in rows), "zero_nov5": sum(r["nov5"] == 0 for r in rows),
        "one_dec31": sum(r["dec31"] == 1 for r in rows), "one_nov5": sum(r["nov5"] == 1 for r in rows),
    }
    out["counties_newly_zero"] = [r for r in rows if r["dec31"] > 0 and r["nov5"] == 0]
    out["counties_down_to_one"] = sorted((r for r in rows if r["dec31"] >= 2 and r["nov5"] == 1),
                                         key=lambda r: (-r["dec31"], r["name"]))
    out["counties_halved"] = sorted((r for r in rows if r["dec31"] >= 2 and 1 < r["nov5"] <= r["dec31"] / 2),
                                    key=lambda r: (r["nov5"] / r["dec31"], -r["dec31"], r["name"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT}")

    # Charts.
    IMG.mkdir(parents=True, exist_ok=True)
    S = figures.S
    figures.colbars_png(
        IMG / "post8-net.png", [str(y) for y in YEARS], [net[y]["net"] for y in YEARS],
        title=f"Net change in SNAP stores, December 31 to {label}",
        subtitle=(f"stores authorized on {label} minus stores authorized on December 31 of the year before;\n"
                  "2026 counts the live list on November 5"),
        highlight="2026",
    )
    wf = out["waterfall"]
    figures.waterfall_png(
        IMG / "post8-waterfall.png", ("Dec 31\n2025", wf["start"]),
        [(s["group"].replace(" ", "\n", 1), s["net"]) for s in wf["steps"]],
        (f"{snap:%b} {snap.day}\n{snap.year}", wf["end"]),
        title=f"Where the net drop in SNAP stores came from, 2026",
        subtitle="stores authorized; net of new authorizations; the axis does not start at zero",
        note="Source: USDA, SNAP retailer historical data and live feed.",
    )
    ind = rates["independent_convenience"]
    ch = rates["chain_convenience"]
    figures.line_png(
        IMG / "post8-independents-trend.png", YEARS,
        [{"name": "Independent", "values": [ind[y]["pct"] for y in YEARS], "slot": 2},
         {"name": "Chain", "values": [ch[y]["pct"] for y in YEARS], "slot": 1}],
        title=f"Convenience stores that left SNAP between January 1 and {label}",
        subtitle="% of each group authorized on December 31 of the year before;\n"
                 "excludes exits replaced at the same address",
        annotate=[{"year": 2026, "text": "live list"}],
    )
    pts = [g for g in G26 if g["format"] == CONV and g["ownership"] == "independent"]
    x0, y0, x1, y1 = usmap.LO48
    in48 = lambda lo, la: x0 <= lo <= x1 and y0 <= la <= y1
    g48 = [p for p in ground if in48(*p)]
    p48 = [(p["longitude"], p["latitude"]) for p in pts if in48(p["longitude"], p["latitude"])]
    xy = lambda rows: usmap.albers([r[0] for r in rows], [r[1] for r in rows])
    figures.map_pair_png(
        IMG / "post8-independents-map.png",
        [{"title": "", "layers": [
            {"xy": xy(g48), "color": figures.MUTED, "size": 0.18, "alpha": 0.35},
            {"xy": xy(p48), "color": S[1], "size": 0.9, "alpha": 0.8}],
          "keys": [{"label": f"{len(pts):,} independent convenience stores that left", "color": S[1]},
                   {"label": "still in SNAP", "color": figures.MUTED}]}],
        width=8.0,
        title=f"Independent convenience stores that left SNAP by {label}, 2026",
        subtitle="authorized December 31, 2025; no new authorization at the same address",
        note=(f"Counts are national; the map shows the lower 48 ({len(p48):,} of {len(pts):,}). "
              "Source: USDA, SNAP retailer historical data and live feed."),
    )
    nyc, us = rates["nyc_small"], rates["us_small_outside_nyc"]
    figures.line_png(
        IMG / "post8-nyc-trend.png", YEARS,
        [{"name": "New York City", "values": [nyc[y]["pct"] for y in YEARS], "slot": 2},
         {"name": "Rest of the US", "values": [us[y]["pct"] for y in YEARS], "slot": 1}],
        title=f"Convenience stores and small groceries that left SNAP, January 1 to {label}",
        subtitle="% authorized on December 31 of the year before;\nexcludes exits replaced at the same address",
        annotate=[{"year": 2026, "text": "live list"}],
    )
    boro = [c for c in cty if c[0] in NYC_FIPS]
    rings = [r for c in boro for r in c[3]]
    nyc_left = [g for g in G26 if g["record_id"] in nyc_ids and g["format"] in (CONV, SMALL)]
    nyc_all_left = [g for g in G26 if g["record_id"] in nyc_ids]
    still = [(r["lon"], r["lat"]) for r in B26 if group(r) == GROUPS[0]]
    out["nyc_map"] = {"left_conv_small": len(nyc_left), "left_all_types": len(nyc_all_left),
                      "still_in_snap": len(still)}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    figures.local_map_png(
        IMG / "post8-nyc-map.png", rings,
        [{"lon": [p[0] for p in still], "lat": [p[1] for p in still], "color": figures.MUTED,
          "size": 2.5, "alpha": 0.6},
         {"lon": [g["longitude"] for g in nyc_left], "lat": [g["latitude"] for g in nyc_left],
          "color": S[1], "size": 7, "alpha": 0.9}],
        [{"label": f"{len(nyc_left):,} convenience stores and small groceries that left", "color": S[1]},
         {"label": f"{len(still):,} stores still in SNAP", "color": figures.MUTED}],
        title=f"New York City: convenience stores and small groceries that left SNAP by {label}, 2026",
        subtitle="authorized December 31, 2025; no new authorization at the same address",
        note="Source: USDA, SNAP retailer historical data and live feed; Census county boundaries.",
    )
    top = out["places"]["top"]
    figures.hbar_png(
        IMG / "post8-places.png",
        [{"label": r["place"].replace(" County", ""), "value": r["left"], "slot": 2 if i == 0 else 0}
         for i, r in enumerate(top)],
        title=f"Places with the most convenience stores and small groceries leaving SNAP, 2026",
        subtitle=(f"stores that left by {label}, no new authorization at the same address;\n"
                  "New York City's five boroughs counted as one place"),
    )
    print(f"wrote charts to {IMG}")
    return out


if __name__ == "__main__":
    main()
