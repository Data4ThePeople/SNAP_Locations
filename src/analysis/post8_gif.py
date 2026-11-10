"""Animated map for post 8 social posts: independent convenience stores that
left SNAP between January 1 and November 5, one frame per year, 2019 to 2026.

Each frame is drawn with the same renderer, wording and layers as chart 04
(post8-independents-map.png), so the last frame is that chart. Orange dots are
the year's exits (not replaced at the same address); gray dots are every store
still in SNAP on November 5 of that year (the live list for 2026, as in the
chart). Every count on a frame is that year's real count; there are no
in-between frames.

About 1.1 seconds per year (8 years, about 9 seconds), then the 2026 frame
holds for 5 seconds.

    python -m analysis.post8_gif      (from src/)
"""
import tempfile
from datetime import date
from pathlib import Path

from PIL import Image

from analysis import figures, usmap
from analysis.left_2026 import active, exits
from analysis.figures import S
from config import ROOT, connect

OUT = ROOT / "posts" / "snap-stores-leaving-2026" / "social"
YEARS = list(range(2019, 2027))
CONV = "Convenience Store"
STEP_MS, HOLD_MS = 1100, 5000
WIDTH_PX = 960


def main():
    con = connect(read_only=True)
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    label = f"{snap:%B} {snap.day}"
    x0, y0, x1, y1 = usmap.LO48
    in48 = lambda lo, la: x0 <= lo <= x1 and y0 <= la <= y1
    xy = lambda rows: usmap.albers([r[0] for r in rows], [r[1] for r in rows])
    frames, counts = [], {}
    tmp = Path(tempfile.mkdtemp())
    for y in YEARS:
        a, b = date(y - 1, 12, 31), date(y, snap.month, snap.day)
        live = y == 2026
        pts = [g for g in exits(con, a, b, live=live)
               if not g["replaced"] and g["format"] == CONV and g["ownership"] == "independent"]
        if live:
            ground = con.execute("SELECT lon, lat FROM live_store WHERE excluded IS NULL AND mappable").fetchall()
        else:
            ground = con.execute(f"""SELECT d.longitude, d.latitude FROM dim_store d
                                     JOIN {active(b)} USING (record_id) WHERE d.mappable""").fetchall()
        g48 = [p for p in ground if in48(*p)]
        p48 = [(p["longitude"], p["latitude"]) for p in pts if in48(p["longitude"], p["latitude"])]
        counts[y] = len(pts)
        png = tmp / f"{y}.png"
        figures.map_pair_png(
            png,
            [{"title": "", "layers": [
                {"xy": xy(g48), "color": figures.MUTED, "size": 0.18, "alpha": 0.35},
                {"xy": xy(p48), "color": S[1], "size": 0.9, "alpha": 0.8}],
              "keys": [{"label": f"{len(pts):,} independent convenience stores that left", "color": S[1]},
                       {"label": "all stores still in SNAP", "color": figures.MUTED}]}],
            width=8.0,
            title=f"Independent convenience stores that left SNAP by {label}, {y}",
            subtitle=f"authorized December 31, {y - 1}; no new authorization at the same address",
            note=(f"Counts are national; the map shows the lower 48 ({len(p48):,} of {len(pts):,}). "
                  "Source: USDA, SNAP retailer historical data" + (" and live feed." if live else ".")),
        )
        im = Image.open(png).convert("RGB")
        frames.append(im)
        print(f"  {y}: {len(pts):,} left")
    con.close()

    # Every frame the size of the 2026 frame (map_pair_png crops tight, so a
    # longer note can change the width by a few pixels).
    W, H = frames[-1].size
    frames = [f if f.size == (W, H) else f.resize((W, H), Image.LANCZOS) for f in frames]
    h = round(H * WIDTH_PX / W)
    frames = [f.resize((WIDTH_PX, h), Image.LANCZOS) for f in frames]
    pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    OUT.mkdir(parents=True, exist_ok=True)
    gif = OUT / "snap-stores-leaving-2026-independents-by-year.gif"
    q[0].save(gif, save_all=True, append_images=q[1:],
              duration=[STEP_MS] * (len(q) - 1) + [HOLD_MS], loop=0, disposal=1)
    frames[-1].save(OUT / "snap-stores-leaving-2026-independents-by-year-final-frame.png")
    print(f"wrote {gif} ({gif.stat().st_size / 1e6:.1f} MB, {WIDTH_PX}x{h})")
    return counts


if __name__ == "__main__":
    main()
