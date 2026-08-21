"""Render reports/post6.html from reports/data/post6.json.

Three sections, four figures:
  1. the category grew — and two very different things are called growth
  2. fuel margins doubled after 2020 and never came back
  3. the format thrives; the people running the stores turn over

Segments are named for who runs the store, because that is what the split
measures. An oil brand on the canopy is a fuel supply contract, not an owner, so
a "Shell" station counts as a single-owner store. That distinction used to have
its own row and it made the table unreadable.
"""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post6.json"
OUT = ROOT / "reports" / "post6.html"

# One hue per segment, held across every figure in the piece.
SLOT = {"chains that sell fuel": 1, "dollar stores": 2, "other chains": 3,
        "single-owner stores": 5}
ORDER = list(SLOT)


def main():
    d = json.loads(DATA.read_text())
    palette.validate(5, "light", verbose=False)
    palette.validate(5, "dark", verbose=False)

    surv = {r["segment"]: r for r in d["survival"]}
    sc, cbp, cens = d["stock_change"], d["cbp"], d["census"]
    _f = sc["chains that sell fuel"]
    fuel_pct = round(100 * (_f["y2025"] / _f["y2006"] - 1))
    fm = d["fuel_margin"]
    ch, so = surv["chains that sell fuel"], surv["single-owner stores"]
    mu = fm["companies"]["Murphy USA"]
    cy = fm["companies"]["Casey's General Stores"]
    mac = fm["macro"]
    ks = sorted(int(k) for k in d["shares"])
    sh0, sh1 = d["shares"][str(ks[0])], d["shares"][str(ks[-1])]
    conv_total = d["convenience_total"]

    # Percentages, not just multiples: 47,761 -> 76,496 is +60%, which is not
    # "barely moving" however small it looks beside the chains.
    pct = lambda k: 100 * (sc[k]["y2025"] / sc[k]["y2006"] - 1)

    # Indexed to 2006 = 100: the raw counts only show that single-owner stores
    # are the biggest group, which buries the growth comparison the section is
    # actually making.
    idx = {k: [round(100 * v / d["stock"]["series"][k][0], 1)
               for v in d["stock"]["series"][k]] for k in ORDER}
    conv25 = sum(d["stock"]["series"][k][-1] for k in
                 ("chains that sell fuel", "other chains", "single-owner stores"))
    c_stock = charts.line_chart(
        d["stock"]["years"],
        [{"name": k, "values": idx[k], "slot": SLOT[k]} for k in ORDER],
        y_label="authorized stores, indexed to 2006 = 100",
        title="Only the fuel chains kept pace with the dollar store")

    myrs = sorted(set(map(int, mu["series"])) & set(map(int, cy["series"])))
    c_marg = charts.line_chart(
        myrs,
        [{"name": "Murphy USA", "values": [mu["series"][str(y)] for y in myrs], "slot": 1},
         {"name": "Casey's", "values": [cy["series"][str(y)] for y in myrs], "slot": 3}],
        y_zero=False, y_label="cents earned per gallon sold",
        title="Fuel profit doubled after 2020 and stayed there")

    leg_seg = charts.legend([{"name": k, "slot": SLOT[k]} for k in ORDER])
    leg_marg = charts.legend([{"name": "Murphy USA", "slot": 1},
                              {"name": "Casey's", "slot": 3}])

    c_surv = charts.bar_chart(
        [{"label": k, "value": surv[k]["rate"],
          "slot": SLOT[k] if k in ("chains that sell fuel", "single-owner stores") else 0}
         for k in ORDER], suffix="%",
        title="A chain store stays. A single-owner store usually does not.",
        subtitle="share of 2008-2012 stores still authorized in 2025")

    html = f"""{HEAD}<title>Convenience stores and the advantage hiding in plain sight</title>
<style>{CSS}</style>
<main>
<h1>Convenience stores and the advantage hiding in plain sight</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · EIA weekly gasoline prices · retail fuel margins
from Murphy USA and Casey's 10-K filings · {conv_total:,} convenience stores in the file</p>

<div class="ledger">
  <div><b>{fuel_pct:+}%</b><span>change in chains that sell fuel
    since {d['stock']['years'][0]}</span></div>
  <div><b>{ch['rate']}%</b><span>of their 2008–2012 stores are still authorized. For
    single-owner stores it is {so['rate']}%</span></div>
  <div><b>+{round(mu['pct'])}%</b><span>growth in Murphy USA's fuel margin per gallon
    after 2020</span></div>
</div>

<p><em>Anytime we refer to "growth" in this post, it is growth in SNAP-authorized stores, not
growth in store counts. See the Limits section for more on this.</em></p>

<p>Yesterday ended on a puzzle. Dollar stores thrived because they are chains. Convenience stores
are the opposite: only about a third belong to a chain, and there are more of them than any other
kind of SNAP retailer. If you read the last two days of analysis, you may have expected them to go
the way of the small grocer.</p>

<p>They did not. But the reason has less to do with ownership, and more to do with an advantage
few other store formats had.</p>

<h2>One store format masks different growth trends</h2>

<p>The convenience store format is enormous. There are {conv25:,} stores authorized to accept SNAP
benefits today, far surpassing any other store format. That makes sense: it is not uncommon to see
a gas station at every major intersection.</p>

<p>But we cannot analyze the convenience store format as one thing, because within it live very
different kinds of stores, and they grew at very different rates. There are chains that sell fuel —
Wawa, Sheetz, Casey's, QuikTrip and the like — which surged
<strong>{pct('chains that sell fuel'):.0f}%</strong> between 2006 and 2025. There are chains that
are not built around fuel — 7-Eleven, above all — which grew {pct('other chains'):.0f}%. And there
are single-owner stores, which make up most of the category and grew
{pct('single-owner stores'):.0f}%.</p>

<p>The chart below shows the growth of each, compared with the dollar store, indexed to 100 in
2006. Only one comes close to matching the dollar store: the chains that sell fuel.</p>

<figure>{c_stock}{leg_seg}
<figcaption>Stores authorized on 31 December of each year, indexed to 100 in 2006, by who runs the
store. Dollar stores are shown as the benchmark.</figcaption></figure>

<p>The fuel chains went from {sh0['chains that sell fuel']}% of the category to
{sh1['chains that sell fuel']}%.</p>

<h2>The fuel advantage</h2>

<p>There is something else you need to know about this format, and it has nothing to do with what
is on the shelves.
After 2020, selling fuel became far more profitable.</p>

<p>Two of these chains are public companies and report their fuel margin in cents per gallon.</p>

<figure>{c_marg}{leg_marg}
<figcaption>Retail fuel margin in cents per gallon, as reported in each company's annual 10-K
filings. Casey's fiscal year ends 30 April, so its 2020 spans the March–April 2020
collapse.</figcaption></figure>

<p>Murphy USA earned {mu['pre_mean']} cents a gallon before 2020 and {mu['post_mean']} after.
Casey's went from {cy['pre_mean']} to {cy['post_mean']}. <strong>Both roughly doubled.</strong> Before
2020 Murphy's margin never left the 11.6 to 14.7 cent band. Since 2021 it has never dropped below
21.9. The two ranges do not overlap at all.</p>

<p>A check, because a doubling is a big claim. Take what drivers pay at the pump and subtract the
wholesale price at the New York Harbor trading hub. That gap widened by
<strong>{mac['delta_cpg']:.1f} cents</strong> between 2015–2019 and 2021–2025. Murphy's own margin grew
{mu['delta_cpg']:.1f} cents. Those are nearly the same number, which tells you where the money most
likely went: taxes and shipping did not absorb it. <strong>It appears that almost all of it became
store profit.</strong></p>

<p>Why it happened is worth pondering. Note that this is our hypothesis. But we have poked at it
using the data, and it seems to hold. It also jibes with our lived experience, which should not be
discounted.</p>

<p>When COVID stopped people driving, fuel volume and store traffic fell together — Casey's reported same-store gallons down 8.1% and inside customer traffic down 8.7%. With fewer customers coming through, the fuel had to earn more from each one. Margins rose.</p>

<p>What nobody expected is that fuel margins stayed there. Customers came back. Margins did not fall. Casey's now tells its investors it expects them to &ldquo;remain elevated from historical levels for the foreseeable future&rdquo;. Murphy is still selling about 5% fewer gallons per store than in 2019 — and earning twice as much on each one.</p>

<p>So, post-COVID fuel margins are the advantage we have been teasing throughout this post. File
that knowledge away as we turn back to the topic at hand — SNAP authorizations.</p>

<h2>The format thrives, but are all owners realizing the benefit?</h2>

<p>Everything so far has been about the chains. What about the much larger group of single-owner stores?</p>

<p>On the surface they look fine. They added about {sc['single-owner stores']['y2025'] - sc['single-owner stores']['y2006']:,} authorizations over the same nineteen years, growth of {pct('single-owner stores'):.0f}%. Slower than the chains, but a category adding that many stores is not a category in trouble.</p>

<p>The difference only shows up when you stop counting stores and start asking whether they are the <em>same</em> stores.</p>

<figure>{c_surv}
<figcaption>Share of stores first authorized 2008–2012 that were still authorized on 31 December
2025.</figcaption></figure>

<p>Take every store authorized between 2008 and 2012 and ask how many are still authorized thirteen
years later. For chains that sell fuel it is <strong>{ch['rate']}%</strong> — the same rate as dollar
stores, which is the benchmark from yesterday. For single-owner stores it is
<strong>{so['rate']}%</strong>.</p>

<p>It would be easy to read that as a wave of closures. It is not, and the check matters. The Census
Bureau counts business locations whether or not they take EBT. Between {cbp['base_year']} and
{cbp['last_year']} convenience establishments <strong>rose {cbp['cbp_pct']:+.1f}%</strong>. The
under-ten-staff slice — the cut we used for grocers — slipped {abs(cbp['cbp_under10_pct']):.1f}%,
while the very smallest stores, under five staff, <strong>rose
{cbp['cbp_under5_pct']:+.1f}%</strong>.</p>

<p>So the corner store is not disappearing. What is more likely happening is that the <em>specific business or owner</em> in the building keeps changing. A store is sold, renamed, re-registered, and a new record appears. The storefront stays. The
owner turns over.</p>

<p><strong>That is the difference between a chain and a single owner.</strong> A chain compounds:
whatever it built twenty years ago, it largely still has, and it adds to it. A single-owner site is
likely churning — handing the keys to the next person. Same storefront, same shelves, new name on the paperwork — and in this data,
a new record starting from scratch.</p>

<h2>What it adds up to</h2>

<p>Drilling into this format does not give a new answer. It reinforces the same takeaway.</p>

<p>Small grocers are disadvantaged because they are small and alone. Dollar stores are advantaged because they are small and part of a massive chain. Convenience stores split along exactly that line: the fuel-selling chains kept <strong>{ch['rate']}%</strong> of their stores over thirteen years, the single owners only kept <strong>{so['rate']}%</strong>.</p>

<p>So think of that Wawa or Sheetz going up on the corner near you as something close to a dollar store with one extra advantage: a fuel margin that doubled after 2020 and never came back. Same small footprint, same chain economics, plus a second profit stream that got far more profitable.</p>

<p>For a household with an EBT card, the practical result is the same either way. In a small town,
the gravitational pull of grocery economics is leaving them two options: a dollar store and a gas
station. Both are now cheap to run, both can be profitable at smaller volume. <strong>Unfortunately,
neither was designed to sell the week of groceries assumed by the government's Thrifty Food
Plan.</strong></p>

<p>But that is today. The million-dollar question is what happens to SNAP authorization for these
fuel convenience stores when the new stocking rule takes effect in a few short months, raising the
number of staple items required on the shelf from 36 to 84. We will explore this in depth in the
closing post of this series, but for now we can see a few options — and they will not fall
evenly. A single-owner station pays the cost alone; a chain writes one shelf plan for thousands of
stores. So:</p>

<ol>
<li>They can drop SNAP, further limiting food access for our nation's most vulnerable
population.</li>
<li>They can comply and eat the cost, sacrificing profits (not likely).</li>
<li>Or they can comply and pass the cost on at the pump — where margins have already doubled once
this decade.</li>
</ol>

<p>Note that if we head down path 3 — which any profit-maximizing business would likely choose —
they will be doing it in the middle of what is, in our view, a fuel crisis of a magnitude we have
not seen since 1973.</p>

<p>Another lesson in the law of unintended consequences.</p>

<p><strong>Next week: we turn our attention to the larger store formats.</strong></p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>An oil brand on the canopy is not an owner.</strong> A "Shell" or "BP" station is almost
never owned by Shell or BP — it is somebody's own business with a fuel supply contract. So those
stores count here as single-owner stores. Broken out separately they survive at 20.6% against 13.5%
for stores with no brand at all: a real difference, too small to change the picture.</p>
<p><strong>The list of fuel chains is a judgment call.</strong> Twenty-four operators are named
because they run fuel pumps at essentially all their US sites. The list is in the code. 7-Eleven is
deliberately left out — it is the largest convenience brand here by a wide margin and is mixed on
fuel, so including it would let one brand carry a claim about fuel economics.</p>
<p><strong>Margin is not profit.</strong> Fuel margin is revenue minus the cost of the fuel. It does
not subtract labor, rent, card fees or the pumps themselves.</p>
<p><strong>Growth in the single-owner segment is ambiguous.</strong> A rising count can mean more
stores or wider EBT take-up among stores that already existed. The census comparison is what separates
those, and it is only available for the category as a whole.</p>
<p>Two companies are not an industry. Murphy USA and Casey's are the operators here that publish a
fuel margin. Circle K's parent files in Canada rather than with the SEC. The national price gap is
what carries the claim beyond these two, and it agrees with them.</p>
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
    print(f"  chains {ch['rate']}% vs single owners {so['rate']}%")


if __name__ == "__main__":
    main()
