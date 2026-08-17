"""Assemble reports/post2/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post2.json"
DIR = ROOT / "reports" / "post2"
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

    fl, yrs = d["flows"], d["flows"]["years"]
    arc, dr, rc, ctx = d["arc"], d["drivers"], d["reclass"], d["context"]
    lap = {r["format"]: r for r in d["lapse"]}
    st = d["states"]
    picks = ["Grocery (Small)", "Grocery (Medium)", "Grocery (Large)",
             "Supermarket", "Super Store"]

    print("figures:")
    fig(0, "key-figures",
        "Headline figures.",
        figures.ledger_png,
        [{"value": f"{arc['pct_fall']}%",
          "label": f"fall in authorized small grocers, {arc['peak_year']} peak to "
                   f"{arc['trough_year']} trough"},
         {"value": f"{100*(dr['new_after']/dr['new_before']-1):+.0f}%",
          "label": "change in new small-grocery authorizations per year"},
         {"value": f"{100*rc['share_of_exits']:.1f}%",
          "label": "of exits are explained by reclassification"}])

    fig(1, "small-grocery-arc",
        "Small grocery stores with an active SNAP authorization on 31 December of each year.",
        figures.line_png, yrs,
        [{"name": "small grocers", "values": fl["stock"], "slot": 4}],
        ylabel="active small grocery stores",
        annotate=[{"year": arc["peak_year"], "text": "peak"},
                  {"year": arc["trough_year"], "text": "trough"}])

    fig(2, "grocery-formats",
        "Active SNAP authorizations by grocery format, 2006–2025.",
        figures.line_png, ctx["Grocery (Small)"]["years"],
        [{"name": f, "values": ctx[f]["stock"], "slot": 4 if f == "Grocery (Small)" else i + 1}
         for i, f in enumerate(picks)], ylabel="active stores")

    fig(3, "format-change-table",
        "Change in active authorizations by grocery format, 2006 to 2025.",
        figures.table_png, ["Format", "2006", "2025", "Change"],
        [[f, f"{ctx[f]['stock'][0]:,}", f"{ctx[f]['stock'][-1]:,}",
          f"{ctx[f]['change_pct']:+.1f}%"] for f in picks], highlight_row=0)

    fig(4, "successor-formats",
        "What opened at the address of a departed small grocer, 2012–2022. A shared store "
        "name is the signature of one business re-registering.",
        figures.table_png, ["Successor format", "Pairs", "Same name", "Share"],
        [[t["format"], f"{t['n']:,}", f"{t['same_name']:,}",
          f"{100*t['same_name']/t['n']:.0f}%"] for t in d["successor_types"]])

    fig(5, "entries-vs-exits",
        "New small-grocery authorizations and authorizations ending, per year.",
        figures.line_png, yrs,
        [{"name": "new authorizations", "values": fl["new"], "slot": 1},
         {"name": "authorizations ending", "values": fl["departed"], "slot": 2}],
        ylabel="stores per year")

    fig(6, "lapsed-and-returned",
        "Share of each format's stores that lost authorization and later regained it.",
        figures.hbar_png,
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 4 if f == "Grocery (Small)" else 0}
         for f in ["Grocery (Medium)", "Convenience Store", "Grocery (Small)",
                   "Supermarket", "Dollar Store"] if f in lap], suffix="%")

    fig(7, "states",
        f"Largest percentage falls in authorized small grocers, {arc['peak_year']} to 2025, "
        "among states with at least 150 at peak.",
        figures.hbar_png,
        [{"label": f"{t['state']}  {t['then']:,}→{t['now']:,}", "value": abs(t["pct"]),
          "slot": 4 if t["state"] == "NY" else 0} for t in st[:8]], suffix="%")

    exit_change = 100 * (dr["exit_rate_after"] / dr["exit_rate_before"] - 1)
    md = f"""# Half of America's small grocers left SNAP. Three explanations don't hold.

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
{arc['peak']:,} small grocery stores in {arc['peak_year']}, {arc['latest']:,} today.*

**{arc['pct_fall']}%** fall in authorized small grocers, {arc['peak_year']} peak to
{arc['trough_year']} trough.
**{100*(dr['new_after']/dr['new_before']-1):+.0f}%** change in new small-grocery authorizations per year.
**{100*rc['share_of_exits']:.1f}%** of exits are explained by reclassification.

![Headline figures](images/00-key-figures.png)

---

Between {arc['peak_year']} and {arc['trough_year']}, the number of small grocery stores authorized to
accept SNAP fell from {arc['peak']:,} to {arc['trough']:,} — a drop of {abs(arc['pct_fall'])}%. It has
since flattened rather than recovered, sitting at {arc['latest']:,} at the end of {arc['latest_year']}.

![{figs[1]['caption']}](images/{figs[1]['file']})

That is a big number, and "the death of the small grocer" is the obvious way to read it. Before
accepting that, it is worth testing the explanations that would produce the same chart without any
store dying.

## It is not grocery in general

If shoppers were simply abandoning grocery stores for superstores, every grocery format would sag.
None of the others do.

![{figs[2]['caption']}](images/{figs[2]['file']})

![{figs[3]['caption']}](images/{figs[3]['file']})

Medium grocery ended **{ctx['Grocery (Medium)']['change_pct']:+.0f}%**, superstores
**{ctx['Super Store']['change_pct']:+.0f}%**, supermarkets
**{ctx['Supermarket']['change_pct']:+.0f}%**. Only the smallest format fell. Whatever happened,
happened to small stores specifically.

## It is not reclassification

USDA sorts stores by how much staple food they stock, so a store could in principle move from "small
grocery" to another category without changing at all. This dataset can test that directly: a store's
type never changes within its record, so a reclassified store has to reappear as a *new* record at the
*same address*. When it also carries the same store name, that is one business re-registering rather
than a different tenant moving in.

Of {rc['exits']:,} small-grocery exits between 2012 and 2022, {rc['with_successor']:,} had another
store show up at the same address. Among {rc['successor_pairs']:,} successor pairs, just
**{rc['same_name_diff_type']:,}** share the name and differ in type — {100*rc['share_of_pairs']:.1f}%
of pairs, and **{100*rc['share_of_exits']:.1f}% of all exits**.

![{figs[4]['caption']}](images/{figs[4]['file']})

Reclassification is real and it is small. What the table does show is churn: the most common successor
at a departed small grocer's address is a convenience store, and the second most common is another
small grocery. The storefront often keeps selling food. It frequently does so under a different owner
and a different classification.

## It is not a wave of closures either

This is the part that surprised me. If small grocers were dying, departures should spike. They did
not — the number leaving each year is *lower* now than in 2008. What collapsed was arrivals.

![{figs[5]['caption']}](images/{figs[5]['file']})

New authorizations fell from {dr['new_before']:,.0f} a year in 2009–2013 to {dr['new_after']:,.0f} in
2016–2020, a drop of **{100*(dr['new_after']/dr['new_before']-1):.0f}%**. Departures over the same
period fell {abs(100*(dr['dep_after']/dr['dep_before']-1)):.0f}% in absolute terms — though because the
population was shrinking, the *rate* at which a given store left rose from {dr['exit_rate_before']:.0%}
to {dr['exit_rate_after']:.0%}, about {exit_change:.0f}% higher.

So both blades of the scissors moved, but the dominant one is entry. Small grocery did not suddenly
start dying; it stopped being replaced. Small grocers have always churned hard — that is the nature of
a thin-margin corner business — and for years enough new ones opened to cover the losses. After 2014
they stopped.

The timing points somewhere specific. The 2014 Farm Bill directed USDA to raise stocking requirements,
and the resulting rule — finalised in 2016 and enforced from 2018 — increased both the number of staple
varieties a store must carry and the requirement for perishables. A higher bar for *new* applicants
predicts precisely this shape: entries fall, departures stay flat, the population settles at a lower
level. That is a well-supported candidate, not a proven cause: these records carry no field for why an
authorization ended.

## What we cannot rule out

One explanation survives, and it is the one the data cannot settle. A store that closes and a store
that stays open but stops accepting EBT look identical here — both are simply an authorization that
ended.

We know the second thing happens, because some stores do it and come back:

![{figs[6]['caption']}](images/{figs[6]['file']})

**{100*lap['Grocery (Small)']['rate']:.1f}%** of small grocers have gone unauthorized and returned,
median gap {lap['Grocery (Small)']['median_gap_days']} days. Those stores were plainly open the whole
time. And that is a floor, not an estimate: any store that dropped SNAP and never came back is
indistinguishable from one that shut its doors.

Settling it requires a source that counts businesses rather than authorizations. Census County Business
Patterns publishes establishment counts for grocery retailers by county and size class; if small
grocery establishments held steady while SNAP authorizations halved, they left the program, and if both
fell together, they closed. That comparison is the next thing to run, and until it is run the honest
headline is the one at the top of this page: they left SNAP.

## Where it happened

The decline is not evenly spread. New York lost more small grocers than any other state, by a wide
margin.

![{figs[7]['caption']}](images/{figs[7]['file']})

New York went from {st[0]['then']:,} to {st[0]['now']:,}, a fall of {abs(st[0]['pct']):.0f}%. A state
with that many small groceries is a state of bodegas and corner stores, and it absorbed the largest
share of whatever changed.

## Limits

Every figure here counts **authorizations**. "Left SNAP" is the strongest claim the data supports;
"closed" is not, except where an outside source can corroborate it.

Address matching for the successor test is exact on street number, street name, city and state. Stores
whose address was recorded differently across records will be missed, so
{100*rc['share_of_exits']:.1f}% is a lower bound on reclassification.

The 2016 stocking-standards rule is offered as a candidate explanation on timing and shape. These
records contain no reason code, so it cannot be confirmed from this source alone.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 611,164 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December. Entries
and exits count stores, not authorization spells, so a store that lapsed and resumed is not
double-counted. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post2.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post2.html", DIR / "post2-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post2.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
