"""PNG renderers for charts and tables, for pasting into Mailchimp or Prismic.

The HTML report uses inline SVG with CSS tokens so it can follow the reader's
theme. Email and CMS layouts cannot, so these render the same figures to PNG at
2x on one fixed ground. Both read the same JSON, so the numbers cannot diverge —
only the styling.

That ground is dark (#181a1b), matching the surface these get pasted onto. The
series colours therefore come from palette.DARK rather than palette.LIGHT: the
light slots are tuned for a white surface and several of them fall below the
3:1 contrast minimum against this one. Every dark slot clears it, and the
adjacent-pair CVD separation is validated in palette.validate(n, "dark").

Everything is drawn in monospace, matching the report's treatment of figures as
record-keeping rather than display type.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from analysis import palette

PAPER = "#181a1b"      # the ground these are pasted onto
INK = "#bbbdc0"        # 9.28:1 — headline values, emphasised cells
INK_MID = "#a7a9ab"    # 7.41:1 — axis ticks, ordinary cells
INK_SOFT = "#828486"   # 4.65:1 — captions, notes, column heads
RULE = "#33383a"       # gridlines and hairlines: visible, still recessive
MUTED = "#727a82"      # 4.01:1 — slot-0 context bars, which carry no identity
DPI = 200
MONO = ["DejaVu Sans Mono"]

S = palette.DARK  # slot 1..8 -> S[0..7]


def _style(ax):
    ax.set_facecolor(PAPER)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(RULE)
        ax.spines[side].set_linewidth(1)
    ax.tick_params(colors=INK_SOFT, labelsize=8, length=3, width=1)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontfamily(MONO)


def _thousands(v, _=None):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 10_000:
        return f"{v/1000:,.0f}k"
    # Below 10k a whole-thousand label repeats itself: 1,500 and 2,400 both
    # render as "2k" and the axis reads as though it has duplicate gridlines.
    if v >= 1_000:
        return f"{v/1000:.1f}k"
    return f"{v:,.0f}"



MONO_ADVANCE = 0.6023   # DejaVu Sans Mono advance width, in em


def _titles(fig, ax, title, subtitle, gutter_pt=0):
    """Put a plain-language title above the plot, with units beneath it.

    The reader meets the figure before the caption, so the figure has to say what
    it is on its own. Title carries the claim in words; subtitle carries the units
    and stays recessive so it cannot compete with it.

    `gutter_pt` is for the bar charts, whose row labels are drawn OUTSIDE the axes
    to its left. Anchoring a title to the axes puts it at the bar origin, where it
    reads as indented against those labels; anchoring it to the figure does not
    work either, because the labels overhang the figure edge and the tight bounding
    box then shifts everything right by the overhang. So the title is offset left
    from the axes corner by the width of the widest label. DejaVu Sans Mono has a
    fixed advance of 0.6023 em, which makes that width exact rather than guessed.
    """
    if gutter_pt:
        dy = 8
        if subtitle:
            ax.annotate(subtitle, (0, 1), xycoords="axes fraction",
                        textcoords="offset points", xytext=(-gutter_pt, dy),
                        ha="left", va="bottom", fontsize=8, family=MONO,
                        color=INK_SOFT, annotation_clip=False)
            dy += 15
        if title:
            ax.annotate(title, (0, 1), xycoords="axes fraction",
                        textcoords="offset points", xytext=(-gutter_pt, dy),
                        ha="left", va="bottom", fontsize=10.5, family=MONO,
                        color=INK, fontweight="bold", annotation_clip=False)
        return
    if title:
        ax.set_title(title, loc="left", fontsize=10.5, family=MONO, color=INK,
                     fontweight="bold", pad=20 if subtitle else 10)
    if subtitle:
        # Axes coordinates, just above the plot, so it sits between the title and
        # the top gridline regardless of figure height.
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, ha="left", va="bottom",
                fontsize=8, family=MONO, color=INK_SOFT)


def line_png(path, years, series, ylabel="", width=6.6, height=3.3, annotate=None,
             label_ends=True, title="", subtitle=""):
    """`series` = [{name, values, slot}]. Direct end labels satisfy the relief
    rule for the lighter slots, which sit under 3:1 on a light ground.

    `subtitle` is an alias for `ylabel` so that every renderer here takes the same
    title/subtitle pair, and a caller can switch chart type without rewriting the
    keyword. ylabel wins if both are given.
    """
    ylabel = ylabel or subtitle
    fig, ax = plt.subplots(figsize=(width, height), dpi=DPI, facecolor=PAPER)
    _style(ax)
    ax.grid(axis="y", color=RULE, lw=1, zorder=0)
    ax.set_axisbelow(True)
    for s in series:
        c = S[s["slot"] - 1]
        ax.plot(years, s["values"], color=c, lw=2, solid_capstyle="round", zorder=3)
        if label_ends:
            ax.plot([years[-1]], [s["values"][-1]], "o", color=c, ms=5,
                    mec=PAPER, mew=1.5, zorder=4)

    if label_ends:
        # Series that finish close together would print their labels on top of
        # each other, so nudge them apart while leaving the markers on the data.
        hi_all = max(max(s["values"]) for s in series)
        gap = hi_all * 0.055
        ends = sorted(((s["values"][-1], s) for s in series), key=lambda t: t[0])
        placed = []
        for val, s in ends:
            y = val if not placed else max(val, placed[-1] + gap)
            placed.append(y)
            c = S[s["slot"] - 1]
            # A swatch beside the label carries identity. Label text stays in ink
            # per convention, so without this a nudged label cannot be matched to
            # its line — which is exactly what happened where two series both
            # finished near zero.
            ax.annotate("\u25cf", (years[-1], y), textcoords="offset points",
                        xytext=(9, 0), va="center", ha="left", fontsize=5.5,
                        color=c, zorder=5, annotation_clip=False)
            ax.annotate(f"  {s['name']}", (years[-1], y), textcoords="offset points",
                        xytext=(14, 0), va="center", ha="left", fontsize=8,
                        family=MONO, color=INK_MID, zorder=5, annotation_clip=False)
    for a in (annotate or []):
        ax.axvline(a["year"], color=INK_SOFT, lw=1, ls=(0, (3, 3)), zorder=1)
        ax.annotate(a["text"], (a["year"], ax.get_ylim()[1]),
                    textcoords="offset points", xytext=(4, -11),
                    fontsize=7.5, family=MONO, color=INK_SOFT)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylim(bottom=0)
    ax.set_xlim(min(years), max(years) + (max(years) - min(years)) * 0.30)
    # First and last always shown; regular ticks only where they will not
    # collide with them.
    mids = [y for y in years if y % 4 == 0 and years[0] + 3 <= y <= years[-1] - 3]
    ax.set_xticks([years[0]] + mids + [years[-1]])
    _titles(fig, ax, title, ylabel)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


def hbar_png(path, rows, suffix="", width=6.6, note_key=None, title="",
             subtitle="", direction="right"):
    """`rows` = [{label, value, slot?, note?}], drawn top-to-bottom as given.

    direction="left" anchors the bars to a right-hand baseline and grows them
    leftward, with labels on the right. Pass the values signed (negative for a
    decline): a series of drops then reads as drops, "-64%" and pointing down
    the scale, instead of as positive magnitudes.
    """
    h = 0.42 * len(rows) + 0.55 + (0.42 if title else 0)
    fig, ax = plt.subplots(figsize=(width, h), dpi=DPI, facecolor=PAPER)
    ax.set_facecolor(PAPER)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)
    ys = range(len(rows))
    hi = max(abs(r["value"]) for r in rows)
    left = direction == "left"
    sgn = -1 if left else 1
    for y, r in zip(ys, rows):
        slot = r.get("slot", 1)
        # Slot 0 is a non-identity neutral: context bars should not
        # spend a categorical hue, and green would read as "good".
        c = MUTED if slot == 0 else S[slot - 1]
        v = sgn * abs(r["value"]) if left else r["value"]
        ax.barh(y, v, height=0.56, color=c, zorder=3)
        ax.text(-sgn * 0.014 * hi, y, r["label"], ha="left" if left else "right",
                va="center", fontsize=8.5, family=MONO, color=INK_MID)
        txt = f"{r['value']:,.1f}{suffix}".replace(".0" + suffix, suffix)
        ax.text(v + sgn * 0.012 * hi, y, txt, ha="right" if left else "left",
                va="center", fontsize=8.5, family=MONO, color=INK)
        if note_key and r.get(note_key):
            ax.text(v + sgn * 0.17 * hi, y, str(r[note_key]),
                    ha="right" if left else "left", va="center",
                    fontsize=7.5, family=MONO, color=INK_SOFT)
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim((-hi * 1.52, 0) if left else (0, hi * 1.52))
    # Widest row label, converted to points, plus the label-to-bar gap. With the
    # labels on the right nothing overhangs the left edge, so no gutter.
    gutter = 0 if left else \
        max(len(str(r["label"])) for r in rows) * 8.5 * MONO_ADVANCE + 7
    _titles(fig, ax, title, subtitle, gutter_pt=gutter)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


def scatter_png(path, points, xlabel="", ylabel="", width=6.6, height=4.2,
                xsuffix="", ysuffix="", quadrant=None, title="", subtitle="",
                note=""):
    """`points` = [{name, x, y, slot}] with direct labels on every mark.

    Two measures that a bar chart can only show one at a time. Every point is
    labelled, so identity never rests on colour alone and no legend is needed.

    `quadrant` = {"x": v, "y": v} draws faint reference lines, for when the
    interesting thing is which corner a point sits in rather than its exact
    coordinates.
    """
    fig, ax = plt.subplots(figsize=(width, height), dpi=DPI, facecolor=PAPER)
    _style(ax)
    ax.grid(color=RULE, lw=1, zorder=0)
    ax.set_axisbelow(True)

    if quadrant:
        for axis, v in (("x", quadrant.get("x")), ("y", quadrant.get("y"))):
            if v is None:
                continue
            (ax.axvline if axis == "x" else ax.axhline)(
                v, color=INK_SOFT, lw=1, ls=(0, (3, 3)), zorder=1)

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    padx = (max(xs) - min(xs)) * 0.10 or 1
    pady = (max(ys) - min(ys)) * 0.10 or 1
    # Right padding is wider than left: labels sit to the right of their mark by
    # default, and the rightmost point needs room for its whole label or it has
    # to flip sides and read as detached.
    # A percentage cannot go below zero, and an axis that offers "-8%" as a tick
    # invites the reader to think the scale means something it does not. Where
    # every value is non-negative, the axis floor is too.
    ax.set_xlim(max(0, min(xs) - padx) if min(xs) >= 0 else min(xs) - padx,
                max(xs) + padx * 2.6)
    ax.set_ylim(max(0, min(ys) - pady) if min(ys) >= 0 else min(ys) - pady,
                max(ys) + pady)

    for pt in points:
        ax.plot([pt["x"]], [pt["y"]], "o", color=S[pt["slot"] - 1], ms=9,
                mec=PAPER, mew=1.5, zorder=4)

    # Label placement in DISPLAY space, because the two axes are on different
    # scales and a nudge expressed in data units is a different distance
    # vertically than horizontally. Each label takes the first candidate offset
    # whose measured box clears every box already placed and stays inside the
    # axes; anything pushed off its mark gets a leader line, since a label that
    # floats free of its dot is worse than no label.
    fig.canvas.draw()
    box = ax.get_window_extent()
    CANDIDATES = [(13, 0), (13, 13), (13, -13), (-13, 0), (-13, 13), (-13, -13),
                  (13, 26), (13, -26), (-13, 26), (-13, -26)]
    placed = []
    for pt in sorted(points, key=lambda q: (-q["y"], q["x"])):
        px, py = ax.transData.transform((pt["x"], pt["y"]))
        w = _text_px(fig, pt["name"], family=MONO, fontsize=8)
        h = 11.0
        chosen = None
        for dx, dy in CANDIDATES:
            x0 = px + dx if dx > 0 else px + dx - w
            y0 = py + dy - h / 2
            if x0 < box.x0 or x0 + w > box.x1 or y0 < box.y0 or y0 + h > box.y1:
                continue
            if any(not (x0 + w + 4 < q[0] or x0 > q[0] + q[2] + 4
                        or y0 + h + 2 < q[1] or y0 > q[1] + q[3] + 2) for q in placed):
                continue
            chosen = (dx, dy, x0, y0)
            break
        if chosen is None:                       # nothing clear — take the default
            dx, dy = CANDIDATES[0]
            chosen = (dx, dy, px + dx, py + dy - h / 2)
        dx, dy, x0, y0 = chosen
        placed.append((x0, y0, w, h))
        if abs(dy) > 4:
            ax.annotate("", (pt["x"], pt["y"]), xycoords="data",
                        textcoords="offset points", xytext=(dx * 0.62, dy),
                        arrowprops=dict(arrowstyle="-", color=RULE, lw=0.9,
                                        shrinkA=0, shrinkB=3), zorder=2,
                        annotation_clip=False)
        ax.annotate(pt["name"], (pt["x"], pt["y"]), textcoords="offset points",
                    xytext=(dx, dy), va="center", ha="left" if dx > 0 else "right",
                    fontsize=8, family=MONO, color=INK_MID, zorder=5,
                    annotation_clip=False)

    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}{xsuffix}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}{ysuffix}"))
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8, family=MONO, color=INK_SOFT, labelpad=7)
    _titles(fig, ax, title, ylabel or subtitle)
    if note:
        ax.annotate(note, (0, 0), xycoords="axes fraction",
                    textcoords="offset points", xytext=(0, -34), ha="left",
                    va="top", fontsize=7, family=MONO, color=INK_SOFT,
                    annotation_clip=False)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


def ledger_png(path, items, width=8.6, accent=None):
    """The headline figures band, as an image.

    Mirrors the report's ledger treatment — a heavy rule above, hairlines
    between columns, the number in accent mono and its caption beneath — on the
    same dark ground as the chapter cards, so the two can sit together in a
    Prismic or Mailchimp layout without looking like different documents.
    """
    n = len(items)
    W = width * DPI
    M = 0.30 * DPI          # outer margin, same as the chapter cards
    pad_x = 0.13 * DPI      # gap from a column's divider to its text
    inner = W - 2 * M
    col = inner / n
    num_kw = dict(family=MONO, fontsize=26)
    lab_kw = dict(family=MONO, fontsize=9)

    # Measured wrapping rather than a character estimate: the caption sits in a
    # column barely wider than the number above it, and an estimate that is even
    # slightly generous runs the last line into the divider rule.
    scratch = plt.figure(figsize=(width, 3), dpi=DPI)
    scratch.canvas.draw()
    avail = col - 2 * pad_x
    wrapped = [_wrap_px(scratch, i["label"], avail, avail, **lab_kw) for i in items]
    plt.close(scratch)
    lines = max(len(w) for w in wrapped)
    # No truncation. An earlier version capped this at three lines, which cut a
    # caption off mid-phrase and looked deliberate rather than broken. The band
    # grows instead, and a long caption is reported so it can be shortened at
    # source rather than silently mangled here.
    if lines > 3:
        longest = max(items, key=lambda i: len(i["label"]))["label"]
        print(f"    note: ledger caption wraps to {lines} lines — consider "
              f"shortening {longest[:60]!r}...")

    px = lambda pt: pt * DPI / 72.0
    lead = px(9 * 1.5)
    rule_gap = 0.26 * DPI   # heavy rule down to the top of the numerals
    num_h = 0.30 * DPI
    H = M + rule_gap + num_h + 0.17 * DPI + lines * lead + 0.22 * DPI + M

    fig = plt.figure(figsize=(width, H / DPI), dpi=DPI, facecolor=CARD_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_facecolor(CARD_BG)

    y_top = H - M
    y_bot = M
    ax.plot([M, W - M], [y_top] * 2, color=CARD_INK, lw=2, clip_on=False)
    ax.plot([M, W - M], [y_bot] * 2, color=CARD_RULE, lw=1, clip_on=False)
    for i in range(1, n):
        x = M + i * col
        ax.plot([x, x], [y_bot + 0.04 * DPI, y_top - 0.04 * DPI],
                color=CARD_RULE, lw=1, clip_on=False)

    base = y_top - rule_gap - num_h
    for i, (item, lab) in enumerate(zip(items, wrapped)):
        x = M + i * col + (pad_x if i else 0)
        ax.text(x, base, item["value"], ha="left", va="baseline",
                color=CARD_ACCENT, **num_kw)
        for k, ln in enumerate(lab):
            ax.text(x, base - 0.17 * DPI - k * lead, ln, ha="left", va="top",
                    color=CARD_MUTED, **lab_kw)
    fig.savefig(path, facecolor=CARD_BG, dpi=DPI)
    plt.close(fig)
    return path


def table_png(path, headers, rows, width=6.6, align=None, highlight_row=None,
              title="", subtitle="", note=""):
    """A table as an image, so it can be dropped into a layout like any figure.

    `note` renders INSIDE the image. Any marker in a cell — an asterisk, a dash,
    a "too few" — needs its key in the same PNG, because these files are dropped
    into a newsletter and a CMS on their own and the markdown caption does not
    travel with them. A table that explains its own symbols only in its caption
    ships an asterisk pointing at nothing.
    """
    n = len(rows)
    # Reserve height for the note before the figure exists, from the mono advance
    # width; the real wrap happens against the drawn axes further down.
    note_lines = 0
    if note:
        cpl = max(20, int(width * 72 * 0.94 / (MONO_ADVANCE * 7.0)))
        note_lines = max(1, -(-len(note) // cpl))
    h = (0.34 * (n + 1.6) + (0.42 if title else 0) + (0.24 if subtitle else 0)
         + (0.16 + 0.13 * note_lines if note else 0))
    fig, ax = plt.subplots(figsize=(width, h), dpi=DPI, facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.axis("off")
    ncol = len(headers)
    align = align or (["left"] + ["right"] * (ncol - 1))
    # First column is the label and gets the left half; the right-aligned numeric
    # columns share the rest evenly, ending flush at the right edge.
    if ncol == 1:
        xs = [0.0]
    elif ncol == 2:
        xs = [0.0, 1.0]
    else:
        xs = [0.0] + [0.52 + 0.48 * i / (ncol - 2) for i in range(ncol - 1)]
    top = 1.0
    rh = 1.0 / (n + 1.6)

    # Stacked upward from the top of the axes in points, not axes fractions: the
    # axes height varies with row count, so a fractional offset would put the
    # title on top of the header row in a tall table and far above it in a short
    # one. Subtitle sits closest to the header, title above it.
    dy = 6
    if subtitle:
        ax.annotate(subtitle, (0, 1.0), xycoords=ax.transAxes,
                    textcoords="offset points", xytext=(0, dy), ha="left",
                    va="bottom", fontsize=8, family=MONO, color=INK_SOFT,
                    annotation_clip=False)
        dy += 13
    if title:
        ax.annotate(title, (0, 1.0), xycoords=ax.transAxes,
                    textcoords="offset points", xytext=(0, dy), ha="left",
                    va="bottom", fontsize=10.5, family=MONO, color=INK,
                    fontweight="bold", annotation_clip=False)

    # Column heads are right-aligned at fixed x positions, so a long one runs
    # left into its neighbour and the two print on top of each other. Measure
    # against the AXES width, not the figure width — the axes is inset by the
    # subplot margins, and using the figure width made the gap look ~30% roomier
    # than it is, which let a real collision through.
    fig.canvas.draw()
    ax_px = ax.get_window_extent().width
    # Check the widest thing in each column, not just the header. A header can
    # fit while the values below it collide — which is exactly what shipped when
    # only headers were measured.
    for i in range(1, ncol):
        gap = (xs[i] - xs[i - 1]) * ax_px
        widest, w_px = headers[i].upper(), _text_px(
            fig, headers[i].upper(), family=MONO, fontsize=7.5)
        for row in rows:
            if i < len(row):
                cw = _text_px(fig, str(row[i]), family=MONO, fontsize=8.5)
                if cw > w_px:
                    widest, w_px = str(row[i]), cw
        if w_px > gap - 8:
            print(f"    note: table column {headers[i]!r} overruns — {widest!r} needs "
                  f"{w_px:.0f}px in a {gap:.0f}px column; shorten it or drop a column")

    for i, hd in enumerate(headers):
        ax.text(xs[i], top, hd.upper(), ha=align[i], va="top", fontsize=7.5,
                family=MONO, color=INK_SOFT, transform=ax.transAxes)
    ax.plot([0, 1], [top - rh * 0.62] * 2, color=INK, lw=1.1,
            transform=ax.transAxes, clip_on=False)

    for r, row in enumerate(rows):
        y = top - rh * (r + 1.5)
        strong = highlight_row is not None and r == highlight_row
        for i, cell in enumerate(row):
            ax.text(xs[i], y, str(cell), ha=align[i], va="center",
                    fontsize=8.5, family=MONO, transform=ax.transAxes,
                    color=INK if strong or i == 0 else INK_MID,
                    fontweight="bold" if strong else "normal")
        ax.plot([0, 1], [y - rh * 0.5] * 2, color=RULE, lw=0.8,
                transform=ax.transAxes, clip_on=False)

    if note:
        lines = _wrap_px(fig, note, ax_px, ax_px, family=MONO, fontsize=7)
        if len(lines) > note_lines:
            print(f"    note: table footnote wrapped to {len(lines)} lines, "
                  f"{note_lines} reserved — it may crowd the last row")
        ax.annotate("\n".join(lines), (0, top - rh * (n + 1.0)),
                    xycoords=ax.transAxes, textcoords="offset points",
                    xytext=(0, -11), ha="left", va="top", fontsize=7,
                    family=MONO, color=INK_SOFT, linespacing=1.5,
                    annotation_clip=False)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


# --- chapter cards -----------------------------------------------------------
# The roadmap in post 0 renders as styled HTML, which cannot be pasted into
# Prismic or Mailchimp. These reproduce the same card as a flat image, on the
# dark ground those platforms use.

CARD_BG = PAPER
CARD_INK = INK
CARD_MUTED = INK_SOFT
CARD_ACCENT = S[0]        # dark-theme slot 1; 4.80:1 on this ground
CARD_RULE = "#2b2f31"     # slightly softer than the chart grid
SERIF = ["Charter", "Palatino", "Georgia", "DejaVu Serif"]


def _text_px(fig, s, **kw):
    """Width of `s` in pixels, measured with the real font rather than guessed."""
    t = fig.text(0, 0, s, **kw)
    w = t.get_window_extent(renderer=fig.canvas.get_renderer()).width
    t.remove()
    return w


def _wrap_px(fig, s, first_px, rest_px, **kw):
    """Greedy wrap to a pixel width, measuring each candidate line.

    Character-count wrapping is unreliable across a proportional serif and a
    monospace face at different sizes, and these cards mix both. `first_px`
    differs from `rest_px` so a line can start after an inline stat number.
    """
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        limit = first_px if not lines else rest_px
        if cur and _text_px(fig, trial, **kw) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def chapter_card_png(path, day, headline, topic, stat_value, stat_label, placement,
                     width=8.6, bg=CARD_BG, ink=CARD_INK):
    """One roadmap entry as a standalone image, sized to its own content."""
    hl_kw = dict(family=SERIF, fontsize=15, fontweight="bold")
    tp_kw = dict(family=SERIF, fontsize=12.5)
    sv_kw = dict(family=MONO, fontsize=12, fontweight="bold")
    sl_kw = dict(family=MONO, fontsize=10.5)
    pl_kw = dict(family=SERIF, fontsize=11.5)

    W = width * DPI
    pad = 0.30 * DPI
    gutter = 1.05 * DPI                 # the "DAY n" column
    bx = pad + gutter                   # body left edge, in pixels
    bw = W - bx - pad                   # body width
    quote_indent = 0.17 * DPI

    # Pass one measures on a scratch canvas; the real figure needs its height
    # up front, and that depends on how many lines each block wraps to.
    scratch = plt.figure(figsize=(width, 4), dpi=DPI)
    scratch.canvas.draw()
    hl = _wrap_px(scratch, headline, bw, bw, **hl_kw)
    tp = _wrap_px(scratch, topic, bw, bw, **tp_kw)
    sv_w = _text_px(scratch, stat_value, **sv_kw)
    sl = _wrap_px(scratch, stat_label, bw - sv_w - 0.13 * DPI, bw, **sl_kw)
    pl = _wrap_px(scratch, placement, bw - quote_indent, bw - quote_indent, **pl_kw)
    plt.close(scratch)

    lead = {"hl": 15 * 1.34, "tp": 12.5 * 1.46, "sl": 10.5 * 1.62, "pl": 11.5 * 1.5}
    px = lambda pt: pt * DPI / 72.0
    h_px = (pad
            + len(hl) * px(lead["hl"]) + 0.07 * DPI
            + len(tp) * px(lead["tp"]) + 0.13 * DPI
            + len(sl) * px(lead["sl"]) + 0.15 * DPI
            + len(pl) * px(lead["pl"]) + pad)

    fig = plt.figure(figsize=(width, h_px / DPI), dpi=DPI, facecolor=bg)
    H = h_px
    # y is measured downward from the top in pixels, converted to the figure's
    # bottom-left fraction at draw time.
    fy = lambda y: 1 - y / H
    fx = lambda x: x / W
    put = lambda x, y, s, **kw: fig.text(fx(x), fy(y), s, va="baseline", **kw)

    y = pad + px(lead["hl"]) * 0.74
    put(pad, y, f"DAY {day}", family=MONO, fontsize=9.5, color=CARD_MUTED)
    for i, line in enumerate(hl):
        put(bx, y + i * px(lead["hl"]), line, color=ink, **hl_kw)
    y += len(hl) * px(lead["hl"]) + 0.07 * DPI

    for i, line in enumerate(tp):
        put(bx, y + i * px(lead["tp"]), line, color=ink, **tp_kw)
    y += len(tp) * px(lead["tp"]) + 0.13 * DPI

    put(bx, y, stat_value, color=CARD_ACCENT, **sv_kw)
    for i, line in enumerate(sl):
        x = bx + (sv_w + 0.13 * DPI if i == 0 else 0)
        put(x, y + i * px(lead["sl"]), line, color=CARD_MUTED, **sl_kw)
    y += len(sl) * px(lead["sl"]) + 0.15 * DPI

    q_top, q_h = y - px(lead["pl"]) * 0.82, len(pl) * px(lead["pl"])
    fig.add_artist(plt.Line2D([fx(bx), fx(bx)], [fy(q_top + q_h), fy(q_top)],
                              color=CARD_RULE, lw=2.2, solid_capstyle="butt"))
    for i, line in enumerate(pl):
        put(bx + quote_indent, y + i * px(lead["pl"]), line, color=CARD_MUTED, **pl_kw)

    fig.savefig(path, facecolor=bg, dpi=DPI)
    plt.close(fig)
    return path
