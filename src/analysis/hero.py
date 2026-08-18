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

# One signature hue per chapter. These are seen side by side on the site, so
# the frame is what makes them a set and the colour is what tells them apart.
# Before this they were all blue-dominant and only looked varied by accident,
# which is how Day 6 and Day 7 ended up reading as the same picture.
#
# The order is chosen, not listed: searching the permutations for the one that
# maximises the smallest gap between consecutive days takes the worst adjacent
# pair from dE 13.0 to 26.5, clear of the 15 normal-vision floor. Every hue
# clears 4.4:1 on the ground.
#
# Day 6 repeats Day 0's blue on purpose — the summary returns to the whole
# picture the opener showed — and they sit six apart with different layer
# structures, so they do not read as a pair.
HUE = {0: S[0],   # blue        every store
       1: S[7],   # coral       small grocery, the loss
       2: S[2],   # green       dollar stores
       3: S[1],   # orange-red  convenience
       4: S[6],   # violet      the size ladder
       5: S[3],   # gold        chain pharmacies
       6: S[0],   # blue        the synthesis
       7: S[4]}   # pink        the new rule

# Grey carries context on every frame: the layer a chapter is NOT about. Keeping
# it hue-free means the signature is never competing with a second colour.

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


def split(con, where, then, now):
    """Three sets: authorized in `then` and still in `now`, lost since, added since.

    Two snapshots drawn over each other cannot show a loss — the later layer
    just covers the earlier one. Diffing the record ids does, and it is the
    honest picture for a chapter about stores going away.
    """
    def ids(y):
        return f"""SELECT DISTINCT p.record_id FROM panel p JOIN fact_spell s
            USING(record_id) WHERE {where} AND NOT s.date_anomaly
              AND {ACTIVE.format(y=y)}"""
    rows = con.execute(f"""
        WITH a AS ({ids(then)}), b AS ({ids(now)})
        SELECT p.longitude, p.latitude,
               CASE WHEN a.record_id IS NOT NULL AND b.record_id IS NOT NULL THEN 'kept'
                    WHEN a.record_id IS NOT NULL THEN 'lost' ELSE 'added' END AS bucket
        FROM panel p
        LEFT JOIN a ON a.record_id = p.record_id
        LEFT JOIN b ON b.record_id = p.record_id
        WHERE (a.record_id IS NOT NULL OR b.record_id IS NOT NULL)
          AND p.longitude BETWEEN {usmap.LO48[0]} AND {usmap.LO48[2]}
          AND p.latitude  BETWEEN {usmap.LO48[1]} AND {usmap.LO48[3]}""").fetchall()
    out = {}
    for k in ("kept", "lost", "added"):
        pts = [(r[0], r[1]) for r in rows if r[2] == k]
        out[k] = (usmap.albers([q[0] for q in pts], [q[1] for q in pts]), len(pts))
    return out


def split(con, where, then, now):
    """Three sets: authorized in `then` and still in `now`, lost since, added since.

    Two snapshots drawn over each other cannot show a loss — the later layer
    just covers the earlier one. Diffing the record ids does, and it is the
    honest picture for a chapter about stores going away.
    """
    def ids(y):
        return f"""SELECT DISTINCT p.record_id FROM panel p JOIN fact_spell s
            USING(record_id) WHERE {where} AND NOT s.date_anomaly
              AND {ACTIVE.format(y=y)}"""
    rows = con.execute(f"""
        WITH a AS ({ids(then)}), b AS ({ids(now)})
        SELECT p.longitude, p.latitude,
               CASE WHEN a.record_id IS NOT NULL AND b.record_id IS NOT NULL THEN 'kept'
                    WHEN a.record_id IS NOT NULL THEN 'lost' ELSE 'added' END AS bucket
        FROM panel p
        LEFT JOIN a ON a.record_id = p.record_id
        LEFT JOIN b ON b.record_id = p.record_id
        WHERE (a.record_id IS NOT NULL OR b.record_id IS NOT NULL)
          AND p.longitude BETWEEN {usmap.LO48[0]} AND {usmap.LO48[2]}
          AND p.latitude  BETWEEN {usmap.LO48[1]} AND {usmap.LO48[3]}""").fetchall()
    out = {}
    for k in ("kept", "lost", "added"):
        pts = [(r[0], r[1]) for r in rows if r[2] == k]
        out[k] = (usmap.albers([q[0] for q in pts], [q[1] for q in pts]), len(pts))
    return out


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
    # A panel is needed because the dense half of the map moves between chapters
    # — type legible over the empty west on one hero lands on Chicago on the
    # next — and it is sized to the text rather than being a fixed rectangle,
    # because the caption length changes with every chapter.
    #
    # The text is DRAWN FIRST and the panel fitted to its measured extents. The
    # panel used to be estimated from the line with the most characters times
    # its own point size, which is not the widest line once sizes are mixed: a
    # short line set large beats a long line set small, and the estimate put the
    # backing narrower than the type it was meant to sit behind.
    import textwrap
    PT = 200 / 72 / H_PX          # one point, as a fraction of frame height
    block = [(" ".join(SERIES.split(" ")), 13, INK_SOFT, 2.4),
             (f"DAY {day}" if day else "THE MAP", 24, HUE.get(day, S[0]), 2.0)]
    for L in [q for q in layers if q.get("label")]:
        block.append(("\u25cf  " + L["label"], 14, L["color"], 1.55))
    for i, line in enumerate(textwrap.wrap(caption, 24)):
        block.append((line, 15, INK, 1.9 if i == 0 else 1.35))
    block.append(("lower 48  ·  SNAP authorizations", 11, INK_SOFT, 2.2))

    LX = 0.135
    height = sum(sz * lead * PT for _, sz, _, lead in block)
    top = 0.500 + height / 2          # vertically centred on the frame

    drawn, y = [], top
    for text, size, color, lead in block:
        y -= size * lead * PT
        drawn.append(ax.text(LX, y, text, transform=ax.transAxes,
                             family="DejaVu Sans Mono", fontsize=size, color=color,
                             va="bottom", zorder=9,
                             fontweight="bold" if size == 24 else "normal"))

    fig.canvas.draw()
    inv = ax.transAxes.inverted()
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for txt in drawn:
        bb = txt.get_window_extent(renderer=fig.canvas.get_renderer())
        (ax0, ay0), (ax1, ay1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        x0, y0 = min(x0, ax0), min(y0, ay0)
        x1, y1 = max(x1, ax1), max(y1, ay1)
    pad_x, pad_y = 0.026, 0.028
    ax.add_patch(plt.Rectangle((x0 - pad_x, y0 - pad_y),
                               (x1 - x0) + pad_x * 2, (y1 - y0) + pad_y * 2,
                               transform=ax.transAxes, facecolor=PAPER, alpha=0.80,
                               edgecolor="none", zorder=8))
    if x1 + pad_x > 0.82:
        print(f"    note: text block reaches x={x1 + pad_x:.2f}, outside the "
              f"0.18-0.82 crop-safe band")

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
               [{"xy": allpts, "color": HUE[0], "size": 0.6, "alpha": 0.75}],
               f"{national:,} stores in 2025")

    if want is None or 2 in want:
        old, n06 = points(con, "p.format = 'Dollar Store'", 2006)
        new, n25 = points(con, "p.format = 'Dollar Store'", 2025)
        render(OUT / "day-2.png", 2,
               [{"xy": new, "color": HUE[2], "size": 1.1, "label": f"2025  {n25:,}"},
                {"xy": old, "color": MUTED, "size": 1.1, "alpha": 0.9,
                 "label": f"2006  {n06:,}", "z": 3}],
               f"Dollar stores, 2006 to 2025")

    if want is None or 1 in want:
        s = split(con, "p.format = 'Grocery (Small)'", 2006, 2025)
        render(OUT / "day-1.png", 1,
               [{"xy": s["added"][0], "color": MUTED, "size": 1.4, "alpha": 0.45,
                 "label": f"authorized since 2006  {s['added'][1]:,}"},
                {"xy": s["kept"][0], "color": MUTED, "size": 1.6, "alpha": 0.95,
                 "label": f"authorized then and now  {s['kept'][1]:,}"},
                {"xy": s["lost"][0], "color": HUE[1], "size": 1.6, "z": 3,
                 "label": f"left SNAP since 2006  {s['lost'][1]:,}"}],
               "Small grocery")

    if want is None or 3 in want:
        chain, nc = points(con, "p.format = 'Convenience Store' AND p.ownership = 'chain'", 2025)
        indie, ni = points(con, "p.format = 'Convenience Store' AND p.ownership = 'independent'", 2025)
        render(OUT / "day-3.png", 3,
               [{"xy": indie, "color": MUTED, "size": 0.9, "alpha": 0.85,
                 "label": f"single owner  {ni:,}"},
                {"xy": chain, "color": HUE[3], "size": 0.9,
                 "label": f"chain  {nc:,}"}],
               "Convenience stores, 2025")

    if want is None or 4 in want:
        big, nb = points(con, "p.format IN ('Super Store','Supermarket')", 2025)
        mid, nm = points(con, "p.format IN ('Grocery (Large)','Grocery (Medium)')", 2025)
        sml, ns = points(con, "p.format = 'Grocery (Small)'", 2025)
        render(OUT / "day-4.png", 4,
               # Largest first so the smallest end up on top. Drawn the other
               # way the biggest dots, which are also the most numerous here,
               # covered both smaller tiers and the ladder vanished.
               # An ordered variable, so one hue stepped by alpha and size
               # rather than three competing colours.
               [{"xy": big, "color": HUE[4], "size": 2.4, "alpha": 0.35,
                 "label": f"supermarket and up  {nb:,}"},
                {"xy": mid, "color": HUE[4], "size": 1.2, "alpha": 0.65,
                 "label": f"medium and large  {nm:,}"},
                {"xy": sml, "color": HUE[4], "size": 0.9, "alpha": 1.0,
                 "label": f"small grocery  {ns:,}"}],
               "Grocery by store size")

    if want is None or 5 in want:
        s = split(con, "p.brand IN ('Walgreens','CVS','Rite Aid','Duane Reade')", 2016, 2025)
        render(OUT / "day-5.png", 5,
               [{"xy": s["kept"][0], "color": MUTED, "size": 1.8, "alpha": 0.9,
                 "label": f"still authorized  {s['kept'][1]:,}"},
                {"xy": s["lost"][0], "color": HUE[5], "size": 1.8, "z": 3,
                 "label": f"left SNAP since 2016  {s['lost'][1]:,}"}],
               "Chain pharmacies")

    if want is None or 6 in want:
        # Not chain against independent: two dense categories over the whole
        # country cannot show a 59/41 split, because whichever draws last buries
        # the other. This shows what happened to the chain estate instead.
        #
        # All THREE buckets are plotted and keyed. An earlier cut dropped the
        # departures and labelled the survivors "chain, authorized in 2006",
        # which read as the 2006 total — 62,213 — when it is the 37,149 of them
        # that were still authorized in 2025. The 25,064 that left were nowhere
        # on the frame. With all three, both totals are recoverable: survivors
        # plus departures is 2006, survivors plus arrivals is 2025.
        s = split(con, "p.ownership = 'chain'", 2006, 2025)
        render(OUT / "day-6.png", 6,
               [{"xy": s["lost"][0], "color": MUTED, "size": 0.6, "alpha": 0.45,
                 "label": f"left SNAP since 2006  {s['lost'][1]:,}"},
                {"xy": s["kept"][0], "color": MUTED, "size": 0.6, "alpha": 0.95,
                 "label": f"authorized in 2006 and now  {s['kept'][1]:,}"},
                {"xy": s["added"][0], "color": HUE[6], "size": 0.6, "alpha": 0.9,
                 "label": f"authorized since 2006  {s['added'][1]:,}"}],
               # "Chains went 39% to 50%" invited the reader to derive a share
               # from two counts it cannot be derived from. Says share now.
               "Chain share of all SNAP stores: 39% to 50%")

    if want is None or 7 in want:
        # Only ONE count is keyed here, deliberately.
        #
        # Day 7's card quotes USDA's "71% of stores, 11% of spending" from the
        # rule's impact analysis. That is USDA's figure, on USDA's categories,
        # over USDA's universe of 269,217 authorized retailers. Ours is 249,083
        # — a different denominator, since theirs includes Alaska, Hawaii and
        # the territories — and no format set here reaches 71% anyway: the four
        # small formats give 63.4%, and adding dollar stores overshoots to
        # 78.4%. The RIA does not publish the category list behind its number.
        #
        # Keying both layers would let a reader derive 63.4% off the image and
        # read it against the 71% on the card, which would look like the series
        # contradicting itself when it is really two different measurements. So
        # the backdrop is drawn as context and left uncounted, and the frame
        # claims only what it can source: where these stores are.
        SMALL = ("p.format IN ('Convenience Store','Grocery (Small)',"
                 "'Grocery (Medium)','Combination Grocery/Other')")
        rest, _ = points(con, f"NOT ({SMALL})", 2025)
        small, ns = points(con, SMALL, 2025)
        # Pink rather than the blue used everywhere else. Day 6 is also
        # blue-dominant and the two frames read as the same picture side by
        # side, which is how these will be seen on the site. Of the two hues
        # not already in the set, pink sits dE 19.3 from the nearest colour in
        # play against violet's 9.8 — violet is close to the very blue this is
        # separating from — and clears the contrast floor on this ground.
        render(OUT / "day-7.png", 7,
               [{"xy": rest, "color": MUTED, "size": 0.5, "alpha": 0.4},
                {"xy": small, "color": HUE[7], "size": 0.6,
                 "label": f"small formats  {ns:,}"}],
               "Stores at most risk from new rule")


if __name__ == "__main__":
    main()
