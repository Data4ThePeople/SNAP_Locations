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

    c_growth = charts.bar_chart(
        [{"label": SHORT[f], "value": gr[f]["mult"],
          "slot": 2 if f == "Dollar Store" else (1 if f == "Super Store" else 0)}
         for f in sorted(L + B, key=lambda x: -gr[x]["mult"])], suffix="x",
        title="The most durable format is also the slowest growing",
        subtitle="SNAP-authorized stores in 2025 as a multiple of 2006")

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

<h2>The large format wins at staying and loses at spreading</h2>

<p>One more thing falls out of the same table, and it is the opposite of what the first two rules
suggest.</p>

<figure>{c_growth}
<figcaption>Change in the number of SNAP-authorized stores between 2006 and 2025, by store
type.</figcaption></figure>

<p>The super store is the most durable format in the data and close to the slowest growing:
<strong>{gr['Super Store']['mult']}x</strong> since 2006, against
<strong>{gr['Dollar Store']['mult']}x</strong> for dollar stores and {gr['Convenience Store']['mult']}x
for convenience stores. Supermarkets barely moved at {gr['Supermarket']['mult']}x.</p>

<p>Durability and growth are not the same trait. The formats that lasted best are not the ones that
spread. What spread was the format that found a way to be small and be a chain at the same time.</p>

<h2>What it adds up to</h2>

<p>Two rules, and they are worth stating plainly because between them they cover almost everything in
this series so far.</p>

<p><strong>Rule one: a bigger store was likelier to keep its SNAP authorization.</strong> That held for
every independent store in the data, right down the size order.</p>

<p><strong>Rule two: rule one does not apply to chains.</strong> A dollar store the size of a corner shop
held its authorization as reliably as a super store.</p>

<p>Put the two together and you can see the shape of the last twenty years. The stores that went away
were small and independent — they had neither advantage. The stores that grew were small and chained —
they had the one that could be bought. And the large format, which had both, mostly stayed where it
was.</p>

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
