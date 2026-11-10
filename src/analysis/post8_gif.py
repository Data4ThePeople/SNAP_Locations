"""Animated chart 01 for post 8 social posts: SNAP stores that left between
January 1 and November 5, by year, 2019 to 2026.

The bars grow in one at a time, left to right, over about 8 seconds, then the
finished chart holds for 5 seconds. Each bar's label appears only when the bar
is complete, so no frame shows an in-between value. The last frame is drawn by
the same call as chart 01 (post8-exits.png), from the same tied-out numbers in
reports/data/post8_beats.json.

    python -m analysis.post8_gif      (from src/)
"""
import json
import tempfile
from pathlib import Path

from PIL import Image

from analysis import figures
from config import ROOT, connect

OUT = ROOT / "posts" / "snap-stores-leaving-2026" / "social"
NAME = "snap-stores-leaving-2026-exits-by-year"
YEARS = list(range(2019, 2027))
SUB = 6                     # frames per bar
FRAME_MS = 170              # 8 bars x 6 frames x 170 ms = about 8.2 seconds
HOLD_MS = 5000
WIDTH_PX = 1080


def main():
    ex = json.loads((ROOT / "reports" / "data" / "post8_beats.json").read_text())["exits"]
    values = [ex[str(y)]["left"] for y in YEARS]
    con = connect(read_only=True)
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    con.close()
    label = f"{snap:%B} {snap.day}"
    kw = dict(
        title=f"SNAP stores that left between January 1 and {label}",
        subtitle=("stores authorized on December 31 of the year before, gone by {0},\n"
                  "no new authorization at the same address; 2026 uses the live list").format(label),
        highlight="2026", fmt=lambda v: f"{v:,}", axis_fmt=lambda v, _: f"{v:,.0f}",
    )
    steps = [[0.0] * len(YEARS)]
    for i in range(len(YEARS)):
        for k in range(1, SUB + 1):
            g = list(steps[-1])
            g[i] = k / SUB
            steps.append(g)
    tmp = Path(tempfile.mkdtemp())
    frames = []
    for n, g in enumerate(steps):
        png = tmp / f"{n:03d}.png"
        figures.colbars_png(png, [str(y) for y in YEARS], values, grow=g, **kw)
        frames.append(Image.open(png).convert("RGB"))
    W, H = frames[-1].size
    frames = [f if f.size == (W, H) else f.resize((W, H), Image.LANCZOS) for f in frames]
    h = round(H * WIDTH_PX / W)
    frames = [f.resize((WIDTH_PX, h), Image.LANCZOS) for f in frames]
    pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    OUT.mkdir(parents=True, exist_ok=True)
    gif = OUT / f"{NAME}.gif"
    q[0].save(gif, save_all=True, append_images=q[1:],
              duration=[FRAME_MS] * (len(q) - 1) + [HOLD_MS], loop=0, disposal=1)
    frames[-1].save(OUT / f"{NAME}-final-frame.png")
    print(f"wrote {gif} ({gif.stat().st_size / 1e6:.2f} MB, {WIDTH_PX}x{h}, {len(q)} frames)")


if __name__ == "__main__":
    main()
