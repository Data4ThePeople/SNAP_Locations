"""Inline-SVG charts for the reports.

SVG references CSS custom properties (`var(--s1)`, `var(--ink-2)`) rather than
literal hex, so one chart renders correctly in light and dark without being
generated twice. The report defines those tokens per theme.

Conventions follow the dataviz skill: 2px lines, recessive grid and axes, a
legend whenever there are two or more series, selective direct labels rather
than a number on every point, and text in ink tokens rather than series colour.
"""
from html import escape

PAD = {"t": 18, "r": 96, "b": 34, "l": 58}

# Height reserved above the plot for a title, and for a units line beneath it.
TITLE_H, SUB_H = 22, 15


def _heading(title, subtitle, x, y):
    """Title in ink above the plot, units beneath it in soft ink.

    The reader meets the figure before its caption, so the figure states what it
    shows on its own. The title carries the claim in words; the units line stays
    recessive so it does not compete.
    """
    parts, cy = [], y
    if title:
        parts.append(f'<text x="{x}" y="{cy}" class="chart-title">{escape(title)}</text>')
        cy += SUB_H
    if subtitle:
        parts.append(f'<text x="{x}" y="{cy}" class="axis-title">{escape(subtitle)}</text>')
    return parts


def _fmt(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 10_000:
        return f"{round(v/1000):,.0f}k"
    if v >= 1_000:
        return f"{v/1000:.1f}k"
    return f"{v:,.0f}"


def line_chart(years, series, width=720, height=330, y_zero=True, y_label="",
              value_labels=True, annotate=None, title="", subtitle=""):
    """`series` is a list of {name, values, slot} — slot is the 1-based palette index.

    `subtitle` is an alias for `y_label`, so every chart here takes the same
    title/subtitle pair and a caller can change chart type without renaming the
    keyword. y_label wins if both are supplied.
    """
    y_label = y_label or subtitle
    head = (TITLE_H if title else 0) + (SUB_H if y_label else 0)
    w, h = width, height + head
    x0, x1 = PAD["l"], w - PAD["r"]
    y0, y1 = h - PAD["b"], PAD["t"] + head
    lo = 0 if y_zero else min(min(s["values"]) for s in series) * 0.95
    hi = max(max(s["values"]) for s in series) * 1.06
    sx = lambda i: x0 + (x1 - x0) * i / max(len(years) - 1, 1)
    sy = lambda v: y1 + (y0 - y1) * (1 - (v - lo) / (hi - lo))

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart">']

    # Grid and y axis — deliberately recessive.
    steps = 4
    for k in range(steps + 1):
        v = lo + (hi - lo) * k / steps
        y = sy(v)
        parts.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" '
                     f'stroke="var(--grid)" stroke-width="1"/>')
        parts.append(f'<text x="{x0-8}" y="{y+4:.1f}" text-anchor="end" '
                     f'class="tick">{_fmt(v)}</text>')
    # x axis: first, last and every fourth year, to avoid a crowded axis.
    keep = {years[0], years[-1]} | {y for y in years
                                    if y % 4 == 0 and years[0] + 3 <= y <= years[-1] - 3}
    for i, yr in enumerate(years):
        if yr in keep:
            parts.append(f'<text x="{sx(i):.1f}" y="{y0+20}" text-anchor="middle" '
                         f'class="tick">{yr}</text>')

    for s in series:
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(s["values"]))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="var(--s{s["slot"]})" '
                     f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{sx(len(years)-1):.1f}" cy="{sy(s["values"][-1]):.1f}" r="3.5" '
                     f'fill="var(--s{s["slot"]})" stroke="var(--surface)" stroke-width="2"/>')

    # Direct labels at the line ends, nudged apart where series finish close
    # together so two labels never print on top of each other.
    placed = []
    for val, s in sorted(((s["values"][-1], s) for s in series), key=lambda t: -t[0]):
        ly = sy(val)
        if placed and ly - placed[-1] < 14:
            ly = placed[-1] + 14
        placed.append(ly)
        # Swatch beside the label: the text is an ink token, so the mark is what
        # ties a nudged label back to its line.
        parts.append(f'<circle cx="{x1+12:.1f}" cy="{ly:.1f}" r="3" '
                     f'fill="var(--s{s["slot"]})"/>')
        parts.append(f'<text x="{x1+20}" y="{ly+4:.1f}" class="dlabel">'
                     f'{escape(s["name"])}{" " + _fmt(val) if value_labels else ""}</text>')

    for a in (annotate or []):
        i = years.index(a["year"])
        parts.append(f'<line x1="{sx(i):.1f}" x2="{sx(i):.1f}" y1="{y1}" y2="{y0}" '
                     f'stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{sx(i)+5:.1f}" y="{y1+11}" class="note">'
                     f'{escape(a["text"])}</text>')

    parts.extend(_heading(title, y_label, x0, PAD["t"] - 2 + (TITLE_H - 8 if title else 0)))
    parts.append("</svg>")
    return "\n".join(parts)


def bar_chart(rows, width=720, row_h=30, slot=1, suffix="", note_key=None,
              title="", subtitle="", direction="right"):
    """Horizontal bars, `rows` = [{label, value, note}]. One hue: length is the
    encoding, so spending the identity channel on it would be redundant.

    direction="left" anchors the bars to a right-hand baseline and grows them
    leftward, with labels on the right. Pass the values signed (negative for a
    decline): a series of drops then reads as drops, "-64%" and pointing down
    the scale, instead of as positive magnitudes."""
    head = (TITLE_H if title else 0) + (SUB_H if subtitle else 0)
    h = PAD["t"] + PAD["b"] + row_h * len(rows) + head
    left = direction == "left"
    x0, x1 = (74, width - 186) if left else (186, width - 74)
    hi = max(abs(r["value"]) for r in rows) * 1.02
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" class="chart">']
    parts.extend(_heading(title, subtitle, 0, PAD["t"] - 2 + (TITLE_H - 8 if title else 0)))
    for i, r in enumerate(rows):
        y = PAD["t"] + head + row_h * i
        bw = (x1 - x0) * abs(r["value"]) / hi
        lx, la = (x1 + 10, "start") if left else (x0 - 10, "end")
        parts.append(f'<text x="{lx}" y="{y+row_h/2+4:.0f}" text-anchor="{la}" '
                     f'class="blabel">{escape(r["label"])}</text>')
        # 4px rounded data-end, anchored to the baseline.
        sl = r.get("slot", slot)
        fill = "var(--muted)" if sl == 0 else f"var(--s{sl})"
        bx = x1 - bw if left else x0
        parts.append(f'<rect x="{bx:.1f}" y="{y+5:.0f}" width="{max(bw,2):.1f}" '
                     f'height="{row_h-12}" rx="4" fill="{fill}"/>')
        vx, va = (x1 - bw - 8, "end") if left else (x0 + bw + 8, "start")
        parts.append(f'<text x="{vx:.1f}" y="{y+row_h/2+4:.0f}" text-anchor="{va}" '
                     f'class="bvalue">'
                     f'{r["value"]:,.1f}{suffix}'.replace(".0" + suffix, suffix) + '</text>')
        if note_key and r.get(note_key):
            nx, na = (x1 - bw - 58, "end") if left else (x0 + bw + 58, "start")
            parts.append(f'<text x="{nx:.1f}" y="{y+row_h/2+4:.0f}" text-anchor="{na}" '
                         f'class="note">{escape(str(r[note_key]))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _nice_ticks(lo, hi, target=4):
    """Round tick values covering [lo, hi], and the range they imply.

    Dividing a data range into four equal parts gives ticks like 48.8% and
    194.2%, which are unreadable and imply a precision the axis does not have.
    Step up to a 1/2/2.5/5 x power-of-ten instead, and let the axis end on the
    ticks rather than on the data.
    """
    import math
    span = (hi - lo) or 1
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if raw <= step:
            break
    t0 = math.floor(lo / step) * step
    t1 = math.ceil(hi / step) * step
    n = int(round((t1 - t0) / step))
    ticks = [t0 + step * i for i in range(n + 1)]
    # -0.0 prints as "-0"; snap anything within a rounding error of zero.
    ticks = [0.0 if abs(v) < step * 1e-9 else v for v in ticks]
    return ticks, t0, t1


def scatter_chart(points, width=720, height=400, x_label="", y_label="",
                  x_suffix="", y_suffix="", quadrant=None, title="", subtitle="",
                  note=""):
    """`points` is a list of {name, x, y, slot} — every mark directly labelled.

    Two measures at once, which a bar chart can only show one of. Because every
    point carries its own label, identity never rests on colour and no legend is
    needed; the caller is expected to put the distinguishing attribute in the
    name as well as the slot.
    """
    head = (TITLE_H if title else 0) + (SUB_H if (y_label or subtitle) else 0)
    sub = y_label or subtitle
    w, h = width, height + head
    x0, x1 = PAD["l"], w - 24
    y0, y1 = h - PAD["b"] - (14 if note else 0), PAD["t"] + head

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    padx = (max(xs) - min(xs)) * 0.08 or 1
    pady = (max(ys) - min(ys)) * 0.08 or 1
    # A percentage cannot go below zero, and an axis that offers "-8%" as a tick
    # invites the reader to think the scale means something it does not. Where
    # every value is non-negative, the axis floor is too.
    xlo, xhi = min(xs) - padx, max(xs) + padx
    ylo, yhi = min(ys) - pady, max(ys) + pady
    if min(xs) >= 0:
        xlo = max(0, xlo)
    if min(ys) >= 0:
        ylo = max(0, ylo)
    # Five steps on x, four on y: with four, a range of about 400 points
    # rounds its step up to 200 and puts the first tick at -200%, below the
    # -100% floor a count change can reach. Five lands it on -100%.
    xticks, xlo, xhi = _nice_ticks(xlo, xhi, target=5)
    yticks, ylo, yhi = _nice_ticks(ylo, yhi)
    # Labels sit to the right of their mark, so the rightmost point needs room
    # for its text. That room comes out of the PLOT WIDTH, not the data range.
    # Padding the range instead put ticks at -200% and 600% on data running
    # -41% to +307%, and a store cannot fall by more than 100%.
    xplot = x1 - (x1 - x0) * 0.28
    sx = lambda v: x0 + (xplot - x0) * (v - xlo) / (xhi - xlo)
    sy = lambda v: y0 - (y0 - y1) * (v - ylo) / (yhi - ylo)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart">']

    for v in yticks:
        y = sy(v)
        parts.append(f'<line x1="{x0}" x2="{xplot:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                     f'stroke="var(--grid)" stroke-width="1"/>')
        parts.append(f'<text x="{x0-8}" y="{y+4:.1f}" text-anchor="end" '
                     f'class="tick">{v:g}{escape(y_suffix)}</text>')
    for v in xticks:
        parts.append(f'<text x="{sx(v):.1f}" y="{y0+20}" text-anchor="middle" '
                     f'class="tick">{v:g}{escape(x_suffix)}</text>')

    if quadrant and quadrant.get("x") is not None:
        qx = sx(quadrant["x"])
        parts.append(f'<line x1="{qx:.1f}" x2="{qx:.1f}" y1="{y1}" y2="{y0}" '
                     f'stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
    if quadrant and quadrant.get("y") is not None:
        qy = sy(quadrant["y"])
        parts.append(f'<line x1="{x0}" x2="{xplot:.1f}" y1="{qy:.1f}" y2="{qy:.1f}" '
                     f'stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')

    for pt in points:
        parts.append(f'<circle cx="{sx(pt["x"]):.1f}" cy="{sy(pt["y"]):.1f}" r="5" '
                     f'fill="var(--s{pt["slot"]})" stroke="var(--surface)" '
                     f'stroke-width="2"/>')

    # Labels: right of the mark by default, else the first candidate offset whose
    # box clears everything already placed and stays inside the plot. Anything
    # pushed off its mark gets a leader, because a label floating free of its dot
    # is worse than no label. .dlabel is 11.5px mono, so ~6.9px per character.
    CH = 6.9
    CANDIDATES = [(11, 4), (11, -8), (11, 16), (-11, 4), (-11, -8), (-11, 16),
                  (11, -20), (11, 28), (-11, -20), (-11, 28)]
    placed = []
    for pt in sorted(points, key=lambda q: (-q["y"], q["x"])):
        cx, cy = sx(pt["x"]), sy(pt["y"])
        tw = len(pt["name"]) * CH
        chosen = None
        for dx, dy in CANDIDATES:
            bx = cx + dx if dx > 0 else cx + dx - tw
            by = cy + dy - 11
            if bx < x0 - 40 or bx + tw > w - 2 or by < y1 - 4 or by + 13 > y0 + 2:
                continue
            if any(not (bx + tw + 4 < q[0] or bx > q[0] + q[2] + 4
                        or by + 13 < q[1] or by > q[1] + 13) for q in placed):
                continue
            chosen = (dx, dy, bx, by)
            break
        if chosen is None:
            dx, dy = CANDIDATES[0]
            chosen = (dx, dy, cx + dx, cy + dy - 11)
        dx, dy, bx, by = chosen
        placed.append((bx, by, tw))
        if abs(dy - 4) > 5:
            parts.append(f'<line x1="{cx:.1f}" x2="{cx + dx * 0.6:.1f}" '
                         f'y1="{cy:.1f}" y2="{cy + dy - 4:.1f}" '
                         f'stroke="var(--grid)" stroke-width="1"/>')
        parts.append(f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" '
                     f'text-anchor="{"start" if dx > 0 else "end"}" '
                     f'class="dlabel">{escape(pt["name"])}</text>')

    if x_label:
        parts.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 33}" '
                     f'text-anchor="middle" class="axis-title">{escape(x_label)}</text>')
    if note:
        parts.append(f'<text x="{x0}" y="{h - 3}" class="note">{escape(note)}</text>')
    parts.extend(_heading(title, sub, x0, PAD["t"] - 2 + (TITLE_H - 8 if title else 0)))
    parts.append("</svg>")
    return "\n".join(parts)


def legend(series):
    items = "".join(
        f'<span class="lg"><i style="background:var(--s{s["slot"]})"></i>'
        f'{escape(s["name"])}</span>' for s in series)
    return f'<div class="legend">{items}</div>'
