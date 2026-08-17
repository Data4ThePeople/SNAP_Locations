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


def _fmt(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 10_000:
        return f"{round(v/1000):,.0f}k"
    if v >= 1_000:
        return f"{v/1000:.1f}k"
    return f"{v:,.0f}"


def line_chart(years, series, width=720, height=330, y_zero=True, y_label="",
              value_labels=True, annotate=None):
    """`series` is a list of {name, values, slot} — slot is the 1-based palette index."""
    w, h = width, height
    x0, x1 = PAD["l"], w - PAD["r"]
    y0, y1 = h - PAD["b"], PAD["t"]
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
        parts.append(f'<text x="{x1+8}" y="{ly+4:.1f}" class="dlabel">'
                     f'{escape(s["name"])}{" " + _fmt(val) if value_labels else ""}</text>')

    for a in (annotate or []):
        i = years.index(a["year"])
        parts.append(f'<line x1="{sx(i):.1f}" x2="{sx(i):.1f}" y1="{y1}" y2="{y0}" '
                     f'stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{sx(i)+5:.1f}" y="{y1+11}" class="note">'
                     f'{escape(a["text"])}</text>')

    if y_label:
        parts.append(f'<text x="{x0}" y="{y1-6}" class="axis-title">{escape(y_label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def bar_chart(rows, width=720, row_h=30, slot=1, suffix="", note_key=None):
    """Horizontal bars, `rows` = [{label, value, note}]. One hue: length is the
    encoding, so spending the identity channel on it would be redundant."""
    h = PAD["t"] + PAD["b"] + row_h * len(rows)
    x0, x1 = 186, width - 74
    hi = max(r["value"] for r in rows) * 1.02
    parts = [f'<svg viewBox="0 0 {width} {h}" role="img" class="chart">']
    for i, r in enumerate(rows):
        y = PAD["t"] + row_h * i
        bw = (x1 - x0) * r["value"] / hi
        parts.append(f'<text x="{x0-10}" y="{y+row_h/2+4:.0f}" text-anchor="end" '
                     f'class="blabel">{escape(r["label"])}</text>')
        # 4px rounded data-end, anchored to the baseline.
        sl = r.get("slot", slot)
        fill = "var(--muted)" if sl == 0 else f"var(--s{sl})"
        parts.append(f'<rect x="{x0}" y="{y+5:.0f}" width="{max(bw,2):.1f}" '
                     f'height="{row_h-12}" rx="4" fill="{fill}"/>')
        parts.append(f'<text x="{x0+bw+8:.1f}" y="{y+row_h/2+4:.0f}" class="bvalue">'
                     f'{r["value"]:,.1f}{suffix}'.replace(".0" + suffix, suffix) + '</text>')
        if note_key and r.get(note_key):
            parts.append(f'<text x="{x0+bw+58:.1f}" y="{y+row_h/2+4:.0f}" class="note">'
                         f'{escape(str(r[note_key]))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def legend(series):
    items = "".join(
        f'<span class="lg"><i style="background:var(--s{s["slot"]})"></i>'
        f'{escape(s["name"])}</span>' for s in series)
    return f'<div class="legend">{items}</div>'
