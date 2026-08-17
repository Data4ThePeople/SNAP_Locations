"""PNG renderers for charts and tables, for pasting into Mailchimp or Prismic.

The HTML report uses inline SVG with CSS tokens so it can follow the reader's
theme. Email and CMS layouts cannot, so these render the same figures to PNG on
a solid light ground at 2x. Both read the same JSON, so the numbers cannot
diverge — only the styling.

Everything is drawn in monospace, matching the report's treatment of figures as
record-keeping rather than display type.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from analysis import palette

PAPER = "#ffffff"      # solid white: safest ground for email clients
INK = "#16191c"
INK_MID = "#4d545c"
INK_SOFT = "#7c848c"
RULE = "#dee4e9"
MUTED = "#b9c0c7"
DPI = 200
MONO = ["DejaVu Sans Mono"]

S = palette.LIGHT  # slot 1..8 -> S[0..7]


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


def line_png(path, years, series, ylabel="", width=6.6, height=3.3, annotate=None,
             label_ends=True):
    """`series` = [{name, values, slot}]. Direct end labels satisfy the relief
    rule for the lighter slots, which sit under 3:1 on a light ground."""
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
            ax.annotate(f" {s['name']}", (years[-1], y),
                        textcoords="offset points", xytext=(7, 0), va="center",
                        fontsize=8, family=MONO, color=INK_MID, zorder=5)
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
    if ylabel:
        ax.set_title(ylabel, loc="left", fontsize=8, family=MONO, color=INK_SOFT, pad=8)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


def hbar_png(path, rows, suffix="", width=6.6, note_key=None):
    """`rows` = [{label, value, slot?, note?}], drawn top-to-bottom as given."""
    h = 0.42 * len(rows) + 0.55
    fig, ax = plt.subplots(figsize=(width, h), dpi=DPI, facecolor=PAPER)
    ax.set_facecolor(PAPER)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False, labelleft=False)
    ys = range(len(rows))
    hi = max(r["value"] for r in rows)
    for y, r in zip(ys, rows):
        slot = r.get("slot", 1)
        # Slot 0 is a non-identity neutral: context bars should not
        # spend a categorical hue, and green would read as "good".
        c = MUTED if slot == 0 else S[slot - 1]
        ax.barh(y, r["value"], height=0.56, color=c, zorder=3)
        ax.text(-0.014 * hi, y, r["label"], ha="right", va="center",
                fontsize=8.5, family=MONO, color=INK_MID)
        txt = f"{r['value']:,.1f}{suffix}".replace(".0" + suffix, suffix)
        ax.text(r["value"] + 0.012 * hi, y, txt, ha="left", va="center",
                fontsize=8.5, family=MONO, color=INK)
        if note_key and r.get(note_key):
            ax.text(r["value"] + 0.17 * hi, y, str(r[note_key]), ha="left", va="center",
                    fontsize=7.5, family=MONO, color=INK_SOFT)
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim(0, hi * 1.52)
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path


def ledger_png(path, items, width=6.6, accent=1):
    """The headline figures band, as an image.

    Mirrors the report's ledger treatment: a heavy rule above, hairlines between
    columns, the number in accent mono and its caption beneath in soft ink. Kept
    as a figure so the stat block can be dropped into a layout like any chart.
    """
    import textwrap

    n = len(items)
    # Wrap to the column, not a guessed character count: at 8pt a monospace glyph
    # is about 0.6em wide, so a third-width column holds far fewer than 34 and the
    # caption would otherwise run into the divider rule.
    label_pt = 8
    col_in = width / n - 0.34
    chars = max(14, int(col_in / (label_pt * 0.60 / 72)))
    wrapped = [textwrap.wrap(i["label"], chars)[:3] for i in items]
    lines = max(len(w) for w in wrapped)

    # Laid out in inches, not axis fractions: with fractions the caption's last
    # line drifted into the bottom rule as soon as a label needed three lines.
    LINE_H, NUM_TOP, BOTTOM_PAD = 0.145, 0.44, 0.18
    height = NUM_TOP + LINE_H * lines + BOTTOM_PAD
    fig = plt.figure(figsize=(width, height), dpi=DPI, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    col = width / n

    ax.plot([0, width], [height - 0.03, height - 0.03], color=INK, lw=2, clip_on=False)
    ax.plot([0, width], [0.05, 0.05], color=RULE, lw=1, clip_on=False)
    for i in range(1, n):
        ax.plot([i * col, i * col], [0.08, height - 0.08], color=RULE, lw=1, clip_on=False)

    for i, (item, lab) in enumerate(zip(items, wrapped)):
        x = i * col + 0.12
        ax.text(x, height - NUM_TOP, item["value"], ha="left", va="baseline",
                fontsize=25, family=MONO, color=S[accent - 1])
        for k, ln in enumerate(lab):
            ax.text(x, height - NUM_TOP - 0.14 - k * LINE_H, ln, ha="left", va="top",
                    fontsize=8, family=MONO, color=INK_SOFT)
    fig.savefig(path, facecolor=PAPER, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return path


def table_png(path, headers, rows, width=6.6, align=None, highlight_row=None):
    """A table as an image, so it can be dropped into a layout like any figure."""
    n = len(rows)
    h = 0.34 * (n + 1.6)
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
    fig.savefig(path, bbox_inches="tight", facecolor=PAPER, pad_inches=0.16)
    plt.close(fig)
    return path
