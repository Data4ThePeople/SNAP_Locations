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
        c = ow[f][o]
        if c["n"] == 0:
            return "—"
        return f"{c['rate']}%" + ("*" if c["thin"] else "")
    fig(2, "ownership-split",
        "The same survival rates split by ownership. Cells marked * rest on fewer "
        f"than {d['min_n']} stores and are shown for completeness only.",
        figures.table_png,
        ["Store type", "Independent", "Chain", "All"],
        [[SHORT[f], cell(f, "independent"), cell(f, "chain"), f"{sv[f]['rate']}%"]
         for f in L + B],
        highlight_row=len(L) + 0,
        title="Among independents size decides. Among chains it does not.",
        subtitle="still authorized in 2025, by store type and ownership")

    fig(3, "growth",
        "Change in the number of SNAP-authorized stores between 2006 and 2025, by "
        "store type.",
        figures.hbar_png,
        [{"label": SHORT[f], "value": gr[f]["mult"],
          "slot": 2 if f == "Dollar Store" else (1 if f == "Super Store" else 0)}
         for f in sorted(L + B, key=lambda x: -gr[x]["mult"])], suffix="x",
        title="The most durable format is also the slowest growing",
        subtitle="SNAP-authorized stores in 2025 as a multiple of 2006")

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

## Rule two: chains do not need to be big

Except that size is not quite what is doing the work. Split each format by who owns it and the ladder
comes apart.

![{figs["ownership-split"]['caption']}](images/{figs["ownership-split"]['file']})

Among independent stores the ladder holds exactly as before: **{' , '.join(f"{r}%" for r in ind)}** down
the size order. So size is real. It is not merely standing in for something else.

But look along the chain row. A chain super store survives at **{ssc['rate']}%**. A dollar store — the
smallest box in the whole table — survives at **{dol['rate']}%**. Those are the same number. For a chain,
being large stopped mattering.

That is the second rule, and it is the one that explains the last two days. **Being part of a chain
substitutes for being big.** Dollar stores are small and every one of them is a chain. The convenience
stores that endured were the fuel chains, at 78.7%; the single-owner ones managed 14.2%.

Neither format was breaking the size rule. Both were beating it with a different one.

## The large format wins at staying and loses at spreading

One more thing falls out of the same table, and it is the opposite of what the first two rules suggest.

![{figs["growth"]['caption']}](images/{figs["growth"]['file']})

The super store is the most durable format in the data and close to the slowest growing:
**{gr['Super Store']['mult']}x** since 2006, against **{gr['Dollar Store']['mult']}x** for dollar stores
and {gr['Convenience Store']['mult']}x for convenience stores. Supermarkets barely moved at
{gr['Supermarket']['mult']}x.

Durability and growth are not the same trait. The formats that lasted best are not the ones that spread.
What spread was the format that found a way to be small and be a chain at the same time.

## What it adds up to

Two rules, and they are worth stating plainly because between them they cover almost everything in this
series so far.

**A bigger store was likelier to keep its SNAP authorization.** That held for every independent store in
the data, right down the size order.

**A chain store did not need to be big.** A dollar store the size of a corner shop held its authorization
as reliably as a super store.

Put the two together and you can see the shape of the last twenty years. The stores that went away were
small and independent — they had neither advantage. The stores that grew were small and chained — they
had the one that could be bought. And the large format, which had both, mostly stayed where it was.

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
