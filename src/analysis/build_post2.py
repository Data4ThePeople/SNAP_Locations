"""Render reports/post2.html from reports/data/post2.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS
from config import ROOT

DATA = ROOT / "reports" / "data" / "post2.json"
OUT = ROOT / "reports" / "post2.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(6, "light", verbose=False)
    palette.validate(6, "dark", verbose=False)

    fl, yrs = d["flows"], d["flows"]["years"]
    arc, dr, rc = d["arc"], d["drivers"], d["reclass"]
    ctx = d["context"]
    lap = {r["format"]: r for r in d["lapse"]}
    st = d["states"]

    # 1. the arc
    c_arc = charts.line_chart(yrs, [{"name": "small grocers", "values": fl["stock"], "slot": 4}],
                              y_label="active small grocery stores",
                              annotate=[{"year": arc["peak_year"], "text": "peak"},
                                        {"year": arc["trough_year"], "text": "trough"}])

    # 2. which side of the ledger moved
    s_fl = [{"name": "new authorizations", "values": fl["new"], "slot": 1},
            {"name": "authorizations ending", "values": fl["departed"], "slot": 2}]
    c_fl = charts.line_chart(yrs, s_fl, y_label="stores per year")

    # 3. every other grocery format
    picks = ["Grocery (Small)", "Grocery (Medium)", "Grocery (Large)",
             "Supermarket", "Super Store"]
    s_ctx = [{"name": f, "values": ctx[f]["stock"], "slot": 4 if f == "Grocery (Small)" else i + 1}
             for i, f in enumerate(picks)]
    c_ctx = charts.line_chart(ctx["Grocery (Small)"]["years"], s_ctx, y_label="active stores")

    # 4. successor formats
    succ_tbl = "".join(
        f"<tr><td>{t['format']}</td><td>{t['n']:,}</td><td>{t['same_name']:,}</td>"
        f"<td>{100*t['same_name']/t['n']:.0f}%</td></tr>" for t in d["successor_types"])

    # 5. lapse
    c_lap = charts.bar_chart(
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 4 if f == "Grocery (Small)" else 0}
         for f in ["Grocery (Medium)", "Convenience Store", "Grocery (Small)",
                   "Supermarket", "Dollar Store"] if f in lap], suffix="%")

    # 6. states
    worst = st[:8]
    c_st = charts.bar_chart(
        [{"label": f"{t['state']}  {t['then']:,}→{t['now']:,}", "value": abs(t["pct"]),
          "slot": 4 if t["state"] == "NY" else 0} for t in worst], suffix="%")

    ec = {r["format"]: r for r in d["entry_change"]}
    co, dl = ec["Combination Grocery/Other"], ec["Dollar Store"]
    md, sm = ec["Grocery (Medium)"], ec["Supermarket"]
    c_ec = charts.bar_chart(
        [{"label": r["format"], "value": abs(r["pct"]),
          "slot": 2 if r["format"] == "Combination Grocery/Other"
                  else (1 if r["format"] == "Dollar Store" else 0)}
         for r in sorted(d["entry_change"], key=lambda r: r["pct"])], suffix="%")

    exit_rate_change = 100 * (dr["exit_rate_after"] / dr["exit_rate_before"] - 1)

    html = f"""<title>Half of America's small grocers left SNAP. Three explanations don't hold.</title>
<style>{CSS}</style>
<main>
<h1>Half of America's small grocers left SNAP. Three explanations don't hold.</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · {arc['peak']:,} small grocery stores in {arc['peak_year']}, {arc['latest']:,} today</p>

<div class="ledger">
  <div><b>{arc['pct_fall']}%</b><span>fall in authorized small grocers, {arc['peak_year']} peak to {arc['trough_year']} trough</span></div>
  <div><b>{100*(dr['new_after']/dr['new_before']-1):+.0f}%</b><span>change in new small-grocery authorizations per year</span></div>
  <div><b>{100*rc['share_of_exits']:.1f}%</b><span>of exits are explained by reclassification</span></div>
</div>

<p>Between {arc['peak_year']} and {arc['trough_year']}, the number of small grocery stores authorized
to accept SNAP fell from {arc['peak']:,} to {arc['trough']:,} — a drop of
{abs(arc['pct_fall'])}%. It has since flattened rather than recovered, sitting at
{arc['latest']:,} at the end of {arc['latest_year']}.</p>

<figure>{c_arc}
<figcaption>Small grocery stores with an active SNAP authorization on 31 December of each
year.</figcaption></figure>

<p>That is a big number, and "the death of the small grocer" is the obvious way to read it — but the
records only show stores leaving the program, which is not the same claim. Before
accepting that, it is worth testing the explanations that would produce the same chart for reasons
other than stores going out of business.</p>

<h2>It is not grocery in general</h2>
<p>If shoppers were simply abandoning grocery stores for superstores, every grocery format would
sag. None of the others do.</p>

<figure>{c_ctx}{charts.legend(s_ctx)}
<figcaption>Active SNAP authorizations by grocery format, 2006–2025.</figcaption></figure>

<table><thead><tr><th>Format</th><th>2006</th><th>2025</th><th>Change</th></tr></thead>
<tbody>{"".join(f"<tr><td>{f}</td><td>{ctx[f]['stock'][0]:,}</td><td>{ctx[f]['stock'][-1]:,}</td>"
                f"<td>{ctx[f]['change_pct']:+.1f}%</td></tr>" for f in picks)}</tbody></table>

<p>Medium grocery ended <strong>{ctx['Grocery (Medium)']['change_pct']:+.0f}%</strong>, superstores
<strong>{ctx['Super Store']['change_pct']:+.0f}%</strong>, supermarkets
<strong>{ctx['Supermarket']['change_pct']:+.0f}%</strong>. Only the smallest format fell. Whatever
happened, it happened to small stores specifically.</p>

<h2>It is not reclassification</h2>
<p>USDA sorts stores by how much staple food they stock, so a store could in principle move from
"small grocery" to another category without changing at all. This dataset can test that directly: a
store's type never changes within its record, so a reclassified store has to reappear as a
<em>new</em> record at the <em>same address</em>. When it also carries the same store name, that is
one business re-registering rather than a different tenant moving in.</p>

<p>Of {rc['exits']:,} small-grocery exits between 2012 and 2022, {rc['with_successor']:,} had another
store show up at the same address. Among {rc['successor_pairs']:,} successor pairs, just
<strong>{rc['same_name_diff_type']:,}</strong> share the name and differ in type —
{100*rc['share_of_pairs']:.1f}% of pairs, and <strong>{100*rc['share_of_exits']:.1f}% of all
exits</strong>.</p>

<table><thead><tr><th>Successor format</th><th>Pairs</th><th>Same name</th><th>Share</th></tr></thead>
<tbody>{succ_tbl}</tbody></table>

<p>Reclassification is real and it is small. What the table does show is churn: the most common
successor at a departed small grocer's address is a convenience store, and the second most common is
another small grocery. The storefront often keeps selling food. It frequently does so under a
different owner and a different classification.</p>

<h2>Departures did not spike. Arrivals collapsed.</h2>
<p>This is the part that surprised me. If stores were leaving the program faster, departures should
spike. They did not — the number leaving each year is <em>lower</em> now than in 2008. What collapsed was
arrivals.</p>

<figure>{c_fl}{charts.legend(s_fl)}
<figcaption>New small-grocery authorizations and authorizations ending, per year.</figcaption></figure>

<p>New authorizations fell from {dr['new_before']:,.0f} a year in 2009–2013 to
{dr['new_after']:,.0f} in 2016–2020, a drop of
<strong>{100*(dr['new_after']/dr['new_before']-1):.0f}%</strong>. Departures over the same period fell
{abs(100*(dr['dep_after']/dr['dep_before']-1)):.0f}% in absolute terms — though because the population
was shrinking, the <em>rate</em> at which a given store left rose from
{dr['exit_rate_before']:.0%} to {dr['exit_rate_after']:.0%}, about {exit_rate_change:.0f}% higher.</p>

<p>So both blades of the scissors moved, but the dominant one is entry. Small grocery did not
start leaving faster; it stopped being replaced. Small grocers have always churned hard — that is
the nature of a thin-margin corner business — and for years enough new ones opened to cover the
losses. After 2014 they stopped.</p>

<p>The timing points somewhere specific, though the detail matters. The 2014 Farm Bill
directed USDA to raise stocking requirements from three to seven varieties in each staple category,
and to require perishables in three categories instead of two. Those two provisions were
<strong>blocked</strong>: an appropriations rider in May 2017 (P.L. 115-31, §765) sent USDA back to
three varieties and two perishable categories, and they were not enforced.</p>

<p>What did take effect, in January 2018, was less headline-grabbing and probably more consequential
for a very small store: a <strong>depth-of-stock</strong> requirement of three units of each variety —
36 qualifying items on the shelf continuously — and a narrowed definition of which foods count toward
the staple categories at all. For a store with limited shelf space and thin working capital, that is a
permanent inventory commitment.</p>

<h2>The bar sorted by owner, not by format</h2>

<p>Here is the part that makes the policy story credible, and it is not what I expected. The stocking
rules apply to any retailer authorized on inventory, which includes dollar stores and drug stores, not
just grocers. So if the rule mattered, its fingerprints should appear across formats. They do — but
along a different seam.</p>

<figure>{c_ec}
<figcaption>Change in new SNAP authorizations per year, 2012–13 average against 2018–19
average.</figcaption></figure>

<p>Compare the top and bottom rows. <strong>Combination Grocery/Other</strong> — USDA's bucket for
retailers whose main business is general merchandise — fell {abs(co['pct']):.0f}%, the steepest of any
format. <strong>Dollar stores fell {abs(dl['pct']):.0f}%.</strong> And dollar stores <em>are</em>
Combination Grocery/Other: USDA files them in exactly that category. They are only shown separately
here because we identified them by brand.</p>

<p>Same rule, same USDA classification, opposite outcomes. The independents in that category collapsed
while the chains inside it barely moved. Medium grocery and supermarkets — bigger stores that already
carried deep staple inventory — were untouched at {abs(md['pct']):.0f}% and {abs(sm['pct']):.0f}%.</p>

<p>That points at compliance cost rather than format. Thirty-six qualifying items across four
categories, held continuously, is a planogram revision for a chain: decide once, roll it to twenty
thousand stores, amortise the cooler over a national footprint. Dollar General was adding refrigerated
capacity through exactly these years anyway. For a single independent corner store it is a permanent
working-capital and spoilage commitment with nothing to spread it across.</p>

<p>This remains a candidate rather than a proven cause, and two things argue for caution. The decline
in small-grocery entries begins in 2014, before the rule took effect, so something else is also at
work. And these records carry no field for why an authorization ended.</p>

<h2>What we cannot rule out</h2>
<p>One explanation survives, and it is the one the data cannot settle. A store that closes and a
store that stays open but stops accepting EBT look identical here — both are simply an authorization
that ended.</p>

<p>We know the second thing happens, because some stores do it and come back:</p>

<figure>{c_lap}
<figcaption>Share of each format's stores that lost authorization and later regained it.</figcaption></figure>

<p><strong>{100*lap['Grocery (Small)']['rate']:.1f}%</strong> of small grocers have gone unauthorized
and returned, median gap {lap['Grocery (Small)']['median_gap_days']} days. Those stores were plainly
open the whole time. And that is a floor, not an estimate: any store that dropped SNAP and never came
back is indistinguishable from one that shut its doors.</p>

<p>Settling it requires a source that counts businesses rather than authorizations. Census County
Business Patterns publishes establishment counts for grocery retailers by county and size class; if
small grocery establishments held steady while SNAP authorizations halved, they left the program, and
if both fell together, they closed. That comparison is the next thing to run, and until it is run the
honest headline is the one at the top of this page: they left SNAP.</p>

<h2>Where it happened</h2>
<p>The decline is not evenly spread. New York lost more small grocers than any other state, by a
wide margin.</p>

<figure>{c_st}
<figcaption>Largest percentage falls in authorized small grocers, {arc['peak_year']} to 2025, among
states with at least 150 at peak. Labels show the count then and now.</figcaption></figure>

<p>New York went from {st[0]['then']:,} to {st[0]['now']:,}, a fall of {abs(st[0]['pct']):.0f}%. A
state with that many small groceries is a state of bodegas and corner stores, and it absorbed the
largest share of whatever changed.</p>

<div class="caveat">
<h3>Limits</h3>
<p>Every figure here counts <strong>authorizations</strong>. "Left SNAP" is the strongest claim the
data supports; "closed" is not, except where an outside source can corroborate it.</p>
<p>Address matching for the successor test is exact on street number, street name, city and state.
Stores whose address was recorded differently across records will be missed, so
{100*rc['share_of_exits']:.1f}% is a lower bound on reclassification.</p>
<p>The 2016 stocking-standards rule is offered as a candidate explanation on timing and shape. These
records contain no reason code, so it cannot be confirmed from this source alone.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 611,164 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Entries and exits count stores, not authorization spells, so a store that lapsed and resumed is not
double-counted. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  arc: {arc['peak']:,} ({arc['peak_year']}) -> {arc['trough']:,} "
          f"({arc['trough_year']}) -> {arc['latest']:,}")
    print(f"  reclassification explains {100*rc['share_of_exits']:.1f}% of exits")


if __name__ == "__main__":
    main()
