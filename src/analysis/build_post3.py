"""Render reports/post3.html from reports/data/post3.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
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
                              y_label="% of US population within reach",
        title="Take Walmart out and the reach drops sharply",
        subtitle="share of the US population within a given distance of a superstore")

    c_gap = charts.bar_chart(
        [{"label": f"{a['radius']} miles", "value": round(a["depends_on_walmart"] / 1e6, 1),
          "slot": 1 if a["radius"] == 10 else 0} for a in acc], suffix="M",
        title="13 million people depend on Walmart at ten miles",
        subtitle="people who would fall outside the radius without a Walmart")

    c_sp = charts.bar_chart([
        {"label": "Walmart, median spacing", "value": sp["Walmart"]["median"], "slot": 1},
        {"label": "other superstores, median", "value": sp["all other superstores"]["median"],
         "slot": 0}], suffix=" mi",
        title="Walmart spaces its stores out. Others pile up.",
        subtitle="median miles to the nearest other store of the same group")

    acc_tbl = "".join(
        f"<tr><td>{a['radius']} mi</td><td>{a['with_pct']}%</td><td>{a['without_pct']}%</td>"
        f"<td>{a['depends_on_walmart']/1e6:.1f}M</td></tr>" for a in acc)

    html = f"""{HEAD}<title>13 million people reach a superstore only because of Walmart</title>
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

<p>On the map of SNAP retailers, Walmart looks different from every other chain. Other superstores cluster where the people are. Walmart's are spread out almost evenly, including across country with very little else in it. This piece tries to put a number on what that spread covers.</p>

<p>First, a check the rest of this depends on. Walmart has <strong>{cen['authorized']:,}</strong> SNAP-authorized superstores. The company reports operating about {cen['reported']:,}. That is a ratio of {cen['ratio']}. For this chain the record really is a store count, so we can talk about stores rather than paperwork.</p>

<h2>What disappears without it</h2>

<p>Take every populated census tract. Measure how far it is to the nearest SNAP-authorized superstore. Then do it twice: once with all {st['all']:,} of them, and once with Walmart's {st['walmart']:,} taken off the map. The gap between the two lines is what Walmart covers.</p>

<figure>{c_acc}{charts.legend(s_acc)}
<figcaption>Share of the US population within a given straight-line distance of a SNAP-authorized superstore.</figcaption></figure>

<p>The same curve as exact counts, band by band:</p>

<table><thead><tr><th>Distance</th><th>With Walmart</th><th>Without</th><th>Difference</th></tr></thead>
<tbody>{acc_tbl}</tbody></table>

<p>At ten miles the gap is <strong>{a10['depends_on_walmart']/1e6:.1f} million people</strong>. At twenty miles it is {a20['depends_on_walmart']/1e6:.1f} million. The gap narrows as the circle widens. That is the shape you would expect. Give people far enough to drive and someone else's store comes into range.</p>

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

<p>That is the answer to what the map looks like. Walmart is not evenly spread for its own sake. It is the only chain of this size that builds where the population does not obviously justify it.</p>

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

<p>Earlier pieces argued that thin markets only support stores that are cheap to run. That is why dollar stores and gas stations are what remain in small towns. Walmart looks like the opposite case. It is about the most expensive format there is, and it reaches into places with sixty people per square mile.</p>

<p>It is not a contradiction. It is a different answer to the same problem. Take the {z10['base']:,} ZIP codes that lost their last chain pharmacy, and ask how many can reach a superstore.</p>

<p><strong>{z20['with_walmart']:,} of {z20['base']:,}</strong> are within twenty miles of one.
Without Walmart, {z20['without_walmart']:,}. So these places are not superstore deserts at all. They
are within driving distance of a very large store, and Walmart is why for
{z20['with_walmart'] - z20['without_walmart']} of them.</p>

<p>What they lack is anything <em>local</em>. The dollar store solves the scale problem by being small enough to live on six thousand people. Walmart solves it by being big enough to pull from a whole county, and asking the county to drive. Both work. What vanished is the format in the middle: the full-line grocery store on a small town's main street, big enough to stock fresh food and close enough to walk to.</p>

<p>That carries no verdict. A household with a car and a Walmart twenty miles away gets better prices and far more choice than a small-town grocer offered in 2006. A household without a car has a dollar store. Same change, opposite results. This data cannot tell you which one fits any given family.</p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>Removing stores from a map is not a counterfactual.</strong> The "without Walmart" figures
say what coverage looks like if those stores vanish today. They do not say what the country would look like if Walmart had never existed. Other chains might have built some of those sites. Walmart's arrival probably stopped others from being built at all. So read the gap as today's dependence, not as history.</p>
<p>Distances are straight lines from the middle of each tract. A real drive usually runs 1.2 to 1.4 times further. So the twenty-mile row is more like a twenty-five to twenty-eight mile drive. People also do not all live at the middle of a tract, and rural tracts are large.</p>
<p>"Superstore" is USDA's own category. It covers warehouse clubs and mass merchants as well as supercenters. Some of those need a paid membership, and not all sell a full range of groceries. So this overstates food access a little for the non-Walmart group.</p>
<p>Nothing here measures prices, selection, or transport. Above all it does not know whether a household has a car. That is the thing that decides whether twenty miles is a quick errand or a real wall.</p>
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
