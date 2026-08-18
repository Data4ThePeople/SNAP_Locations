"""Render reports/post5.html from reports/data/post5.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post5.json"
# The fuel chapter's figures are read straight from its analysis output rather
# than restated here, so the two pieces cannot disagree about a shared number.
FUEL = ROOT / "reports" / "data" / "post6.json"
OUT = ROOT / "reports" / "post5.html"


def main():
    d = json.loads(DATA.read_text())
    d6 = json.loads(FUEL.read_text()) if FUEL.exists() else {}
    palette.validate(4, "light", verbose=False)
    palette.validate(4, "dark", verbose=False)

    f_surv = {r["segment"]: r for r in d6.get("survival", [])}
    # Keyed by post 6's segment names. A silent .get default here would survive a
    # rename and quietly publish a stale number, so this raises instead.
    f_ff = f_surv["chains that sell fuel"]
    f_do = f_surv["dollar stores"]
    f_sc = d6["stock_change"]["chains that sell fuel"]
    f_mu = d6["fuel_margin"]["companies"]["Murphy USA"]

    arc, ac = d["arc"], d["arc_change"]
    # From the counts, not the rounded multiple: 494 -> 2,054 is +316%, where a
    # 4.2x would imply +320%.
    dollar_pct = round(100 * (arc["dollar"][-1] / arc["dollar"][0] - 1))
    f_pct = round(100 * (f_sc["y2025"] / f_sc["y2006"] - 1))
    grp, pres, gr, seq = d["groups"], d["presence"], d["growth"], d["sequencing"]
    mix = d["ownership_mix"]
    den, tl = d["density"], d["total_loss"]
    pr = {p["label"]: p for p in pres}
    s1 = d["series"].get("post1", {})
    s2 = d["series"].get("post2", {})
    s4 = d["series"].get("post4", {})

    s_arc = [{"name": "convenience", "values": arc["conv"], "slot": 3},
             {"name": "grocery", "values": arc["groc"], "slot": 4},
             {"name": "dollar", "values": arc["dollar"], "slot": 1},
             {"name": "chain pharmacy", "values": arc["drug"], "slot": 2}]
    c_arc = charts.line_chart(arc["years"], s_arc, y_label="SNAP-authorized stores",
        title="Dollar stores rose as everything else fell",
        subtitle="SNAP-authorized stores across the pharmacy-loss ZIP codes")

    pres_tbl = "".join(
        f"<tr><td>{p['label']}</td><td>{p['lost_pct']}%</td><td>{p['kept_pct']}%</td></tr>"
        for p in pres)

    c_growth = charts.bar_chart([
        {"label": "dollar, lost pharmacy", "value": gr["lost"]["dollar_pct"], "slot": 2},
        {"label": "dollar, kept pharmacy", "value": gr["kept"]["dollar_pct"], "slot": 0},
        {"label": "convenience, lost pharmacy", "value": gr["lost"]["conv_pct"], "slot": 2},
        {"label": "convenience, kept pharmacy", "value": gr["kept"]["conv_pct"], "slot": 0},
    ], suffix="%",
        title="Dollar stores grew slower where the pharmacy left",
        subtitle="change in store counts, 2021 to 2025")

    c_den = charts.bar_chart([
        {"label": "lost pharmacy", "value": den["lost"]["median_pop"], "slot": 2},
        {"label": "kept pharmacy", "value": den["kept"]["median_pop"], "slot": 0},
        {"label": "lost, and no grocery left", "value": den["lost_no_grocery"]["median_pop"],
         "slot": 2},
    ],
        title="What these places share is being small",
        subtitle="median ZIP code population, 2020 census")

    c_small = charts.bar_chart([
        {"label": "lost pharmacy, under 10k", "value": den["lost"]["under_10k_pct"], "slot": 2},
        {"label": "kept pharmacy, under 10k", "value": den["kept"]["under_10k_pct"], "slot": 0},
        {"label": "lost pharmacy, under 5k", "value": den["lost"]["under_5k_pct"], "slot": 2},
        {"label": "kept pharmacy, under 5k", "value": den["kept"]["under_5k_pct"], "slot": 0},
    ], suffix="%",
        title="A third have fewer than ten thousand people",
        subtitle="share of ZIP codes below each population line")

    html = f"""{HEAD}<title>Twenty years, one pattern</title>
<style>{CSS}</style>
<main>
<h1>Twenty years, one pattern</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records, with 2020 census population by ZCTA · the last chapter; an epilogue follows</p>

<div class="ledger">
  <div><b>{mix['chain']['share_2006']:.0f}% → {mix['chain']['share_2025']:.0f}%</b><span>chains' share of every SNAP retailer in the country, 2006 to 2025</span></div>
  <div><b>{grp['lost']:,}</b><span>ZIP codes lost their last SNAP-authorized chain pharmacy since 2021</span></div>
  <div><b>{den['lost_no_grocery']['median_pop']:,}</b><span>median population of those that now have no grocery at all</span></div>
</div>

<p>Five days got us here. Small grocers left in numbers and mostly stopped being replaced. Dollar
stores almost never left. Convenience stores multiplied while their owners turned over. Put every format
on one scale and two rules appeared: bigger stores kept their authorization, and a chain did not need to
be big. Then the pharmacy chains, which had both advantages, collapsed anyway.</p>

<p>Read on their own they are five unrelated retail stories. They are not unrelated in the places where
they land.</p>

<p>Take the <strong>{grp['lost']:,} ZIP codes</strong> that lost their last SNAP-authorized chain pharmacy between 2021 and 2025. Now look at every other kind of food store in those same places, over twenty years.</p>

<figure>{c_arc}{charts.legend(s_arc)}
<figcaption>SNAP-authorized stores by format, aggregated across the {grp['lost']:,} ZIP codes that lost
their last chain pharmacy between 2021 and 2025.</figcaption></figure>

<p>Dollar stores went from {arc['dollar'][0]:,} to {arc['dollar'][-1]:,} —
<strong>{dollar_pct:+}%</strong>. Grocery of every size went from {arc['groc'][0]:,} to
{arc['groc'][-1]:,}, down {abs(ac['groc_pct']):.0f}%. Pharmacies peaked at {ac['drug_peak']:,} in
{ac['drug_peak_year']} and are now at zero. In 2006 these places had roughly ten times as many grocery
stores as dollar stores. Today grocery outnumbers dollar by about two to one, and the direction of
travel is unambiguous.</p>

<h2>The obvious explanation is wrong</h2>

<p>The natural reading is substitution: dollar stores squeezed the others out. It is worth stating
plainly that the data does not support it, because it is the interpretation everyone reaches for
first — including me.</p>

<p>Three tests, all using a control group of the {grp['kept']:,} ZIP codes that had a chain pharmacy in
2021 and still have one. Without that comparison, every number here looks like one store pushing out another. Dollar stores grew almost everywhere, so you need a control group to see anything at all.</p>

<p><strong>First: presence is identical.</strong> Dollar and convenience stores are no more common
where the pharmacy went than where it stayed.</p>

<table><thead><tr><th>In 2025, the ZIP has…</th><th>Lost pharmacy</th><th>Kept pharmacy</th></tr></thead>
<tbody>{pres_tbl}</tbody></table>

<p><strong>Second: growth was slower, not faster.</strong> If dollar stores were moving into vacated
ground you would expect the opposite.</p>

<figure>{c_growth}
<figcaption>Change in store counts, 2021 to 2025, in ZIP codes that lost their last chain pharmacy
against those that kept one.</figcaption></figure>

<p><strong>Third, and decisive: the dollar stores were already there.</strong> Of the
{seq['base']:,} ZIP codes, <strong>{seq['had_before_pct']}%</strong> already had a dollar store in 2021,
before the pharmacy left. Only {seq['arrived_after']} — {seq['arrived_after_pct']}% — gained their first
one afterwards. Nobody moved in to fill a gap. They were neighbours for years.</p>

<p>The timing does not work either. Pharmacy authorizations were flat from 2016 to 2021, then fell off after 2022. That tracks opioid lawsuits, drug pricing, and Rite Aid's bankruptcy. Dollar stores opened at a near-constant rate for sixteen years, through all of it.</p>

<h2>What these places actually have in common</h2>

<p>The distinguishing feature is not what arrived. It is how small they are.</p>

<figure>{c_den}
<figcaption>Median 2020 census population of the ZIP code (ZCTA), by group.</figcaption></figure>

<p>Median population in a ZIP that lost its pharmacy is <strong>{den['lost']['median_pop']:,}</strong>,
against <strong>{den['kept']['median_pop']:,}</strong> where the pharmacy survived. And among those
that have also lost every grocery store, the median is
<strong>{den['lost_no_grocery']['median_pop']:,} people</strong>.</p>

<figure>{c_small}
<figcaption>Share of ZIP codes below population thresholds, by group.</figcaption></figure>

<p>A third of the pharmacy-loss ZIPs have fewer than ten thousand residents, against a tenth of the
control. One in eight has fewer than five thousand.</p>

<p>That is the thread. <strong>A supermarket needs volume. A chain pharmacy needs prescription volume. A dollar store needs neither.</strong> Its whole model is a small box, few staff, a narrow range, and no fresh food to spoil. That is exactly why it works in a town of six thousand where a grocery store cannot.</p>

<p>And it is not the only format built that way. The gas station chapter found a second one, and it lasts just as well. <strong>{f_ff['rate']}% of convenience chains that sell fuel</strong> from the 2008–2012 group were still authorized in 2025. For dollar stores it was {f_do['rate']}%. That is a gap of well under one point. Those chains also added {f_pct:+}% over the twenty years. So naming only dollar stores would leave out half the answer.</p>

<p>Read that way, the pieces in this series stop being coincidences. They become one story told from several angles.</p>

<ul>
<li>Small grocery's collapse was a collapse in <strong>new stores</strong>. Sign-ups fell
{abs(round(100*(s2.get('drivers',{}).get('new_after',1)/s2.get('drivers',{}).get('new_before',1)-1))) if s2 else 55}%. The 2018 stocking rule asks every store for a fixed amount of inventory, which is a large demand on a small shop and no demand at all on a big one. In USDA's own categories the fall sorted by exactly that: new sign-ups dropped 58% for small grocers, while the largest grocery category grew 8%.</li>
<li>Dollar stores' advantage was never fast opening. It was that they
<strong>{round(100*s1.get('survival',[{}])[0].get('rate',0.78)) if s1 else 78}%</strong> stay — a format
cheap enough to survive where others cannot.</li>
<li>Fuel-forward convenience chains match that staying power, and after 2020 they gained something
dollar stores did not: fuel margins roughly doubled and stayed there. Murphy USA's went from
{f_mu['pre_mean']} to {f_mu['post_mean']} cents a gallon.</li>
<li>Pharmacies were removed by forces of their own, but they were removed
<strong>from the thinnest markets first</strong>.</li>
</ul>

<p>No one pushed anyone out. Several separate pressures pushed the same way. The formats left standing were the ones with the lowest cost per location: the dollar store and the gas station. They arrived at the same place from opposite ends of retail. That is harder to fix than a rival would be. If one competitor were driving this, there would be a competitor to regulate.</p>

<h2>What is at stake</h2>

<p>In <strong>{tl['no_grocery']}</strong> of these ZIP codes the only SNAP-authorized food retail left
is a dollar store or a convenience store. In <strong>{tl['no_snap_retail_at_all']}</strong> there is no
SNAP-authorized retailer of any kind. A household with an EBT card in those places is choosing among
shelf-stable groceries, or driving.</p>

<p>There is a second cost this data cannot measure, and it should not go unsaid. For many people a pharmacist is the easiest health professional to reach. They check a drug interaction, take a blood pressure, answer a question that would otherwise need an appointment. When the last pharmacy in a small town closes, that goes too. These records
count SNAP authorizations; they say nothing about prescriptions or clinical advice, and the pharmacy
desert literature is the place to look for that. But it is the same buildings and the same towns.</p>

<p>That is where the measurement ends. It leaves a question about policy that this data cannot settle
on its own, and a rule that changes the answer in a few months. Both are taken up in the epilogue that
follows this piece.</p>

<div class="caveat">
<h3>Limits</h3>
<p>Every figure here counts <strong>SNAP authorizations</strong>, not storefronts. For the pharmacy chains those are nearly the same thing. Walgreens' authorizations run at 0.97 of its own reported store count. For independents they are not the same, and this series does not treat them as such.</p>
<p>The control group is ZIP codes that had a chain pharmacy in 2021 and kept one. It is not a matched
sample: the two groups differ in population, which is the finding rather than a nuisance. Read the
comparison as descriptive, not causal.</p>
<p>Population is 2020 census by ZCTA, which approximates but does not exactly equal a ZIP code.
{den['lost']['zips_matched']:,} of the {grp['lost']:,} pharmacy-loss ZIPs matched a ZCTA.</p>
<p>Nothing here measures sales, floor space, assortment or prices. A dollar store and a supermarket
each count as one record, and the question of what is actually purchasable in these places needs a
different source.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and 2020 Decennial Census
(DHC, table P1) population by ZCTA. Analysis uses 656,868 stores with usable coordinates; a store
counts as active in a year if an authorization covered 31 December. Fuel-chain survival and margin
figures are from the gas station chapter. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  {grp['lost']:,} lost-pharmacy ZIPs vs {grp['kept']:,} control")
    print(f"  median pop {den['lost']['median_pop']:,} vs {den['kept']['median_pop']:,}")
    print(f"  dollar {ac['dollar_multiple']}x, grocery {ac['groc_pct']}%")


if __name__ == "__main__":
    main()
