"""Render reports/post3.html from reports/data/post3.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS
from config import ROOT

DATA = ROOT / "reports" / "data" / "post3.json"
OUT = ROOT / "reports" / "post3.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(3, "light", verbose=False)
    palette.validate(3, "dark", verbose=False)

    acc, sp, den = d["access"], d["spacing"], d["density_20mi"]
    st, cen, zl = d["stores"], d["census"], d["pharmacy_loss_zips"]
    radii = [a["radius"] for a in acc]
    tot = d["total_pop"]
    a10 = next(a for a in acc if a["radius"] == 10)
    a20 = next(a for a in acc if a["radius"] == 20)
    z10 = next(z for z in zl if z["radius"] == 10)
    z20 = next(z for z in zl if z["radius"] == 20)

    s_acc = [{"name": "with Walmart", "values": [a["with_pct"] for a in acc], "slot": 1},
             {"name": "without Walmart", "values": [a["without_pct"] for a in acc], "slot": 2}]
    c_acc = charts.line_chart(radii, s_acc, y_zero=False,
                              y_label="% of US population within reach")

    c_gap = charts.bar_chart(
        [{"label": f"{a['radius']} miles", "value": round(a["depends_on_walmart"] / 1e6, 1),
          "slot": 1 if a["radius"] == 10 else 0} for a in acc], suffix="M")

    c_sp = charts.bar_chart([
        {"label": "Walmart, median spacing", "value": sp["Walmart"]["median"], "slot": 1},
        {"label": "other superstores, median", "value": sp["all other superstores"]["median"],
         "slot": 0}], suffix=" mi")

    acc_tbl = "".join(
        f"<tr><td>{a['radius']} mi</td><td>{a['with_pct']}%</td><td>{a['without_pct']}%</td>"
        f"<td>{a['depends_on_walmart']/1e6:.1f}M</td></tr>" for a in acc)

    html = f"""<title>13 million people reach a superstore only because of Walmart</title>
<style>{CSS}</style>
<main>
<h1>13 million people reach a superstore only because of Walmart</h1>
<p class="sub">SNAP-authorized retailers, 2025, against 2020 census tract population ·
{st['all']:,} superstores, of which {st['walmart']:,} are Walmart · straight-line distance</p>

<div class="ledger">
  <div><b>{a10['depends_on_walmart']/1e6:.0f}M</b><span>people within 10 miles of a superstore only because of Walmart</span></div>
  <div><b>{den['median_density']:.0f}</b><span>people per square mile in the tracts that depend on it, against {den['median_density_all']:,.0f} nationally</span></div>
  <div><b>{sp['Walmart']['median']:.1f} mi</b><span>median distance between Walmart superstores, against {sp['all other superstores']['median']:.1f} for everyone else</span></div>
</div>

<p>Looking at the map of SNAP retailers, Walmart's footprint reads differently from every other
chain. Other superstores cluster where the people are. Walmart's are spread out almost evenly,
including across country where there is very little else. This is an attempt to put a number on what
that spread covers.</p>

<p>First, a check the rest of this depends on. Walmart's SNAP authorizations come to
<strong>{cen['authorized']:,}</strong> superstores against roughly {cen['reported']:,} the company
reports operating — a ratio of {cen['ratio']}. For this chain the authorization record is effectively
a store census, so it is fair to treat these as stores rather than paperwork.</p>

<h2>What disappears without it</h2>

<p>Take every populated census tract, measure the distance from its centre to the nearest
SNAP-authorized superstore, and do it twice: once with all {st['all']:,} of them, and once with
Walmart's {st['walmart']:,} removed.</p>

<figure>{c_acc}{charts.legend(s_acc)}
<figcaption>Share of the US population within a given straight-line distance of a SNAP-authorized
superstore.</figcaption></figure>

<table><thead><tr><th>Distance</th><th>With Walmart</th><th>Without</th><th>Difference</th></tr></thead>
<tbody>{acc_tbl}</tbody></table>

<p>At ten miles the gap is <strong>{a10['depends_on_walmart']/1e6:.1f} million people</strong>. At
twenty it is {a20['depends_on_walmart']/1e6:.1f} million. The gap narrows as the radius widens,
which is the expected shape: give people far enough to drive and someone else's store eventually comes
into range.</p>

<figure>{c_gap}
<figcaption>Population whose nearest superstore is a Walmart, and who would fall outside the radius
without one.</figcaption></figure>

<h2>The difference is almost entirely rural</h2>

<p>The {den['tracts']:,} tracts that reach a superstore within twenty miles only because of Walmart
hold <strong>{den['pop']/1e6:.1f} million people</strong>, and they are not a random slice of the
country. Median population density in those tracts is
<strong>{den['median_density']:.0f} people per square mile</strong>, against
{den['median_density_all']:,.0f} nationally — roughly
{den['median_density_all']/den['median_density']:.0f} times sparser.</p>

<p>That is the answer to the visual impression. It is not that Walmart is evenly spread for its own
sake; it is that Walmart is the only operator of this format that builds where the density does not
obviously justify it.</p>

<figure>{c_sp}
<figcaption>Median distance from each superstore to the nearest other store of the same
group.</figcaption></figure>

<p>The spacing bears it out. The typical Walmart superstore sits
<strong>{sp['Walmart']['median']:.1f} miles</strong> from the next one. The typical non-Walmart
superstore sits <strong>{sp['all other superstores']['median']:.1f} miles</strong> from its nearest
neighbour — they are effectively piled on top of each other in metros. Walmart's spacing is also more
even: a coefficient of variation of {sp['Walmart']['cv']} against
{sp['all other superstores']['cv']}. Not a literal grid, but far closer to one than anything else in
this format.</p>

<h2>How this fits the rest of the series</h2>

<p>The last piece in this series argued that thin markets only sustain retail with low fixed costs,
which is why dollar stores are what remains in small towns. Walmart looks like a direct contradiction:
about the highest-fixed-cost format there is, reaching into tracts at sixty people per square mile.</p>

<p>It is not a contradiction. It is a different solution to the same problem. Take the
{z10['base']:,} ZIP codes from that piece — the ones that lost their last chain pharmacy — and ask how
many can reach a superstore:</p>

<p><strong>{z20['with_walmart']:,} of {z20['base']:,}</strong> are within twenty miles of one.
Without Walmart, {z20['without_walmart']:,}. So these places are not superstore deserts at all. They
are within driving distance of a very large store, and Walmart is why for
{z20['with_walmart'] - z20['without_walmart']} of them.</p>

<p>What they lack is anything <em>local</em>. The dollar store solves the scale problem by being small
enough to survive on six thousand people. Walmart solves it by being large enough to pull from a
whole county, and asking the county to drive. Both work. What vanished between them is the format that
used to sit in the middle — the full-line grocery store on the main street of a small town, big enough
to stock fresh food and close enough to walk to.</p>

<p>That framing carries no verdict. A household with a car and a Walmart twenty miles away has better
prices and far better selection than the same household had from a small-town grocer in 2006. A
household without a car has a dollar store. Those are very different outcomes from the same
transformation, and this data cannot tell you which describes any particular family.</p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>Removing stores from a map is not a counterfactual.</strong> The "without Walmart" figures
say what coverage looks like if those stores vanish today. They do not say what the country would look
like had Walmart never existed — other retailers might have built some of those locations, and
Walmart's arrival plausibly deterred some that never got built. Read the gap as a measure of current
dependence, not of historical causation.</p>
<p>Distances are straight-line from the tract's centre of population. Road distance typically runs
1.2–1.4 times further, so the twenty-mile row is closer to a twenty-five to twenty-eight mile drive,
and the fifteen-mile row is nearer a twenty-mile drive. A tract's residents are also not all at its
centroid, and rural tracts are large.</p>
<p>"Superstore" is USDA's category, which includes warehouse clubs and mass merchants alongside
supercentres. Some require paid membership, and not all carry a full grocery assortment, so this
overstates full-line food access somewhat for the non-Walmart group.</p>
<p>Nothing here measures prices, assortment, transport, or whether a household has a car — which is
the variable that decides whether twenty miles is a minor errand or a real barrier.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and 2020 Decennial Census (DHC,
table P1) tract population with 2020 Gazetteer tract centroids; {tot:,} people across
{len(radii)} distance bands. Walmart store count from company reporting. Code, pipeline and
verification: <a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  10 mi gap {a10['depends_on_walmart']:,}  20 mi gap {a20['depends_on_walmart']:,}")
    print(f"  spacing: Walmart {sp['Walmart']['median']} mi vs "
          f"{sp['all other superstores']['median']} mi")


if __name__ == "__main__":
    main()
