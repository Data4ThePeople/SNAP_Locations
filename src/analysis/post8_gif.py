"""Animated map for post 8 social posts: independent convenience stores in
SNAP, one frame per year, December 31, 2005 to December 31, 2025, then the
live list on November 5, 2026.

Each frame maps every independent convenience store authorized and mappable on
that date (lower 48 shown), with a counter at the side giving the national
count and a line of the counts so far. Every number on a frame is that date's
real count; there are no in-between frames.

Universe: the post's store universe. Historical dates use dim_store
(format 'Convenience Store', ownership 'independent', mappable, an active
spell on the date). November 5, 2026 uses the live list's map layer
(excluded IS NULL, mappable) with the same format and ownership. The
December 31, 2025 to November 5, 2026 change is the waterfall's net change
for independent convenience stores (-5,870).

About 8 seconds for the 22 dates, then the 2026 frame holds for 5 seconds.

    python -m analysis.post8_gif      (from src/)
"""
import io
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image

from analysis import usmap
from analysis.figures import INK, INK_SOFT, MONO, PAPER, RULE
from analysis.left_2026 import active
from config import ROOT, connect

OUT = ROOT / "posts" / "snap-stores-leaving-2026" / "social"
NAME = "snap-stores-leaving-2026-independents-in-snap"
YEARS = list(range(2005, 2026))
BRIGHT = "#ff8a4c"          # a lighter step of the post's orange, so the dots carry on a phone
STEP_MS, HOLD_MS = 360, 5000
W_IN, H_IN, DPI = 9.6, 5.4, 100   # 960x540
WHERE = "d.mappable AND d.format = 'Convenience Store' AND d.ownership = 'independent'"


def frames_data(con):
    out = []
    for y in YEARS:
        rows = con.execute(f"""SELECT d.longitude, d.latitude FROM dim_store d
                               JOIN {active(f'{y}-12-31')} USING (record_id) WHERE {WHERE}""").fetchall()
        out.append((f"Dec 31, {y}", y, rows))
    snap = con.execute("SELECT any_value(snapshot_date) FROM live_store").fetchone()[0]
    rows = con.execute("""SELECT lon, lat FROM live_store WHERE excluded IS NULL AND mappable
                          AND format = 'Convenience Store' AND ownership = 'independent'""").fetchall()
    out.append((f"{snap:%b} {snap.day}, {snap.year}", snap.year + (snap.timetuple().tm_yday - 1) / 365, rows))
    return out


def render(i, data, segs):
    label, _, rows = data[i]
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=PAPER)
    ax = fig.add_axes([0.02, 0.08, 0.64, 0.80])
    ax.set_facecolor(PAPER)
    ax.set_axis_off()
    ax.add_collection(LineCollection(segs, colors=RULE, linewidths=0.5, zorder=1))
    x0, y0, x1, y1 = usmap.LO48
    pts = [r for r in rows if x0 <= r[0] <= x1 and y0 <= r[1] <= y1]
    xs, ys = usmap.albers([p[0] for p in pts], [p[1] for p in pts])
    ax.scatter(xs, ys, s=1.2, c=BRIGHT, marker=".", linewidths=0, alpha=0.85, zorder=2)
    ax.set_xlim(LIM[0], LIM[1]); ax.set_ylim(LIM[2], LIM[3]); ax.set_aspect("equal")

    fig.text(0.03, 0.93, "Independent convenience stores in SNAP, 2005 to 2026",
             family=MONO, fontsize=14, fontweight="bold", color=INK)
    # Counter
    fig.text(0.70, 0.74, label, family=MONO, fontsize=15, color=INK_SOFT)
    fig.text(0.70, 0.60, f"{len(rows):,}", family=MONO, fontsize=34, fontweight="bold", color=BRIGHT)
    fig.text(0.70, 0.555, "stores", family=MONO, fontsize=11, color=INK_SOFT)
    # The counts so far, as a line under the counter.
    lx = fig.add_axes([0.70, 0.16, 0.27, 0.30])
    lx.set_facecolor(PAPER)
    for s in lx.spines.values():
        s.set_visible(False)
    xs_all = [d[1] for d in data]
    ns_all = [len(d[2]) for d in data]
    lx.plot(xs_all[: i + 1], ns_all[: i + 1], color=BRIGHT, lw=2, solid_capstyle="round")
    lx.plot([xs_all[i]], [ns_all[i]], "o", color=BRIGHT, ms=5)
    lx.set_xlim(2005, 2027.2)
    lx.set_ylim(0, 65000)
    lx.axhline(0, color=RULE, lw=1)
    lx.set_yticks([])
    lx.set_xticks([2005, 2015, 2026], ["2005", "2015", "2026"])
    lx.tick_params(axis="x", colors=INK_SOFT, labelsize=9, length=0)
    for t in lx.get_xticklabels():
        t.set_family(MONO)
    fig.text(0.03, 0.03, "Lower 48 shown; counts are national. Dec 31 each year, then USDA's live list on "
             f"{data[-1][0]}. Source: USDA.", family=MONO, fontsize=8, color=INK_SOFT)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=PAPER, dpi=DPI)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


LIM = None


def main():
    global LIM
    con = connect(read_only=True)
    data = frames_data(con)
    con.close()
    segs = []
    for ring in usmap.rings():
        xs, ys = usmap.albers([q[0] for q in ring], [q[1] for q in ring])
        segs.append(list(zip(xs, ys)))
    allx = [p[0] for s in segs for p in s]
    ally = [p[1] for s in segs for p in s]
    px, py = (max(allx) - min(allx)) * 0.04, (max(ally) - min(ally)) * 0.04
    LIM = (min(allx) - px, max(allx) + px, min(ally) - py, max(ally) + py)

    frames = [render(i, data, segs) for i in range(len(data))]
    pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    OUT.mkdir(parents=True, exist_ok=True)
    gif = OUT / f"{NAME}.gif"
    q[0].save(gif, save_all=True, append_images=q[1:],
              duration=[STEP_MS] * (len(q) - 1) + [HOLD_MS], loop=0, disposal=1)
    frames[-1].save(OUT / f"{NAME}-final-frame.png")
    counts = {d[0]: len(d[2]) for d in data}
    (OUT / f"{NAME}-counts.json").write_text(json.dumps(counts, indent=1))
    for k, v in counts.items():
        print(f"  {k}: {v:,}")
    print(f"wrote {gif} ({gif.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
