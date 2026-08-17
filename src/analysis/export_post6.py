"""Assemble reports/post6/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post6.json"
DIR = ROOT / "reports" / "post6"
IMG = DIR / "images"

SLOT = {"fuel-forward chains": 1, "dollar stores": 2, "other convenience chains": 3,
        "fuel-branded single sites": 4, "unbranded convenience": 5}
ORDER = list(SLOT)


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        # Keyed by slug rather than list position. With a list, a duplicated
        # number or an inserted figure shifted every later figs[i] lookup by one
        # and silently printed the wrong chart under the text — which is exactly
        # what happened in this series.
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    surv = {r["segment"]: r for r in d["survival"]}
    sc, fm, cens, cbp = d["stock_change"], d["fuel_margin"], d["census"], d["cbp"]
    ff, do = surv["fuel-forward chains"], surv["dollar stores"]
    mu = fm["companies"]["Murphy USA"]
    cy = fm["companies"]["Casey's General Stores"]
    mac = fm["macro"]
    ks = sorted(int(k) for k in d["shares"])
    sh0, sh1 = d["shares"][str(ks[0])], d["shares"][str(ks[-1])]
    pres = {r["label"]: r for r in d["post5"]["presence"]}["convenience store"]
    myrs = sorted(set(map(int, mu["series"])) & set(map(int, cy["series"])))

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{ff['rate']}%",
          "label": f"of fuel-forward chain stores authorized {d['cohort'][0]}-{d['cohort'][1]} "
                   f"were still authorized in {d['cohort_end']}"},
         {"value": f"{do['rate']}%",
          "label": "for dollar stores over the same window, reached a different way"},
         {"value": f"+{round(mu['pct'])}%",
          "label": "growth in Murphy USA's fuel margin per gallon, 2015-2019 vs 2021-2025"}])

    fig(1, "survival-by-segment",
        f"Share of stores first authorized {d['cohort'][0]}-{d['cohort'][1]} that were still "
        f"authorized on 31 December {d['cohort_end']}.",
        figures.hbar_png,
        [{"label": k, "value": surv[k]["rate"],
          "slot": SLOT[k] if k in ("fuel-forward chains", "dollar stores") else 0}
         for k in ORDER], suffix="%", title="Chains keep their stores. Single sites do not.",
        subtitle="share of 2008-2012 stores still authorized in 2025")

    fig(2, "stock-by-segment",
        "Stores authorized on 31 December of each year, by segment.",
        figures.line_png, d["stock"]["years"],
        [{"name": k, "values": d["stock"]["series"][k], "slot": SLOT[k]} for k in ORDER],
        ylabel="stores authorized on 31 December", title="Chain gas stations tripled. Everyone else flattened.")

    fig(3, "survival-table",
        "Survival and growth by segment, with the counts each rate is built from.",
        figures.table_png,
        ["Segment", "Still active after 13 yrs", "Count", "Growth 2006-2025"],
        [[k, f"{surv[k]['rate']}%", f"{surv[k]['survived']:,} of {surv[k]['cohort']:,}",
          f"{sc[k]['multiple']}x"] for k in ORDER], highlight_row=0,
        title="Who stays, and who grows, by operator")

    fig(4, "fuel-margin",
        "Retail fuel margin in cents per gallon, from each company's annual 10-K filings.",
        figures.line_png, myrs,
        [{"name": "Murphy USA", "values": [mu["series"][str(y)] for y in myrs], "slot": 1},
         {"name": "Casey's", "values": [cy["series"][str(y)] for y in myrs], "slot": 3}],
        ylabel="cents earned per gallon sold", title="Fuel profit doubled after 2020 and stayed there")

    fig(5, "category-share",
        "Share of all SNAP-authorized convenience stores, by segment.",
        figures.hbar_png, [
            {"label": f"fuel-forward chains, {ks[0]}", "value": sh0["fuel-forward chains"],
             "slot": 0},
            {"label": f"fuel-forward chains, {ks[-1]}", "value": sh1["fuel-forward chains"],
             "slot": 1},
            {"label": f"no chain brand, {ks[0]}", "value": sh0["unbranded convenience"],
             "slot": 0},
            {"label": f"no chain brand, {ks[-1]}", "value": sh1["unbranded convenience"],
             "slot": 5}], suffix="%", title="Chains took a bigger slice of the same category",
        subtitle="share of all SNAP convenience stores")

    fig(6, "census-vs-snap",
        "Census business locations against SNAP authorizations without a chain brand.",
        figures.table_png,
        ["Year", "Census stores", "Under 5 staff", "SNAP, unbranded"],
        [[str(y), f"{cbp['cbp'][str(y)]['establishments']:,}",
          f"{cbp['cbp'][str(y)]['under_5_emp']:,}", f"{cbp['snap_unbranded'][str(y)]:,}"]
         for y in cbp["years"]], title="Corner stores grew while SNAP sign-ups fell",
        subtitle="convenience establishments, United States")

    fig(7, "chain-census",
        "SNAP authorizations against each company's own reported store count.",
        figures.table_png, ["Chain", "SNAP-authorized 2025", "Reported stores", "Ratio"],
        [[c["chain"], f"{c['authorized']:,}", f"{c['reported']:,}", f"{c['ratio']}"]
         for c in cens], title="For these chains, an authorization really is a store")

    md = f"""# The gas station is the other store that stayed

*SNAP-authorized retailers, 2006–2025. EIA weekly gasoline prices. Retail fuel margins from Murphy USA
and Casey's 10-K filings.*

**{ff['rate']}%** of fuel-forward chain stores authorized in {d['cohort'][0]}–{d['cohort'][1]} were
still authorized in {d['cohort_end']}.
**{do['rate']}%** for dollar stores over the same window — the same rate, reached a different way.
**+{round(mu['pct'])}%** growth in Murphy USA's fuel margin per gallon, comparing 2015–2019 with
2021–2025.

![Headline figures](images/00-key-figures.png)

---

The last piece in this series ended on one idea. In small markets, the stores that survive are the ones
that are cheap to run. It named dollar stores as the format that fits.

That answer was half right. There is a second format that fits just as well, and this data shows it
plainly once you stop treating it as one thing.

## "Convenience store" is four different businesses

USDA files every corner store, truck stop and gas station under a single store type. That one label
hides everything interesting. Split it by who runs the store and the pieces move in different
directions.

The test is simple. Take every store first authorized between {d['cohort'][0]} and {d['cohort'][1]}.
Then ask how many were still authorized in {d['cohort_end']}, thirteen years later. Dollar stores are
included as a yardstick, because post 1 already measured them.

![{figs["survival-table"]['caption']}](images/{figs["survival-table"]['file']})

The survival column on its own, so the gap is easier to see:

![{figs["survival-by-segment"]['caption']}](images/{figs["survival-by-segment"]['file']})

**Fuel-forward chains stay at {ff['rate']}%. Dollar stores stay at {do['rate']}%.** That gap is
{abs(d['survival_gap_pp'])} of a percentage point. These two formats look nothing alike, but they hold
onto their locations equally well.

Now look down the table. Other chains stay at {surv['other convenience chains']['rate']}%. Single sites
flying an oil company's sign stay at {surv['fuel-branded single sites']['rate']}%. Stores with no chain
behind them at all stay at {surv['unbranded convenience']['rate']}%.

The thing that predicts survival is not the format. It is whether a company with scale is behind the
store.

![{figs["stock-by-segment"]['caption']}](images/{figs["stock-by-segment"]['file']})

Chains also grew. Fuel-forward chains went from {sc['fuel-forward chains']['y2006']:,} stores in 2006 to
{sc['fuel-forward chains']['y2025']:,} in 2025 — **{sc['fuel-forward chains']['multiple']} times** as
many. Their share of the whole convenience category went from {sh0['fuel-forward chains']}% to
{sh1['fuel-forward chains']}%.

![{figs["category-share"]['caption']}](images/{figs["category-share"]['file']})

## Why fuel changed the math

Dollar stores and gas stations both run on low fixed costs. But after 2020 the gas station got something
the dollar store did not. Selling fuel became much more profitable.

This is measurable two ways, and both point the same direction.

**The first way is national prices.** Take what drivers pay at the pump and subtract the wholesale price
of gasoline at the New York Harbor trading hub. The gap covers taxes, shipping and the store's own cut.
Comparing 2015–2019 with 2021–2025, that gap widened by **{mac['delta_cpg']:.1f} cents a gallon**.

**The second way is company filings.** Two chains in this data are public companies and report their
fuel margin in cents per gallon. Their own numbers are far more direct.

![{figs["fuel-margin"]['caption']}](images/{figs["fuel-margin"]['file']})

Murphy USA earned {mu['pre_mean']} cents a gallon before 2020. It now earns {mu['post_mean']}. Casey's
went from {cy['pre_mean']} cents to {cy['post_mean']}. **Both roughly doubled.** Before 2020 Murphy's
margin sat between 11.6 and 14.7 cents every single year. Since 2021 it has not dropped below 21.9. The
two ranges do not overlap at all.

Here is what makes these two measures worth showing together. The national gap widened by
{mac['delta_cpg']:.1f} cents. Murphy's own margin grew by {mu['delta_cpg']:.1f} cents. Those are almost
the same number.

That tells us where the money went. Taxes and shipping did not absorb the increase. **Nearly all of it
became store profit.** It also explains why the national gap only rose {mac['pct']:.0f}% while margins
doubled: most of that gap is fixed tax the retailer never touches, so a small percentage move in the
total is a large move in the part the store keeps.

## A check before going further

These records count SNAP authorizations, not buildings. That difference matters, and this series does
not paper over it.

For chains it can be checked directly. Murphy USA and Casey's both publish store counts in their
filings, and both appear in this data.

![{figs["chain-census"]['caption']}](images/{figs["chain-census"]['file']})

Around nine in ten of their stores take EBT. Close enough that talking about "stores" is fair for these
operators. For a single gas station with no parent company, no such check exists.

## The single sites did not close. They changed hands.

It would be easy to read {surv['unbranded convenience']['rate']}% survival as a wave of closures. That
reading is wrong, and it is worth correcting carefully.

The Census Bureau counts business locations whether or not they accept EBT. If corner stores were
closing, that count would fall.

![{figs["census-vs-snap"]['caption']}](images/{figs["census-vs-snap"]['file']})

It did the opposite. Between {cbp['base_year']} and {cbp['last_year']}, convenience establishments rose
**{cbp['cbp_pct']:+.1f}%**. The smallest ones — under five employees — rose {cbp['cbp_under5_pct']:+.1f}%.
Over the same years SNAP authorizations without a chain brand moved {cbp['snap_pct']:+.1f}%.

So the corner store is not vanishing. The *specific business* in that building keeps changing. A store
is sold, renamed, re-registered, and a new record number appears. The storefront stays; the operator
turns over.

That is the real contrast. **Chains accumulate stores. Single sites cycle through owners.** Over twenty
years a chain compounds what it built. An independent operator mostly hands the keys to the next person.

## What this means for food access

Post 5 looked at {d['post5']['groups']['lost']:,} ZIP codes that lost their last chain pharmacy. A
convenience store is present in {pres['lost_pct']}% of them. It is also in {pres['kept_pct']}% of the
comparison group, so this is not something unusual about those places. It is nearly everywhere.

That is the point. For a household using SNAP in a small town, the realistic options are narrowing to
two: a dollar store, or a gas station. Both are now run largely by companies with scale. Both are
profitable at a size no supermarket can match.

Neither one is trying to be a grocery store. A gas station's food is built for a driver buying one
thing — packaged, quick, priced for convenience. When it becomes the closest food retailer to a home,
that assortment is doing a job it was never designed for.

There is no villain in this. Fuel margins widened because of how fuel markets work, not because anyone
targeted small towns. Chains expanded because expanding is what a business with capital does. The
outcome was assembled out of ordinary decisions, which is exactly what makes it hard to reverse.

## Limits

**The fuel-forward list is a judgement call.** Twenty-four chains are named as fuel-forward because they
run fuel pumps at essentially all their US locations. The list is printed in the code so it can be
checked. 7-Eleven is deliberately left out: it is the largest convenience brand in this data by a wide
margin and is mixed on fuel, so including it would let one brand carry a claim about fuel economics.
Excluding it makes the chain figures smaller, not larger.

**Margin is not profit.** Fuel margin is revenue minus the cost of the fuel. It does not subtract
labour, rent, card fees or the cost of the pumps. A doubling in margin is not a doubling in earnings. It
does mean the fuel side of the store got substantially better at covering its own fixed costs.

**Two companies are not an industry.** Murphy USA and Casey's are the operators in this data that
publish the number. Circle K's parent files in Canada rather than with the SEC and is not included. The
national price gap is what carries the claim beyond these two, and it agrees with them.

**Growth in the single-site segments is ambiguous.** Rising authorization counts can mean more stores or
wider EBT take-up among stores that already existed. The Census comparison is what separates those, and
it is only available for the category as a whole, not for the segments.

Nothing here measures what is on the shelves. A gas station and a supermarket each count as one record.
What can actually be bought with an EBT card in these places needs a different source.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. EIA weekly US retail regular
gasoline (EMM_EPMR_PTE_NUS_DPG) and NY Harbor conventional regular spot (EER_EPMRU_PF4_Y35NY_DPG).
Murphy USA (CIK 1573516) and Casey's General Stores (CIK 726958) 10-K filings via SEC EDGAR. Census
County Business Patterns, NAICS {'/'.join(cbp['cbp'][str(cbp['years'][0])]['naics'])}. A store counts as
active in a year if an authorization covered 31 December. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post6.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post6.html", DIR / "post6-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post6.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
