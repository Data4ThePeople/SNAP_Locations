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
                  {"year": arc["trough_year"], "text": "trough"}],
        title="Small grocers halved, then stopped falling", subtitle="stores authorized on 31 December")

    fig(2, "grocery-formats",
        "Active SNAP authorizations by grocery format, 2006–2025.",
        figures.line_png, ctx["Grocery (Small)"]["years"],
        [{"name": f, "values": ctx[f]["stock"], "slot": 4 if f == "Grocery (Small)" else i + 1}
         for i, f in enumerate(picks)], ylabel="active stores",
        title="Only the smallest format dropped", subtitle="stores authorized on 31 December")

    fig(3, "format-change-table",
        "Change in active authorizations by grocery format, 2006 to 2025.",
        figures.table_png, ["Format", "2006", "2025", "Change"],
        [[f, f"{ctx[f]['stock'][0]:,}", f"{ctx[f]['stock'][-1]:,}",
          f"{ctx[f]['change_pct']:+.1f}%"] for f in picks], highlight_row=0,
        title="Every other grocery size held or grew", subtitle="change in authorized stores, 2006 to 2025")

    fig(4, "successor-formats",
        "What opened at the address of a departed small grocer, 2012–2022. A shared store "
        "name is the signature of one business re-registering.",
        figures.table_png, ["Successor format", "Pairs", "Same name", "Share"],
        [[t["format"], f"{t['n']:,}", f"{t['same_name']:,}",
          f"{100*t['same_name']/t['n']:.0f}%"] for t in d["successor_types"]],
        title="Most replacements are a different business", subtitle="what opened at a departed small grocer's address")

    fig(5, "entries-vs-exits",
        "New small-grocery authorizations and authorizations ending, per year.",
        figures.line_png, yrs,
        [{"name": "new authorizations", "values": fl["new"], "slot": 1},
         {"name": "authorizations ending", "values": fl["departed"], "slot": 2}],
        ylabel="stores per year",
        title="Departures held steady. New sign-ups halved.", subtitle="small grocery stores per year")

    fig(6, "lapsed-and-returned",
        "Share of each format's stores that lost authorization and later regained it.",
        figures.hbar_png,
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 4 if f == "Grocery (Small)" else 0}
         for f in ["Grocery (Medium)", "Convenience Store", "Grocery (Small)",
                   "Supermarket", "Dollar Store"] if f in lap], suffix="%",
        title="Some stores drop out and come back", subtitle="share that lost authorization, then regained it")

    fig(7, "states",
        f"Largest percentage falls in authorized small grocers, {arc['peak_year']} to 2025, "
        "among states with at least 150 at peak.",
        figures.hbar_png,
        [{"label": f"{t['state']}  {t['then']:,}→{t['now']:,}", "value": abs(t["pct"]),
          "slot": 4 if t["state"] == "NY" else 0} for t in st[:8]], suffix="%",
        title="New York lost the most, by a wide margin", subtitle="fall in authorized small grocers, 2012 to 2025")

    ecm = {r["format"]: r for r in d["entry_change"]}
    co, dl = ecm["Combination Grocery/Other"], ecm["Dollar Store"]
    md, sm = ecm["Grocery (Medium)"], ecm["Supermarket"]
    fig(8, "entry-change-by-format",
        "Change in new SNAP authorizations per year, 2012-13 average against 2018-19 average.",
        figures.hbar_png,
        [{"label": r["format"], "value": abs(r["pct"]),
          "slot": 2 if r["format"] == "Combination Grocery/Other"
                  else (1 if r["format"] == "Dollar Store" else 0)}
         for r in sorted(d["entry_change"], key=lambda r: r["pct"])], suffix="%",
        title="Independents fell. The dollar chains did not.", subtitle="change in new sign-ups per year, 2012-13 vs 2018-19")

    cb, mix = d["cbp"], d["entry_mix"]
    fig(9, "cbp-vs-snap",
        f"Percentage decline, {cb['base_year']} to {cb['last_year']}. Census establishment counts "
        "against SNAP authorizations.",
        figures.hbar_png, [
            {"label": "Census, all grocery", "value": abs(cb["cbp_total_pct"]), "slot": 0},
            {"label": "Census, under 5 staff", "value": abs(cb["cbp_under5_pct"]), "slot": 1},
            {"label": "Census, under 10 staff", "value": abs(cb["cbp_under10_pct"]), "slot": 1},
            {"label": "SNAP Small + Medium", "value": abs(cb["snap_small_mid_pct"]), "slot": 3},
            {"label": "SNAP Small only", "value": abs(cb["snap_small_pct"]), "slot": 2}], suffix="%",
        title="Census says 22%. SNAP's Small category says 46%.",
        subtitle="decline 2012 to 2023")
    fig(10, "classification-shift",
        "Share of new SNAP grocery authorizations classified Medium rather than Small.",
        figures.hbar_png,
        [{"label": m["period"], "value": m["medium_share"],
          "slot": 2 if m["period"] == "2018-2021" else 0} for m in mix], suffix="%",
        title="Census says 22%. SNAP's Small category says 46%.", subtitle="decline 2012 to 2023")

    exit_change = 100 * (dr["exit_rate_after"] / dr["exit_rate_before"] - 1)
    md = f"""# SNAP shows small grocers down 46%. The census says 22%. Both are right.

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

![{figs["small-grocery-arc"]['caption']}](images/{figs["small-grocery-arc"]['file']})

That is a big drop, and "the death of the small grocer" is the obvious way to read it. But these records only show stores leaving the program. That is not the same as stores closing. Three other things could produce the same chart, so we tested each one.

## It is not grocery in general

If shoppers were just switching to superstores, every size of grocery store would sag. None of the others do. Here is each format on the same axis:

![{figs["grocery-formats"]['caption']}](images/{figs["grocery-formats"]['file']})

The same thing as start-and-end numbers:

![{figs["format-change-table"]['caption']}](images/{figs["format-change-table"]['file']})

Medium grocery ended **{ctx['Grocery (Medium)']['change_pct']:+.0f}%**, superstores
**{ctx['Super Store']['change_pct']:+.0f}%**, supermarkets
**{ctx['Supermarket']['change_pct']:+.0f}%**. Only the smallest format fell. Whatever happened,
happened to small stores specifically.

## Existing stores were not re-registered under a new type

USDA sorts stores by how much staple food they stock. So a store could move out of "small grocery" without changing at all. We can test that here. A store's type never changes inside its own record. A re-sorted store therefore has to show up as a *new* record at the *same address*. If it also keeps the same name, that is one business signing up again — not a new tenant.

Of {rc['exits']:,} small-grocery exits between 2012 and 2022, {rc['with_successor']:,} had another
store show up at the same address. Among {rc['successor_pairs']:,} successor pairs, just
**{rc['same_name_diff_type']:,}** share the name and differ in type — {100*rc['share_of_pairs']:.1f}%
of pairs, and **{100*rc['share_of_exits']:.1f}% of all exits**.

![{figs["successor-formats"]['caption']}](images/{figs["successor-formats"]['file']})

So signing up again is real, but small. Hold onto that number. A different kind of re-sorting turns up later, and it is much bigger. What the table does show is churn. The most common replacement at a departed small grocer's address is a convenience store. The second most common is another small grocery. The storefront often keeps selling food, just under a new owner and a new label.

## Departures did not spike. Arrivals collapsed.

This is the part that surprised me. If stores were leaving faster, departures should spike. They did not. The number leaving each year is *lower* now than in 2008. What collapsed was arrivals. Both lines are below:

![{figs["entries-vs-exits"]['caption']}](images/{figs["entries-vs-exits"]['file']})

New authorizations fell from {dr['new_before']:,.0f} a year in 2009–2013 to {dr['new_after']:,.0f} in
2016–2020, a drop of **{100*(dr['new_after']/dr['new_before']-1):.0f}%**. Departures fell {abs(100*(dr['dep_after']/dr['dep_before']-1)):.0f}% over the same period. But the pool of stores was shrinking too. So the *rate* at which any one store left actually rose, from {dr['exit_rate_before']:.0%} to {dr['exit_rate_after']:.0%}.

Both sides moved, but entry is the bigger one. Small grocery did not start leaving faster. It stopped being replaced. These stores have always churned hard, because a corner shop runs on thin margins. For years, enough new ones opened to cover the losses. After 2014 they stopped.

The timing points somewhere specific, but the detail matters. The 2014 Farm Bill told USDA to raise stocking rules. Stores would need seven kinds of food in each staple category instead of three, and fresh food in three categories instead of two. Congress then **blocked** both changes. A May 2017 spending rider (P.L. 115-31, §765) sent USDA back to three and two.

Something quieter did take effect in January 2018. Stores now had to keep **three units of every kind** of staple food in stock. That works out to 36 items on the shelf at all times. USDA also narrowed which foods counted at all. For a big chain that is a shelf plan. For a small store with little space and little cash, it is a permanent bill.

## The bar sorted by owner, not by format

Here is the part that makes the policy story believable, and it is not what I expected. The stocking rules cover every store judged on its inventory. That includes dollar stores and drug stores, not just grocers. So if the rule mattered, its mark should show up across formats. It does. But it follows a different line than you would guess. This chart is the change in new sign-ups per year, by format:

![{figs["entry-change-by-format"]['caption']}](images/{figs["entry-change-by-format"]['file']})

Compare the top and bottom rows. **Combination Grocery/Other** is where USDA files stores that mainly sell general goods. New sign-ups there fell {abs(co['pct']):.0f}%, the steepest of any format. **Dollar stores fell {abs(dl['pct']):.0f}%.** Now the catch. Dollar stores *are* Combination Grocery/Other. USDA files them in that exact category. They only sit on their own line here because we picked them out by brand name.

Same rule. Same USDA category. Opposite results. The independents in that bucket collapsed. The chains inside it barely moved. Medium grocery and supermarkets were nearly untouched, at {abs(md['pct']):.0f}% and {abs(sm['pct']):.0f}%. Those stores already carried deep stock.

That points at the cost of complying, not at the format. For a chain, 36 items on the shelf is a shelf plan. Decide once, send it to twenty thousand stores, and spread the cost of a cooler across all of them. Dollar General was adding coolers in these very years anyway. For one corner store, the same rule means cash tied up in stock and food that may spoil, with nothing to spread it across.

This is still a likely cause, not a proven one. Two things argue for caution. New sign-ups start falling in 2014, before the rule took effect, so something else is at work too. And these records never say why an authorization ended.

## The question these records cannot answer

One explanation survives all three tests. It is also the one this data cannot settle. A store that closes and a store that stays open but drops EBT look exactly the same here. Both are just an authorization that ended.

We know the second thing happens, because some stores do it and come back:

![{figs["lapsed-and-returned"]['caption']}](images/{figs["lapsed-and-returned"]['file']})

**{100*lap['Grocery (Small)']['rate']:.1f}%** of small grocers have gone unauthorized and returned,
median gap {lap['Grocery (Small)']['median_gap_days']} days. Those stores were plainly open the whole
time. And that is a floor, not an estimate.

## So we asked a source that counts businesses instead

The Census Bureau counts *business locations* — every grocery store with staff, whether or not it takes EBT. That gives us a clean test. If locations held steady while authorizations halved, stores left the program. If both fell together, stores closed. Here are the two counts side by side:

![{figs["cbp-vs-snap"]['caption']}](images/{figs["cbp-vs-snap"]['file']})

Grocery locations with fewer than five staff fell **{abs(cb['cbp_under5_pct'])}%**. Under ten staff, **{abs(cb['cbp_under10_pct'])}%**. Those businesses are gone, not just out of the program. So a real share of the headline drop is genuine. Grocery of all sizes fell only {abs(cb['cbp_total_pct'])}%, which puts the losses in the smallest stores. The SNAP data said the same thing.

Now look at the two SNAP rows. **Small and Medium grocery together fell {abs(cb['snap_small_mid_pct'])}%.** That is within a point of the census figure. **Small alone fell {abs(cb['snap_small_pct'])}%.** So SNAP is right about small grocery businesses. It is wrong about its own Small category. That can only mean one thing: the line between Small and Medium moved.

## The definition moved, and the same rule moved it

It did move, and you can watch it happen. This chart is the share of new grocery stores USDA filed as Medium rather than Small.

![{figs["classification-shift"]['caption']}](images/{figs["classification-shift"]['file']})

For a decade, about {mix[1]['medium_share']:.0f}% of new grocery sign-ups were filed as Medium. In 2018–21 that jumped to **{mix[3]['medium_share']:.0f}%**. Recall the 2018 rule: 36 items on the shelf at all times. In USDA's own words, a store holding that much stock has a "moderate selection" rather than a small one. The floor for joining the program rose above what "Small" used to mean.

This is not the same thing we tested earlier. Existing stores signing up under a new type is rare, at {100*rc['share_of_exits']:.1f}% of exits. What moved is where the line sits for *new* stores. Both are true, and only the second shows up in the totals.

So the answer comes in three parts. Small grocery really did shrink, by about a quarter. SNAP's own Small category fell twice that far, because the rule that drove part of the shrinking also redrew the category. And the stores that went were mostly the ones too small to absorb a new fixed cost.

## Where it happened

The drop is not spread evenly. New York lost far more small grocers than any other state:

![{figs["states"]['caption']}](images/{figs["states"]['file']})

New York went from {st[0]['then']:,} to {st[0]['now']:,}, a fall of {abs(st[0]['pct']):.0f}%. A state
with that many small groceries is a state of bodegas and corner stores, and it absorbed the largest
share of whatever changed.

## Limits

Every figure here counts **authorizations**. "Left SNAP" is the strongest claim the data supports;
"closed" is not, except where an outside source can corroborate it.

The address test matches exactly on street number, street name, city and state. Stores whose address was typed differently in two records will be missed. So {100*rc['share_of_exits']:.1f}% is a floor, not a full count.

The stocking rule is offered as a likely explanation, based on timing and shape. These records carry no reason code, so this source alone cannot confirm it.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
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
