"""US state outlines for the series hero images, with no GIS stack.

The heroes have to regenerate reproducibly alongside everything else, which
rules out the web map: its basemap tiles come from CARTO over the network, so
the same command would not produce the same image twice. This draws the
boundaries ourselves from the Census cartographic file.

geopandas, shapely and cartopy are all absent and would be heavy additions for
one job, so the .shp binary is read directly. The format is simple and stable:
a 100-byte header, then variable-length records, each a polygon carrying a
bounding box, a list of part offsets, and a flat run of (x, y) doubles. Parts
are rings — a state with islands has many.

Lower 48 only. Alaska and Hawaii are conventionally inset on a map this shape,
and an inset would fight the dot field the heroes exist to show, so they are cut
by bounding box instead. Any figure quoted beside one of these images is a
national figure and should say so.

Projection is Albers equal-area conic on the USGS parameters for the contiguous
states (29.5N/45.5N standard parallels, 96W central meridian). Equal-area
matters here: the images compare dot DENSITY between regions, and Mercator would
inflate the northern half of the country against the south.
"""
import math
import struct
import urllib.request
import zipfile
from io import BytesIO

from config import DATA

URL = ("https://www2.census.gov/geo/tiger/GENZ2020/shp/"
       "cb_2020_us_state_20m.zip")
CACHE = DATA / "raw" / "cb_2020_us_state_20m.shp"

# Contiguous-states window. Puerto Rico, the island areas, Alaska and Hawaii all
# fall outside it.
LO48 = (-125.0, 24.0, -66.5, 49.5)

# USGS Albers for the contiguous US.
LAT0, LON0, LAT1, LAT2 = 23.0, -96.0, 29.5, 45.5


def _shp_bytes():
    if CACHE.exists():
        return CACHE.read_bytes()
    print(f"  fetching {URL.rsplit('/', 1)[1]}")
    req = urllib.request.Request(URL, headers={"User-Agent": "Data4ThePeople SNAP research"})
    with urllib.request.urlopen(req, timeout=300) as r:
        blob = r.read()
    with zipfile.ZipFile(BytesIO(blob)) as z:
        name = next(n for n in z.namelist() if n.endswith(".shp"))
        data = z.read(name)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(data)
    print(f"  cached {len(data)/1024:.0f} KB to {CACHE}")
    return data


def rings():
    """Every boundary ring in the lower 48, as [(lon, lat), ...]."""
    b = _shp_bytes()
    if struct.unpack(">i", b[:4])[0] != 9994:
        raise SystemExit("not a shapefile: bad magic number")
    end = struct.unpack(">i", b[24:28])[0] * 2      # file length, 16-bit words
    out, pos = [], 100
    while pos < end:
        _, clen = struct.unpack(">ii", b[pos:pos + 8])
        pos += 8
        rec = b[pos:pos + clen * 2]
        pos += clen * 2
        if struct.unpack("<i", rec[:4])[0] != 5:     # 5 = polygon
            continue
        nparts, npoints = struct.unpack("<ii", rec[36:44])
        parts = struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])
        off = 44 + 4 * nparts
        pts = struct.unpack(f"<{2 * npoints}d", rec[off:off + 16 * npoints])
        for i, start in enumerate(parts):
            stop = parts[i + 1] if i + 1 < nparts else npoints
            ring = [(pts[2 * j], pts[2 * j + 1]) for j in range(start, stop)]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            # Drop rings wholly outside the window rather than clipping them:
            # a clipped ring leaves a straight edge across the map.
            if (max(xs) < LO48[0] or min(xs) > LO48[2]
                    or max(ys) < LO48[1] or min(ys) > LO48[3]):
                continue
            out.append(ring)
    return out


def albers(lon, lat):
    """Longitude/latitude to Albers equal-area x/y. Accepts scalars or lists."""
    single = not hasattr(lon, "__len__")
    lons = [lon] if single else lon
    lats = [lat] if single else lat
    r = math.radians
    n = (math.sin(r(LAT1)) + math.sin(r(LAT2))) / 2
    C = math.cos(r(LAT1)) ** 2 + 2 * n * math.sin(r(LAT1))
    rho0 = math.sqrt(C - 2 * n * math.sin(r(LAT0))) / n
    xs, ys = [], []
    for lo, la in zip(lons, lats):
        theta = n * r(lo - LON0)
        v = C - 2 * n * math.sin(r(la))
        rho = math.sqrt(max(v, 0.0)) / n
        xs.append(rho * math.sin(theta))
        ys.append(rho0 - rho * math.cos(theta))
    return (xs[0], ys[0]) if single else (xs, ys)


if __name__ == "__main__":
    rs = rings()
    print(f"{len(rs):,} rings in the lower 48, "
          f"{sum(len(x) for x in rs):,} points")
