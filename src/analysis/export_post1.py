"""Assemble reports/post1/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post1.json"
DIR = ROOT / "reports" / "post1"
IMG = DIR / "images"


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = []

    def fig(n, slug, caption, fn, *a, **kw):
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs.append({"file": p.name, "caption": caption})
        print(f"  {p.name}")
        return p

    surv = sorted(d["survival"], key=lambda r: -r["rate"])
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")
    fl, yrs = d["dollar_flows"], d["dollar_flows"]["years"]
    z = d["dollar_only_zip"]
    lap = {r["format"]: r for r in d["lapse"]}
    vol = {v["format"]: v for v in d["volatility"]}

    print("figures:")
    fig(1, "cohort-retention",
        "Share of the 2008–2012 entry cohort still authorized at the end of 2025.",
        figures.hbar_png,
        [{"label": r["format"], "value": round(100 * r["rate"], 1),
          "note": f"{r['still_open']:,} of {r['cohort']:,}",
          "slot": 1 if r["format"] == "Dollar Store" else
                  (2 if r["format"] == "Grocery (Small)" else 0)} for r in surv],
        suffix="%", note_key="note")

    fig(2, "chain-store-census",
        "SNAP authorizations against each company's own reported store count.",
        figures.table_png,
        ["Brand", "SNAP-authorized 2025", "Company-reported", "Ratio"],
        [[c["brand"], f"{c['authorized']:,}", f"{c['reported']:,}", f"{c['ratio']:.2f}"]
         for c in d["chain_census"]], highlight_row=0)

    fig(3, "lapsed-and-returned",
        "Share of each format's stores that lost authorization and later regained it — "
        "direct evidence of stores operating while unauthorized.",
        figures.hbar_png,
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 1 if f == "Dollar Store" else 0}
         for f in ["Grocery (Medium)", "Grocery (Large)", "Convenience Store",
                   "Grocery (Small)", "Supermarket", "Super Store", "Dollar Store"]
         if f in lap], suffix="%")

    fig(4, "authorization-churn",
        "Authorizations ending 2009–2023 as a multiple of average active stock.",
        figures.hbar_png,
        [{"label": f, "value": round(vol[f]["churn"], 2),
          "slot": 1 if f == "Dollar Store" else 0}
         for f in ["Dollar Store", "Super Store", "Supermarket",
                   "Combination Grocery/Other", "Grocery (Medium)",
                   "Convenience Store", "Grocery (Small)"] if f in vol], suffix="x")

    fig(5, "openings-vs-endings",
        "Dollar store authorizations beginning and ending each year.",
        figures.line_png, yrs,
        [{"name": "beginning", "values": fl["new"], "slot": 1},
         {"name": "ending", "values": fl["departed"], "slot": 2}],
        ylabel="authorizations per year", annotate=[{"year": 2024, "text": "2024"}])

    ctx = d["context"]
    picks = ["Dollar Store", "Supermarket", "Super Store", "Grocery (Small)",
             "Grocery (Medium)", "Grocery (Large)"]
    fig(6, "format-stock",
        "Active SNAP authorizations by store format. Convenience stores omitted for "
        "scale — there are about 119,000.",
        figures.line_png, ctx["Dollar Store"]["years"],
        [{"name": f, "values": ctx[f]["stock"], "slot": i + 1} for i, f in enumerate(picks)],
        ylabel="active stores")

    fig(7, "endings-2024",
        "Authorizations ending in 2024, by brand.",
        figures.table_png, ["Brand", "Authorizations ending 2024"],
        [[s["brand"], f"{s['n']:,}"] for s in d["spike_2024"][:5]], highlight_row=0)

    bpick = [b for b in ["Dollar General", "Dollar Tree", "Family Dollar", "99 Cents Only"]
             if b in d["brands"]]
    fig(8, "brands",
        "Active SNAP authorizations by dollar-store brand. 99 Cents Only reaches zero in 2024.",
        figures.line_png, d["brands"]["Dollar General"]["years"],
        [{"name": b, "values": d["brands"][b]["stock"], "slot": i + 1}
         for i, b in enumerate(bpick)], ylabel="active stores")

    fig(9, "dollar-only-zips",
        "ZIP codes with a SNAP-authorized dollar store and no supermarket, superstore, "
        "or grocery store of any size.",
        figures.line_png, [r["yr"] for r in z],
        [{"name": "ZIPs", "values": [r["dollar_only"] for r in z], "slot": 2}],
        ylabel="ZIP codes")

    g_rate = 100 * lap["Grocery (Small)"]["rate"]
    md = f"""# Dollar stores almost never leave SNAP. Small grocers almost always do.

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
{d['headline']['dollar_2025']:,} dollar stores were authorized at the end of 2025.*

**{100*ds['rate']:.0f}%** of dollar stores authorized 2008–2012 are still authorized today.
**{100*sg['rate']:.1f}%** of small grocers from the same cohort still are.
**{z[-1]['dollar_only']:,}** ZIP codes have a dollar store and no grocery of any size.

---

Everyone knows dollar stores grew. The more revealing question is what happened to the stores that
were already there. Take every retailer that entered the SNAP program between 2008 and 2012, and ask
how many are still in it at the end of 2025.

![{figs[0]['caption']}](images/{figs[0]['file']})

*{figs[0]['caption']} Counts are stores, not authorization spells, so a store that lapsed and
returned is counted once.*

Small grocery is the extreme: {sg['still_open']:,} of {sg['cohort']:,} are still in the program. A
dollar store from those same years is **{d['survival_gap']['multiple']}× more likely** to still be
authorized.

## What an ended authorization actually means

Before reading that as a survival rate, it is worth being exact about what this dataset records. It
tracks *authorizations*, not storefronts. When a record ends, the store might have closed — or it
might still be open and no longer taking EBT. Those are very different claims, and the raw data
cannot tell them apart.

Two things narrow it, and they point in opposite directions for chains and for independents.

**For the dollar chains, authorization is effectively a store census.**

![{figs[1]['caption']}](images/{figs[1]['file']})

Essentially every Dollar General and Dollar Tree in the country accepts SNAP. So for these retailers
the authorization record really is a store count, and an ending really does mean a closed store. That
is what licenses closure language for them — but only for them.

**For independents, the opposite caution applies.** Some stores drop out of the program and come
back, which proves they were open the whole time.

![{figs[2]['caption']}](images/{figs[2]['file']})

*{figs[2]['caption']} Median gaps run from 9 days for superstores to 85 for convenience stores.*

A small grocer is **{d['lapse_gap']['multiple']}× more likely** than a dollar store to have dropped
out and returned. And that {g_rate:.0f}% is only a floor: it counts stores that came back. Any store
that left the program and stayed open is invisible here.

So the honest reading of the headline chart is that it measures **program retention, not survival**.
For dollar stores those are nearly the same thing. For small grocers they are not, and the gap
between them is unknown — resolving it requires business-registry data rather than SNAP records.

## The pattern that produces the gap

The story is usually told as dollar stores opening aggressively, and they do open steadily — but on
that measure they are not even unusual. Supermarket openings vary less from year to year than dollar
store openings do. What is distinctive is the other side of the ledger.

![{figs[3]['caption']}](images/{figs[3]['file']})

*{figs[3]['caption']} Small grocery cycled through more than three times its own population; dollar
stores shed about one store in seven.*

Roughly {d['metronome']['mean_new']:,.0f} new dollar store authorizations a year against about
{d['metronome']['mean_closed']:,.0f} endings produces a line that only goes one way.

![{figs[4]['caption']}](images/{figs[4]['file']})

*{figs[4]['caption']} The two lines cross for the first time in 2024.*

Set against the grocery formats, the result is stark. Dollar stores passed every individual grocery
format years ago and are now the second most common type of SNAP retailer in the country, behind only
convenience stores.

![{figs[5]['caption']}](images/{figs[5]['file']})

## 2024 breaks the pattern

Endings jumped from a few hundred a year to **{fl['departed'][yrs.index(2024)]:,}** in 2024. This is
the one place we can check the data against events that were independently reported.

![{figs[6]['caption']}](images/{figs[6]['file']})

Dollar Tree spent 2024 closing Family Dollar locations, and 99 Cents Only liquidated entirely that
spring. Both appear here on schedule, which is a useful confidence check: when something verifiable
happens in retail, these records see it.

![{figs[7]['caption']}](images/{figs[7]['file']})

## Where it matters

Growth in aggregate is not the same as growth where it counts. The sharper question is how often a
dollar store is the *only* option.

![{figs[8]['caption']}](images/{figs[8]['file']})

In 2008 that described {z[0]['dollar_only']:,} ZIP codes. By 2024 it described
**{z[-1]['dollar_only']:,}** — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of every ZIP code
that has a dollar store at all. Nationally there are now {d['headline']['dollar_2025']:,} dollar
stores against {d['headline']['all_grocery_2025']:,} grocery stores of every size combined.

## Limits

Nothing here measures floor space, sales, or what is actually on the shelves. A dollar store and a
supermarket each count as one record. USDA classifies stores by stocking breadth, and the 2016
stocking-standards rule moved that bar mid-series — which affects grocery formats far more than dollar
stores, and is the subject of the next piece.

Store-level SNAP redemption dollars are not public. *Food Marketing Institute v. Argus Leader* (2019)
placed them under FOIA Exemption 4, so we can see where authorized retailers are but never how much
any one of them transacts.

Company-reported store counts are as of early 2025 to early 2026 and are compared against
end-of-2025 authorizations, so the ratios are close rather than exact.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, covering retailers authorized at
any point in the window. Analysis uses 611,164 stores with usable coordinates. A store counts as
active in a year if an authorization covered 31 December. Company store counts from Dollar General and
Dollar Tree investor releases; Family Dollar via trade press. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post1.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post1.html", DIR / "post1-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post1.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
