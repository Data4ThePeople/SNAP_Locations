"""Did fuel retailing get more profitable after 2020, and by how much?

Post 6 argues that fuel/convenience chains endure in thin markets for the same
reason dollar stores do — low fixed cost per site — plus one thing dollar stores
do not have: a fuel margin that widened after 2020 and never came back.

That claim needs evidence outside the SNAP panel, so this pulls two independent
sources that can corroborate each other:

  1. MACRO. EIA weekly US retail regular gasoline minus NY Harbor spot. The gap
     covers taxes, distribution, freight and retail margin, so it is an upper
     bound on the retailer's cut, not the cut itself. Both series are keyless
     XLS. They are stamped on different weekdays, so they are resampled to
     monthly means before differencing — an exact-date join is empty.

  2. MICRO. Retail fuel margin in cents per gallon as reported by two SEC
     filers, from the 10-Ks themselves. This is the retailer's actual cut.
     Murphy USA (CIK 1573516) and Casey's General Stores (CIK 726958).

The two sources are wired to check each other: if the macro spread widened by
about the same number of cents as the filers' own margins, then essentially all
of the spread expansion accrued to retailers rather than to taxes or midstream,
and the macro and micro stories are the same story. If they disagree, the macro
number is measuring something else and should not be described as margin.

Fuel margin is a non-GAAP operating metric. It is NOT tagged in XBRL — the
companyfacts API carries no fuel, margin or gallon concept for either company —
so it has to come out of the MD&A tables as text. Two hazards follow, and both
are tested rather than assumed:

  - Definitions drift between filing vintages. Casey's parenthetical changes
    from "excluding depreciation and amortization and credit card fees" to
    "excluding depreciation and amortization" at the FY2023 filing.
  - Extraction by regex can silently grab the wrong row.

Each 10-K restates two or three prior years, so consecutive filings overlap.
Those overlaps are the test: a year reported identically by two different
filings is both correctly extracted and comparably defined. A year whose value
changes between vintages was restated, and the series cannot be pooled across
that break. check_overlaps() enforces this.

Fiscal years: Murphy USA ends 31 December, so its labels are calendar years.
Casey's ends 30 April, so FY2020 runs May 2019 to April 2020 and contains the
March-April 2020 collapse. FY2020 is therefore excluded from the pre-COVID mean
as contaminated, and FY2021 (May 2020 to April 2021) is the first post year.
"""
import html
import io
import json
import re
import urllib.request

from config import RAW

OUT = None  # set in main() to avoid importing ROOT at module load for tests
UA = {"User-Agent": "Data4ThePeople SNAP research eric@asaltollc.com"}
CACHE = RAW / "fuel_margin_cache.json"

PRE = (2015, 2019)    # calendar pre-COVID window
POST = (2021, 2025)   # calendar post-COVID window

FAILURES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def fetch(url, timeout=240):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- macro (EIA)

EIA_RETAIL = "https://www.eia.gov/dnav/pet/hist_xls/EMM_EPMR_PTE_NUS_DPGw.xls"
EIA_SPOT = "https://www.eia.gov/dnav/pet/hist_xls/EER_EPMRU_PF4_Y35NY_DPGw.xls"


def eia_series(url):
    """Weekly EIA price series as a monthly-mean pandas Series."""
    import pandas as pd
    df = pd.ExcelFile(io.BytesIO(fetch(url))).parse("Data 1", skiprows=2)
    df.columns = ["date", "value"]
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["value"].astype(float).resample("MS").mean()


def macro():
    import pandas as pd
    retail, spot = eia_series(EIA_RETAIL), eia_series(EIA_SPOT)
    j = pd.concat({"retail": retail, "spot": spot}, axis=1).dropna()
    j["spread"] = j.retail - j.spot
    ann = j.spread.groupby(j.index.year).mean()
    pre = j.loc[f"{PRE[0]}-01-01":f"{PRE[1]}-12-31"]
    post = j.loc[f"{POST[0]}-01-01":f"{POST[1]}-12-31"]
    return {
        "months": int(len(j)),
        "annual_spread": {int(y): round(v, 4) for y, v in ann.items() if y >= 2010},
        "pre_window": list(PRE), "post_window": list(POST),
        "pre_retail": round(pre.retail.mean(), 4), "pre_spot": round(pre.spot.mean(), 4),
        "post_retail": round(post.retail.mean(), 4), "post_spot": round(post.spot.mean(), 4),
        "pre_spread": round(pre.spread.mean(), 4),
        "post_spread": round(post.spread.mean(), 4),
        "delta_cpg": round(100 * (post.spread.mean() - pre.spread.mean()), 2),
        "pct": round(100 * (post.spread.mean() / pre.spread.mean() - 1), 1),
    }


# ------------------------------------------------------------- micro (EDGAR)

def filings(cik, form="10-K"):
    """[(report_date, accession, primary_doc)] newest first, HTML primaries only."""
    sub = json.loads(fetch(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    r = sub["filings"]["recent"]
    return [(r["reportDate"][i], r["accessionNumber"][i], r["primaryDocument"][i])
            for i, f in enumerate(r["form"])
            if f == form and r["primaryDocument"][i].endswith(".htm")]


def filing_text(cik, acc, doc):
    """Filing HTML flattened to whitespace-normalised text, tags become spaces
    so adjacent table cells stay separated rather than concatenating."""
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"
    t = html.unescape(re.sub(r"<[^>]+>", " ", fetch(url).decode("utf-8", "replace")))
    return re.sub(r"[\xa0\s]+", " ", t)


# Anchors only. The label must be followed immediately by its unit so that MD&A
# prose ("Retail fuel margin decreased in 2019 to 13.8 cpg") cannot match — only
# the key-metrics table row can.
#
# Values are then taken from a window after the anchor, requiring a decimal
# point. That matters: footnote markers render as bare integers, either "(1)" or
# a naked "1", and a pattern that accepts integers will eat the leading digit of
# the first value instead — turning 22.9 into 2.9 and 13.8 into 3.8. Every
# reported figure here has a decimal, so requiring one separates data from
# footnotes without having to model every way a footnote is typeset.
MURPHY_ROW = re.compile(r"Retail fuel margin(?: per gallon)?\s*\(cpg\)", re.I)

# Casey's parenthetical is captured because it is the metric's definition, and
# it drifts between vintages ("...and credit card fees" is dropped at FY2023).
CASEY_ROW = re.compile(
    r"Average revenue less cost of goods sold per gallon\s*(\([^)]*\))?", re.I)

VALUE = re.compile(r"\d+\.\d+")
WINDOW = 110   # chars after the anchor; comfortably covers a 5-column row
NVALUES = 3    # every filing restates at least three years


def row_values(text, pattern):
    """(definition, [values]) for the first anchor with >= NVALUES decimals."""
    for m in pattern.finditer(text):
        vals = VALUE.findall(text[m.end():m.end() + WINDOW])
        if len(vals) >= NVALUES:
            definition = (m.group(1) or "") if m.re.groups else ""
            return definition.strip(), [float(v) for v in vals[:NVALUES]]
    return None, []


def scrape(cik, name, pattern, fy_end_month, cache):
    """Per-filing {fiscal_year: value} plus the definition string, newest first.

    Returns {report_year: {"values": {fy: v}, "definition": str}} so that the
    same fiscal year appearing under two filings can be compared.
    """
    out = {}
    for rep, acc, doc in filings(cik):
        ry = int(rep[:4])
        key = f"{name}:{acc}"
        if key in cache:
            out[ry] = cache[key]
            continue
        try:
            t = filing_text(cik, acc, doc)
        except Exception as e:
            print(f"    {name} {rep}: {type(e).__name__} — skipped")
            continue
        definition, vals = row_values(t, pattern)
        if not vals:
            continue
        # Columns run newest first: report FY, then FY-1, FY-2, ...
        rec = {"values": {str(ry - i): v for i, v in enumerate(vals)},
               "definition": (definition or "").strip(),
               "accession": acc}
        cache[key] = rec
        out[ry] = rec
    return out


def check_overlaps(name, byfiling):
    """A fiscal year reported by two filings must carry the same value.

    This is the whole basis for trusting the extraction and for pooling years
    across a definition change: matching values mean the metric was not
    restated, so the label drifted but the series did not.
    """
    seen, conflicts, confirmed = {}, [], 0
    for ry in sorted(byfiling, reverse=True):
        for fy, v in byfiling[ry]["values"].items():
            if fy in seen:
                if abs(seen[fy][0] - v) > 0.005:
                    conflicts.append((fy, seen[fy], (v, ry)))
                else:
                    confirmed += 1
            else:
                seen[fy] = (v, ry)
    check(f"{name}: no fiscal year restated across filings",
          not conflicts,
          f"{confirmed} year-values confirmed by a second filing"
          + (f"; conflicts {conflicts}" if conflicts else ""))
    defs = sorted({b["definition"] for b in byfiling.values() if b["definition"]})
    return {int(k): v for k, (v, _) in seen.items()}, defs, confirmed


def window_mean(series, lo, hi):
    vals = [v for y, v in series.items() if lo <= y <= hi]
    return (sum(vals) / len(vals), len(vals)) if vals else (0.0, 0)


def main():
    from config import ROOT
    out_dir = ROOT / "reports" / "data"
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    print("1. Macro: EIA retail regular minus NY Harbor spot, monthly means")
    mac = macro()
    print(f"   {mac['months']:,} months aligned")
    print(f"   {PRE[0]}-{PRE[1]}  retail ${mac['pre_retail']:.2f}  spot ${mac['pre_spot']:.2f}"
          f"  spread ${mac['pre_spread']:.3f}")
    print(f"   {POST[0]}-{POST[1]}  retail ${mac['post_retail']:.2f}  spot ${mac['post_spot']:.2f}"
          f"  spread ${mac['post_spread']:.3f}")
    print(f"   change {mac['delta_cpg']:+.1f} cpg ({mac['pct']:+.0f}%)")
    check("macro spread widened", mac["delta_cpg"] > 0, f"{mac['delta_cpg']:+.1f} cpg")
    check("every year 2021-2025 above every year 2015-2019",
          min(v for y, v in mac["annual_spread"].items() if POST[0] <= y <= POST[1])
          > max(v for y, v in mac["annual_spread"].items() if PRE[0] <= y <= PRE[1]),
          "the step change is not driven by one outlier year")

    print("\n2. Micro: retail fuel margin (cpg) from 10-K MD&A")
    print("   Murphy USA")
    mu_f = scrape(1573516, "murphy", MURPHY_ROW, 12, cache)
    mu, mu_defs, mu_conf = check_overlaps("Murphy USA", mu_f)
    print("   Casey's General Stores")
    cy_f = scrape(726958, "casey", CASEY_ROW, 4, cache)
    cy, cy_defs, cy_conf = check_overlaps("Casey's", cy_f)

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))

    # Casey's FY ends 30 April, so FY2020 spans the March-April 2020 collapse
    # and cannot sit in a pre-COVID mean. Its first clean post year is FY2021.
    cos = {
        "Murphy USA": {"series": mu, "definitions": mu_defs, "confirmed": mu_conf,
                       "fy_end": "12-31", "pre": PRE, "post": POST,
                       "excluded": []},
        "Casey's General Stores": {
            "series": cy, "definitions": cy_defs, "confirmed": cy_conf,
            "fy_end": "04-30", "pre": (2016, 2019), "post": (2021, 2026),
            "excluded": [2020]},
    }

    print(f"\n{'company':>26} | {'years':>22} | {'pre':>7} {'post':>7} {'delta':>8} {'pct':>7}")
    print("   " + "-" * 84)
    for name, c in cos.items():
        lo, hi = c["pre"]
        plo, phi = c["post"]
        pre_m, npre = window_mean(c["series"], lo, hi)
        post_m, npost = window_mean(c["series"], plo, phi)
        c.update(pre_mean=round(pre_m, 2), post_mean=round(post_m, 2),
                 n_pre=npre, n_post=npost,
                 delta_cpg=round(post_m - pre_m, 2),
                 pct=round(100 * (post_m / pre_m - 1), 1) if pre_m else 0.0)
        yrs = f"{min(c['series'])}-{max(c['series'])} ({len(c['series'])})"
        print(f"{name:>26} | {yrs:>22} | {pre_m:>7.2f} {post_m:>7.2f} "
              f"{c['delta_cpg']:>+8.2f} {c['pct']:>+6.0f}%")
        check(f"{name}: margin roughly doubled", c["pct"] > 50,
              f"{c['pre_mean']} -> {c['post_mean']} cpg")
        check(f"{name}: no post year below any pre year",
              min(v for y, v in c["series"].items() if plo <= y <= phi)
              > max(v for y, v in c["series"].items() if lo <= y <= hi))

    print("\n   full series, cents per gallon")
    allyrs = sorted(set(mu) | set(cy))
    for y in allyrs:
        a = f"{mu[y]:>6.1f}" if y in mu else "     ."
        b = f"{cy[y]:>6.2f}" if y in cy else "     ."
        tag = "  <- Casey's FY spans the 2020 collapse; excluded" if y == 2020 else ""
        print(f"     {y}  Murphy {a}   Casey's {b}{tag}")

    print("\n3. Do macro and micro agree?")
    mu_d = cos["Murphy USA"]["delta_cpg"]
    ratio = mu_d / mac["delta_cpg"] if mac["delta_cpg"] else 0
    print(f"   macro spread widened      {mac['delta_cpg']:+.1f} cpg")
    print(f"   Murphy's own margin grew  {mu_d:+.1f} cpg")
    print(f"   ratio {ratio:.2f}")
    agree = 0.7 <= ratio <= 1.3
    check("macro and micro agree within 30%", agree, f"ratio {ratio:.2f}")
    if agree:
        print("   -> Essentially the whole widening of the retail-minus-spot spread shows")
        print("      up as retailer margin. Taxes and midstream did not absorb it, and the")
        print("      macro series and the filings are describing the same shift.")

    res = {"macro": mac,
           "companies": {k: {kk: vv for kk, vv in v.items()} for k, v in cos.items()},
           "macro_micro_ratio": round(ratio, 3),
           "verdict": "margin_expanded_and_persisted" if agree else "sources_disagree"}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fuel_margin.json").write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {out_dir / 'fuel_margin.json'}")

    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("all checks passed")


if __name__ == "__main__":
    main()
