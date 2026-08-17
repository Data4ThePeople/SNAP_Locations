"""Render reports/post5.html from reports/data/post5.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS
from config import ROOT

DATA = ROOT / "reports" / "data" / "post5.json"
OUT = ROOT / "reports" / "post5.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(4, "light", verbose=False)
    palette.validate(4, "dark", verbose=False)

    arc, ac = d["arc"], d["arc_change"]
    grp, pres, gr, seq = d["groups"], d["presence"], d["growth"], d["sequencing"]
    den, tl = d["density"], d["total_loss"]
    pr = {p["label"]: p for p in pres}
    s1 = d["series"].get("post1", {})
    s2 = d["series"].get("post2", {})
    s4 = d["series"].get("post4", {})

    s_arc = [{"name": "convenience", "values": arc["conv"], "slot": 3},
             {"name": "grocery", "values": arc["groc"], "slot": 4},
             {"name": "dollar", "values": arc["dollar"], "slot": 1},
             {"name": "chain pharmacy", "values": arc["drug"], "slot": 2}]
    c_arc = charts.line_chart(arc["years"], s_arc, y_label="SNAP-authorized stores")

    pres_tbl = "".join(
        f"<tr><td>{p['label']}</td><td>{p['lost_pct']}%</td><td>{p['kept_pct']}%</td></tr>"
        for p in pres)

    c_growth = charts.bar_chart([
        {"label": "dollar, lost pharmacy", "value": gr["lost"]["dollar_pct"], "slot": 2},
        {"label": "dollar, kept pharmacy", "value": gr["kept"]["dollar_pct"], "slot": 0},
        {"label": "convenience, lost pharmacy", "value": gr["lost"]["conv_pct"], "slot": 2},
        {"label": "convenience, kept pharmacy", "value": gr["kept"]["conv_pct"], "slot": 0},
    ], suffix="%")

    c_den = charts.bar_chart([
        {"label": "lost pharmacy", "value": den["lost"]["median_pop"], "slot": 2},
        {"label": "kept pharmacy", "value": den["kept"]["median_pop"], "slot": 0},
        {"label": "lost, and no grocery left", "value": den["lost_no_grocery"]["median_pop"],
         "slot": 2},
    ])

    c_small = charts.bar_chart([
        {"label": "lost pharmacy, under 10k", "value": den["lost"]["under_10k_pct"], "slot": 2},
        {"label": "kept pharmacy, under 10k", "value": den["kept"]["under_10k_pct"], "slot": 0},
        {"label": "lost pharmacy, under 5k", "value": den["lost"]["under_5k_pct"], "slot": 2},
        {"label": "kept pharmacy, under 5k", "value": den["kept"]["under_5k_pct"], "slot": 0},
    ], suffix="%")

    html = f"""<title>The pharmacy left. The grocery left. The dollar store stayed.</title>
<style>{CSS}</style>
<main>
<h1>The pharmacy left. The grocery left. The dollar store stayed.</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records, with 2020 census population by ZCTA · the fifth and last in this series</p>

<div class="ledger">
  <div><b>{grp['lost']:,}</b><span>ZIP codes lost their last SNAP-authorized chain pharmacy since 2021</span></div>
  <div><b>{ac['dollar_multiple']}×</b><span>growth in dollar stores in those same ZIP codes since 2006</span></div>
  <div><b>{den['lost_no_grocery']['median_pop']:,}</b><span>median population of those that now have no grocery at all</span></div>
</div>

<p>The four earlier pieces in this series each followed one format. Dollar stores almost never leave
the program. Small grocers left in numbers, and mostly stopped being replaced. Pharmacy chains held
flat for years and then collapsed. Read separately they are three unrelated retail stories.</p>

<p>They are not unrelated in the places where they land. Take the
<strong>{grp['lost']:,} ZIP codes</strong> that lost their last SNAP-authorized chain pharmacy between
2021 and 2025, and look at what has happened to every other kind of food retailer in those same
places over twenty years.</p>

<figure>{c_arc}{charts.legend(s_arc)}
<figcaption>SNAP-authorized stores by format, aggregated across the {grp['lost']:,} ZIP codes that lost
their last chain pharmacy between 2021 and 2025.</figcaption></figure>

<p>Dollar stores went from {arc['dollar'][0]:,} to {arc['dollar'][-1]:,} —
<strong>{ac['dollar_multiple']}×</strong>. Grocery of every size went from {arc['groc'][0]:,} to
{arc['groc'][-1]:,}, down {abs(ac['groc_pct']):.0f}%. Pharmacies peaked at {ac['drug_peak']:,} in
{ac['drug_peak_year']} and are now at zero. In 2006 these places had roughly ten times as many grocery
stores as dollar stores. Today grocery outnumbers dollar by about two to one, and the direction of
travel is unambiguous.</p>

<h2>The obvious explanation is wrong</h2>

<p>The natural reading is substitution: dollar stores squeezed the others out. It is worth stating
plainly that the data does not support it, because it is the interpretation everyone reaches for
first — including me.</p>

<p>Three tests, all using a control group of the {grp['kept']:,} ZIP codes that had a chain pharmacy in
2021 and still have one. Without that comparison every number here looks like substitution, because
dollar stores grew almost everywhere.</p>

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

<p>And the timing does not work either. Pharmacy authorizations were flat from 2016 to 2021 and fell
off after 2022, tracking opioid litigation, pharmacy reimbursement and Rite Aid's bankruptcy. Dollar
store openings ran at a near-constant rate for sixteen years, indifferent to all of it.</p>

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

<p>That is the thread. <strong>A supermarket needs volume. A chain pharmacy needs prescription
volume. A dollar store needs neither.</strong> Its whole model is a small box, a narrow assortment,
few staff and no fresh inventory to spoil — which is precisely why it works in a market of six
thousand people where a grocery store does not.</p>

<p>Read that way, the three stories in this series stop being coincidences and become the same story
told from three angles:</p>

<ul>
<li>Small grocery's collapse was an <strong>entry</strong> collapse — new authorizations fell
{abs(round(100*(s2.get('drivers',{}).get('new_after',1)/s2.get('drivers',{}).get('new_before',1)-1))) if s2 else 55}%
— and the 2018 depth-of-stock rule added a fixed cost that a chain absorbs and a single store cannot.
Within USDA's own Combination Grocery/Other category, independents fell 64% while the dollar chains in
that same category fell 5%.</li>
<li>Dollar stores' advantage was never fast opening. It was that they
<strong>{round(100*s1.get('survival',[{}])[0].get('rate',0.78)) if s1 else 78}%</strong> stay — a format
cheap enough to survive where others cannot.</li>
<li>Pharmacies were removed by forces of their own, but they were removed
<strong>from the thinnest markets first</strong>.</li>
</ul>

<p>No one displaced anyone. Three different pressures pushed in the same direction, and the formats
with the lowest fixed costs were the ones left standing. That is harder to address than displacement
would be: if a competitor were driving this, there would be a competitor to regulate.</p>

<h2>What is at stake</h2>

<p>In <strong>{tl['no_grocery']}</strong> of these ZIP codes the only SNAP-authorized food retail left
is a dollar store or a convenience store. In <strong>{tl['no_snap_retail_at_all']}</strong> there is no
SNAP-authorized retailer of any kind. A household with an EBT card in those places is choosing among
shelf-stable groceries, or driving.</p>

<p>There is a second consequence this data cannot measure but which should not go unmentioned. A
retail pharmacy is, for many people, the most accessible health professional they have — the person who
checks an interaction, takes a blood pressure, gives advice that would otherwise require an
appointment. When the last pharmacy in a small town closes, that access goes with it. These records
count SNAP authorizations; they say nothing about prescriptions or clinical advice, and the pharmacy
desert literature is the place to look for that. But it is the same buildings and the same towns.</p>

<div class="caveat">
<h3>Limits</h3>
<p>Every retail figure counts <strong>SNAP authorizations</strong>, not storefronts. For the pharmacy
chains those are nearly the same thing — Walgreens' authorizations run at 0.97 of its own reported
store count — but for independents they are not, and this series does not treat them as such.</p>
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
(DHC, table P1) population by ZCTA. Analysis uses 611,164 stores with usable coordinates; a store
counts as active in a year if an authorization covered 31 December. Code, pipeline and verification:
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
