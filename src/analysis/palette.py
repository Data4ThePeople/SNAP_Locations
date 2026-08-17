"""Chart palette, with the validator that proves it is safe.

The colours are the documented categorical order from the dataviz skill. This
module re-implements the skill's six checks in Python (there is no JS runtime
here) so the palette is validated in-repo rather than trusted. The port was
confirmed against the skill's published figures before use: full eight slots
adjacent give worst CVD dE 9.1 light / 8.4 dark and worst normal-vision dE 19.6
light / 19.3 dark, which this reproduces exactly.

Line and bar charts compare only *neighbouring* series, so the adjacent pairlist
applies and all eight slots are usable. The map is different — any two dots can
touch, which is the all-pairs case, and there only the first three slots pass.
"""
import itertools
import math

# Categorical slots, fixed order. Never cycled, never reordered.
LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
         "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
DARK = ["#3987e5", "#d95926", "#199e70", "#c98500",
        "#d55181", "#008300", "#9085e9", "#e66767"]

SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}
INK = {"light": {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#8a8984",
                 "grid": "#e6e5e1"},
       "dark": {"primary": "#ffffff", "secondary": "#c3c2b7", "muted": "#8a8984",
                "grid": "#2e2e2b"}}

BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}
CHROMA_FLOOR = 0.10
CVD_TARGET, CVD_FLOOR = 8.0, 6.0
NORMAL_FLOOR = 15.0
CONTRAST_MIN = 3.0

MACHADO = {
    "protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216],
               [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413],
               [-0.011820, 0.042940, 0.968881]],
}


def _lin(h):
    h = h.lstrip("#")
    return [((c / 255) / 12.92 if (c / 255) <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4)
            for c in (int(h[i:i + 2], 16) for i in (0, 2, 4))]


def _oklab(rgb):
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s]


def _oklch(h):
    L, a, b = _oklab(_lin(h))
    return L, math.hypot(a, b)


def contrast(a, b):
    def lum(h):
        r, g, bl = _lin(h)
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _sim(h, kind):
    r, g, b = _lin(h)
    M = MACHADO[kind]
    return [min(1.0, max(0.0, M[i][0] * r + M[i][1] * g + M[i][2] * b)) for i in range(3)]


def delta_e(h1, h2, kind=None):
    a = _oklab(_sim(h1, kind) if kind else _lin(h1))
    b = _oklab(_sim(h2, kind) if kind else _lin(h2))
    return 100 * math.dist(a, b)


def validate(n_series, mode="light", pairs="adjacent", verbose=True):
    """Check the first `n_series` slots. Raises unless every hard gate passes."""
    pal = (LIGHT if mode == "light" else DARK)[:n_series]
    surface = SURFACE[mode]
    lo, hi = BAND[mode]
    problems, warns = [], []

    off = [(c, round(_oklch(c)[0], 3)) for c in pal if not lo <= _oklch(c)[0] <= hi]
    if off:
        problems.append(f"lightness band {lo}-{hi}: {off}")
    low = [(c, round(_oklch(c)[1], 3)) for c in pal if _oklch(c)[1] < CHROMA_FLOOR]
    if low:
        problems.append(f"chroma floor: {low}")

    idx = range(len(pal))
    plist = (list(itertools.combinations(idx, 2)) if pairs == "all"
             else [(i, i + 1) for i in range(len(pal) - 1)])
    worst_cvd = worst_nrm = None
    if plist:
        worst_cvd = min((min(delta_e(pal[i], pal[j], "protan"),
                             delta_e(pal[i], pal[j], "deutan")), pal[i], pal[j])
                        for i, j in plist)
        worst_nrm = min((delta_e(pal[i], pal[j]), pal[i], pal[j]) for i, j in plist)
        if worst_cvd[0] < CVD_FLOOR:
            problems.append(f"CVD separation {worst_cvd[0]:.1f} < {CVD_FLOOR}")
        elif worst_cvd[0] < CVD_TARGET:
            warns.append(f"CVD in warn band ({worst_cvd[0]:.1f}) — needs direct labels")
        if worst_nrm[0] < NORMAL_FLOOR:
            problems.append(f"normal-vision floor {worst_nrm[0]:.1f} < {NORMAL_FLOOR}")

    thin = [(c, round(contrast(c, surface), 2)) for c in pal
            if contrast(c, surface) < CONTRAST_MIN]
    if thin:
        warns.append(f"sub-3:1 vs surface, relief rule applies (legend + labels): {thin}")

    if verbose:
        print(f"  {mode:5} n={n_series} pairs={pairs}: "
              f"CVD dE {worst_cvd[0]:.1f}  normal dE {worst_nrm[0]:.1f}  "
              f"{'FAIL' if problems else 'PASS'}")
        for w in warns:
            print(f"        WARN {w}")
    if problems:
        raise SystemExit(f"PALETTE FAILS ({mode}, n={n_series}): " + "; ".join(problems))
    return pal


if __name__ == "__main__":
    # Reproduce the skill's published figures, then clear the sizes the reports use.
    print("Port check against the skill's documented values:")
    for mode, cvd, nrm in (("light", 9.1, 19.6), ("dark", 8.4, 19.3)):
        pal = LIGHT if mode == "light" else DARK
        wc = min(min(delta_e(pal[i], pal[i + 1], "protan"),
                     delta_e(pal[i], pal[i + 1], "deutan")) for i in range(7))
        wn = min(delta_e(pal[i], pal[i + 1]) for i in range(7))
        ok = abs(wc - cvd) < 0.1 and abs(wn - nrm) < 0.1
        print(f"  {mode:5} 8 slots adjacent: CVD {wc:.1f} (doc {cvd})  "
              f"normal {wn:.1f} (doc {nrm})  {'MATCH' if ok else 'MISMATCH'}")
        if not ok:
            raise SystemExit("port does not reproduce the documented palette figures")
    print("\nSizes the reports use:")
    for n in (2, 4, 6, 8):
        validate(n, "light")
        validate(n, "dark")
