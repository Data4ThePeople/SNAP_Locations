"""Assemble reports/post6/ — markdown text, PNG figures, and the HTML archive.

Four figures, matching build_post6.py. See that module's docstring for why the
segments are named for who runs the store.
"""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post6.json"
DIR = ROOT / "reports" / "post6"
IMG = DIR / "images"

SLOT = {"chains that sell fuel": 1, "dollar stores": 2, "other chains": 3,
        "single-owner stores": 5}
ORDER = list(SLOT)


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    surv = {r["segment"]: r for r in d["survival"]}
    sc, cbp, fm = d["stock_change"], d["cbp"], d["fuel_margin"]
    _f = sc["chains that sell fuel"]
    fuel_pct = round(100 * (_f["y2025"] / _f["y2006"] - 1))
    ch, so = surv["chains that sell fuel"], surv["single-owner stores"]
    mu = fm["companies"]["Murphy USA"]
    cy = fm["companies"]["Casey's General Stores"]
    mac = fm["macro"]
    ks = sorted(int(k) for k in d["shares"])
    sh0, sh1 = d["shares"][str(ks[0])], d["shares"][str(ks[-1])]
    conv_total = d["convenience_total"]
    # Convenience stores active at the end of 2025: the three convenience
    # segments, leaving out the dollar stores drawn alongside them.
    conv25 = sum(d["stock"]["series"][k][-1] for k in
                 ("chains that sell fuel", "other chains", "single-owner stores"))
    myrs = sorted(set(map(int, mu["series"])) & set(map(int, cy["series"])))

    # Percentages, not just multiples: 47,761 -> 76,496 is +60%, which is not
    # "barely moving" however small it looks beside the chains.
    pct = lambda k: 100 * (sc[k]["y2025"] / sc[k]["y2006"] - 1)

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{fuel_pct:+}%",
          "label": f"change in chains that sell fuel since {d['stock']['years'][0]}"},
         {"value": f"{ch['rate']}%",
          "label": f"of their 2008-2012 stores are still authorized. For single-owner "
                   f"stores it is {so['rate']}%"},
         {"value": f"+{round(mu['pct'])}%",
          "label": "growth in Murphy USA's fuel margin per gallon after 2020"}])

    # Indexed to 2006 = 100: the raw counts only show that single-owner stores
    # are the biggest group, which buries the growth comparison the section is
    # actually making.
    idx = {k: [round(100 * v / d["stock"]["series"][k][0], 1)
               for v in d["stock"]["series"][k]] for k in ORDER}
    fig(1, "growth-by-owner",
        "Stores authorized on 31 December of each year, indexed to 100 in 2006, by who runs "
        "the store. Dollar stores are shown as the benchmark.",
        figures.line_png, d["stock"]["years"],
        [{"name": k, "values": idx[k], "slot": SLOT[k]} for k in ORDER],
        ylabel="authorized stores, indexed to 2006 = 100",
        title="Only the fuel chains kept pace with the dollar store")

    fig(2, "fuel-margin",
        "Retail fuel margin in cents per gallon, from each company's annual 10-K filings.",
        figures.line_png, myrs,
        [{"name": "Murphy USA", "values": [mu["series"][str(y)] for y in myrs], "slot": 1},
         {"name": "Casey's", "values": [cy["series"][str(y)] for y in myrs], "slot": 3}],
        ylabel="cents earned per gallon sold",
        title="Fuel profit doubled after 2020 and stayed there")

    fig(3, "survival-by-owner",
        "Share of stores first authorized 2008–2012 that were still authorized on "
        "31 December 2025.",
        figures.hbar_png,
        [{"label": k, "value": surv[k]["rate"],
          "slot": SLOT[k] if k in ("chains that sell fuel", "single-owner stores") else 0}
         for k in ORDER], suffix="%",
        title="A chain store stays. A single-owner store usually does not.",
        subtitle="share of 2008-2012 stores still authorized in 2025")

    md = f"""# Convenience stores and the advantage hiding in plain sight

*SNAP-authorized retailers, 2006–2025. EIA weekly gasoline prices. Retail fuel margins from Murphy USA
and Casey's 10-K filings. {conv_total:,} convenience stores in the file.*

**{fuel_pct:+}%** change in chains that sell fuel since {d['stock']['years'][0]}. **{ch['rate']}%** of their 2008–2012 stores are still authorized. For single-owner stores it is {so['rate']}%. **+{round(mu['pct'])}%** growth in Murphy USA's fuel margin per gallon after 2020.

![Headline figures](images/00-key-figures.png)

---

*Anytime we refer to "growth" in this post, it is growth in SNAP-authorized stores, not growth in
store counts. See the Limits section for more on this.*

Yesterday ended on a puzzle. Dollar stores thrived because they are chains. Convenience stores are
the opposite: only about a third belong to a chain, and there are more of them than any other kind
of SNAP retailer. If you read the last two days of analysis, you may have expected them to go the
way of the small grocer.

They did not. But the reason has less to do with ownership, and more to do with an advantage few
other store formats had.

## One store format masks different growth trends

The convenience store format is enormous. There are {conv25:,} stores authorized to accept SNAP
benefits today, far surpassing any other store format. That makes sense: it is not uncommon to see
a gas station at every major intersection.

But we cannot analyze the convenience store format as one thing, because within it live very
different kinds of stores, and they grew at very different rates. There are chains that sell fuel —
Wawa, Sheetz, Casey's, QuikTrip and the like — which surged **{pct('chains that sell fuel'):.0f}%**
between 2006 and 2025. There are chains that are not built around fuel — 7-Eleven, above all —
which grew {pct('other chains'):.0f}%. And there are single-owner stores, which make up most of the
category and grew {pct('single-owner stores'):.0f}%.

The chart below shows the growth of each, compared with the dollar store, indexed to 100 in 2006.
Only one comes close to matching the dollar store: the chains that sell fuel.

![{figs["growth-by-owner"]['caption']}](images/{figs["growth-by-owner"]['file']})

The fuel chains went from {sh0['chains that sell fuel']}% of the category to
{sh1['chains that sell fuel']}%.

## The fuel advantage

There is something else you need to know about this format, and it has nothing to do with what is
on the shelves. After
2020, selling fuel became far more profitable.

Two of these chains are public companies and report their fuel margin in cents per gallon.

![{figs["fuel-margin"]['caption']}](images/{figs["fuel-margin"]['file']})

Murphy USA earned {mu['pre_mean']} cents a gallon before 2020 and {mu['post_mean']} after. Casey's went
from {cy['pre_mean']} to {cy['post_mean']}. **Both roughly doubled.** Before 2020 Murphy's margin never
left the 11.6 to 14.7 cent band. Since 2021 it has never dropped below 21.9. The two ranges do not
overlap at all.

A check, because a doubling is a big claim. Take what drivers pay at the pump and subtract the wholesale
price at the New York Harbor trading hub. That gap widened by **{mac['delta_cpg']:.1f} cents** between
2015–2019 and 2021–2025. Murphy's own margin grew {mu['delta_cpg']:.1f} cents. Those are nearly the same
number, which tells you where the money most likely went: taxes and shipping did not absorb it. **It
appears that almost all of it became store profit.**

Why it happened is worth pondering. Note that this is our hypothesis. But we have poked at it using
the data, and it seems to hold. It also jibes with our lived experience, which should not be
discounted.

When COVID stopped people driving, fuel volume and store traffic fell together — Casey's reported same-store gallons down 8.1% and inside customer traffic down 8.7%. With fewer customers coming through, the fuel had to earn more from each one. Margins rose.

What nobody expected is that fuel margins stayed there. Customers came back. Margins did not fall. Casey's now tells its investors it expects them to “remain elevated from historical levels for the foreseeable future”. Murphy is still selling about 5% fewer gallons per store than in 2019 — and earning twice as much on each one.

So, post-COVID fuel margins are the advantage we have been teasing throughout this post. File that
knowledge away as we turn back to the topic at hand — SNAP authorizations.

## The format thrives, but are all owners realizing the benefit?

Everything so far has been about the chains. What about the much larger group of single-owner stores?

On the surface they look fine. They added about {sc['single-owner stores']['y2025'] - sc['single-owner stores']['y2006']:,} authorizations over the same nineteen years, growth of {pct('single-owner stores'):.0f}%. Slower than the chains, but a category adding that many stores is not a category in trouble.

The difference only shows up when you stop counting stores and start asking whether they are the *same* stores.

![{figs["survival-by-owner"]['caption']}](images/{figs["survival-by-owner"]['file']})

Take every store authorized between 2008 and 2012 and ask how many are still authorized thirteen years
later. For chains that sell fuel it is **{ch['rate']}%** — the same rate as dollar stores, which is the
benchmark from yesterday. For single-owner stores it is **{so['rate']}%**.

It would be easy to read that as a wave of closures. It is not, and the check matters. The Census Bureau
counts business locations whether or not they take EBT. Between {cbp['base_year']} and
{cbp['last_year']} convenience establishments **rose {cbp['cbp_pct']:+.1f}%**. The under-ten-staff
slice — the cut we used for grocers — slipped {abs(cbp['cbp_under10_pct']):.1f}%, while the very
smallest stores, under five staff, **rose {cbp['cbp_under5_pct']:+.1f}%**.

So the corner store is not disappearing. What is more likely happening is that the *specific business or owner* in the building keeps changing. A store
is sold, renamed, re-registered, and a new record appears. The storefront stays. The owner turns over.

**That is the difference between a chain and a single owner.** A chain compounds: whatever it built
twenty years ago, it largely still has, and it adds to it. A single-owner site is likely churning —
handing the keys to the next person. Same storefront, same shelves, new name on the paperwork — and in this data, a new record
starting from scratch.

## What it adds up to

Drilling into this format does not give a new answer. It reinforces the same takeaway.

Small grocers are disadvantaged because they are small and alone. Dollar stores are advantaged because they are small and part of a massive chain. Convenience stores split along exactly that line: the fuel-selling chains kept **{ch['rate']}%** of their stores over thirteen years, the single owners only kept **{so['rate']}%**.

So think of that Wawa or Sheetz going up on the corner near you as something close to a dollar store with one extra advantage: a fuel margin that doubled after 2020 and never came back. Same small footprint, same chain economics, plus a second profit stream that got far more profitable.

For a household with an EBT card, the practical result is the same either way. In a small town, the
gravitational pull of grocery economics is leaving them two options: a dollar store and a gas
station. Both are now cheap to run, both can be profitable at smaller volume. **Unfortunately,
neither was designed to sell the week of groceries assumed by the government's Thrifty Food Plan.**

But that is today. The million-dollar question is what happens to SNAP authorization for these fuel
convenience stores when the new stocking rule takes effect in a few short months, raising the
number of staple items required on the shelf from 36 to 84. We will explore this in depth in the
closing post of this series, but for now we can see a few options — and they will not fall evenly.
A single-owner station pays the cost alone; a chain writes one shelf plan for thousands of stores.
So:

1. They can drop SNAP, further limiting food access for our nation's most vulnerable population.
2. They can comply and eat the cost, sacrificing profits (not likely).
3. Or they can comply and pass the cost on at the pump — where margins have already doubled once
   this decade.

Note that if we head down path 3 — which any profit-maximizing business would likely choose — they
will be doing it in the middle of what is, in our view, a fuel crisis of a magnitude we have not
seen since 1973.

Another lesson in the law of unintended consequences.

**Next week: we turn our attention to the larger store formats.**

## Limits

**An oil brand on the canopy is not an owner.** A "Shell" or "BP" station is almost never owned by Shell
or BP — it is somebody's own business with a fuel supply contract. So those stores count here as
single-owner stores. Broken out separately they survive at 20.6% against 13.5% for stores with no brand
at all: a real difference, too small to change the picture.

**The list of fuel chains is a judgment call.** Twenty-four operators are named because they run fuel
pumps at essentially all their US sites. The list is in the code. 7-Eleven is deliberately left out — it
is the largest convenience brand here by a wide margin and is mixed on fuel, so including it would let
one brand carry a claim about fuel economics.

**Margin is not profit.** Fuel margin is revenue minus the cost of the fuel. It does not subtract labor,
rent, card fees or the pumps themselves.

**Growth in the single-owner segment is ambiguous.** A rising count can mean more stores or wider EBT
take-up among stores that already existed. The census comparison is what separates those, and it is only
available for the category as a whole.

Two companies are not an industry. Murphy USA and Casey's are the operators here that publish a fuel
margin. Circle K's parent files in Canada rather than with the SEC. The national price gap is what
carries the claim beyond these two, and it agrees with them.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. EIA weekly US retail regular gasoline
(EMM_EPMR_PTE_NUS_DPG) and NY Harbor conventional regular spot (EER_EPMRU_PF4_Y35NY_DPG). Murphy USA
(CIK 1573516) and Casey's General Stores (CIK 726958) 10-K filings via SEC EDGAR. Census County Business
Patterns, NAICS {'/'.join(cbp['cbp'][str(cbp['years'][0])]['naics'])}. A store counts as active in a year
if an authorization covered 31 December. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post6.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post6.html", DIR / "post6-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post6.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
