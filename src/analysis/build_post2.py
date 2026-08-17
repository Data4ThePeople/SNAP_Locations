"""Render reports/post2.html from reports/data/post2.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
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
                                        {"year": arc["trough_year"], "text": "trough"}],
        title="Small grocers halved, then stopped falling",
        subtitle="stores authorized on 31 December")

    # 2. which side of the ledger moved
    s_fl = [{"name": "new authorizations", "values": fl["new"], "slot": 1},
            {"name": "authorizations ending", "values": fl["departed"], "slot": 2}]
    c_fl = charts.line_chart(yrs, s_fl, y_label="stores per year",
        title="Departures held steady. New sign-ups halved.",
        subtitle="small grocery stores per year")

    # 3. every other grocery format
    picks = ["Grocery (Small)", "Grocery (Medium)", "Grocery (Large)",
             "Supermarket", "Super Store"]
    s_ctx = [{"name": f, "values": ctx[f]["stock"], "slot": 4 if f == "Grocery (Small)" else i + 1}
             for i, f in enumerate(picks)]
    c_ctx = charts.line_chart(ctx["Grocery (Small)"]["years"], s_ctx, y_label="active stores",
        title="Only the smallest format dropped",
        subtitle="stores authorized on 31 December")

    # 4. successor formats
    succ_tbl = "".join(
        f"<tr><td>{t['format']}</td><td>{t['n']:,}</td><td>{t['same_name']:,}</td>"
        f"<td>{100*t['same_name']/t['n']:.0f}%</td></tr>" for t in d["successor_types"])

    # 5. lapse
    c_lap = charts.bar_chart(
        [{"label": f, "value": round(100 * lap[f]["rate"], 1),
          "slot": 4 if f == "Grocery (Small)" else 0}
         for f in ["Grocery (Medium)", "Convenience Store", "Grocery (Small)",
                   "Supermarket", "Dollar Store"] if f in lap], suffix="%",
        title="Some stores drop out and come back",
        subtitle="share that lost authorization, then regained it")

    # 6. states
    worst = st[:8]
    c_st = charts.bar_chart(
        [{"label": f"{t['state']}  {t['then']:,}→{t['now']:,}", "value": abs(t["pct"]),
          "slot": 4 if t["state"] == "NY" else 0} for t in worst], suffix="%",
        title="New York lost the most, by a wide margin",
        subtitle="fall in authorized small grocers, 2012 to 2025")

    ec = {r["format"]: r for r in d["entry_change"]}
    co, dl = ec["Combination Grocery/Other"], ec["Dollar Store"]
    md, sm = ec["Grocery (Medium)"], ec["Supermarket"]
    c_ec = charts.bar_chart(
        [{"label": r["format"], "value": abs(r["pct"]),
          "slot": 2 if r["format"] == "Combination Grocery/Other"
                  else (1 if r["format"] == "Dollar Store" else 0)}
         for r in sorted(d["entry_change"], key=lambda r: r["pct"])], suffix="%",
        title="Independents fell. The dollar chains did not.",
        subtitle="change in new sign-ups per year, 2012-13 vs 2018-19")

    cb = d["cbp"]
    mix = d["entry_mix"]
    c_cbp = charts.bar_chart([
        {"label": "Census, all grocery", "value": abs(cb["cbp_total_pct"]), "slot": 0},
        {"label": "Census, under 5 staff", "value": abs(cb["cbp_under5_pct"]), "slot": 1},
        {"label": "Census, under 10 staff", "value": abs(cb["cbp_under10_pct"]), "slot": 1},
        {"label": "SNAP Small + Medium", "value": abs(cb["snap_small_mid_pct"]), "slot": 3},
        {"label": "SNAP Small only", "value": abs(cb["snap_small_pct"]), "slot": 2},
    ], suffix="%",
        title="Census says 22%. SNAP's Small category says 46%.",
        subtitle="decline 2012 to 2023")
    s_mix = [{"name": "Medium share of new authorizations",
              "values": [m["medium_share"] for m in mix], "slot": 2}]
    c_mix = charts.bar_chart(
        [{"label": m["period"], "value": m["medium_share"],
          "slot": 2 if m["period"] == "2018-2021" else 0} for m in mix], suffix="%",
        title="After 2018, new stores were filed as Medium",
        subtitle="share of new grocery sign-ups classed Medium")

    exit_rate_change = 100 * (dr["exit_rate_after"] / dr["exit_rate_before"] - 1)

    html = f"""{HEAD}<title>SNAP shows small grocers down 46%. The census says 22%. Both are right.</title>
<style>{CSS}</style>
<main>
<h1>SNAP shows small grocers down 46%. The census says 22%. Both are right.</h1>
<p class="sub">SNAP-authorized retailers 2006–2025, against Census County Business Patterns
establishment counts · {arc['peak']:,} small grocery stores authorized in {arc['peak_year']},
{arc['latest']:,} today</p>

<div class="ledger">
  <div><b>{cb['snap_small_pct']}%</b><span>fall in SNAP-authorized small grocers, {cb['base_year']} to {cb['last_year']}</span></div>
  <div><b>{cb['cbp_under10_pct']}%</b><span>fall in census-counted grocery establishments under 10 staff</span></div>
  <div><b>{mix[3]['medium_share']:.0f}%</b><span>of new grocery authorizations were classed Medium in 2018–21, up from {mix[1]['medium_share']:.0f}%</span></div>
</div>

<p>Between {arc['peak_year']} and {arc['trough_year']}, the number of small grocery stores authorized
to accept SNAP fell from {arc['peak']:,} to {arc['trough']:,} — a drop of
{abs(arc['pct_fall'])}%. It has since flattened rather than recovered, sitting at
{arc['latest']:,} at the end of {arc['latest_year']}.</p>

<figure>{c_arc}
<figcaption>Small grocery stores with an active SNAP authorization on 31 December of each
year.</figcaption></figure>

<p>That is a big drop, and "the death of the small grocer" is the obvious way to read it. But these records only show stores leaving the program. That is not the same as stores closing. Three other things could produce the same chart, so we tested each one.</p>

<h2>It is not grocery in general</h2>
<p>If shoppers were just switching to superstores, every size of grocery store would sag. None of the others do. Here is each format on the same axis:</p>

<figure>{c_ctx}{charts.legend(s_ctx)}
<figcaption>Active SNAP authorizations by grocery format, 2006–2025.</figcaption></figure>

<p>The same thing as start-and-end numbers:</p>

<table><thead><tr><th>Format</th><th>2006</th><th>2025</th><th>Change</th></tr></thead>
<tbody>{"".join(f"<tr><td>{f}</td><td>{ctx[f]['stock'][0]:,}</td><td>{ctx[f]['stock'][-1]:,}</td>"
                f"<td>{ctx[f]['change_pct']:+.1f}%</td></tr>" for f in picks)}</tbody></table>

<p>Medium grocery ended <strong>{ctx['Grocery (Medium)']['change_pct']:+.0f}%</strong>, superstores
<strong>{ctx['Super Store']['change_pct']:+.0f}%</strong>, supermarkets
<strong>{ctx['Supermarket']['change_pct']:+.0f}%</strong>. Only the smallest format fell. Whatever
happened, it happened to small stores specifically.</p>

<h2>Existing stores were not re-registered under a new type</h2>
<p>USDA sorts stores by how much staple food they stock. So a store could move out of "small grocery" without changing at all. We can test that here. A store's type never changes inside its own record. A re-sorted store therefore has to show up as a <em>new</em> record at the <em>same address</em>. If it also keeps the same name, that is one business signing up again — not a new tenant.</p>

<p>Of {rc['exits']:,} small-grocery exits between 2012 and 2022, {rc['with_successor']:,} had another
store show up at the same address. Among {rc['successor_pairs']:,} successor pairs, just
<strong>{rc['same_name_diff_type']:,}</strong> share the name and differ in type —
{100*rc['share_of_pairs']:.1f}% of pairs, and <strong>{100*rc['share_of_exits']:.1f}% of all
exits</strong>.</p>

<table><thead><tr><th>Successor format</th><th>Pairs</th><th>Same name</th><th>Share</th></tr></thead>
<tbody>{succ_tbl}</tbody></table>

<p>So signing up again is real, but small. Hold onto that number. A different kind of re-sorting turns up later, and it is much bigger. What the table does show is churn. The most common replacement at a departed small grocer's address is a convenience store. The second most common is another small grocery. The storefront often keeps selling food, just under a new owner and a new label.</p>

<h2>Departures did not spike. Arrivals collapsed.</h2>
<p>This is the part that surprised me. If stores were leaving faster, departures should spike. They did not. The number leaving each year is <em>lower</em> now than in 2008. What collapsed was arrivals. Both lines are below:</p>

<figure>{c_fl}{charts.legend(s_fl)}
<figcaption>New small-grocery authorizations and authorizations ending, per year.</figcaption></figure>

<p>New authorizations fell from {dr['new_before']:,.0f} a year in 2009–2013 to
{dr['new_after']:,.0f} in 2016–2020, a drop of
<strong>{100*(dr['new_after']/dr['new_before']-1):.0f}%</strong>. Departures fell {abs(100*(dr['dep_after']/dr['dep_before']-1)):.0f}% over the same period. But the pool of stores was shrinking too. So the <em>rate</em> at which any one store left actually rose, from {dr['exit_rate_before']:.0%} to {dr['exit_rate_after']:.0%}.</p>

<p>Both sides moved, but entry is the bigger one. Small grocery did not start leaving faster. It stopped being replaced. These stores have always churned hard, because a corner shop runs on thin margins. For years, enough new ones opened to cover the losses. After 2014 they stopped.</p>

<p>The timing points somewhere specific, but the detail matters. The 2014 Farm Bill told USDA to raise stocking rules. Stores would need seven kinds of food in each staple category instead of three, and fresh food in three categories instead of two. Congress then <strong>blocked</strong> both changes. A May 2017 spending rider (P.L. 115-31, §765) sent USDA back to three and two.</p>

<p>Something quieter did take effect in January 2018. Stores now had to keep <strong>three units of every kind</strong> of staple food in stock. That works out to 36 items on the shelf at all times. USDA also narrowed which foods counted at all. For a big chain that is a shelf plan. For a small store with little space and little cash, it is a permanent bill.</p>

<h2>The bar sorted by owner, not by format</h2>

<p>Here is the part that makes the policy story believable, and it is not what I expected. The stocking rules cover every store judged on its inventory. That includes dollar stores and drug stores, not just grocers. So if the rule mattered, its mark should show up across formats. It does. But it follows a different line than you would guess. This chart is the change in new sign-ups per year, by format:</p>

<figure>{c_ec}
<figcaption>Change in new SNAP authorizations per year, 2012–13 average against 2018–19
average.</figcaption></figure>

<p>Compare the top and bottom rows. <strong>Combination Grocery/Other</strong> is where USDA files stores that mainly sell general goods. New sign-ups there fell {abs(co['pct']):.0f}%, the steepest of any format. <strong>Dollar stores fell {abs(dl['pct']):.0f}%.</strong> Now the catch. Dollar stores <em>are</em> Combination Grocery/Other. USDA files them in that exact category. They only sit on their own line here because we picked them out by brand name.</p>

<p>Same rule. Same USDA category. Opposite results. The independents in that bucket collapsed. The chains inside it barely moved. Medium grocery and supermarkets were nearly untouched, at {abs(md['pct']):.0f}% and {abs(sm['pct']):.0f}%. Those stores already carried deep stock.</p>

<p>That points at the cost of complying, not at the format. For a chain, 36 items on the shelf is a shelf plan. Decide once, send it to twenty thousand stores, and spread the cost of a cooler across all of them. Dollar General was adding coolers in these very years anyway. For one corner store, the same rule means cash tied up in stock and food that may spoil, with nothing to spread it across.</p>

<p>This is still a likely cause, not a proven one. Two things argue for caution. New sign-ups start falling in 2014, before the rule took effect, so something else is at work too. And these records never say why an authorization ended.</p>

<h2>The question these records cannot answer</h2>
<p>One explanation survives all three tests. It is also the one this data cannot settle. A store that closes and a store that stays open but drops EBT look exactly the same here. Both are just an authorization that ended.</p>

<p>We know the second thing happens, because some stores do it and come back:</p>

<figure>{c_lap}
<figcaption>Share of each format's stores that lost authorization and later regained it.</figcaption></figure>

<p><strong>{100*lap['Grocery (Small)']['rate']:.1f}%</strong> of small grocers have gone unauthorized
and returned, median gap {lap['Grocery (Small)']['median_gap_days']} days. Those stores were plainly
open the whole time. And that is a floor, not an estimate.</p>

<h2>So we asked a source that counts businesses instead</h2>

<p>The Census Bureau counts <em>business locations</em> — every grocery store with staff, whether or not it takes EBT. That gives us a clean test. If locations held steady while authorizations halved, stores left the program. If both fell together, stores closed. Here are the two counts side by side:</p>

<figure>{c_cbp}
<figcaption>Percentage decline, {cb['base_year']} to {cb['last_year']}. Census establishment counts
against SNAP authorizations.</figcaption></figure>

<p>Grocery locations with fewer than five staff fell <strong>{abs(cb['cbp_under5_pct'])}%</strong>. Under ten staff, <strong>{abs(cb['cbp_under10_pct'])}%</strong>. Those businesses are gone, not just out of the program. So a real share of the headline drop is genuine. Grocery of all sizes fell only {abs(cb['cbp_total_pct'])}%, which puts the losses in the smallest stores. The SNAP data said the same thing.</p>

<p>Now look at the two SNAP rows. <strong>Small and Medium grocery together fell {abs(cb['snap_small_mid_pct'])}%.</strong> That is within a point of the census figure. <strong>Small alone fell {abs(cb['snap_small_pct'])}%.</strong> So SNAP is right about small grocery businesses. It is wrong about its own Small category. That can only mean one thing: the line between Small and Medium moved.</p>

<h2>The definition moved, and the same rule moved it</h2>

<p>It did move, and you can watch it happen. This chart is the share of new grocery stores USDA filed as Medium rather than Small.</p>

<figure>{c_mix}
<figcaption>Share of new SNAP grocery authorizations classified Medium rather than Small.</figcaption></figure>

<p>For a decade, about {mix[1]['medium_share']:.0f}% of new grocery sign-ups were filed as Medium. In 2018–21 that jumped to <strong>{mix[3]['medium_share']:.0f}%</strong>. Recall the 2018 rule: 36 items on the shelf at all times. In USDA's own words, a store holding that much stock has a "moderate selection" rather than a small one. The floor for joining the program rose above what "Small" used to mean.</p>

<p>This is not the same thing we tested earlier. Existing stores signing up under a new type is rare, at {100*rc['share_of_exits']:.1f}% of exits. What moved is where the line sits for <em>new</em> stores. Both are true, and only the second shows up in the totals.</p>

<p>So the answer to the question this piece opened with, in three parts. Small grocery businesses really
did contract, by about a quarter. SNAP's own Small category fell twice that far because the rule that
drove part of the contraction also redrew the category. And the stores that vanished were disproportionately
the ones with no scale to absorb a new fixed cost.</p>

<h2>Where it happened</h2>
<p>The drop is not spread evenly. New York lost far more small grocers than any other state:</p>

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
<p>The address test matches exactly on street number, street name, city and state. Stores whose address was typed differently in two records will be missed. So {100*rc['share_of_exits']:.1f}% is a floor, not a full count.</p>
<p>The stocking rule is offered as a likely explanation, based on timing and shape. These records carry no reason code, so this source alone cannot confirm it.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
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
