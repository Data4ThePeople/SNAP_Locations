"""Render reports/post6.html from reports/data/post6.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post6.json"
OUT = ROOT / "reports" / "post6.html"

# Slot assignment is fixed per segment so the same segment keeps the same hue in
# every figure. Slot 0 is the neutral used for context rows.
SLOT = {"fuel-forward chains": 1, "dollar stores": 2, "other convenience chains": 3,
        "fuel-branded single sites": 4, "unbranded convenience": 5}


def main():
    d = json.loads(DATA.read_text())
    palette.validate(5, "light", verbose=False)
    palette.validate(5, "dark", verbose=False)

    surv = {r["segment"]: r for r in d["survival"]}
    sc, tot = d["stock_change"], d["totals"]
    fm, cens, cbp = d["fuel_margin"], d["census"], d["cbp"]
    ff, do = surv["fuel-forward chains"], surv["dollar stores"]
    mu = fm["companies"]["Murphy USA"]
    cy = fm["companies"]["Casey's General Stores"]
    mac = fm["macro"]
    sh0 = d["shares"][str(min(int(k) for k in d["shares"]))]
    sh1 = d["shares"][str(max(int(k) for k in d["shares"]))]
    pres = {r["label"]: r for r in d["post5"]["presence"]}["convenience store"]

    order = ["fuel-forward chains", "dollar stores", "other convenience chains",
             "fuel-branded single sites", "unbranded convenience"]

    c_stock = charts.line_chart(
        d["stock"]["years"],
        [{"name": k, "values": d["stock"]["series"][k], "slot": SLOT[k]} for k in order],
        y_label="stores authorized on 31 December",
        title="Chain gas stations tripled. Everyone else flattened.")

    c_surv = charts.bar_chart(
        [{"label": k, "value": surv[k]["rate"],
          "slot": SLOT[k] if k in ("fuel-forward chains", "dollar stores") else 0}
         for k in order], suffix="%",
        title="Chains keep their stores. Single sites do not.",
        subtitle="share of 2008-2012 stores still authorized in 2025")

    # Two companies, one measure, same units — a single axis, per the one-axis rule.
    # Intersect the years: Murphy's series starts a year earlier and Casey's runs a
    # year later, and a None in either would break the axis scaling.
    myrs = sorted(set(map(int, mu["series"])) & set(map(int, cy["series"])))
    c_marg = charts.line_chart(
        myrs,
        [{"name": "Murphy USA", "values": [mu["series"].get(str(y)) for y in myrs], "slot": 1},
         {"name": "Casey's", "values": [cy["series"].get(str(y)) for y in myrs], "slot": 3}],
        y_zero=False, y_label="cents earned per gallon sold",
        title="Fuel profit doubled after 2020 and stayed there")

    c_share = charts.bar_chart(
        [{"label": f"chains, {min(int(k) for k in d['shares'])}",
          "value": sh0["fuel-forward chains"], "slot": 0},
         {"label": f"chains, {max(int(k) for k in d['shares'])}",
          "value": sh1["fuel-forward chains"], "slot": 1},
         {"label": f"single sites, {min(int(k) for k in d['shares'])}",
          "value": sh0["unbranded convenience"], "slot": 0},
         {"label": f"single sites, {max(int(k) for k in d['shares'])}",
          "value": sh1["unbranded convenience"], "slot": 5}], suffix="%",
        title="Chains took a bigger slice of the same category",
        subtitle="share of all SNAP convenience stores")

    surv_tbl = "".join(
        f"<tr><td>{k}</td><td>{surv[k]['rate']}%</td>"
        f"<td>{surv[k]['survived']:,} of {surv[k]['cohort']:,}</td>"
        f"<td>{sc[k]['multiple']}x</td></tr>" for k in order)

    cbp_tbl = "".join(
        f"<tr><td>{y}</td><td>{cbp['cbp'][str(y)]['establishments']:,}</td>"
        f"<td>{cbp['cbp'][str(y)]['under_5_emp']:,}</td>"
        f"<td>{cbp['snap_unbranded'][str(y)]:,}</td></tr>" for y in cbp["years"])

    cens_tbl = "".join(
        f"<tr><td>{c['chain']}</td><td>{c['authorized']:,}</td>"
        f"<td>{c['reported']:,}</td><td>{c['ratio']}</td></tr>" for c in cens)

    html = f"""{HEAD}<title>The gas station is the other store that stayed</title>
<style>{CSS}</style>
<main>
<h1>The gas station is the other store that stayed</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · EIA weekly gasoline prices ·
retail fuel margins from Murphy USA and Casey's 10-K filings</p>

<div class="ledger">
  <div><b>{ff['rate']}%</b><span>of fuel-forward chain stores authorized in
    {d['cohort'][0]}–{d['cohort'][1]} were still authorized in {d['cohort_end']}</span></div>
  <div><b>{do['rate']}%</b><span>for dollar stores over the same window — the same
    rate, reached a different way</span></div>
  <div><b>+{round(mu['pct'])}%</b><span>growth in Murphy USA's fuel margin per gallon,
    comparing 2015–2019 with 2021–2025</span></div>
</div>

<p>The last piece in this series ended on one idea. In small markets, the stores that survive are the
ones that are cheap to run. It named dollar stores as the format that fits.</p>

<p>That answer was half right. There is a second format that fits just as well, and this data shows it
plainly once you stop treating it as one thing.</p>

<h2>"Convenience store" is four different businesses</h2>

<p>USDA files every corner store, truck stop and gas station under a single store type. That one label
hides everything interesting. Split it by who runs the store and the pieces move in different
directions.</p>

<p>The test is simple. Take every store first authorized between {d['cohort'][0]} and
{d['cohort'][1]}. Then ask how many were still authorized in {d['cohort_end']}, thirteen years later.
Dollar stores are included as a yardstick, because post 1 already measured them.</p>

<table><thead><tr><th>Segment</th><th>Still active after 13 years</th><th>Count</th>
<th>Growth 2006→2025</th></tr></thead>
<tbody>{surv_tbl}</tbody></table>

<p>The survival column on its own, so the gap is easier to see:</p>

<figure>{c_surv}
<figcaption>Share of stores first authorized {d['cohort'][0]}–{d['cohort'][1]} that were still
authorized on 31 December {d['cohort_end']}.</figcaption></figure>

<p><strong>Fuel-forward chains stay at {ff['rate']}%. Dollar stores stay at {do['rate']}%.</strong>
That gap is {abs(d['survival_gap_pp'])} of a percentage point. These two formats look nothing alike, but
they hold onto their locations equally well.</p>

<p>Now look down the table. Other chains stay at {surv['other convenience chains']['rate']}%.
Single sites flying an oil company's sign stay at
{surv['fuel-branded single sites']['rate']}%. Stores with no chain behind them at all stay at
{surv['unbranded convenience']['rate']}%.</p>

<p>The thing that predicts survival is not the format. It is whether a company with scale is behind
the store.</p>

<figure>{c_stock}{charts.legend([{"name": k, "slot": SLOT[k]} for k in order])}
<figcaption>Stores authorized on 31 December of each year, by segment.</figcaption></figure>

<p>Chains also grew. Fuel-forward chains went from {sc['fuel-forward chains']['y2006']:,} stores in 2006
to {sc['fuel-forward chains']['y2025']:,} in 2025 — <strong>{sc['fuel-forward chains']['multiple']}
times</strong> as many. Their share of the whole convenience category went from
{sh0['fuel-forward chains']}% to {sh1['fuel-forward chains']}%.</p>

<figure>{c_share}
<figcaption>Share of all SNAP-authorized convenience stores, by segment.</figcaption></figure>

<h2>Why fuel changed the math</h2>

<p>Dollar stores and gas stations both run on low fixed costs. But after 2020 the gas station got
something the dollar store did not. Selling fuel became much more profitable.</p>

<p>This is measurable two ways, and both point the same direction.</p>

<p><strong>The first way is national prices.</strong> Take what drivers pay at the pump and subtract
the wholesale price of gasoline at the New York Harbor trading hub. The gap covers taxes, shipping and
the store's own cut. Comparing 2015–2019 with 2021–2025, that gap widened by
<strong>{mac['delta_cpg']:.1f} cents a gallon</strong>.</p>

<p><strong>The second way is company filings.</strong> Two chains in this data are public companies and
report their fuel margin in cents per gallon. Their own numbers are far more direct.</p>

<figure>{c_marg}{charts.legend([{"name": "Murphy USA", "slot": 1}, {"name": "Casey's", "slot": 3}])}
<figcaption>Retail fuel margin in cents per gallon, as reported in each company's annual 10-K
filings. Casey's fiscal year ends 30 April, so its 2020 spans the March–April 2020 collapse.</figcaption>
</figure>

<p>Murphy USA earned {mu['pre_mean']} cents a gallon before 2020. It now earns
{mu['post_mean']}. Casey's went from {cy['pre_mean']} cents to {cy['post_mean']}.
<strong>Both roughly doubled.</strong> Before 2020 Murphy's margin sat between 11.6 and 14.7 cents
every single year. Since 2021 it has not dropped below 21.9. The two ranges do not overlap at all.</p>

<p>Here is what makes these two measures worth showing together. The national gap widened by
{mac['delta_cpg']:.1f} cents. Murphy's own margin grew by {mu['delta_cpg']:.1f} cents. Those are
almost the same number.</p>

<p>That tells us where the money went. Taxes and shipping did not absorb the increase.
<strong>Nearly all of it became store profit.</strong> It also explains why the national gap only rose
{mac['pct']:.0f}% while margins doubled: most of that gap is fixed tax the retailer never touches, so a
small percentage move in the total is a large move in the part the store keeps.</p>

<h2>A check before going further</h2>

<p>These records count SNAP authorizations, not buildings. That difference matters, and this series
does not paper over it.</p>

<p>For chains it can be checked directly. Murphy USA and Casey's both publish store counts in their
filings, and both appear in this data.</p>

<table><thead><tr><th>Chain</th><th>SNAP-authorized, 2025</th><th>Reported stores</th>
<th>Ratio</th></tr></thead>
<tbody>{cens_tbl}</tbody></table>

<p>Around nine in ten of their stores take EBT. Close enough that talking about "stores" is fair for
these operators. For a single gas station with no parent company, no such check exists.</p>

<h2>The single sites did not close. They changed hands.</h2>

<p>It would be easy to read {surv['unbranded convenience']['rate']}% survival as a wave of closures.
That reading is wrong, and it is worth correcting carefully.</p>

<p>The Census Bureau counts business locations whether or not they accept EBT. If corner stores were
closing, that count would fall.</p>

<table><thead><tr><th>Year</th><th>Census stores</th><th>Under 5 staff</th>
<th>SNAP, unbranded</th></tr></thead>
<tbody>{cbp_tbl}</tbody></table>

<p>It did the opposite. Between {cbp['base_year']} and {cbp['last_year']}, convenience establishments
rose <strong>{cbp['cbp_pct']:+.1f}%</strong>. The smallest ones — under five employees — rose
{cbp['cbp_under5_pct']:+.1f}%. Over the same years SNAP authorizations without a chain brand moved
{cbp['snap_pct']:+.1f}%.</p>

<p>So the corner store is not vanishing. The <em>specific business</em> in that building keeps
changing. A store is sold, renamed, re-registered, and a new record number appears. The storefront
stays; the operator turns over.</p>

<p>That is the real contrast. <strong>Chains accumulate stores. Single sites cycle through
owners.</strong> Over twenty years a chain compounds what it built. An independent operator mostly
hands the keys to the next person.</p>

<h2>What this means for food access</h2>

<p>Post 5 looked at {d['post5']['groups']['lost']:,} ZIP codes that lost their last chain pharmacy. A
convenience store is present in {pres['lost_pct']}% of them. It is also in {pres['kept_pct']}% of the
comparison group, so this is not something unusual about those places. It is nearly everywhere.</p>

<p>That is the point. For a household using SNAP in a small town, the realistic options are narrowing
to two: a dollar store, or a gas station. Both are now run largely by companies with scale. Both are
profitable at a size no supermarket can match.</p>

<p>Neither one is trying to be a grocery store. A gas station's food is built for a driver buying one
thing — packaged, quick, priced for convenience. When it becomes the closest food retailer to a home,
that assortment is doing a job it was never designed for.</p>

<p>There is no villain in this. Fuel margins widened because of how fuel markets work, not because
anyone targeted small towns. Chains expanded because expanding is what a business with capital does.
The outcome was assembled out of ordinary decisions, which is exactly what makes it hard to reverse.</p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>The fuel-forward list is a judgement call.</strong> Twenty-four chains are named as
fuel-forward because they run fuel pumps at essentially all their US locations. The list is printed in
the code so it can be checked. 7-Eleven is deliberately left out: it is the largest convenience brand
in this data by a wide margin and is mixed on fuel, so including it would let one brand carry a claim
about fuel economics. Excluding it makes the chain figures smaller, not larger.</p>
<p><strong>Margin is not profit.</strong> Fuel margin is revenue minus the cost of the fuel. It does
not subtract labour, rent, card fees or the cost of the pumps. A doubling in margin is not a doubling
in earnings. It does mean the fuel side of the store got substantially better at covering its own
fixed costs.</p>
<p><strong>Two companies are not an industry.</strong> Murphy USA and Casey's are the operators in this
data that publish the number. Circle K's parent files in Canada rather than with the SEC and is not
included. The national price gap is what carries the claim beyond these two, and it agrees with
them.</p>
<p><strong>Growth in the single-site segments is ambiguous.</strong> Rising authorization counts can
mean more stores or wider EBT take-up among stores that already existed. The Census comparison is what
separates those, and it is only available for the category as a whole, not for the segments.</p>
<p>Nothing here measures what is on the shelves. A gas station and a supermarket each count as one
record. What can actually be bought with an EBT card in these places needs a different source.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025 · EIA weekly US retail regular
gasoline (EMM_EPMR_PTE_NUS_DPG) and NY Harbor conventional regular spot (EER_EPMRU_PF4_Y35NY_DPG) ·
Murphy USA (CIK 1573516) and Casey's General Stores (CIK 726958) 10-K filings via SEC EDGAR · Census
County Business Patterns, NAICS {'/'.join(cbp['cbp'][str(cbp['years'][0])]['naics'])}. A store counts
as active in a year if an authorization covered 31 December. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  survival: fuel chains {ff['rate']}% vs dollar {do['rate']}%")
    print(f"  margin: Murphy {mu['pre_mean']}->{mu['post_mean']}, "
          f"Casey's {cy['pre_mean']}->{cy['post_mean']} cpg")
    print(f"  CBP establishments {cbp['cbp_pct']:+.1f}% vs SNAP {cbp['snap_pct']:+.1f}%")


if __name__ == "__main__":
    main()
