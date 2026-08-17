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
    ch, so = surv["chains that sell fuel"], surv["single-owner stores"]
    mu = fm["companies"]["Murphy USA"]
    cy = fm["companies"]["Casey's General Stores"]
    mac = fm["macro"]
    bg, top = d["brand_growth"], d["brand_growth"]["brands"][:10]
    ks = sorted(int(k) for k in d["shares"])
    sh0, sh1 = d["shares"][str(ks[0])], d["shares"][str(ks[-1])]
    conv_total = d["convenience_total"]
    myrs = sorted(set(map(int, mu["series"])) & set(map(int, cy["series"])))

    # Percentages, not just multiples: 47,761 -> 76,496 is +60%, which is not
    # "barely moving" however small it looks beside the chains.
    pct = lambda k: 100 * (sc[k]["y2025"] / sc[k]["y2006"] - 1)

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{sc['chains that sell fuel']['multiple']}x",
          "label": f"growth in chains that sell fuel since {d['stock']['years'][0]}"},
         {"value": f"{ch['rate']}%",
          "label": f"of their 2008-2012 stores are still authorized. For single-owner "
                   f"stores it is {so['rate']}%"},
         {"value": f"+{round(mu['pct'])}%",
          "label": "growth in Murphy USA's fuel margin per gallon after 2020"}])

    fig(1, "growth-by-owner",
        "Stores authorized on 31 December of each year, by who runs the store. Dollar stores "
        "are shown for scale.",
        figures.line_png, d["stock"]["years"],
        [{"name": k, "values": d["stock"]["series"][k], "slot": SLOT[k]} for k in ORDER],
        ylabel="stores authorized on 31 December",
        title="Both grew. Chains grew about four times faster.")

    fig(2, "chain-growth",
        "The ten largest fuel-selling convenience chains, and how fast each grew in a "
        "typical year.",
        figures.table_png, ["Chain", "Stores in 2025", "Typical year"],
        [[r["brand"], f"{r['y1']:,}", f"+{r['median_growth']:.1f}%"] for r in top],
        title="Every big fuel chain grew. None of them shrank.",
        subtitle="median year-over-year change in SNAP-authorized stores")

    fig(3, "fuel-margin",
        "Retail fuel margin in cents per gallon, from each company's annual 10-K filings.",
        figures.line_png, myrs,
        [{"name": "Murphy USA", "values": [mu["series"][str(y)] for y in myrs], "slot": 1},
         {"name": "Casey's", "values": [cy["series"][str(y)] for y in myrs], "slot": 3}],
        ylabel="cents earned per gallon sold",
        title="Fuel profit doubled after 2020 and stayed there")

    fig(4, "survival-by-owner",
        "Share of stores first authorized 2008–2012 that were still authorized on "
        "31 December 2025.",
        figures.hbar_png,
        [{"label": k, "value": surv[k]["rate"],
          "slot": SLOT[k] if k in ("chains that sell fuel", "single-owner stores") else 0}
         for k in ORDER], suffix="%",
        title="A chain store stays. A single-owner store usually does not.",
        subtitle="share of 2008-2012 stores still authorized in 2025")

    md = f"""# Convenience stores thrived. Most of their owners did not.

*SNAP-authorized retailers, 2006–2025. EIA weekly gasoline prices. Retail fuel margins from Murphy USA
and Casey's 10-K filings. {conv_total:,} convenience stores in the file.*

**{sc['chains that sell fuel']['multiple']}×** growth in chains that sell fuel since
{d['stock']['years'][0]}.
**{ch['rate']}%** of their 2008–2012 stores are still authorized. For single-owner stores it is
{so['rate']}%.
**+{round(mu['pct'])}%** growth in Murphy USA's fuel margin per gallon after 2020.

![Headline figures](images/00-key-figures.png)

---

Yesterday ended on a puzzle. Dollar stores thrived because they are chains — every one of them.
Convenience stores are the opposite: only one in five belongs to a chain, and there are more of them
than any other kind of SNAP retailer. By the logic of the dollar store, they should have gone the way of
the small grocer.

They did not. But the reason is not what the headline number suggests.

## Two very different things are called growth

Split the category by who runs the store and the pieces move apart. Chains that sell fuel — Wawa,
Sheetz, Casey's, QuikTrip and the like — went from {sc['chains that sell fuel']['y2006']:,} to
{sc['chains that sell fuel']['y2025']:,}, a rise of **{pct('chains that sell fuel'):.0f}%**. Stores with
a single owner went from {sc['single-owner stores']['y2006']:,} to
{sc['single-owner stores']['y2025']:,}, a rise of **{pct('single-owner stores'):.0f}%**.

Both grew. One grew about four times faster.

![{figs["growth-by-owner"]['caption']}](images/{figs["growth-by-owner"]['file']})

Chains went from {sh0['chains that sell fuel']}% of the category to {sh1['chains that sell fuel']}%.

Which chains? Mostly ones you would recognise. These are the ten largest that sell fuel, with how fast each grew in a typical year — a median, so one unusual year cannot flatter a chain.

![{figs["chain-growth"]['caption']}](images/{figs["chain-growth"]['file']})

Not one of them shrank. **Circle K** and **Speedway** grew around 2% a year, which on a base of thousands of stores is a great many stores. The regional names grew faster: **Love's** above 7%, **QuikTrip** and **Sheetz** above 5%, **Wawa** close behind. Compound 5% for nineteen years and you finish with two and a half times what you started with.

## Then the economics changed

Something else happened to this format, and it has nothing to do with what is on the shelves. After
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
number, which tells you where the money went: taxes and shipping did not absorb it. **Almost all of it
became store profit.**

Why it happened is worth a moment. When COVID stopped people driving, fuel volume and store traffic fell together — Casey's reported same-store gallons down 8.1% and inside customer traffic down 8.7%. With fewer customers coming through, the fuel had to earn more from each one. Margins rose.

What nobody expected is that they stayed there. Customers came back. Margins did not fall. Casey's now tells its investors it expects them to “remain elevated from historical levels for the foreseeable future”. Murphy is still selling about 5% fewer gallons per store than in 2019 — and earning twice as much on each one.

## The format thrives. The owners turn over.

Everything so far has been about the chains. What about the much larger group of single-owner stores?

On the surface they look fine. They added about {sc['single-owner stores']['y2025'] - sc['single-owner stores']['y2006']:,} storefronts over the same nineteen years, growth of {pct('single-owner stores'):.0f}%. Slower than the chains, but a category adding that many stores is not a category in trouble.

The difference only shows up when you stop counting stores and start asking whether they are the *same* stores.

![{figs["survival-by-owner"]['caption']}](images/{figs["survival-by-owner"]['file']})

Take every store authorized between 2008 and 2012 and ask how many are still authorized thirteen years
later. For chains that sell fuel it is **{ch['rate']}%** — the same rate as dollar stores, which is the
benchmark from two days ago. For single-owner stores it is **{so['rate']}%**.

It would be easy to read that as a wave of closures. It is not, and the check matters. The Census Bureau
counts business locations whether or not they take EBT. Between {cbp['base_year']} and
{cbp['last_year']} convenience establishments **rose {cbp['cbp_pct']:+.1f}%**, and the smallest ones —
under five staff — rose {cbp['cbp_under5_pct']:+.1f}%.

So the corner store is not disappearing. What is more likely happening is that the *specific business* in the building keeps changing. A store
is sold, renamed, re-registered, and a new record appears. The storefront stays. The owner turns over.

**That is the difference between a chain and a single owner.** A chain compounds: whatever it built
twenty years ago, it still has, and it adds to it. A single owner mostly hands the keys to the next
person. Same storefront, same shelves, new name on the paperwork — and in this data, a new record
starting from scratch.

## What it adds up to

Drilling into this format does not give a new answer. It gives the same one, in sharper relief.

Small grocers lost because they were small and alone. Dollar stores won because they were small and part of a chain. Convenience stores split along exactly that line: the chains kept **{ch['rate']}%** of their stores over thirteen years, the single owners kept **{so['rate']}%**.

**A chain of small boxes wins both games at once.** Small enough to make money in a thin market where a supermarket cannot. Big enough to spread a fixed cost across thousands of locations. That was the dollar store's trick, and it works just as well with a fuel canopy over it.

Which makes a Wawa or a Sheetz something close to a dollar store with one extra advantage: a fuel margin that doubled after 2020 and never came back. Same small footprint, same chain economics, plus a second profit stream that got far more profitable. If it feels like these have been appearing on every other corner in your town, the data agrees — though it can only show you the store count, not the reason a company chose your corner.

For a household with an EBT card, the practical result is the same either way. In a small town the
realistic options are narrowing to two: a dollar store, or a gas station. Both are now cheap to run, both
are profitable at a size no supermarket can match, and neither was designed to sell a week of groceries.

**Tomorrow: we switch gears to study the largest store of all, and the 13 million people who can only reach one because of it.**

## Limits

**An oil brand on the canopy is not an owner.** A "Shell" or "BP" station is almost never owned by Shell
or BP — it is somebody's own business with a fuel supply contract. So those stores count here as
single-owner stores. Broken out separately they survive at 20.6% against 13.5% for stores with no brand
at all: a real difference, too small to change the picture.

**The list of fuel chains is a judgement call.** Twenty-four operators are named because they run fuel
pumps at essentially all their US sites. The list is in the code. 7-Eleven is deliberately left out — it
is the largest convenience brand here by a wide margin and is mixed on fuel, so including it would let
one brand carry a claim about fuel economics.

**The growth rate is a median, and the table shows no starting count.** Both are for the same reason: a chain that joined SNAP late looks tiny at the start even when it was not. Wawa had roughly 540 stores in 2006 and 51 SNAP authorizations, and it added 40% of nineteen years of growth in 2010 alone — the year it signed up, not a year it built. A median cannot be moved by one such year. Murphy USA is left out entirely: its stores date from the 1990s but only eight years of its record are large enough to measure, which is not the same measurement as Circle K's nineteen.

**Margin is not profit.** Fuel margin is revenue minus the cost of the fuel. It does not subtract labour,
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
