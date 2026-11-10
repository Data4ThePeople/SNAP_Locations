"""Post 8: how many people are on SNAP, by month, and where enrollment fell.

Sources (in data/raw/snap_participation/):
- USDA FNS SNAP Data Tables, "SNAP Monthly State Participation and Benefit
  Summary", one workbook per fiscal year (FY19.xls, FY20.xlsx ... FY26.xlsx).
  FY20 on are the "P-EBT/Other Excluded" versions; FY19 predates P-EBT. Each
  workbook has seven regional sheets (one block per state: a name row, then
  month rows of households, persons, cost, cost per household, cost per
  person) and a "US Summary" sheet in the same layout. Unreported months are
  "--". FY26 data as of October 9, 2026; latest month July 2026.
- New York State OTDA, "SNAP Caseloads and Expenditures: Beginning 2002"
  (data.ny.gov dq6j-8u8z), monthly persons by social services district.
  New York City is one district; the other 57 are counties.

Measure: persons participating. The chart starts in January 2020: in January
and February 2019 the partial federal shutdown moved February benefits into
January, and USDA's February 2019 count (7.6 million) reflects that, not a
real drop. Changes run from a start month to July 2026,
the latest month USDA has published. The year-over-year change (July 2025 to
July 2026) avoids seasonal swings; the January 2025 start matches the earlier
draft language.

Groups: limit states are the ten states with SNAP soda or candy limits in
2026 (post8_left2026.RESTRICTED); other states are the remaining 40 states
and DC. Territories are left out.

Trifectas: Ballotpedia party control of state government (copied from Eric's
earlier analysis to data/raw/ballotpedia/trifectas-2025-2026.csv). A state is
a Republican or Democratic trifecta when one party holds the governor's office
and both legislative chambers; otherwise divided. Nebraska's one-house
legislature is nonpartisan and Ballotpedia counts it by the governor's party.
Groups use 2026 status (Virginia became a Democratic trifecta in January 2026;
2025 status is kept as a check). New York City is split out of New York, a
Democratic trifecta, using the OTDA file; DC has no state government and is in
no trifecta group.

Writes reports/data/post8_enrollment.json and post8-enrollment.png.

    python -m analysis.post8_enrollment      (from src/)
"""
import csv
import json
from decimal import ROUND_HALF_UP, Decimal

import openpyxl
import xlrd

from analysis import figures
from analysis.post8_left2026 import RESTRICTED
from config import ROOT

RAW = ROOT / "data" / "raw" / "snap_participation"
OUT = ROOT / "reports" / "data" / "post8_enrollment.json"
IMG = ROOT / "reports" / "post8" / "images"
FYS = range(2019, 2027)
REGIONS = ["NERO", "MARO", "SERO", "MWRO", "SWRO", "MPRO", "WRO"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NY_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"}
STARTS = {"jan2025": (2025, 1), "jul2025": (2025, 7), "dec2025": (2025, 12)}
END = (2026, 7)
TRIFECTAS = ROOT / "data" / "raw" / "ballotpedia" / "trifectas-2025-2026.csv"


def pct1(a, b):
    return float(Decimal(100 * (b - a) / a).quantize(Decimal("0.1"), ROUND_HALF_UP))


def sheet_rows(path, sheet):
    if path.suffix == ".xls":
        s = xlrd.open_workbook(str(path)).sheet_by_name(sheet)
        return [s.row_values(i) for i in range(s.nrows)]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    wb.close()
    return rows


def month_key(label):
    """'Jan 2019 /2' -> (2019, 1); anything else -> None."""
    if not isinstance(label, str):
        return None
    parts = label.split()
    if len(parts) < 2 or parts[0] not in MONTHS or not parts[1].isdigit():
        return None
    return int(parts[1]), MONTHS.index(parts[0]) + 1


def blocks(rows):
    """{name: {(year, month): persons}} for every name-row block in a sheet."""
    out, name = {}, None
    for r in rows:
        if not r or r[0] in (None, ""):
            continue
        k = month_key(r[0])
        if k is None:
            label = str(r[0]).strip()
            name = label if all(v in (None, "") for v in r[1:]) else None
            continue
        if name is not None and r[2] not in ("--", None, ""):
            out.setdefault(name, {})[k] = int(r[2])
    return out


def load_usda():
    us, states = {}, {}
    for fy in FYS:
        path = next(RAW.glob(f"FY{fy % 100:02d}.xls*"))
        us.update(blocks(sheet_rows(path, "US Summary"))["US Summary"])
        for reg in REGIONS:
            for name, months in blocks(sheet_rows(path, reg)).items():
                if name in STATE_ABBR:
                    states.setdefault(STATE_ABBR[name], {}).update(months)
    return us, states


def load_ny():
    nyc, nys = {}, {}
    with open(RAW / "ny-snap-caseloads-dq6j-8u8z.csv", newline="") as f:
        for r in csv.DictReader(f):
            k = (int(r["year"]), NY_MONTHS.index(r["month"]) + 1)
            n = int(r["total_snap_persons"])
            nys[k] = nys.get(k, 0) + n
            if r["district"] == "New York City":
                nyc[k] = n
    return nyc, nys


def load_trifectas(year):
    with open(TRIFECTAS, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["year"] == str(year)]
    assert len(rows) == 50
    return {STATE_ABBR[r["state"]]: {"R": "Republican", "D": "Democratic"}.get(r["trifecta"], "Divided")
            for r in rows}


def changes(series):
    return {name: {"from": series[s], "to": series[END], "pct": pct1(series[s], series[END])}
            for name, s in STARTS.items()}


def main():
    us, states = load_usda()
    assert len(states) == 51, sorted(states)
    nyc, nys = load_ny()
    sum_of = lambda codes: {k: sum(states[c][k] for c in codes)
                            for k in us if all(k in states[c] for c in codes)}
    limit = sum_of(sorted(RESTRICTED))
    other = sum_of(sorted(set(states) - RESTRICTED))
    rest_ny = {k: nys[k] - nyc[k] for k in nyc}

    def trifecta_groups(year):
        tri = load_trifectas(year)
        g = {}
        for party in ("Republican", "Democratic", "Divided"):
            codes = sorted(c for c, t in tri.items() if t == party)
            ser = sum_of(codes)
            if "NY" in codes:   # New York City is shown on its own
                ser = {k: v - nyc[k] for k, v in ser.items() if k in nyc}
            g[party] = {"states": codes, **changes(ser)}
        g["Divided_excl_AZ"] = changes(sum_of(sorted(set(g["Divided"]["states"]) - {"AZ"})))
        g["Republican_excl_TX_FL"] = changes(sum_of(sorted(set(g["Republican"]["states"]) - {"TX", "FL"})))
        return g

    months = sorted(k for k in us if (2019, 1) <= k <= END)
    chart_months = [k for k in months if k >= (2020, 1)]
    out = {
        "source_as_of": "2026-10-09",
        "latest_month": "2026-07",
        "us_monthly": {f"{y}-{m:02d}": us[(y, m)] for y, m in months},
        "us": changes(us),
        "us_peak_2020_2026": max(((us[k], f"{k[0]}-{k[1]:02d}") for k in chart_months)),
        "limit_states": changes(limit),
        "other_states": changes(other),
        "other_states_excl_az": changes(sum_of(sorted(set(states) - RESTRICTED - {"AZ"}))),
        "tx_fl_share_of_limit_loss_jul2025_jul2026": round(100 * sum(
            states[c][(2025, 7)] - states[c][END] for c in ("TX", "FL"))
            / (limit[(2025, 7)] - limit[END])),
        "trifecta_2026": trifecta_groups(2026),
        "trifecta_2025_check": trifecta_groups(2025),
        "ny_state_usda": changes(states["NY"]),
        "ny_state_otda": changes(nys),
        "nyc_otda": changes(nyc),
        "rest_of_ny_otda": changes(rest_ny),
        "nyc_latest": {"month": "2026-08", "persons": nyc[(2026, 8)]},
        "otda_vs_usda_ny_jul2026": {"otda": nys[END], "usda": states["NY"][END]},
        "states_jul2025_jul2026": {c: pct1(states[c][(2025, 7)], states[c][END])
                                   for c in sorted(states)},
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("us_monthly", "states_jul2025_jul2026")}, indent=1))

    xs = [y + (m - 1) / 12 for y, m in chart_months]
    figures.line_png(
        IMG / "post8-enrollment.png", xs,
        [{"name": "People on SNAP", "slot": 1,
          "values": [us[k] / 1e6 for k in chart_months]}],
        title="People on SNAP each month, January 2020 to July 2026",
        subtitle="Millions of people. Source: USDA, SNAP Data Tables, data as of October 9, 2026.",
        label_ends=False,
        xticks=[(y, str(y)) for y in range(2020, 2027)])
    print(f"wrote {IMG / 'post8-enrollment.png'}")

    def people(n):
        """Fewer people, rounded for a chart label: 2.5 million, 155,000."""
        if n >= 1_000_000:
            return f"{Decimal(n / 1e6).quantize(Decimal('0.1'), ROUND_HALF_UP)} million"
        return f"{int(Decimal(n / 1000).quantize(Decimal('1'), ROUND_HALF_UP)):,},000"

    def bar(label, ch, slot):
        lost = ch["jul2025"]["from"] - ch["jul2025"]["to"]
        out["chart_people_lost"][label] = lost
        return {"label": label, "value": ch["jul2025"]["pct"], "slot": slot,
                "value_text": f"{ch['jul2025']['pct']}%, {people(lost)} fewer"}

    out["chart_people_lost"] = {}
    T = out["trifecta_2026"]
    rows = [bar("Republican trifecta states", T["Republican"], 1),
            bar("United States", out["us"], 0),
            bar("Divided states", T["Divided"], 1),
            bar("Democratic trifecta states*", T["Democratic"], 1),
            bar("New York City", out["nyc_otda"], 1)]
    OUT.write_text(json.dumps(out, indent=1))
    figures.hbar_png(
        IMG / "post8-enrollment-change.png", rows,
        suffix="%", direction="left",
        title="Change in people on SNAP, July 2025 to July 2026",
        subtitle="By party control of state government in 2026. *Not counting New York City.\n"
                 "Source: USDA; New York State OTDA; Ballotpedia.")
    print(f"wrote {IMG / 'post8-enrollment-change.png'}")


if __name__ == "__main__":
    main()
