"""Render reports/post3.html from reports/data/post3.json.

Day 4, rebuilt around geography: the metro/nonmetro divergence for the big
formats, the million-plus metros' share of the growth, and the dollar store as
the one format indifferent to county size. Mirrors export_post3.py; see that
module's docstring. The earlier size-ladder and ownership analysis still lives
in post3.json if it is ever wanted back.
"""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post3.json"
OUT = ROOT / "reports" / "post3.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(7, "light", verbose=False)
    palette.validate(7, "dark", verbose=False)

    ru = d["rucc"]
    F = ru["formats"]
    yrs = list(range(2006, 2026))
    pop_nm_m = ru["pop_nonmetro"] / 1e6
    km = ru["kmart_2020"]

    def seg(fmt, which):
        return [F[fmt][which][str(y)] for y in yrs]

    def pchg(fmt, which):
        s = F[fmt][which]
        return 100 * (s["2025"] / s["2006"] - 1)

    def code_chg(fmt, k):
        c = F[fmt]["by_code"][str(k)]
        return 100 * (c["2025"] / c["2006"] - 1)

    def share_1m(fmt):
        net = {k: F[fmt]["by_code"][str(k)]["2025"] - F[fmt]["by_code"][str(k)]["2006"]
               for k in range(1, 10)}
        return 100 * net[1] / sum(net.values())

    idx = lambda vals: [round(100 * v / vals[0], 1) for v in vals]

    s_split = [
        {"name": "super stores — metro", "values": idx(seg("Super Store", "metro")), "slot": 1},
        {"name": "supermarkets — metro", "values": idx(seg("Supermarket", "metro")), "slot": 3},
        {"name": "supermarkets — nonmetro", "values": idx(seg("Supermarket", "nonmetro")), "slot": 5},
        {"name": "super stores — nonmetro", "values": idx(seg("Super Store", "nonmetro")), "slot": 2}]
    c_split = charts.line_chart(
        yrs, s_split, y_zero=False, value_labels=False,
        y_label="authorized stores, indexed to 2006 = 100",
        title="Metro America gained big stores. Nonmetro America lost them.")

    c_share = charts.bar_chart(
        [{"label": "super stores", "value": share_1m("Super Store"), "slot": 1},
         {"label": "supermarkets", "value": share_1m("Supermarket"), "slot": 3}],
        suffix="%",
        title="The million-person metros took almost all of the growth",
        subtitle="share of net 2006-2025 change in metro-1M+ counties")

    s_grad = [
        {"name": "dollar stores", "values": [round(code_chg("Dollar Store", k), 1) for k in range(1, 10)], "slot": 2},
        {"name": "convenience", "values": [round(code_chg("Convenience Store", k), 1) for k in range(1, 10)], "slot": 4},
        {"name": "super stores", "values": [round(code_chg("Super Store", k), 1) for k in range(1, 10)], "slot": 1},
        {"name": "supermarkets", "values": [round(code_chg("Supermarket", k), 1) for k in range(1, 10)], "slot": 3},
        {"name": "small grocery", "values": [round(code_chg("Grocery (Small)", k), 1) for k in range(1, 10)], "slot": 7}]
    c_grad = charts.line_chart(
        list(range(1, 10)), s_grad, y_zero=False, value_labels=False,
        y_label="% change in authorized stores, 2006-2025",
        title="Dollar stores grow everywhere. Everything else grows where people are.")

    leg_split = charts.legend(s_split)
    leg_grad = charts.legend(s_grad)

    html = f"""{HEAD}<title>Super stores for some, dollar stores for the rest</title>
<style>{CSS}</style>
<main>
<h1>Super stores for some, dollar stores for the rest</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025, joined to USDA's Rural-Urban Continuum Codes ·
{pop_nm_m:.1f} million Americans live in the non-metropolitan counties this piece is about</p>

<div class="ledger">
  <div><b>{pchg('Super Store', 'metro'):+.0f}%</b><span>change in metro super stores since 2006; in
    nonmetro counties they fell {abs(pchg('Super Store', 'nonmetro')):.0f}%</span></div>
  <div><b>{pop_nm_m:.1f}M</b><span>Americans live in nonmetro counties</span></div>
  <div><b>+{pchg('Dollar Store', 'nonmetro'):.0f}%</b><span>nonmetro dollar store growth — the only
    format still growing on every rung of the rural-urban ladder</span></div>
</div>

<p><em>As in the earlier pieces: anytime we refer to "growth" in this post, it is growth in
SNAP-authorized stores, not growth in store counts. See the Limits section for more on this.</em></p>

<p>My analysis for today's post made me reflect on my own life. I'm specifically thinking about the
plethora of grocery options I have just minutes from my house in suburban Dayton, Ohio. There are a
Target, a Costco, and a Kroger down the street from me. Drive another few minutes and you'll pass a
Walmart and an Aldi. Another five minutes and there's a Trader Joe's. My weekly grocery trips
involve some ever-changing combination of visits to these stores to get the products my family
likes at the best price. There weren't always this many options. But large-format grocers have flocked to the
metropolitan area in which I live, providing an overabundance of fully stocked grocery
stores for suburban Daytonians.</p>

<p>Most of you reading this can probably relate. But not everyone. If you are one of the
<strong>{pop_nm_m:.1f} million Americans</strong> living in a non-metropolitan county, how you shop
for groceries is likely very different — rather than having more options as time passes, you may
have fewer.</p>

<h2>The two grocery Americas</h2>

<p>How do we know that? The data, of course. The chart below shows the change in the two largest
store formats — super stores and supermarkets — in metropolitan counties against non-metropolitan
counties, indexed to 100 in 2006.</p>

<figure>{c_split}{leg_split}
<figcaption>Authorized super stores and supermarkets, indexed to 100 in 2006, in metropolitan
against non-metropolitan counties (USDA Rural-Urban Continuum Codes; metro is codes
1-3).</figcaption></figure>

<p>In metro counties, super stores are up {pchg('Super Store', 'metro'):.0f}% and supermarkets
{pchg('Supermarket', 'metro'):.0f}%. In nonmetro counties both lines point the other way: down
{abs(pchg('Super Store', 'nonmetro')):.0f}% and {abs(pchg('Supermarket', 'nonmetro')):.0f}%. That
sharp step down in 2020 is the Kmart liquidation — {km['kmart']} nonmetro Kmart supercenters left
the program in a single year.</p>

<p>Reality is even more skewed than that chart lets on. It turns out that nearly three-quarters of
all net super store growth — and {share_1m('Supermarket'):.0f}% of net supermarket growth — happened
in the million-plus metros alone.</p>

<figure>{c_share}
<figcaption>Share of each format's net change in authorized stores, 2006-2025, that landed in
counties belonging to metro areas of a million people or more.</figcaption></figure>

<p>The more we analyze and write, the more we see common threads emerging across this country.
Today's finding is a complement to our deep dive into the structural decline of the labor force — an
extensive piece that tracked the decline in the labor force (and therefore, the economic engine) of
nonmetro counties and the simultaneous surge in the labor forces of large metro counties and their
surrounding suburbs (Austin, Nashville, Salt Lake City). When a county is in structural decline, it
makes sense that it would lose the larger-format grocery stores that need volume to make the
economics work. Two findings from two completely different databases, connected by Ockham's
razor.</p>

<h2>What grows where the big stores don't</h2>

<p>And so, what store formats are growing in nonmetro counties? You guessed it: dollar stores and
convenience stores.</p>

<p>The chart below needs one piece of setup. USDA's Rural-Urban Continuum Codes sort every county
in America onto a nine-rung ladder: code 1 is a county in a metro area of a million people or more,
codes 2 and 3 are smaller metros, and codes 4 through 9 step down through ever smaller and more
remote nonmetro counties, ending at code 9 — fully rural counties not adjacent to any metro area.
The chart runs that ladder left to right and shows each format's growth on every rung. The dollar
store is the only format whose growth was indifferent to the size of the county — the smallest
counties grew at nearly the same pace as the largest ones.</p>

<figure>{c_grad}{leg_grad}
<figcaption>Percent change in authorized stores, 2006 to 2025, by Rural-Urban Continuum Code. Code 1
is counties in metro areas of a million or more; code 9 is fully rural counties not adjacent to any
metro area.</figcaption></figure>

<p>Every other line slopes downhill as the counties get smaller. Convenience stores grew
{code_chg('Convenience Store', 1):.0f}% in the biggest metros but only
{code_chg('Convenience Store', 9):.0f}% in fully rural counties. The big formats flip negative the
moment you leave metro America. Small grocery falls everywhere — steepest at the two extremes, the
big-city bodega and the only-store-in-town. The dollar store's line barely slopes at all.</p>

<p>You are free to have your own views on these different store formats. But the data can help us
remove our views from our own lived experience and try to form them from how others live. What if I
lived in a small county, getting smaller by the day as its labor force shrank through aging, a
declining birth rate, and out-migration to the larger metro areas for better work? Maybe I had one grocery store years ago.
Maybe now it's gone. Maybe I can't get everything I would like to eat at a dollar store. But
calories are better than no calories. And so, I am grateful. The alternative is a long drive,
spending gas money I may not have — especially now, thanks to our self-inflicted fuel crisis.</p>

<h2>The questions this leaves</h2>

<p>Where does this gravitational pull lead? Is it really a good strategy to let so much American
land become uninhabitable over time as it loses its workers and the stores that rely on them to
make their economics work? Should we really expect so many Americans to live off what they can buy
at a dollar store? What right do any of us who don't have to live this way have to criticize the
physical and mental health of those who do? And how can we ever expect the cost of health care to
decline — Medicaid and all the rest — if we can't provide people with access to the healthy foods
that USDA's economists blindly assume they can buy?</p>

<p>Those are just a few of the questions on my mind after studying this data. Feel free to add
yours.</p>

<p><strong>Tomorrow: the mirror image of the dollar store — the one format shrinking everywhere,
even where the people are.</strong></p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>Growth here means authorized stores.</strong> For super stores, supermarkets and dollar
stores the distinction is small — those chains' authorization counts track their reported store
counts almost exactly (see Day 2). For convenience stores a rising count can also mean wider EBT
take-up among stores that already existed, so read its gradient as the shape, not the level.</p>
<p><strong>Counties are classified by their current Rural-Urban Continuum Code</strong> (the 2023
vintage; Connecticut keeps its 2013 county codes because the 2023 file switched to planning
regions). A county keeps one code across the whole window, so within-county comparisons are
consistent — but "metro" means metro as defined today. 99.7% of active stores matched a coded
county; the remainder sit in territories and a few renamed county-equivalents. County populations
are the 2020 census.</p>
<p><strong>A county is a coarse lens.</strong> A metro county contains poor neighborhoods far from
any supermarket, and a rural county can have a town center with three grocers. The RUCC split
measures the county's relationship to a metro area, not any single household's drive to a
store.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. USDA ERS Rural-Urban Continuum
Codes, 2023 (Connecticut: 2013), with 2020 census county populations. Analysis uses 656,868 stores
with usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>
"""
    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
