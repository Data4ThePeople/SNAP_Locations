"""Store-name normalization and brand resolution.

Neither USDA dataset encodes ownership, so chain-vs-independent has to be
derived from store names. Normalization alone is not enough — it shatters
7-Eleven into ELEVEN/ELEVEN A/ELEVEN B and splits DOLLARTREE from DOLLAR TREE —
so normalized names are resolved through a curated crosswalk (data/brands.csv).

Matching is longest-prefix: a pattern matches a name equal to it, or a name
beginning with it followed by a word boundary. That lets one pattern absorb the
store-format and store-number variants a chain generates
("KROGER", "KROGER FUEL CENTER", "KROGER MARKETPLACE").
"""
import csv
import functools
import re

from config import BRANDS_CSV

# Store numbers: pure digits, or digits with a single trailing letter (35283A).
_STORE_NUM = re.compile(r"^\d+[A-Z]?$")
_SUFFIXES = {
    "INC", "INCORPORATED", "LLC", "L L C", "CORP", "CORPORATION", "LTD",
    "LP", "LLP", "PLLC", "CO", "COMPANY", "DBA", "THE",
}


def normalize(name: str) -> str:
    """Normalize a raw store name for brand matching.

    Digits are preserved inside multi-token names (7 ELEVEN) but store numbers
    are dropped, which is the distinction naive digit-stripping gets wrong.
    """
    if not name:
        return ""

    s = name.upper().replace("&", " AND ")
    # Apostrophes are elided, not spaced: CASEY'S -> CASEYS, not CASEY S.
    s = re.sub(r"['‘’`]", "", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    tokens = s.split()

    # Drop long all-digit runs anywhere (store numbers embedded mid-name), but
    # keep short ones so "7 ELEVEN" and "99 CENTS ONLY" survive.
    tokens = [t for t in tokens if not (_STORE_NUM.match(t) and len(t) >= 3)]

    # Drop trailing store numbers of any length, provided a word remains.
    while len(tokens) > 1 and _STORE_NUM.match(tokens[-1]):
        tokens.pop()

    # Drop corporate suffixes, provided a word remains.
    while len(tokens) > 1 and tokens[-1] in _SUFFIXES:
        tokens.pop()
    while len(tokens) > 1 and tokens[0] in _SUFFIXES:
        tokens.pop(0)

    return " ".join(tokens)


@functools.lru_cache(maxsize=1)
def _crosswalk():
    """Load the curated crosswalk, longest pattern first for greedy matching."""
    if not BRANDS_CSV.exists():
        raise SystemExit(f"Missing {BRANDS_CSV} — the curated brand crosswalk.")
    rows = []
    with open(BRANDS_CSV, newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines):
        pattern = (r.get("pattern") or "").strip().upper()
        if not pattern:
            continue
        category = (r.get("chain_category") or "").strip()
        # Banners appear mid-name constantly — "Waynesburg Giant Eagle",
        # "Iversons Piggly Wiggly" — so matching defaults to anywhere in the
        # name. Generic and fuel-brand patterns stay anchored: they are ordinary
        # words, and matching them anywhere would swallow half the independents.
        default = "prefix" if category in ("generic", "fuel_branded") else "any"
        rows.append((
            pattern,
            (r.get("brand") or "").strip() or None,
            category,
            [s for s in (r.get("states") or "").split("|") if s],
            [t for t in (r.get("store_types") or "").split("|") if t],
            (r.get("match") or "").strip().lower() or default,
        ))
    rows.sort(key=lambda t: -len(t[0]))
    return rows


def _hit(name_norm: str, pattern: str, mode: str) -> bool:
    """Word-boundary match: 'GIANT' never matches inside 'GIANTS DELI'."""
    if mode == "prefix":
        return name_norm == pattern or name_norm.startswith(pattern + " ")
    return f" {name_norm} ".find(f" {pattern} ") >= 0


@functools.lru_cache(maxsize=None)
def candidates(name_norm: str):
    """Rules whose pattern matches this name, longest pattern first.

    Longest wins, so specific banners beat generic ones: CONVENIENT FOOD MART
    resolves to the franchise, while a bare FOOD MART stays generic.
    """
    return tuple(r for r in _crosswalk() if _hit(name_norm, r[0], r[5]))


def resolve(name_norm: str, state: str = None, store_type: str = None):
    """Return (brand, chain_category), honoring any state/store-type qualifiers.

    Several banners are shared by unrelated companies — "Metro Market" is
    Kroger's in Wisconsin and independent convenience stores in California —
    so a pattern can be restricted to the states or store types where the
    chain actually operates. Unqualified rules match everywhere.
    """
    for pattern, brand, category, states, types, _mode in candidates(name_norm):
        if states and state not in states:
            continue
        if types and store_type not in types:
            continue
        return brand, category
    return None, None


if __name__ == "__main__":
    # The cases that broke under naive normalization.
    for raw in [
        "7-ELEVEN 35283A", "7 ELEVEN #12345", "DOLLARTREE 10879",
        "Dollar Tree 1234", "WALMART SUPERCENTER 2145", "Walmart 1782",
        "CASEY'S GENERAL STORE #1355", "Casey's 1118", "CVS Pharmacy 5901",
        "Wendy's #24", "Kroger Fuel Center 990", "99 CENTS ONLY STORES 12",
    ]:
        n = normalize(raw)
        b, c = resolve(n) if BRANDS_CSV.exists() else (None, None)
        print(f"{raw:32} -> {n:28} -> {b} / {c}")
