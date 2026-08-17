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
        return p

    surv = sorted(d["survival"], key=lambda r: -r["rate"])
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")
    fl, yrs = d["dollar_flows"], d["dollar_flows"]["years"]
    z = d["dollar_only_zip"]
    lap = {r["format"]: r for r in d["lapse"]}
    vol = {v["format"]: v for v in d["volatility"]}

    print("figures:")
    fig(0, "key-figures",
        "Headline figures.",
        figures.ledger_png,
        [{"value": f"{100*ds['rate']:.0f}%",
          "label": "of dollar stores authorized 2008-2012 are still authorized today"},
         {"value": f"{100*sg['rate']:.1f}%",
          "label": "of small grocers from the same cohort still are"},
         {"value": f"{z[-1]['dollar_only']:,}",
          "label": "ZIP codes have a dollar store and no grocery of any size"}])

    fig(1, "cohort-retention",
        "Share of the 2008–2012 entry cohort still authorized at the end of 2025.",
        figures.hbar_png,
        [{"label": r["format"], "value": round(100 * r["rate"], 1),
          "note": f"{r['still_open']:,} of {r['cohort']:,}",
          "slot": 1 if r["format"] == "Dollar Store" else
                  (2 if r["format"] == "Grocery (Small)" else 0)} for r in surv],
        suffix="%", note_key="note",
        title="Dollar stores stayed. Small grocers did not.",
        subtitle="share of the 2008-2012 cohort still authorized in 2025")

    fig(2, "chain-store-census",
        "SNAP authorizations against each company's own reported store count.",
        figures.table_png,
        ["Brand", "SNAP-authorized 2025", "Company-reported", "Ratio"],
        [[c["brand"], f"{c['authorized']:,}", f"{c['reported']:,}", f"{c['ratio']:.2f}"]
         for c in d["chain_census"]], highlight_row=0,
        title="For the dollar chains, an authorization is a store",
        subtitle="SNAP authorizations vs each company's reported store count")

    fig(3, "lapsed-and-returned",
        "Share of each format's stores that lost authorization and later regained it — "
        "direct evidence of stores operating while unauthorized.",
        figures.hbar_png,
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 1 if f == "Dollar Store" else 0}
         for f in ["Grocery (Medium)", "Grocery (Large)", "Convenience Store",
                   "Grocery (Small)", "Supermarket", "Super Store", "Dollar Store"]
         if f in lap], suffix="%",
        title="Some stores drop out, then come back",
        subtitle="share that lost authorization and later regained it")

    fig(4, "authorization-churn",
        "Authorizations ending 2009–2023 as a multiple of average active stock.",
        figures.hbar_png,
        [{"label": f, "value": round(vol[f]["churn"], 2),
          "slot": 1 if f == "Dollar Store" else 0}
         for f in ["Dollar Store", "Super Store", "Supermarket",
                   "Combination Grocery/Other", "Grocery (Medium)",
                   "Convenience Store", "Grocery (Small)"] if f in vol], suffix="x",
        title="Small grocery churned. Dollar stores barely did.",
        subtitle="authorizations ending 2009-2023, as a multiple of average stock")

    fig(5, "openings-vs-endings",
        "Dollar store authorizations beginning and ending each year.",
        figures.line_png, yrs,
        [{"name": "beginning", "values": fl["new"], "slot": 1},
         {"name": "ending", "values": fl["departed"], "slot": 2}],
        ylabel="authorizations per year", annotate=[{"year": 2024, "text": "2024"}],
        title="Openings ran far ahead of endings until 2024",
        subtitle="dollar store authorizations per year")

    ctx = d["context"]
    picks = ["Dollar Store", "Supermarket", "Super Store", "Grocery (Small)",
             "Grocery (Medium)", "Grocery (Large)"]
    fig(6, "format-stock",
        "Active SNAP authorizations by store format. Convenience stores omitted for "
        "scale — there are about 119,000.",
        figures.line_png, ctx["Dollar Store"]["years"],
        [{"name": f, "values": ctx[f]["stock"], "slot": i + 1} for i, f in enumerate(picks)],
        ylabel="active stores",
        title="Dollar stores passed every grocery format",
        subtitle="stores authorized on 31 December")

    fig(7, "endings-2024",
        "Authorizations ending in 2024, by brand.",
        figures.table_png, ["Brand", "Authorizations ending 2024"],
        [[s["brand"], f"{s['n']:,}"] for s in d["spike_2024"][:5]], highlight_row=0,
        title="Two chains account for the 2024 jump",
        subtitle="authorizations ending in 2024, by brand")

    bpick = [b for b in ["Dollar General", "Dollar Tree", "Family Dollar", "99 Cents Only"]
             if b in d["brands"]]
    fig(8, "brands",
        "Active SNAP authorizations by dollar-store brand. 99 Cents Only reaches zero in 2024.",
        figures.line_png, d["brands"]["Dollar General"]["years"],
        [{"name": b, "values": d["brands"][b]["stock"], "slot": i + 1}
         for i, b in enumerate(bpick)], ylabel="active stores",
        title="99 Cents Only reaches zero in 2024",
        subtitle="stores authorized on 31 December, by brand")

    fig(9, "dollar-only-zips",
        "ZIP codes with a SNAP-authorized dollar store and no supermarket, superstore, "
        "or grocery store of any size.",
        figures.line_png, [r["yr"] for r in z],
        [{"name": "ZIPs", "values": [r["dollar_only"] for r in z], "slot": 2}],
        ylabel="ZIP codes",
        title="More ZIP codes have a dollar store and no grocery",
        subtitle="ZIP codes with a dollar store and no grocery of any size")

    g_rate = 100 * lap["Grocery (Small)"]["rate"]
    md = f"""# Dollar stores almost never leave SNAP. Small grocers almost always do.

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
{d['headline']['dollar_2025']:,} dollar stores were authorized at the end of 2025.*

**{100*ds['rate']:.0f}%** of dollar stores authorized 2008–2012 are still authorized today.
**{100*sg['rate']:.1f}%** of small grocers from the same cohort still are.
**{z[-1]['dollar_only']:,}** ZIP codes have a dollar store and no grocery of any size.

![Headline figures](images/00-key-figures.png)

---

Everyone knows dollar stores grew. The sharper question is what happened to the stores that were already there. So take every retailer that joined SNAP between 2008 and 2012. Then ask how many are still in the program at the end of 2025. Here is that count, by format:

![{figs["cohort-retention"]['caption']}](images/{figs["cohort-retention"]['file']})

*Counts are stores, not authorization spells, so a store that lapsed and returned is counted once.*

Small grocery is the extreme: {sg['still_open']:,} of {sg['cohort']:,} are still in the program. A
dollar store from those same years is **{d['survival_gap']['multiple']}× more likely** to still be
authorized.

## What an ended authorization actually means

Before calling that a survival rate, be exact about what this data records. It tracks *authorizations*, not storefronts. When a record ends, the store might have closed. Or it might still be open and just no longer take EBT. Those are very different claims. The raw data cannot tell them apart.

Two checks narrow it. They point in opposite directions for chains and for independents.

**For the dollar chains, authorization is effectively a store census.**

![{figs["chain-store-census"]['caption']}](images/{figs["chain-store-census"]['file']})

Nearly every Dollar General and Dollar Tree in the country takes SNAP. So for these chains the authorization record really is a store count. An ending really does mean a closed store. That is why we can say "closed" about them, and only about them.

**For independents, the opposite caution applies.** Some stores drop out of the program and come
back, which proves they were open the whole time.

![{figs["lapsed-and-returned"]['caption']}](images/{figs["lapsed-and-returned"]['file']})

*Median gaps run from 9 days for superstores to 85 for convenience stores.*

A small grocer is **{d['lapse_gap']['multiple']}× more likely** than a dollar store to have dropped
out and returned. And that {g_rate:.0f}% is only a floor: it counts stores that came back. Any store
that left the program and stayed open is invisible here.

So the honest reading of the first chart is this. It measures **staying in the program, not staying in business**. For dollar stores those are nearly the same thing. For small grocers they are not. How big the gap is, we cannot say from these records.

## The pattern that produces the gap

The story is usually told as dollar stores opening fast. They do open steadily. But on that measure they are not unusual at all. Supermarket openings actually vary less from year to year. What sets dollar stores apart is the other side of the ledger. This is how many stores each format shed:

![{figs["authorization-churn"]['caption']}](images/{figs["authorization-churn"]['file']})

*Small grocery cycled through more than three times its own population. Dollar stores shed about one store in seven.*

About {d['metronome']['mean_new']:,.0f} dollar stores joined each year. Only about {d['metronome']['mean_closed']:,.0f} left. A gap that wide produces a line that goes one way:

![{figs["openings-vs-endings"]['caption']}](images/{figs["openings-vs-endings"]['file']})

*The two lines cross for the first time in 2024.*

Put next to the grocery formats, the result is stark. Dollar stores passed every single grocery format years ago. They are now the second most common SNAP retailer in the country. Only convenience stores beat them.

![{figs["format-stock"]['caption']}](images/{figs["format-stock"]['file']})

## 2024 breaks the pattern

Endings jumped from a few hundred a year to **{fl['departed'][yrs.index(2024)]:,}** in 2024. This is
the one place we can check the data against events that were independently reported.

![{figs["endings-2024"]['caption']}](images/{figs["endings-2024"]['file']})

Dollar Tree spent 2024 closing Family Dollar stores. 99 Cents Only shut down entirely that spring. Both show up here right on time. That is a useful check. When something real happens in retail, these records catch it.

![{figs["brands"]['caption']}](images/{figs["brands"]['file']})

## Where it matters

Growth in total is not the same as growth where it matters. The sharper question is how often a dollar store is the *only* option nearby.

![{figs["dollar-only-zips"]['caption']}](images/{figs["dollar-only-zips"]['file']})

In 2008 that described {z[0]['dollar_only']:,} ZIP codes. By 2024 it described
**{z[-1]['dollar_only']:,}** — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of every ZIP code
that has a dollar store at all. Across the country there are now {d['headline']['dollar_2025']:,} dollar stores. Grocery stores of every size combined come to {d['headline']['all_grocery_2025']:,}.

## Limits

Nothing here measures floor space, sales, or what is on the shelves. A dollar store and a supermarket each count as one record. USDA sorts stores by how much they stock, and a 2018 rule moved that bar partway through this series. That affects grocery formats far more than dollar stores. The next piece takes it up.

SNAP spending per store is not public. A 2019 Supreme Court case, *Food Marketing Institute v. Argus Leader*, put those figures under a FOIA exemption. So we can see where authorized stores are, but never how much any one of them takes in.

Company store counts are from early 2025 to early 2026. We compare them against authorizations at the end of 2025. So the ratios are close, not exact.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, covering retailers authorized at
any point in the window. Analysis uses 656,868 stores with usable coordinates. A store counts as
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
