"""Assemble reports/post3/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post3.json"
DIR = ROOT / "reports" / "post3"
IMG = DIR / "images"


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        # Keyed by slug rather than list position. With a list, a duplicated
        # number or an inserted figure shifted every later figs[i] lookup by one
        # and silently printed the wrong chart under the text — which is exactly
        # what happened in this series.
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    acc, sp, den = d["access"], d["spacing"], d["density_20mi"]
    st, cen, zl = d["stores"], d["census"], d["pharmacy_loss_zips"]
    radii = [a["radius"] for a in acc]
    a10 = next(a for a in acc if a["radius"] == 10)
    a20 = next(a for a in acc if a["radius"] == 20)
    z20 = next(z for z in zl if z["radius"] == 20)
    other = sp["all other superstores"]

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{a10['depends_on_walmart']/1e6:.0f}M",
          "label": "people within 10 miles of a superstore only because of Walmart"},
         {"value": f"{den['median_density']:.0f}",
          "label": f"people per sq mile in the tracts that depend on it, vs {den['median_density_all']:,.0f} nationally"},
         {"value": f"{sp['Walmart']['median']:.1f} mi",
          "label": f"median gap between Walmart superstores, vs {other['median']:.1f} for everyone else"}])

    fig(1, "access-curve",
        "Share of the US population within a given straight-line distance of a SNAP-authorized superstore.",
        figures.line_png, radii,
        [{"name": "with Walmart", "values": [a["with_pct"] for a in acc], "slot": 1},
         {"name": "without Walmart", "values": [a["without_pct"] for a in acc], "slot": 2}],
        ylabel="% of US population within reach",
        title="Take Walmart out and the reach drops sharply",
        subtitle="share of the US population within a given distance of a superstore")

    fig(2, "access-table",
        "Population within reach of a superstore, with and without Walmart.",
        figures.table_png, ["Distance", "With Walmart", "Without", "Difference"],
        [[f"{a['radius']} mi", f"{a['with_pct']}%", f"{a['without_pct']}%",
          f"{a['depends_on_walmart']/1e6:.1f}M"] for a in acc], highlight_row=1,
        title="How many people reach a superstore, with and without",
        subtitle="US population within each distance band")

    fig(3, "dependence-by-radius",
        "Population that would fall outside the radius without a Walmart.",
        figures.hbar_png,
        [{"label": f"{a['radius']} miles", "value": round(a["depends_on_walmart"]/1e6, 1),
          "slot": 1 if a["radius"] == 10 else 0} for a in acc], suffix="M",
        title="13 million people depend on Walmart at ten miles",
        subtitle="people who would fall outside the radius without a Walmart")

    fig(4, "store-spacing",
        "Median distance from each superstore to the nearest other store of the same group.",
        figures.hbar_png,
        [{"label": "Walmart", "value": sp["Walmart"]["median"], "slot": 1},
         {"label": "all other superstores", "value": other["median"], "slot": 0}],
        suffix=" mi",
        title="Walmart spaces its stores out. Others pile up.",
        subtitle="median miles to the nearest other store of the same group")

    md = f"""# 13 million people reach a superstore only because of Walmart

*SNAP-authorized retailers, 2025, against 2020 census tract population. {st['all']:,} superstores, of
which {st['walmart']:,} are Walmart. Straight-line distance.*

**{a10['depends_on_walmart']/1e6:.0f}M** people within 10 miles of a superstore only because of Walmart.
**{den['median_density']:.0f}** people per square mile in the tracts that depend on it, against
{den['median_density_all']:,.0f} nationally.
**{sp['Walmart']['median']:.1f} mi** median distance between Walmart superstores, against
{other['median']:.1f} for everyone else.

![Headline figures](images/00-key-figures.png)

---

On the map of SNAP retailers, Walmart looks different from every other chain. Other superstores cluster where the people are. Walmart's are spread out almost evenly, including across country with very little else in it. This piece tries to put a number on what that spread covers.

First, a check the rest of this depends on. Walmart has **{cen['authorized']:,}** SNAP-authorized superstores. The company reports operating about {cen['reported']:,}. That is a ratio of {cen['ratio']}. For this chain the record really is a store count, so we can talk about stores rather than paperwork.

## What disappears without it

Take every populated census tract. Measure how far it is to the nearest SNAP-authorized superstore. Then do it twice: once with all {st['all']:,} of them, and once with Walmart's {st['walmart']:,} taken off the map. The gap between the two lines is what Walmart covers.

![{figs["access-curve"]['caption']}](images/{figs["access-curve"]['file']})

The same curve as exact counts, band by band:

![{figs["access-table"]['caption']}](images/{figs["access-table"]['file']})

At ten miles the gap is **{a10['depends_on_walmart']/1e6:.1f} million people**. At twenty miles it is {a20['depends_on_walmart']/1e6:.1f} million. The gap narrows as the circle widens. That is the shape you would expect. Give people far enough to drive and someone else's store comes into range.

![{figs["dependence-by-radius"]['caption']}](images/{figs["dependence-by-radius"]['file']})

## The difference is almost entirely rural

The {den['tracts']:,} tracts that reach a superstore within twenty miles only because of Walmart hold
**{den['pop']/1e6:.1f} million people**, and they are not a random slice of the country. Median
population density in those tracts is **{den['median_density']:.0f} people per square mile**, against
{den['median_density_all']:,.0f} nationally — roughly
{den['median_density_all']/den['median_density']:.0f} times sparser.

That is the answer to what the map looks like. Walmart is not evenly spread for its own sake. It is the only chain of this size that builds where the population does not obviously justify it.

![{figs["store-spacing"]['caption']}](images/{figs["store-spacing"]['file']})

The spacing bears it out. The typical Walmart superstore sits **{sp['Walmart']['median']:.1f} miles**
from the next one. The typical non-Walmart superstore sits **{other['median']:.1f} miles** from its
nearest neighbour — they are effectively piled on top of each other in metros. Walmart's spacing is also
more even: a coefficient of variation of {sp['Walmart']['cv']} against {other['cv']}. Not a literal
grid, but far closer to one than anything else in this format.

## How this fits the rest of the series

Earlier pieces argued that thin markets only support stores that are cheap to run. That is why dollar stores and gas stations are what remain in small towns. Walmart looks like the opposite case. It is about the most expensive format there is, and it reaches into places with sixty people per square mile.

It is not a contradiction. It is a different solution to the same problem. Take the {z20['base']:,} ZIP
codes from that piece — the ones that lost their last chain pharmacy — and ask how many can reach a
superstore.

**{z20['with_walmart']:,} of {z20['base']:,}** are within twenty miles of one. Without Walmart,
{z20['without_walmart']:,}. So these places are not superstore deserts at all. They are within driving
distance of a very large store, and Walmart is why for
{z20['with_walmart'] - z20['without_walmart']} of them.

What they lack is anything *local*. The dollar store solves the scale problem by being small enough to live on six thousand people. Walmart solves it by being big enough to pull from a whole county, and asking the county to drive. Both work. What vanished is the format in the middle: the full-line grocery store on a small town's main street, big enough to stock fresh food and close enough to walk to.

That carries no verdict. A household with a car and a Walmart twenty miles away gets better prices and far more choice than a small-town grocer offered in 2006. A household without a car has a dollar store. Same change, opposite results. This data cannot tell you which one fits any given family.

## Limits

**Removing stores from a map is not a counterfactual.** The "without Walmart" figures say what coverage
looks like if those stores vanish today. They do not say what the country would look like if Walmart had never existed. Other chains might have built some of those sites. Walmart's arrival probably stopped others from being built at all. So read the gap as today's dependence, not as history.

Distances are straight lines from the middle of each tract. A real drive usually runs 1.2 to 1.4 times further. So the twenty-mile row is more like a twenty-five to twenty-eight mile drive. People also do not all live at the middle of a tract, and rural tracts are large.

"Superstore" is USDA's own category. It covers warehouse clubs and mass merchants as well as supercenters. Some of those need a paid membership, and not all sell a full range of groceries. So this overstates food access a little for the non-Walmart group.

Nothing here measures prices, selection, or transport. Above all it does not know whether a household has a car. That is the thing that decides whether twenty miles is a quick errand or a real wall.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and 2020 Decennial Census (DHC,
table P1) tract population with 2020 Gazetteer tract centroids; {d['total_pop']:,} people. Walmart store
count from company reporting. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post3.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post3.html", DIR / "post3-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post3.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
