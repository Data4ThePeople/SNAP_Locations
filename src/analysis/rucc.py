"""USDA ERS Rural-Urban Continuum Codes, joined to the panel's county names.

RUCC classifies every county 1-9: codes 1-3 are metro (by metro-area size),
4-9 are nonmetro (by urban population and metro adjacency). The 2023 vintage
drops Connecticut's counties for planning regions, so CT keeps its 2013 codes —
the panel's CT records carry the old county names. Counties are classified by
their CURRENT code in every year, so within-county comparisons are consistent
and "metro" means metro-as-of-2023.

Files are cached in data/raw; download them once from ERS:
  Ruralurbancontinuumcodes2023.xlsx -> data/raw/rucc2023.xlsx
  ruralurbancodes2013.xls           -> data/raw/rucc2013.xls
"""
import re
import unicodedata

import pandas as pd

from config import ROOT

R2023 = ROOT / "data" / "raw" / "rucc2023.xlsx"
R2013 = ROOT / "data" / "raw" / "rucc2013.xls"

DESC = {1: "metro 1M+", 2: "metro 250k-1M", 3: "metro <250k",
        4: "nonmetro urban 20k+, adjacent", 5: "nonmetro urban 20k+, nonadjacent",
        6: "nonmetro urban 5-20k, adjacent", 7: "nonmetro urban 5-20k, nonadjacent",
        8: "rural, adjacent to a metro", 9: "rural, not adjacent"}


def _norm(n):
    """Match the panel's county spellings: ASCII, uppercase, no punctuation,
    with the generic suffixes stripped. 'city' is NOT stripped — Virginia's
    independent cities carry it in both sources (via the CITY fallback below)."""
    n = unicodedata.normalize("NFKD", str(n)).encode("ascii", "ignore").decode()
    n = re.sub(r"\s+(County|Parish|Borough|Census Area|Municipality|"
               r"City and Borough|Municipio)$", "", n.strip(), flags=re.I)
    return re.sub(r"[^A-Z]", "", n.upper())


def load():
    """(lookup, population) — lookup(state, county_name) -> 1..9 or None;
    population is {code: 2020 census population} over all classified counties."""
    r23 = pd.read_excel(R2023)
    r13 = pd.read_excel(R2013)
    rmap = {("CT", _norm(r.County_Name)): int(r.RUCC_2013)
            for r in r13[r13.State == "CT"].itertuples()}
    pop = {k: 0 for k in range(1, 10)}
    for r in r23.itertuples():
        if pd.isna(r.RUCC_2023):
            continue
        code = int(r.RUCC_2023)
        pop[code] += int(r.Population_2020)
        if r.State != "CT":
            rmap[(r.State, _norm(r.County_Name))] = code
    rmap[("DC", "DISTOFCOLUMBIA")] = rmap.get(("DC", "DISTRICTOFCOLUMBIA"), 1)

    def lookup(state, county):
        k = _norm(county or "")
        return rmap.get((state, k)) or rmap.get((state, k + "CITY"))

    return lookup, pop
