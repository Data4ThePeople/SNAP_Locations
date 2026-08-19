"""Render reports/post1.html from reports/data/post1.json.

Three sections, four figures, one per point:
  1. they grew enormously
  2. they kept their authorizations, unlike small grocers
  3. more of the country now has one and nothing else

Then a "so what" that answers the obvious question — why did they get to keep
SNAP? — and hands off to the gas station piece.

One correction is baked in here. It is tempting to say dollar stores kept their
authorizations because they got the 2016 stocking rule scaled back. They did not.
Section 765 of P.L. 115-31 (May 2017) did roll the rule back to pre-2014 variety
standards, but the record credits the convenience store industry: NACS led it,
Casey's General Stores testified for NACS, and USDA's own preamble says the
concern was that the threshold "would make most convenience stores ineligible."
No evidence points at dollar stores. What the data does support is simpler and
checkable — every dollar store in this file belongs to a chain, and small
grocers are 81% independent.
"""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post1.json"
OUT = ROOT / "reports" / "post1.html"



def main():
    d = json.loads(DATA.read_text())
    # Fail loudly rather than shipping a chart drawn from an unvalidated palette.
    palette.validate(6, "light", verbose=False)
    palette.validate(6, "dark", verbose=False)

    surv = sorted(d["survival"], key=lambda r: -r["rate"])
    z = d["dollar_only_zip"]
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")
    ctx, gap, cen = d["context"], d["survival_gap"], d["chain_census"]
    mn, sp, lap = d["metronome"], d["spike_2024"], d["lapse"]
    fl = d["dollar_flows"]
    # Active on 31 December 2025; the largest single format in the file.
    conv_2025 = 117_055
    stock = ctx["Dollar Store"]["stock"]
    yrs = ctx["Dollar Store"]["years"]
    growth = stock[-1] / stock[0]
    growth_pct = round(100 * (growth - 1))
    lap_sg = next(r for r in lap if r["format"] == "Grocery (Small)")
    # Measured in post1_dollar.py and asserted there, so the scale argument in
    # the closing section cannot drift from the data it rests on.
    mix = d["ownership_mix"]
    m_ds, m_sg, m_cv = (mix["Dollar Store"], mix["Grocery (Small)"],
                        mix["Convenience Store"])

    # 1. growth, in the company of the formats it overtook
    picks = ["Dollar Store", "Supermarket", "Grocery (Medium)", "Grocery (Small)",
             "Super Store"]
    s_ctx = [{"name": p.replace("Grocery ", "").strip("()").lower()
              if p != "Dollar Store" else "dollar stores",
              "values": ctx[p]["stock"], "slot": 2 if p == "Dollar Store" else 0}
             for p in picks if p in ctx]
    for i, s in enumerate(s_ctx):
        if s["slot"] == 0:
            s["slot"] = 3 + (i % 4)
    c_ctx = charts.line_chart(yrs, s_ctx, y_label="stores authorized on 31 December",
                              title="Dollar stores passed every grocery format")

    # 2. retention
    c_surv = charts.bar_chart(
        [{"label": r["format"], "value": 100 * r["rate"],
          "slot": 2 if r["format"] == "Dollar Store"
          else (1 if r["format"] == "Grocery (Small)" else 0)} for r in surv],
        suffix="%",
        title="Dollar stores stayed. Small grocers did not.",
        subtitle="share of the 2008-2012 cohort still authorized in 2025")

    cen_tbl = "".join(
        f"<tr><td>{c['brand']}</td><td>{c['authorized']:,}</td>"
        f"<td>{c['reported']:,}</td><td>{c['ratio']:.2f}</td></tr>" for c in cen)

    # 3. reliance
    c_z = charts.line_chart(
        [r["yr"] for r in z],
        [{"name": "ZIP codes", "values": [r["dollar_only"] for r in z], "slot": 2}],
        y_label="ZIP codes with a dollar store and no grocery",
        title="More places now have a dollar store and nothing else")

    html = f"""{HEAD}<title>Dollar stores cracked the code small grocers could not</title>
<style>{CSS}</style>
<main>
<h1>Dollar stores cracked the code small grocers could not</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · {d['headline']['dollar_2025']:,} dollar stores authorized at the end of 2025, against
{d['headline']['all_grocery_2025']:,} grocery stores of every size</p>

<div class="ledger">
  <div><b>{growth_pct:+}%</b><span>change in SNAP-authorized dollar stores since {yrs[0]}</span></div>
  <div><b>{100*ds['rate']:.0f}%</b><span>of dollar stores authorized in 2008–2012 are still
    authorized today</span></div>
  <div><b>{100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}%</b><span>of ZIP codes with a dollar
    store have no grocery store at all, up from
    {100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}% in {z[0]['yr']}</span></div>
</div>

<p>Yesterday's piece ended on a question. Small grocery is a small format that could not make the
numbers work. The dollar store is a small format too — same small box, narrow range, few staff. It
did the opposite.</p>

<h2>This time, an authorization is a store</h2>

<p>Yesterday we had to be careful: when a small grocer leaves the SNAP file, the records cannot say
whether it closed or just stopped taking EBT. Dollar stores are a different case. Nearly all of them
belong to a handful of public chains — Dollar General, Dollar Tree, Family Dollar — and those
companies tell their investors exactly how many stores they run. So set the SNAP authorization
counts at the end of 2025 against the companies' own reported store counts:</p>

<figure><table><thead><tr><th>Chain</th><th>SNAP-authorized</th><th>Reported stores</th><th>Ratio</th></tr>
</thead><tbody>{cen_tbl}</tbody></table>
<figcaption>SNAP authorizations at the end of 2025 against each company's most recently reported
store count, early 2025 to February 2026.</figcaption></figure>

<p>Essentially every Dollar General and Dollar Tree in the country takes SNAP. Because the two
counts line up, we can read store openings and closings for these chains straight out of the SNAP
file — something yesterday's data could not give us. Keep that in mind through everything that
follows: for dollar stores, authorization counts are store counts.</p>

<h2>They grew enormously</h2>

<p>Dollar stores went from {stock[0]:,} SNAP-authorized stores in {yrs[0]} to {stock[-1]:,} in
{yrs[-1]}. That is a <strong>{growth_pct:+}%</strong> change, while every grocery format either
shrank or stood still.</p>

<figure>{c_ctx}{charts.legend(s_ctx)}
<figcaption>Stores authorized on 31 December of each year, by format.</figcaption></figure>

<p>They are now the second most common kind of SNAP retailer in the country, behind only convenience
stores. There are {d['headline']['dollar_2025']:,} of them against
{d['headline']['all_grocery_2025']:,} grocery stores of every size combined.</p>

<h2>They kept their authorizations</h2>

<p>Growth is the easy part of the story. The harder question is what happened to the stores that were
already there. Take every retailer that joined SNAP between 2008 and 2012, and ask how many are still
in the program at the end of 2025.</p>

<figure>{c_surv}
<figcaption>Share of the 2008–2012 entry cohort still authorized at the end of 2025. Counts are
stores, not authorization spells, so a store that lapsed and returned is counted once.</figcaption>
</figure>

<p><strong>{100*ds['rate']:.0f}% of dollar stores are still authorized. Meanwhile, just
{100*sg['rate']:.1f}% of small grocers are.</strong> A dollar store from those years is <strong>{gap['multiple']}× more likely</strong>
to still be in the program.</p>

<p>And since an authorization here is a store, those stores are still open. That says something
about the economics. These are public companies, and they do close stores that stop working. In 2024 dollar store endings jumped from a few hundred a year to {fl['departed'][fl['years'].index(2024)]:,} — Dollar Tree shutting Family Dollar locations ({sp[0]['n']}) and 99 Cents Only liquidating ({sp[1]['n']}). So the survival rate is not a company failing to notice. When a listed retailer culls that hard the moment the numbers stop working, and still has {100*ds['rate']:.0f}% of a cohort trading thirteen years later, the fair read is that these stores pay.</p>

<h2>More of the country has one and nothing else</h2>

<p>Growth in total is not the same as growth where it matters. The sharper question is how often a dollar store is the <em>only</em> option nearby. So count the ZIP codes that have a dollar store and no grocery store of any size — no supermarket, no superstore, no large, medium or small grocer.</p>

<figure>{c_z}
<figcaption>ZIP codes with a SNAP-authorized dollar store and no supermarket, superstore, or grocery
store of any size.</figcaption></figure>

<p>In {z[0]['yr']} that described {z[0]['dollar_only']:,} ZIP codes. By {z[-1]['yr']} it described
<strong>{z[-1]['dollar_only']:,}</strong> — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of
every ZIP code that has a dollar store at all, up from
{100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}%. In one ZIP code in four, the dollar store is not
one option among several. It is the option.</p>

<h2>What it adds up to</h2>

<p>Dollar stores ended up on both sides of a line everyone else has to choose.</p>

<p>They are <strong>small where small pays</strong>: a box that makes money in a town of a few thousand people, where a supermarket cannot. And they are <strong>big where big pays</strong>: a chain that works out how to clear USDA's stocking bar once, then spreads the cost of doing it across twenty thousand stores.</p>

<p>Small grocers only ever get the first half. {m_sg['independent']:.0f}% of them are independent and {m_sg['chain']:.0f}% belong to a chain. Same small box, no big company behind it.</p>

<p>Put the two halves together and the growth stops being surprising. It is no wonder dollar stores have outgrown every grocery format in the country.</p>

<p>But hold on to the second half. Why is that bar low enough for a small box to clear? Partly because someone else fought to keep it there. The 2016 stocking rule would have raised it sharply. It was rolled back in May 2017 — by the <strong>convenience store</strong> industry, lobbying hard for its members. Dollar stores never led that campaign. They just got the benefit.</p>

<p>Which is where we go next: the country's <strong>{conv_2025:,} convenience stores</strong>, the
single largest group in this data, and how they have thrived without anything like the chain
concentration dollar stores enjoy. Only {m_cv['chain']:.0f}% of them belong to a chain at all.</p>

<p><strong>Tomorrow: the convenience store.</strong></p>

<div class="caveat">
<h3>Limits</h3>
<p>Nothing here measures floor space, sales, or what is on the shelves. A dollar store and a
supermarket each count as one record.</p>
<p><strong>The chain-store check is what licenses closure language, and only for these chains.</strong>
For an independent store an ended authorization may mean the shop closed or may mean it stopped taking
EBT. {100*lap_sg['rate']:.1f}% of small grocers lost their authorization and later regained it, median
gap {lap_sg['median_gap_days']} days — those were open the whole time.</p>
<p>The 2024 closures above were both announced by the companies and widely reported at the time, which is a useful check on the file: when something real happens in retail, these records catch it.</p>
<p>Store-level SNAP spending is not public. A 2019 Supreme Court case put those figures under a FOIA
exemption, so we can see where authorized stores are but never how much any one of them takes in.</p>
<p>Company store counts are from early 2025 to early 2026 and are compared against authorizations at
the end of 2025, so the ratios are close, not exact.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, covering retailers authorized at
any point in the window. Analysis uses 656,868 stores with usable coordinates. A store counts as
active in a year if an authorization covered 31 December. Company store counts from Dollar General and
Dollar Tree investor releases; Family Dollar via trade press. The 2017 rollback is Section 765 of
P.L. 115-31. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  growth {growth:.2f}x, retention {100*ds['rate']:.0f}% vs {100*sg['rate']:.1f}%")
    print(f"  dollar-only ZIPs {z[0]['dollar_only']:,} -> {z[-1]['dollar_only']:,}")


if __name__ == "__main__":
    main()
