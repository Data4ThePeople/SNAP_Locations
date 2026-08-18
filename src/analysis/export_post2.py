"""Assemble reports/post2/ — markdown text, PNG figures, and the HTML archive.

Four figures, matching build_post2.py. See that module's docstring for why the
ownership split was removed rather than trimmed.
"""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post2.json"
DIR = ROOT / "reports" / "post2"
IMG = DIR / "images"

# Super Store is deliberately absent. Its new authorizations fell 36%, and most
# of that is Walmart — 168 a year to 10 — pausing a supercenter program that was
# already built out. A supercenter clears any stocking floor without trying, so
# the rule cannot be what moved it, and leaving the row in a table about store
# size invites the reader to think it can. Called out in the limits instead.
LADDER = ["Small Grocery Store", "Convenience Store", "Combination Grocery/Other",
          "Medium Grocery Store", "Supermarket", "Large Grocery Store"]


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    arc, cb = d["arc"], d["cbp"]
    st = d["states"]
    eu = {r["store_type"]: r for r in d["entry_change_usda"]}
    lap = next(r for r in d["lapse"] if r["format"] == "Grocery (Small)")
    yrs = d["flows"]["years"]

    # One comparison everywhere: the 2012-13 vs 2018-19 windows the size-ladder
    # table uses, so the prose cannot disagree with the figure below it.
    sg = eu["Small Grocery Store"]
    entry_drop = round(sg["pct"])
    dep = dict(zip(yrs, d["flows"]["departed"]))
    dep_before = (dep[2012] + dep[2013]) / 2
    dep_after = (dep[2018] + dep[2019]) / 2
    exit_drop = round(100 * (dep_after / dep_before - 1))

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{abs(cb['cbp_under10_pct']):.0f}%",
          "label": f"fall in small grocery businesses, {cb['base_year']} to "
                   f"{cb['last_year']}, by the Census Bureau's count"},
         {"value": f"{abs(cb['snap_small_pct']):.0f}%",
          "label": f"fall in SNAP's own Small Grocery category, {cb['base_year']} "
                   f"to {cb['last_year']}"},
         {"value": f"{abs(entry_drop)}%",
          "label": "fall in small grocers signing up for SNAP each year, "
                   "2012–13 to 2018–19"}])

    fig(1, "small-grocery-arc",
        "Small grocery stores with an active SNAP authorization on 31 December of each year.",
        figures.line_png, yrs,
        [{"name": "small grocery stores", "values": d["flows"]["stock"], "slot": 1}],
        ylabel="stores authorized on 31 December",
        title="Authorized small grocers fell by nearly half")

    fig(2, "census-vs-snap",
        f"Percentage change, {cb['base_year']} to {cb['last_year']}. Census business counts "
        "against SNAP authorizations.",
        figures.hbar_png, [
            {"label": "Census, all grocery", "value": cb["cbp_total_pct"], "slot": 1},
            {"label": "Census, under 5 staff", "value": cb["cbp_under5_pct"], "slot": 1},
            {"label": "Census, under 10 staff", "value": cb["cbp_under10_pct"], "slot": 1},
            {"label": "SNAP, all grocery", "value": cb["snap_all_pct"], "slot": 2},
            {"label": "SNAP, Small only", "value": cb["snap_small_pct"], "slot": 2}],
        suffix="%", direction="left",
        title="The businesses fell a quarter. SNAP's Small category fell twice that.",
        subtitle=f"change {cb['base_year']} to {cb['last_year']}")

    fig(3, "size-ladder",
        "Change in new SNAP sign-ups per year, 2012-13 average against 2018-19 average, by "
        "USDA's own store type.",
        figures.table_png, ["USDA store type", "Change in new sign-ups"],
        [[t, f"{eu[t]['pct']:+.0f}%"] for t in LADDER if t in eu],
        title="The fall sorts by store size",
        subtitle="new sign-ups per year, 2012-13 vs 2018-19")

    fig(4, "states",
        f"Largest percentage falls in authorized small grocers, {arc['peak_year']} to 2025, "
        "among states with at least 150 at peak.",
        figures.hbar_png,
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": r["pct"],
          "slot": 2 if r["state"] == "NY" else 0} for r in st[:8]], suffix="%",
        direction="left",
        title="New York lost the most, by a wide margin",
        subtitle=f"change in authorized small grocers, {arc['peak_year']} to 2025")

    md = f"""# One in four of the smallest grocery stores is gone

*SNAP-authorized retailers, 2006–2025, checked against Census County Business Patterns.
{arc['peak']:,} small grocery stores in {arc['peak_year']}, {arc['latest']:,} today.*

**{abs(cb['cbp_under10_pct']):.0f}%** fall in the number of small grocery businesses,
{cb['base_year']} to {cb['last_year']}, by the Census Bureau's count.
**{abs(cb['snap_small_pct']):.0f}%** fall in SNAP's own Small Grocery category,
{cb['base_year']} to {cb['last_year']}.
**{abs(entry_drop)}%** fall in the number of small grocers signing up for SNAP each year,
2012–13 to 2018–19.

![Headline figures](images/00-key-figures.png)

---

Small grocery stores are leaving the SNAP program in large numbers. The obvious way to read that is
that the neighborhood grocery store is dying. That turns out to be partly true, and the honest
version is more useful than the headline.

## How much of the drop is real

Start with what the SNAP records show. Stores authorized as small grocers peaked at {arc['peak']:,}
in {arc['peak_year']}. They bottomed at {arc['trough']:,} in {arc['trough_year']} and sit at
{arc['latest']:,} today.

![{figs["small-grocery-arc"]['caption']}](images/{figs["small-grocery-arc"]['file']})

That is a fall of **{abs(cb['snap_small_pct']):.0f}%**. Before taking that number at face value, we
checked it against a source that counts businesses instead of paperwork. The Census Bureau counts
every grocery store with staff, whether or not it takes EBT.

![{figs["census-vs-snap"]['caption']}](images/{figs["census-vs-snap"]['file']})

The census says the smallest grocery businesses fell **{abs(cb['cbp_under5_pct'])}%** if you count
those with under five staff, and **{abs(cb['cbp_under10_pct'])}%** under ten. Not 46%.

Why the two counts disagree, we can't say for certain. But here is what we do know.

First, the USDA only counts stores authorized to accept SNAP. The census counts stores. As we
discussed yesterday, these are not the same. A store could drop SNAP if it became too onerous to
maintain eligibility and still continue to operate.

Second, the size definitions are totally different. USDA defines a small grocer as one that
"carries a small selection of all four staple food categories." The census categorizes stores by
employee count. Different measures (one not even quantitative) would produce different results.

So, if we are trying to quantify the decline in small grocery stores, we'd use the census's data as
a conservative estimate. But that is easy for us to write as we sit at our desks next to a fridge
full of food. If you rely on SNAP, the **{abs(cb['snap_small_pct']):.0f}%** decline in small
grocery stores is the real number.

## It happened by stores not opening

The next question is how they went. If small grocers were being pushed out, we would expect a rise
in the number of stores dropping their SNAP authorization. That is not what happened.

The decline was driven by the other side of the ledger: a steep fall in new grocers signing up to
replace natural attrition. Sign-ups dropped from about {sg['before']:,.0f} a year to
{sg['after']:,.0f} — a **{abs(entry_drop)}%** decline in six years. The number of stores losing
their authorization each year actually fell {abs(exit_drop)}%. That paints a different picture —
not incumbent grocers being shoved out of the market, but new small grocers no longer showing up
to take their place.

![{figs["size-ladder"]['caption']}](images/{figs["size-ladder"]['file']})

The small formats collapsed. The large ones did not move, and the largest grocery category actually
grew. That is the shape a stocking requirement would produce: the rule asks for a fixed amount of
inventory, which is a large demand on a small store and no demand at all on a big one.

**While this would be a neat and tidy explanation for this table, sadly we can't prove it with the
data we have.** New sign-ups had been falling since 2012, years before
the rule took effect in 2018, so something else is at work too. And these records carry no field for why an authorization
ended. We can show the shape and the timing. We cannot show the reason.

## It is not happening evenly

The decline is concentrated. New York lost more small grocers than any other state, by a wide margin.

![{figs["states"]['caption']}](images/{figs["states"]['file']})

New York went from {st[0]['then']:,} to {st[0]['now']:,}, a fall of {abs(st[0]['pct']):.0f}%. Nearly
all of that is New York City: the five boroughs (packed with bodegas and corner stores) held
{d['nyc']['then']:,} of those stores in {arc['peak_year']} and account for
{d['nyc']['share_of_loss']:.0%} of the loss.

## What it adds up to

No matter how you count it, the past decade has been hard on small grocery stores. SNAP's own records say the category fell {abs(cb['snap_small_pct']):.0f}%. The census says the businesses fell about a quarter. Either way, thousands of the smallest food stores in the country are gone, and almost none of the loss landed on the big ones.

The best explanation we have is a rule that was meant to help shoppers. Making every SNAP store keep 36 staple items in stock at all times means someone walking in with an EBT card finds real food on the shelf. That is a sensible aim. But it asks the same of a corner store as of a supermarket. A chain writes the shelf plan once and spreads the cost over thousands of stores. A single shop pays it alone, in cash tied up in stock and food that may spoil. We cannot prove that is what happened. The timing and the shape both fit.

There is another small format worth looking at before drawing any conclusions. A dollar store is a small box too: narrow range, few staff, cheap to run. Everything a small grocer is. Did it meet the same fate? Or did it find a way to thrive in a system that rewards size?

**Tomorrow: the dollar store.**

## Limits

**"Left SNAP" is the strongest claim these records support.** A store that closes and a store that
stays open but stops taking EBT look identical here. That is why the census check matters, and why
the headline number is the census one.

Some stores do drop out and come back: **{100*lap['rate']:.1f}%** of small grocers lost their
authorization and later regained it, with a median gap of {lap['median_gap_days']} days. Those stores
were plainly open the whole time.

The Census Bureau counts businesses with paid employees. A grocery store run entirely by its owner
with no payroll is not in that count, so the comparison covers employer businesses only.

One category is left out of that table. New Super Store authorizations also fell, by 36%, and most of that is Walmart — from about 168 a year to 10 — pausing a supercenter program that was already close to complete. A store that size meets any stocking requirement without trying, so the rule cannot be what moved it.

The stocking rule is offered as a likely explanation, on timing and shape. These records carry no reason code, so this source alone cannot confirm it.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and Census County Business
Patterns, NAICS 445110. Analysis uses 656,868 stores with usable coordinates; a store counts as
active in a year if an authorization covered 31 December. Entries and exits count stores, not
authorization spells, so a store that lapsed and resumed is not double-counted. Code, pipeline and
verification: [Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post2.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post2.html", DIR / "post2-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post2.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
