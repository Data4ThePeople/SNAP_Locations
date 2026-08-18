"""Series hero images: one frame, one palette, only the data changes.

Every post in the series gets the same picture of the country — same projection,
same crop, same ground, same lockup in the same corner — and the only thing that
differs between them is which stores are lit. The set reads as a set because the
frame never moves; each one is distinguishable because the dot field IS that
chapter's subject.

Rendered from the database and the Census boundary file, not from the web map,
so a hero regenerates identically on any machine. The web map's basemap is
fetched from CARTO at draw time and could not offer that.

    python -m analysis.hero            # all defined heroes
    python -m analysis.hero 0 2        # just these days
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from analysis import panel, usmap
from analysis.figures import INK, INK_SOFT, MUTED, PAPER, RULE, S
from config import ROOT

OUT = ROOT / "reports" / "assets" / "heroes"

# Prismic hero. Change here and every hero follows.
W_PX, H_PX = 1680, 1080
DPI = 200
SERIES = "THE STORES THAT STAYED"

ACTIVE = ("s.auth_date <= make_date({y}, 12, 31) AND "
          "(s.end_date IS NULL OR s.end_date >= make_date({y}, 12, 31))")


def points(con, where, year):
    """(lon, lat) for every mappable store matching `where`, active at year end."""
    rows = con.execute(f"""
        SELECT p.longitude, p.latitude FROM panel p JOIN fact_spell s USING(record_id)
        WHERE {where} AND NOT s.date_anomaly AND {ACTIVE.format(y=year)}
          AND p.longitude BETWEEN {usmap.LO48[0]} AND {usmap.LO48[2]}
          AND p.latitude  BETWEEN {usmap.LO48[1]} AND {usmap.LO48[3]}
        GROUP BY 1, 2""").fetchall()
    lons = [r[0] for r in rows]
    lats = [r[1] for r in rows]
    return usmap.albers(lons, lats), len(rows)


def render(path, day, layers, caption):
    """`layers` = [{xy, color, size, alpha}] drawn in order, first at the back."""
    fig = plt.figure(figsize=(W_PX / DPI, H_PX / DPI), dpi=DPI, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(PAPER)
    ax.set_axis_off()

    segs = []
    for ring in usmap.rings():
        xs, ys = usmap.albers([p[0] for p in ring], [p[1] for p in ring])
        segs.append(list(zip(xs, ys)))
    ax.add_collection(LineCollection(segs, colors=RULE, linewidths=0.6, zorder=1))

    for L in layers:
        xs, ys = L["xy"]
        ax.scatter(xs, ys, s=L.get("size", 0.7), c=L["color"], marker=".",
                   linewidths=0, alpha=L.get("alpha", 0.85), zorder=L.get("z", 2))

    ax.autoscale_view()
    ax.set_aspect("equal")
    # Breathing room so no dot sits against the frame edge.
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    # No headroom reserved for the lockup. The frame's corners are ocean at this
    # crop, so the type sits over them and the map keeps the whole frame.
    px, py = (x1 - x0) * 0.012, (y1 - y0) * 0.03
    ax.set_xlim(x0 - px, x1 + px)
    ax.set_ylim(y0 - py, y1 + py)

    # Type sits INSIDE a centre-safe box, never in the corners: Prismic crops the
    # hero responsively and a square crop of a 1680x1080 keeps only x 0.18-0.82.
    #
    # The lines are assembled first and the panel is sized to them, rather than
    # the panel being a fixed rectangle. A fixed one either floated well clear of
    # short content or let a wrapped caption run out of the bottom, and the
    # caption length changes with every chapter.
    #
    # A panel is needed at all because the dense half of the map moves between
    # chapters — type that is legible over the empty west on one hero sits on
    # top of Chicago on the next.
    import textwrap
    PT = 200 / 72 / H_PX          # one point, as a fraction of frame height
    block = [(" ".join(SERIES.split(" ")), 13, INK_SOFT, 2.4),
             (f"DAY {day}" if day else "THE MAP", 24, S[0], 2.0)]
    for L in [q for q in layers if q.get("label")]:
        block.append(("\u25cf  " + L["label"], 14, L["color"], 1.55))
    for i, line in enumerate(textwrap.wrap(caption, 24)):
        block.append((line, 15, INK, 1.9 if i == 0 else 1.35))
    block.append(("lower 48 shown  ·  USDA FNS", 11, INK_SOFT, 2.2))

    LX = 0.135
    height = sum(sz * lead * PT for _, sz, _, lead in block)
    top = 0.500 + height / 2          # vertically centred on the frame
    pad_x, pad_y = 0.030, 0.030
    widest = max(len(s) for s, _, _, _ in block)
    wide_pt = max(sz for s, sz, _, _ in block if len(s) == widest)
    panel_w = widest * 0.6023 * wide_pt * PT * (H_PX / W_PX) + pad_x * 2
    ax.add_patch(plt.Rectangle((LX - pad_x, top - height - pad_y),
                               panel_w, height + pad_y * 2, transform=ax.transAxes,
                               facecolor=PAPER, alpha=0.80, edgecolor="none", zorder=8))

    y = top
    for text, size, color, lead in block:
        y -= size * lead * PT
        ax.text(LX, y, text, transform=ax.transAxes, family="DejaVu Sans Mono",
                fontsize=size, color=color, va="bottom", zorder=9,
                fontweight="bold" if size == 24 else "normal")

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER, dpi=DPI)
    plt.close(fig)

    # Email variant. The Prismic PNG is over 1MB, which is most of an email's
    # weight on its own; 1200px wide covers a 600px column at 2x.
    from PIL import Image
    im = Image.open(path).convert("RGB")
    em = path.with_name(path.stem + "-email.jpg")
    im.resize((1200, round(1200 * im.size[1] / im.size[0])), Image.LANCZOS).save(
        em, quality=82, optimize=True, progressive=True)
    print(f"  {path.name}  {W_PX}x{H_PX}  "
          f"({path.stat().st_size/1024:.0f} KB)   "
          f"{em.name}  ({em.stat().st_size/1024:.0f} KB)")


def main():
    want = {int(a) for a in sys.argv[1:]} or None
    con = panel.build()
    print("heroes:")

    if want is None or 0 in want:
        # One colour, everything on it. The chain/independent split is Day 6's
        # picture and using it here would spend that image early. The count is
        # national; the frame is the lower 48, which the corner note says.
        allpts, _ = points(con, "TRUE", 2025)
        national = con.execute(f"""
            SELECT count(DISTINCT p.record_id) FROM panel p JOIN fact_spell s
            USING(record_id) WHERE NOT s.date_anomaly AND {ACTIVE.format(y=2025)}
            """).fetchone()[0]
        render(OUT / "day-0.png", 0,
               [{"xy": allpts, "color": S[0], "size": 0.6, "alpha": 0.75}],
               f"{national:,} stores in 2025")

    if want is None or 2 in want:
        old, n06 = points(con, "p.format = 'Dollar Store'", 2006)
        new, n25 = points(con, "p.format = 'Dollar Store'", 2025)
        render(OUT / "day-2.png", 2,
               [{"xy": new, "color": S[0], "size": 1.1, "label": f"2025  {n25:,}"},
                {"xy": old, "color": S[3], "size": 1.1, "label": f"2006  {n06:,}", "z": 3}],
               f"Dollar stores, 2006 to 2025")


if __name__ == "__main__":
    main()
