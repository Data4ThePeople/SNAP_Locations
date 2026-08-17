"""Assemble reports/post3/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post3.json"
DIR = ROOT / "reports" / "post3"
IMG = DIR / "images"


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        # Keyed by slug, not list position — see the note in export_post4.
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    L, B = d["ladder"], d["breakers"]
    sv, ow, gr = d["survival"], d["by_ownership"], d["growth"]
    go = d["growth_by_ownership"]
    SHORT = {"Super Store": "Super store", "Supermarket": "Supermarket",
             "Grocery (Large)": "Large grocery", "Grocery (Medium)": "Medium grocery",
             "Grocery (Small)": "Small grocery", "Dollar Store": "Dollar store",
             "Convenience Store": "Convenience store"}

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{sv['Grocery (Small)']['rate']}%",
          "label": f"of small groceries authorized in {d['cohort']} are still authorized, "
                   f"against {sv['Super Store']['rate']:.0f}% of super stores"},
         {"value": f"{ow['Super Store']['chain']['rate']:.0f}%",
          "label": "survival for a chain store — about the same whether it is the "
                   "largest format or the smallest"},
         {"value": f"{gr['Super Store']['mult']}x",
          "label": f"super store growth since 2006, against the dollar store's "
                   f"{gr['Dollar Store']['mult']}x"}])

    # Rule one. Ladder order is the finding, so it is never re-sorted by value.
    fig(1, "size-ladder",
        "Share of stores authorized in 2008-2012 that were still authorized at the "
        "end of 2025, by USDA store type, largest to smallest.",
        figures.hbar_png,
        [{"label": SHORT[f], "value": sv[f]["rate"], "slot": 1 if f == L[0] else 0}
         for f in L], suffix="%",
        title="The bigger the store, the likelier it kept its authorization",
        subtitle=f"still authorized in 2025, of those authorized {d['cohort']}")

    # Rule two: the same numbers, split by who owns the store.
    def cell(f, o):
        # A rate on ~110 stores is noise, and printing it does real damage here:
        # the three thin chain-grocery cells read as 21.1 / 6.7 / 3.6 going down
        # the column, which looks like the very size ladder this table exists to
        # show does NOT apply to chains. Say "too few" instead of showing a
        # number the reader will reasonably believe.
        c = ow[f][o]
        if c["n"] == 0:
            return "none"
        return "too few" if c["thin"] else f"{c['rate']}%"

    NOTE = ('"too few" = fewer than %d stores in that cell, so no rate is shown. '
            '"none" = there are no stores of that kind: every dollar store is a chain.'
            % d["min_n"])
    fig(2, "ownership-split",
        "The same survival rates split by ownership.",
        figures.table_png,
        ["Store type", "Independent", "Chain", "All"],
        [[SHORT[f], cell(f, "independent"), cell(f, "chain"), f"{sv[f]['rate']}%"]
         for f in L + B],
        highlight_row=len(L) + 0,
        title="Among independents size decides. Among chains it does not.",
        subtitle="still authorized in 2025, by store type and ownership",
        note=NOTE)

    # Every (format, ownership) pair where both measures clear the sample floor.
    # Ownership is in the LABEL, not only in the colour, so the point is
    # identifiable in print and to a colourblind reader without a legend.
    def pts():
        out = []
        for f in L + B:
            for o in ("chain", "independent"):
                g, s = go[f][o], ow[f][o]
                if g["thin"] or s["thin"]:
                    continue
                out.append({"name": f"{SHORT[f]} ({o[:5] if o == 'chain' else 'indep'})",
                            "x": g["mult"], "y": s["rate"],
                            "slot": 1 if o == "chain" else 3})
        return out
    fig(3, "growth-vs-survival",
        "Growth against survival, by store type and ownership. Only pairs with "
        f"at least {d['min_n']} stores on both measures are plotted.",
        figures.scatter_png, pts(),
        xlabel="growth: 2025 stores as a multiple of 2006", xsuffix="x",
        ylabel="still authorized in 2025", ysuffix="%",
        quadrant={"x": 1.0}, width=7.2, height=4.6,
        title="Only one format did both",
        note="Points left of the dashed line have fewer stores than in 2006.")

    ss, sg = sv["Super Store"], sv["Grocery (Small)"]
    ssc, dol = ow["Super Store"]["chain"], sv["Dollar Store"]
    ind = [ow[f]["independent"]["rate"] for f in L]

    md = f"""# The bigger the store, the better it did — unless it belonged to a chain

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
Survival is measured on the {d['cohort']} cohort: stores first authorized in those years, checked again
at the end of 2025.*

**{sg['rate']}%** of small groceries authorized in {d['cohort']} are still authorized, against {ss['rate']:.0f}% of super stores.
**{ssc['rate']:.0f}%** survival for a chain store — about the same whether it is the largest format or the smallest.
**{gr['Super Store']['mult']}x** super store growth since 2006, against the dollar store's {gr['Dollar Store']['mult']}x.

![Headline figures](images/00-key-figures.png)

---

The last three days each followed one small format. Small groceries went away. Dollar stores grew and
stayed. Convenience stores grew while their owners turned over. Three stories, three explanations.

Put every format on one scale and the three collapse into two rules.

## Rule one: size

Take every store authorized between 2008 and 2012 and ask which ones are still authorized today. Sort
the answer by how big the store is, using USDA's own size categories.

![{figs["size-ladder"]['caption']}](images/{figs["size-ladder"]['file']})

The ladder is almost too neat: **{' , '.join(f"{sv[f]['rate']}%" for f in L)}**, straight down the size
order with nothing out of place. A super store was **{ss['rate']/sg['rate']:.0f} times** likelier to keep
its authorization than a small grocery.

That is a real finding, and on its own it is a bleak one. It says the thing that decided which stores
survived was a thing no small grocer could change.

## Rule two: rule one does not apply to chains

Except that size is not quite what is doing the work. Split each format by who owns it and rule one
comes apart.

![{figs["ownership-split"]['caption']}](images/{figs["ownership-split"]['file']})

Among independent stores rule one holds exactly as stated: **{' , '.join(f"{r}%" for r in ind)}** down
the size order. So size is real. It is not merely standing in for something else.

Now look down the chain column. A chain super store survives at **{ssc['rate']}%**. A dollar store — the
smallest box in the whole table — survives at **{dol['rate']}%**. Those are the same number. For a chain,
being large stopped mattering.

**Rule one does not apply to chains.** That is the whole of rule two, and it is what explains the last
two days. Dollar stores are small, and every one of them is a chain. The convenience stores that endured
were the fuel chains, at 78.7%; the single-owner ones managed 14.2%.

Neither format was breaking rule one. Neither was subject to it.

## Staying power is not the same as growing

Rule one said the super store was the safest place to be. That is true, and it is also the whole of
what being large bought you. The super store grew **{gr['Super Store']['mult']}x** since 2006. Dollar
stores grew **{gr['Dollar Store']['mult']}x**. Supermarkets managed {gr['Supermarket']['mult']}x.

So there are two different things a format can be good at, and they come apart. Put them on the same
chart — growth across the bottom, survival up the side — and split every format by ownership.

![{figs["growth-vs-survival"]['caption']}](images/{figs["growth-vs-survival"]['file']})

Read it in three passes.

**Chains sit above and to the right of their own independents, every time.** Super stores:
{go['Super Store']['chain']['mult']}x and {ow['Super Store']['chain']['rate']}% for the chains, against
{go['Super Store']['independent']['mult']}x and {ow['Super Store']['independent']['rate']}% for the
independents. Supermarkets: {go['Supermarket']['chain']['mult']}x and
{ow['Supermarket']['chain']['rate']}% against {go['Supermarket']['independent']['mult']}x and
{ow['Supermarket']['independent']['rate']}%. Convenience stores:
{go['Convenience Store']['chain']['mult']}x and {ow['Convenience Store']['chain']['rate']}% against
{go['Convenience Store']['independent']['mult']}x and {ow['Convenience Store']['independent']['rate']}%.
In every format where both can be measured, the chains grew faster **and** lasted longer.

**Fast growth does not buy staying power.** Convenience chains grew
{go['Convenience Store']['chain']['mult']}x, second only to dollar stores — and barely half of them,
{ow['Convenience Store']['chain']['rate']}%, were still authorized thirteen years on. That is Day 3 in a
single point: the format kept expanding while the businesses inside it turned over.

**And one point sits on its own in the top right corner.** The dollar store has the fastest growth in the
data and the highest survival in the data. Nothing else has both. The super store lasted nearly as well
and hardly grew; the convenience chains grew nearly as fast and did not last.

## What it adds up to

Two rules, and they are worth stating plainly because between them they cover almost everything in this
series so far.

**Rule one: a bigger store was likelier to keep its SNAP authorization.** That held for every independent
store in the data, right down the size order.

**Rule two: rule one does not apply to chains.** A dollar store the size of a corner shop held its
authorization as reliably as a super store.

And on the second measure, growth, being a chain is the only thing that helped at all. Size did nothing
for it: the largest format in the country grew {gr['Super Store']['mult']}x in twenty years.

Put it together and you can see the shape of the last two decades. The stores that went away were small
and independent — they had neither advantage. The large format had size, and used it to stay put rather
than to spread. What actually spread was the format that worked out how to be small and be a chain at
the same time, and it is the only thing in the data that is winning on both counts at once.

Tomorrow we look at a format that had both advantages and lost anyway. It is the fastest collapse in the
whole dataset, and it happened in the last four years.

## Limits

**These are authorizations, not buildings.** A small grocery at {sg['rate']}% has overwhelmingly left the
program; this source cannot tell you the storefront is empty. Day 1 worked through that gap in detail.
The super store figure is the one place the two nearly coincide, because for the large chains the
authorization list runs close to a store census.

**Ownership is inferred, not reported.** It comes from patterns in store names, and it is unknown for
between {min(sv[f]['unknown_share'] for f in L+B):.0f}% and {max(sv[f]['unknown_share'] for f in L+B):.0f}%
of each format's cohort. Rates are computed over the stores that could be classified, and the unclassified
share is published in the data file beside every one of them.

**Being a chain is not sufficient, and this data cannot show why.** The chain small-grocery cell survives
at {ow['Grocery (Small)']['chain']['rate']}%, no better than independents — but it holds only
{ow['Grocery (Small)']['chain']['n']} stores, far too few to carry a claim, which is why nothing above is
built on it. The likely reason is that "chain" here covers a three-store local operator and a national
retailer with twenty thousand locations alike, and only the second kind has the scale that matters. This
source cannot separate them.

**The cohort is one window.** Stores first authorized in {d['cohort']}, followed to the end of 2025. A
different window would give different levels; the ordering is what this piece rests on.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December. Code,
pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post3.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post3.html", DIR / "post3-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post3.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
