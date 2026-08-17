"""Assemble reports/post7/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

LADDER = ["Small Grocery Store", "Convenience Store", "Combination Grocery/Other",
          "Medium Grocery Store", "Supermarket", "Large Grocery Store"]

SRC = ROOT / "reports" / "data" / "post7.json"
DIR = ROOT / "reports" / "post7"
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

    P = d["policy"]
    tfp, o, n, im = P["tfp"], P["old_standard"], P["new_standard"], P["impact"]
    nfa, dg = P["need_for_access"], P["dollar_general"]
    pre, tm = d["precedent"], d["thin_markets"]
    surv = {r["segment"]: r for r in d["survival"]}
    eu = {r["store_type"]: r for r in d["entry_change_usda"]}
    den, tl = tm["density"], tm["total_loss"]

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{im['stores_losing_authorization']:,}",
          "label": "stores USDA expects to lose SNAP authorization, against "
                   f"{im['baseline_annual_losses']:,} in a normal year"},
         {"value": f"${im['cost_year_one']}",
          "label": "what USDA estimates it costs a store to comply in the first year"},
         {"value": n["compliance"].replace(" 2026", ""),
          "label": "the 2026 date by which every SNAP retailer has to meet it"}])

    fig(1, "standard-change",
        "What the stocking standard requires, before and after November 2026.",
        figures.table_png, ["Requirement", "Until now", "From November"],
        [["Varieties in each of four categories",
          str(o["varieties_per_category"]), str(n["varieties_per_category"])],
         ["Categories needing a perishable food",
          str(o["perishable_categories"]), str(n["perishable_categories"])]],
        title="The bar more than doubles in November",
        subtitle="what a SNAP store must stock")

    fig(2, "entry-vs-exit-2018",
        "New authorizations and departures for small grocery stores. The last time stocking "
        "standards tightened, the entry line moved and the exit line did not.",
        figures.line_png, pre["years"],
        [{"name": "new authorizations", "values": pre["new"], "slot": 1},
         {"name": "departures", "values": pre["departed"], "slot": 2}],
        ylabel="small grocery stores per year",
        annotate=[{"year": 2018, "text": "2018 standard"}],
        title="Last time the rules tightened, new sign-ups fell",
        subtitle="small grocery stores per year")

    fig(3, "size-ladder",
        "Change in new SNAP sign-ups per year, 2012-13 average against 2018-19 average, by "
        "USDA's own store type.",
        figures.table_png, ["USDA store type", "Change in new sign-ups"],
        [[typ, f"{eu[typ]['pct']:+.0f}%"] for typ in LADDER if typ in eu],
        title="The fall sorts by how much stock a store carries",
        subtitle="new sign-ups per year, 2012-13 vs 2018-19")

    fig(4, "positions",
        "Who took a public position on the rule.",
        figures.table_png, ["Organisation", "Represents", "Position"],
        [[p["who"], p["represents"], p["stance"]] for p in P["positions"]],
        align=["left", "left", "right"],
        title="Stores that already comply are in favour",
        subtitle="public positions on the rule")

    md = f"""# In November, the rules change for the stores that are left

*An epilogue. The Thrifty Food Plan, the new SNAP stocking standard, and a prediction made before the
deadline.*

**{im['stores_losing_authorization']:,}** stores USDA expects to lose SNAP authorization under the new
standard, against {im['baseline_annual_losses']:,} in a normal year.
**${im['cost_year_one']}** what USDA estimates it costs a store to comply in the first year.
**{n['compliance']}** the day every SNAP retailer has to meet it.

![Headline figures](images/00-key-figures.png)

---

The six chapters before this one are measurement. This piece is not. It is about a policy that rests on an assumption the measurement has quietly undercut. And about a rule that takes effect in a few months.

Two things here cannot be settled with this data, and both are labelled where they appear.

## The benefit is a shopping list

The size of a SNAP benefit is not chosen. It is calculated. USDA builds a shopping list called the
**Thrifty Food Plan**, prices it, and that price becomes the maximum monthly allotment. The plan was
re-evaluated in {tfp['reevaluated']} for the first time since {tfp['previous']}, as Congress directed in
the {tfp['directive']}.

It is a real list, built to be cheap. It is priced for a family of four: {tfp['reference_family']}. Seafood is the most expensive category on it, at about **${tfp['seafood_weekly_cost']:.2f} a week**. The plan keeps that cost down by assuming cheap choices. It names **tilapia or canned tuna** as its examples. Someone worked out that a family on the lowest
food budget the government models could buy frozen tilapia.

Now notice what the plan does not model. It prices the basket at national average prices. It assumes a
working kitchen, time to cook, storage space, and a way to get to a store. It does not ask whether any
store within reach of a household actually carries the items on the list.

## SNAP's bar for a store is far lower than its own basket

Until this year the bar was low. A store needed three kinds of food in each of four staple categories, three units of each. That is **{o['total_items']} items** in total, of which {o['perishable_items']} had to be perishable, spread across at least {o['perishable_categories']} categories. That is the floor. A store can be fully SNAP-authorized
and carry a small fraction of the basket the benefit was priced from.

Put that beside what this series found. In {tl['no_grocery']} of the ZIP codes that lost their last chain
pharmacy, the only SNAP-authorized food retail left is a dollar store or a convenience store. Both are
formats built around a narrow, shelf-stable assortment.

So the question is simple, and **we cannot answer it**: how much of the Thrifty Food Plan can actually be
bought in these places? There are no shelves in this data. We know where the stores are and what type they
are; we have no idea what is inside them. Anyone offering a number here is guessing, and we are not going
to.

But the question did not use to matter as much, and now it does. The benefit is calculated as though a
household shops somewhere that stocks a full-line basket. In a growing number of places, the store that
stocks a full-line basket is the one that left.

## What changes in November

The floor is about to move. Congress ordered a seven-variety standard back in the {n['directive']}. Then it blocked the same standard in 2017. Now USDA has finalized it. It takes effect **{n['effective']}**, and every authorized store must comply by **{n['compliance']}**.

![{figs["standard-change"]['caption']}](images/{figs["standard-change"]['file']})

The four categories are {n['category_names']}. The variety requirement more than doubles.

USDA has published its own forecast. It expects about **{im['stores_losing_authorization']:,} stores to lose SNAP authorization**. In a normal year about {im['baseline_annual_losses']:,} do. So by the agency's own math, that is a {im['multiple']}-fold jump. Around **{im['small_format_share_pct']}%** of all SNAP retailers are the
small formats most exposed: convenience stores, small grocers, and the combination stores that include
dollar stores.

## Two problems with that forecast

**The first is the cost.** USDA put compliance at about **${im['cost_year_one']} in the first year** and
${im['cost_five_years']} over five years for a store that needs to add varieties. That figure is what let
the agency conclude the rule has "{im['rfa_finding']}".

But the requirement that actually bites is not the seven varieties. A small store can stock seven
shelf-stable varieties in each category without much trouble. It is that perishable foods must now appear
in **{n['perishable_categories']}** of the four categories rather than {o['perishable_categories']}.
Perishable means refrigeration. A commercial cooler does not cost ${im['cost_year_one']}. If that is the
binding constraint, the agency has priced the easy half of its own rule.

**The second is that a store can be spared.** A third authorization pathway, **"need for access"**
({nfa['citation']}), lets USDA keep a store in the program if it sits where food access is significantly
limited. The agency weighs several things: {nfa['factors']}. It can also weigh, in the regulation's own words, "{nfa['catchall']}".

That provision could protect exactly the stores this series has been describing. But it is discretionary,
and **USDA has not published the scoring methodology it uses**. So whether those stores survive is an
administrative decision that currently cannot be audited from outside.

## A prediction, before the deadline

We are writing this before {n['compliance']}, which means we can say what we expect and then be checked
against it. That seems fairer than explaining it afterwards.

**First: it will look like an entry collapse, not a wave of closures.** This is the clearest prediction,
because it already happened. When stocking standards last tightened in 2018, new small-grocery
authorizations fell **{abs(pre['entry_pct']):.0f}%** while departures fell {abs(pre['exit_pct']):.0f}% —
that is, exits did not rise at all. A rule that raises the bar mostly stops the next store from starting.

![{figs["entry-vs-exit-2018"]['caption']}](images/{figs["entry-vs-exit-2018"]['file']})

**Second: the losses will fall on the stores that carry the least stock.** A stocking rule asks for a fixed amount of inventory. That is a large demand on a small store and no demand at all on a big one. When the standard last tightened, the fall sorted by exactly that, in USDA's own categories:

![{figs["size-ladder"]['caption']}](images/{figs["size-ladder"]['file']})

It is tempting to shorten this to "chains will be fine, independents will not." The record does not support that cleanly. Inside the one USDA category that holds both, the non-dollar chains fell as far as the independents did — and those chains are Walgreens, CVS, Rite Aid, Big Lots and Fred's, so their fall is tangled up with a bankruptcy and a liquidation. Scale helps a store stay in the program once it is in. It did not decide who stopped signing up.

**Third: the access consequences will concentrate in the places in this series.** Losing one authorized
store matters little in a city. It matters a great deal in a ZIP code of
{den['lost_no_grocery']['median_pop']:,} people with no grocery store left.

## Who argued about this, and who did not

![{figs["positions"]['caption']}](images/{figs["positions"]['file']})

That line-up is worth sitting with. The formats that already meet the standard are for it. The formats that do not are against it. Whatever the rule does for nutrition, it also hands an advantage to stores that already carry a full range.

The dollar store chains said nothing in public at all. Their actions point both ways. The largest of them has put SNAP payment on delivery apps for more than {dg['ebt_delivery_stores']:,} of its stores. Yet it sells fresh produce in fewer than one in three of them, and it is slowing that rollout down.

There is precedent for what happens next. A version of this rule was proposed in 2019. It drew more than {P['precedent_2019']['opposing_comments']:,} comments against it. Most were about the same worry: {P['precedent_2019']['theme']}.

## What we will do about it

Every figure in this series comes from a file USDA updates. When it updates, the same code that made these charts will show which stores lost authorization. By format, by ZIP code, and by how many people live there. It will also show whether {im['stores_losing_authorization']:,} was close.

We will publish that either way.

None of this argues for a particular policy. It argues something narrower. A benefit priced from a basket is only as good as the nearest store's willingness to stock that basket. And the economics under that assumption have moved a long way in twenty years. If the formats that survive in thin
markets are the ones never designed to sell a week of groceries, then the question is not only how much
money a household gets. It is how food reaches people who have the fewest ways to go and get it.

## Limits

**The Thrifty Food Plan question is a question, not a finding.** This data cannot see inside a store, so no
estimate is made of how much of the plan's basket is stocked anywhere. Measuring that needs shelf-level
audit data — the kind collected by in-store surveys such as NEMS-S, not by an authorization file. The
stocking standards and the plan's assumptions are cited so the gap between them can be checked, not to
imply it has been measured.

**We describe effects, not motives.** USDA's stated purpose for the rule is nutrition. Nothing here claims
it is intended to reduce program spending, and this data could not establish intent if it were. Note also
that fewer authorized stores does not by itself reduce SNAP benefits, which are set by household size and
income against the Thrifty Food Plan price. Any spending effect would run indirectly, through households
finding the program harder to use — which this data cannot observe either.

**The predictions are predictions.** They follow from patterns measured in earlier chapters, not from any
knowledge of how USDA will administer the rule. The "need for access" pathway gives the agency wide
discretion, and a determined effort to protect rural stores could make all three wrong. That would be a
good outcome and we would report it as one.

The compliance-cost and store-loss figures are USDA's own. We have not independently estimated either.

---

*Sources: {tfp['source']}. {o['source']}. {n['source']} (docket {n['docket']}, effective {n['effective']},
compliance {n['compliance']}). {im['source']}. Need-for-access pathway at {nfa['citation']}. Trade
association positions from published statements by FMI and the National Grocers Association and the joint
comments of NACS, NATSO and SIGMA filed 24 November 2025. {dg['source']}. Store-count and survival figures
from USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, using 656,868 stores with usable
coordinates. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post7.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post7.html", DIR / "post7-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post7.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
