"""Render reports/post3.html from reports/data/post3.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post3.json"
OUT = ROOT / "reports" / "post3.html"

SHORT = {"Super Store": "Super store", "Supermarket": "Supermarket",
         "Grocery (Large)": "Large grocery", "Grocery (Medium)": "Medium grocery",
         "Grocery (Small)": "Small grocery", "Dollar Store": "Dollar store",
         "Convenience Store": "Convenience store"}


def main():
    d = json.loads(DATA.read_text())
    palette.validate(4, "light", verbose=False)
    palette.validate(4, "dark", verbose=False)

    L, B = d["ladder"], d["breakers"]
    sv, ow, gr = d["survival"], d["by_ownership"], d["growth"]
    go = d["growth_by_ownership"]

    # Ladder order is the finding, so the chart is never re-sorted by value.
    c_ladder = charts.bar_chart(
        [{"label": SHORT[f], "value": sv[f]["rate"], "slot": 1 if f == L[0] else 0}
         for f in L], suffix="%",
        title="The bigger the store, the likelier it kept its authorization",
        subtitle=f"still authorized in 2025, of those authorized {d['cohort']}")

    def cell(f, o):
        # A rate on ~110 stores is noise, and printing it does real damage here:
        # the three thin chain-grocery cells read as 21.1 / 6.7 / 3.6 going down
        # the column, which looks like the very size ladder this table exists to
        # show does NOT apply to chains. Say "too few" instead of showing a
        # number the reader will reasonably believe.
        c = ow[f][o]
        if c["n"] == 0:
            return "none"
        return "too few" if c["thin"] else f"{c['rate']}%"

    NOTE = ('"too few" = fewer than %d stores in that cell, so no rate is shown. '
            '"none" = there are no stores of that kind: every dollar store is a chain.'
            % d["min_n"])

    own_tbl = "".join(
        f"<tr><td>{SHORT[f]}</td><td>{cell(f,'independent')}</td>"
        f"<td>{cell(f,'chain')}</td><td>{sv[f]['rate']}%</td></tr>" for f in L + B)

    # Every (format, ownership) pair where both measures clear the sample floor.
    # Ownership goes in the LABEL, not only the colour, so no legend is needed
    # and the point stays identifiable to a colourblind reader.
    scatter_pts = [
        {"name": f"{SHORT[f]} ({'chain' if o == 'chain' else 'indep'})",
         "x": go[f][o]["mult"], "y": ow[f][o]["rate"],
         "slot": 1 if o == "chain" else 3}
        for f in L + B for o in ("chain", "independent")
        if not go[f][o]["thin"] and not ow[f][o]["thin"]]
    c_growth = charts.scatter_chart(
        scatter_pts,
        x_label="growth: 2025 stores as a multiple of 2006", x_suffix="x",
        y_label="still authorized in 2025", y_suffix="%",
        quadrant={"x": 1.0}, title="Only one format did both",
        note="Points left of the dashed line have fewer stores than in 2006.")

    ss, sg = sv["Super Store"], sv["Grocery (Small)"]
    ssc, dol = ow["Super Store"]["chain"], sv["Dollar Store"]
    ind = [ow[f]["independent"]["rate"] for f in L]
    lo = min(sv[f]["unknown_share"] for f in L + B)
    hi = max(sv[f]["unknown_share"] for f in L + B)
    T = "The bigger the store, the better it did — unless it belonged to a chain"

    html = f"""{HEAD}<title>{T}</title>
<style>{CSS}</style>
<main>
<h1>{T}</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · survival measured on the {d['cohort']} cohort, checked again at the end of 2025</p>

<div class="ledger">
  <div><b>{sg['rate']}%</b><span>of small groceries authorized in {d['cohort']} are still authorized,
    against {ss['rate']:.0f}% of super stores</span></div>
  <div><b>{ssc['rate']:.0f}%</b><span>survival for a chain store — about the same whether it is the
    largest format or the smallest</span></div>
  <div><b>{gr['Super Store']['mult']}x</b><span>super store growth since 2006, against the dollar
    store's {gr['Dollar Store']['mult']}x</span></div>
</div>

<p>The last three days each followed one small format. Small groceries went away. Dollar stores grew
and stayed. Convenience stores grew while their owners turned over. Three stories, three
explanations.</p>

<p>Put every format on one scale and the three collapse into two rules.</p>

<h2>Rule one: size</h2>

<p>Take every store authorized between 2008 and 2012 and ask which ones are still authorized today.
Sort the answer by how big the store is, using USDA's own size categories.</p>

<figure>{c_ladder}
<figcaption>Share of stores authorized in {d['cohort']} that were still authorized at the end of 2025,
by USDA store type, largest to smallest.</figcaption></figure>

<p>The ladder is almost too neat: <strong>{' , '.join(f"{sv[f]['rate']}%" for f in L)}</strong>, straight
down the size order with nothing out of place. A super store was
<strong>{ss['rate']/sg['rate']:.0f} times</strong> likelier to keep its authorization than a small
grocery.</p>

<p>That is a real finding, and on its own it is a bleak one. It says the thing that decided which stores
survived was a thing no small grocer could change.</p>

<h2>Rule two: rule one does not apply to chains</h2>

<p>Except that size is not quite what is doing the work. Split each format by who owns it and rule one
comes apart.</p>

<table><thead><tr><th>Store type</th><th>Independent</th><th>Chain</th><th>All</th></tr></thead>
<tbody>{own_tbl}</tbody></table>
<p class="fignote">{NOTE}</p>

<p>Among independent stores rule one holds exactly as stated:
<strong>{' , '.join(f"{r}%" for r in ind)}</strong> down the size order. So size is real. It is not merely
standing in for something else.</p>

<p>Now look down the chain column. A chain super store survives at <strong>{ssc['rate']}%</strong>. A
dollar store — the smallest box in the whole table — survives at <strong>{dol['rate']}%</strong>. Those
are the same number. For a chain, being large stopped mattering.</p>

<p><strong>Rule one does not apply to chains.</strong> That is the whole of rule two, and it is what
explains the last two days. Dollar stores are small, and every one of them is a chain. The convenience
stores that endured were the fuel chains, at 78.7%; the single-owner ones managed 14.2%.</p>

<p>Neither format was breaking rule one. Neither was subject to it.</p>

<h2>Staying power is not the same as growing</h2>

<p>Rule one said the super store was the safest place to be. That is true, and it is also the whole of
what being large bought you. The super store grew <strong>{gr['Super Store']['mult']}x</strong> since
2006. Dollar stores grew <strong>{gr['Dollar Store']['mult']}x</strong>. Supermarkets managed
{gr['Supermarket']['mult']}x.</p>

<p>So there are two different things a format can be good at, and they come apart. Put them on the same
chart — growth across the bottom, survival up the side — and split every format by ownership.</p>

<figure>{c_growth}
<figcaption>Growth against survival, by store type and ownership. Only pairs with at least
{d['min_n']} stores on both measures are plotted.</figcaption></figure>

<p>Read it in three passes.</p>

<p><strong>Chains sit above and to the right of their own independents, every time.</strong> Super
stores: {go['Super Store']['chain']['mult']}x and {ow['Super Store']['chain']['rate']}% for the chains,
against {go['Super Store']['independent']['mult']}x and {ow['Super Store']['independent']['rate']}% for
the independents. Supermarkets: {go['Supermarket']['chain']['mult']}x and
{ow['Supermarket']['chain']['rate']}% against {go['Supermarket']['independent']['mult']}x and
{ow['Supermarket']['independent']['rate']}%. Convenience stores:
{go['Convenience Store']['chain']['mult']}x and {ow['Convenience Store']['chain']['rate']}% against
{go['Convenience Store']['independent']['mult']}x and
{ow['Convenience Store']['independent']['rate']}%. In every format where both can be measured, the
chains grew faster <strong>and</strong> lasted longer.</p>

<p><strong>Fast growth does not buy staying power.</strong> Convenience chains grew
{go['Convenience Store']['chain']['mult']}x, second only to dollar stores — and barely half of them,
{ow['Convenience Store']['chain']['rate']}%, were still authorized thirteen years on. That is Day 3 in a
single point: the format kept expanding while the businesses inside it turned over.</p>

<p><strong>And one point sits on its own in the top right corner.</strong> The dollar store has the
fastest growth in the data and the highest survival in the data. Nothing else has both. The super store
lasted nearly as well and hardly grew; the convenience chains grew nearly as fast and did not last.</p>

<h2>What it adds up to</h2>

<p>Two rules, and they are worth stating plainly because between them they cover almost everything in
this series so far.</p>

<p><strong>Rule one: a bigger store was likelier to keep its SNAP authorization.</strong> That held for
every independent store in the data, right down the size order.</p>

<p><strong>Rule two: rule one does not apply to chains.</strong> A dollar store the size of a corner shop
held its authorization as reliably as a super store.</p>

<p>And on the second measure, growth, being a chain is the only thing that helped at all. Size did
nothing for it: the largest format in the country grew {gr['Super Store']['mult']}x in twenty years.</p>

<p>Put it together and you can see the shape of the last two decades. The stores that went away were
small and independent — they had neither advantage. The large format had size, and used it to stay put
rather than to spread. What actually spread was the format that worked out how to be small and be a
chain at the same time, and it is the only thing in the data that is winning on both counts at once.</p>

<p>Tomorrow we look at a format that had both advantages and lost anyway. It is the fastest collapse in
the whole dataset, and it happened in the last four years.</p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>These are authorizations, not buildings.</strong> A small grocery at {sg['rate']}% has
overwhelmingly left the program; this source cannot tell you the storefront is empty. Day 1 worked
through that gap in detail. The super store figure is the one place the two nearly coincide, because for
the large chains the authorization list runs close to a store census.</p>
<p><strong>Ownership is inferred, not reported.</strong> It comes from patterns in store names, and it is
unknown for between {lo:.0f}% and {hi:.0f}% of each format's cohort. Rates are computed over the stores
that could be classified, and the unclassified share is published in the data file beside every one of
them.</p>
<p><strong>Being a chain is not sufficient, and this data cannot show why.</strong> The chain
small-grocery cell survives at {ow['Grocery (Small)']['chain']['rate']}%, no better than independents —
but it holds only {ow['Grocery (Small)']['chain']['n']} stores, far too few to carry a claim, which is
why nothing above is built on it. The likely reason is that "chain" here covers a three-store local
operator and a national retailer with twenty thousand locations alike, and only the second kind has the
scale that matters. This source cannot separate them.</p>
<p><strong>The cohort is one window.</strong> Stores first authorized in {d['cohort']}, followed to the
end of 2025. A different window would give different levels; the ordering is what this piece rests
on.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December. Code,
pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print("  ladder: " + " > ".join(f"{sv[f]['rate']}%" for f in L))
    print(f"  chain super store {ssc['rate']}% vs dollar store {dol['rate']}%")


if __name__ == "__main__":
    main()
