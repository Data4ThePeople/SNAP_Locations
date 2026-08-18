"""Render reports/post2.html from reports/data/post2.json.

Three sections, four figures. The piece used to carry eleven, and the extra
seven were tests that ruled things out rather than steps in the argument.

The spine:
  1. authorizations fell 46%, but the businesses fell about a quarter — and a
     quarter is the number that matters
  2. it happened by stores not opening, and it sorts by store size
  3. it is not evenly spread

Deliberately absent: any split by owner. An earlier version claimed the decline
sorted by chain versus independent inside USDA's Combination Grocery/Other. It
does not — the non-dollar chains in that category fell 60.5% against the
independents' 62.6%, and those chains are Walgreens, CVS, Rite Aid, Big Lots and
Fred's, so their fall is entangled with a bankruptcy and a liquidation. Only the
dollar chains held up, and they opened at a near-constant rate for sixteen years
regardless of anything. The size gradient in USDA's own categories says what
that claim was trying to say, and says it correctly.
"""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post2.json"
OUT = ROOT / "reports" / "post2.html"

# USDA's own store types, largest fall first. No brand breakout: "Dollar Store"
# is our label, not USDA's, and this section is about USDA's categories.
# Super Store is deliberately absent. Its new authorizations fell 36%, and most
# of that is Walmart — 168 a year to 10 — pausing a supercenter program that was
# already built out. A supercenter clears any stocking floor without trying, so
# the rule cannot be what moved it, and leaving the row in a table about store
# size invites the reader to think it can. Called out in the limits instead.
LADDER = ["Small Grocery Store", "Convenience Store", "Combination Grocery/Other",
          "Medium Grocery Store", "Supermarket", "Large Grocery Store"]


def main():
    d = json.loads(DATA.read_text())
    palette.validate(3, "light", verbose=False)
    palette.validate(3, "dark", verbose=False)

    arc, cb = d["arc"], d["cbp"]
    mix, st = d["entry_mix"], d["states"]
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
    med_lo = min(m["medium_share"] for m in mix)
    med_hi = max(m["medium_share"] for m in mix)

    c_arc = charts.line_chart(
        yrs, [{"name": "small grocery stores", "values": d["flows"]["stock"], "slot": 1}],
        y_label="stores authorized on 31 December",
        title="Authorized small grocers fell by nearly half")

    c_gap = charts.bar_chart([
        {"label": "Census, all grocery", "value": cb["cbp_total_pct"], "slot": 0},
        {"label": "Census, under 5 staff", "value": cb["cbp_under5_pct"], "slot": 1},
        {"label": "Census, under 10 staff", "value": cb["cbp_under10_pct"], "slot": 1},
        {"label": "SNAP Small + Medium", "value": cb["snap_small_mid_pct"], "slot": 3},
        {"label": "SNAP Small only", "value": cb["snap_small_pct"], "slot": 2},
    ], suffix="%", direction="left",
        title="The businesses fell a quarter. SNAP's Small category fell twice that.",
        subtitle=f"change {cb['base_year']} to {cb['last_year']}")

    ladder_rows = "".join(
        f"<tr><td>{t}</td><td>{eu[t]['pct']:+.0f}%</td></tr>"
        for t in LADDER if t in eu)

    c_states = charts.bar_chart(
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": r["pct"],
          "slot": 2 if r["state"] == "NY" else 0} for r in st[:8]], suffix="%",
        direction="left",
        title="New York lost the most, by a wide margin",
        subtitle=f"change in authorized small grocers, {arc['peak_year']} to 2025")

    html = f"""{HEAD}<title>One in four of the smallest grocery stores is gone</title>
<style>{CSS}</style>
<main>
<h1>One in four of the smallest grocery stores is gone</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025, checked against Census County Business
Patterns · {arc['peak']:,} small grocery stores in {arc['peak_year']}, {arc['latest']:,} today</p>

<div class="ledger">
  <div><b>{abs(cb['cbp_under10_pct']):.0f}%</b><span>fall in small grocery businesses, {cb['base_year']} to {cb['last_year']}, by the Census Bureau's count</span></div>
  <div><b>{abs(cb['snap_small_pct']):.0f}%</b><span>fall in SNAP's own Small Grocery category over the same years</span></div>
  <div><b>{abs(entry_drop)}%</b><span>fall in small grocers signing up for SNAP each year</span></div>
</div>

<p>Small grocery stores are leaving the SNAP program in large numbers. The obvious way to read that
is that the neighborhood grocery store is dying. That turns out to be partly true, and the honest
version is more useful than the headline.</p>

<h2>How much of the drop is real</h2>

<p>Start with what the SNAP records show. Stores authorized as small grocers peaked at
{arc['peak']:,} in {arc['peak_year']}. They bottomed at {arc['trough']:,} in {arc['trough_year']}
and sit at {arc['latest']:,} today.</p>

<figure>{c_arc}
<figcaption>Small grocery stores with an active SNAP authorization on 31 December of each
year.</figcaption></figure>

<p>That is a fall of <strong>{abs(cb['snap_small_pct']):.0f}%</strong>. Before repeating it, we
checked it against a source that counts businesses instead of paperwork. The Census Bureau counts
every grocery store with staff, whether or not it takes EBT.</p>

<figure>{c_gap}
<figcaption>Percentage change, {cb['base_year']} to {cb['last_year']}. Census business counts
against SNAP authorizations.</figcaption></figure>

<p>The census says the smallest grocery businesses fell
<strong>{abs(cb['cbp_under5_pct'])}%</strong> if you count those with under five staff, and
<strong>{abs(cb['cbp_under10_pct'])}%</strong> under ten. Not 46%.</p>

<p>The gap is not stores quietly leaving the program. It is USDA's own dividing line moving. Look at
the fourth bar: <strong>Small and Medium grocery together fell
{abs(cb['snap_small_mid_pct'])}%</strong>, within a point or two of the census. If small grocers
were dropping out of SNAP in numbers, that combined figure would have fallen much further than the
census too. It did not. Stores were most likely being filed as Medium instead of Small.</p>

<p>You can watch the line move. For a decade about {med_lo:.0f}% of new grocery stores were filed
as Medium. In 2018–21 that jumped to <strong>{med_hi:.0f}%</strong>, exactly when USDA started
requiring 36 items on the shelf at all times. A store carrying that much stock is, in USDA's own
words, closer to a "moderate selection" than a small one.</p>

<p><strong>So the real loss of "small" grocery stores over the past decade and change is probably closer to a quarter.</strong> And a quarter is a lot. Grocery of every size fell only {abs(cb['cbp_total_pct'])}%, so the losses sit almost entirely in the smallest stores — the ones most likely to be the only shop in a small town.</p>

<h2>It happened by stores not opening</h2>

<p>The next question is how they went. If small grocers were being pushed out, departures should
have spiked. They did the opposite.</p>

<p>New small grocers signing up for SNAP fell from about {sg['before']:,.0f} a year to
{sg['after']:,.0f} — <strong>{entry_drop}%</strong>. Stores leaving fell {abs(exit_drop)}%. Small
grocery did not start dying much faster. It stopped being replaced.</p>

<p>And the fall sorts by <strong>store size</strong>. These are USDA's own categories, with nothing
regrouped by us:</p>

<table><thead><tr><th>USDA store type</th><th>Change in new sign-ups per year</th></tr></thead>
<tbody>{ladder_rows}</tbody></table>

<p>The small formats collapsed. The large ones did not move, and the largest grocery category
actually grew. That is the shape a stocking requirement would produce: the rule asks for a fixed
amount of inventory, which is a large demand on a small store and no demand at all on a big one.</p>

<p><strong>This is a candidate, not a proven cause.</strong> New sign-ups had been falling since
2012, years before the rule took effect, so something else is at work too. And these records carry no field for
why an authorization ended. We can show the shape and the timing. We cannot show the reason.</p>

<h2>It is not happening evenly</h2>

<p>The decline is concentrated. New York lost more small grocers than any other state, by a wide
margin.</p>

<figure>{c_states}
<figcaption>Largest percentage falls in authorized small grocers, {arc['peak_year']} to 2025, among
states with at least 150 at peak.</figcaption></figure>

<p>New York went from {st[0]['then']:,} to {st[0]['now']:,}, a fall of
{abs(st[0]['pct']):.0f}%. A state with that many small groceries is a state of bodegas and corner
stores, and it took the largest share of whatever changed.</p>

<h2>What it adds up to</h2>

<p>No matter how you count it, the past decade has been hard on small grocery stores. SNAP's own records say the category fell {abs(cb['snap_small_pct']):.0f}%. The census says the businesses fell about a quarter. Either way, thousands of the smallest food stores in the country are gone, and almost none of the loss landed on the big ones.</p>

<p>The best explanation we have is a rule that was meant to help shoppers. Making every SNAP store keep 36 staple items in stock at all times means someone walking in with an EBT card finds real food on the shelf. That is a sensible aim. But it asks the same of a corner store as of a supermarket. A chain writes the shelf plan once and spreads the cost over thousands of stores. A single shop pays it alone, in cash tied up in stock and food that may spoil. We cannot prove that is what happened. The timing and the shape both fit.</p>

<p>There is another small format worth looking at before drawing any conclusions. A dollar store is a small box too: narrow range, few staff, cheap to run. Everything a small grocer is. Did it meet the same fate? Or did it find a way to thrive in a system that rewards size?</p>

<p><strong>Tomorrow: the dollar store.</strong></p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>"Left SNAP" is the strongest claim these records support.</strong> A store that closes
and a store that stays open but stops taking EBT look identical here. That is why the census check
matters, and why the headline number is the census one.</p>
<p>Some stores do drop out and come back: <strong>{100*lap['rate']:.1f}%</strong> of small grocers
lost their authorization and later regained it, with a median gap of {lap['median_gap_days']} days.
Those stores were plainly open the whole time.</p>
<p>The Census Bureau counts businesses with paid employees. A grocery store run entirely by its
owner with no payroll is not in that count, so the comparison covers employer businesses only.</p>
<p>One category is left out of that table. New Super Store authorizations also fell, by 36%, and most of that is Walmart — from about 168 a year to 10 — pausing a supercenter program that was already close to complete. A store that size meets any stocking requirement without trying, so the rule cannot be what moved it.</p>
<p>The stocking rule is offered as a likely explanation, on timing and shape. These records carry no reason code, so this source alone cannot confirm it.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and Census County Business
Patterns, NAICS 445110. Analysis uses 656,868 stores with usable coordinates; a store counts as
active in a year if an authorization covered 31 December. Entries and exits count stores, not
authorization spells, so a store that lapsed and resumed is not double-counted. Code, pipeline and
verification: <a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  census {cb['cbp_under10_pct']}% vs SNAP Small {cb['snap_small_pct']}%")
    print(f"  entries {entry_drop}%, exits {exit_drop}%")


if __name__ == "__main__":
    main()
