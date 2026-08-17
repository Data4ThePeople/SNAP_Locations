"""Render reports/post1.html from reports/data/post1.json."""
import json

from analysis import charts, palette
from config import ROOT

DATA = ROOT / "reports" / "data" / "post1.json"
OUT = ROOT / "reports" / "post1.html"

CSS = """
/* Subject is a federal authorization ledger, so the identity is serif prose
   against monospaced record-keeping: every figure, axis tick and label is mono
   and tabular. Neutrals are cooled toward the blue accent rather than left as
   default grey, and there is no sans-serif anywhere. */
:root {
  color-scheme: light;
  --paper:    #f5f7f9;
  --ink:      #16191c;
  --ink-mid:  #4d545c;
  --ink-soft: #878e96;
  --rule:     #dee4e9;
  --band:     #ecf0f3;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;
  --s5: #e87ba4; --s6: #008300; --s7: #4a3aa7; --s8: #e34948;
  --grid: var(--rule); --surface: var(--paper);
  --ink-1: var(--ink); --ink-2: var(--ink-mid); --ink-3: var(--ink-soft);
  --serif: "Charter", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, "Cascadia Mono", "Roboto Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --paper: #14171a; --ink: #eef1f4; --ink-mid: #b3bac1; --ink-soft: #7d858d;
    --rule: #262b30; --band: #1b1f23;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
    --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --paper: #14171a; --ink: #eef1f4; --ink-mid: #b3bac1; --ink-soft: #7d858d;
  --rule: #262b30; --band: #1b1f23;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
  --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 17px/1.66 var(--serif);
  -webkit-font-smoothing: antialiased;
}
main {
  max-width: 880px; margin: 0 auto; padding: 64px 24px 110px;
  display: grid; gap: 0;
}
/* Prose keeps a readable measure; figures use the full field. */
h1, h2, p, table, .caveat, .sub, footer, .legend { max-width: 62ch; }

h1 {
  font: 400 clamp(30px, 4.4vw, 42px)/1.14 var(--serif);
  letter-spacing: -.015em; margin: 0 0 14px; text-wrap: balance;
}
.sub {
  font: 400 12px/1.6 var(--mono); color: var(--ink-soft);
  margin: 0 0 40px; letter-spacing: .01em;
}
h2 {
  font: 400 25px/1.25 var(--serif); letter-spacing: -.01em;
  margin: 60px 0 14px; padding-top: 22px; border-top: 1px solid var(--rule);
  text-wrap: balance;
}
p { margin: 0 0 20px; }
em { font-style: italic; }
strong { font-weight: 600; }

/* Ledger band: hairline rules and mono figures, in place of rounded cards. */
.ledger {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0 30px; margin: 34px 0 40px;
  border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule);
}
.ledger div { padding: 16px 0 15px; }
.ledger div + div { border-left: 1px solid var(--rule); padding-left: 24px; }
.ledger b {
  display: block; font: 400 34px/1.05 var(--mono);
  font-variant-numeric: tabular-nums; letter-spacing: -.03em; color: var(--s1);
}
.ledger span {
  display: block; margin-top: 7px;
  font: 400 11.5px/1.45 var(--mono); color: var(--ink-soft);
}

figure { margin: 30px 0 34px; }
figcaption {
  font: 400 11.5px/1.6 var(--mono); color: var(--ink-soft);
  margin-top: 12px; max-width: 74ch;
}
.chart { width: 100%; height: auto; display: block; overflow: visible; }
.tick, .note, .axis-title { font: 400 10.5px var(--mono); fill: var(--ink-soft); }
.dlabel, .bvalue { font: 400 11.5px var(--mono); fill: var(--ink-mid); }
.blabel { font: 400 11.5px var(--mono); fill: var(--ink-mid); }
.bvalue { font-variant-numeric: tabular-nums; }

.legend {
  display: flex; flex-wrap: wrap; gap: 6px 20px; margin: 12px 0 0;
  font: 400 11.5px var(--mono); color: var(--ink-mid);
}
.lg { display: inline-flex; align-items: center; gap: 7px; }
.lg i { width: 11px; height: 3px; flex: none; }

table {
  width: 100%; border-collapse: collapse; margin: 24px 0;
  font: 400 13px var(--mono); font-variant-numeric: tabular-nums;
}
th, td { text-align: right; padding: 9px 12px; border-bottom: 1px solid var(--rule); }
th:first-child, td:first-child { text-align: left; }
th {
  font-weight: 400; color: var(--ink-soft); font-size: 10.5px;
  text-transform: uppercase; letter-spacing: .08em;
  border-bottom: 1px solid var(--ink);
}

.caveat { margin: 42px 0 0; padding: 24px 0 0; border-top: 1px solid var(--rule); }
.caveat h3 {
  font: 400 10.5px var(--mono); text-transform: uppercase; letter-spacing: .1em;
  color: var(--ink-soft); margin: 0 0 12px;
}
.caveat p { font-size: 15.5px; color: var(--ink-mid); }
.caveat p:last-child { margin-bottom: 0; }

footer {
  margin-top: 52px; padding-top: 20px; border-top: 1px solid var(--rule);
  font: 400 11.5px/1.7 var(--mono); color: var(--ink-soft);
}
footer a { color: var(--s1); text-decoration: none; border-bottom: 1px solid var(--rule); }
footer a:hover { border-bottom-color: var(--s1); }
footer a:focus-visible { outline: 2px solid var(--s1); outline-offset: 2px; }
"""


def main():
    d = json.loads(DATA.read_text())
    # Fail loudly rather than shipping a chart drawn from an unvalidated palette.
    palette.validate(6, "light", verbose=False)
    palette.validate(6, "dark", verbose=False)

    surv = sorted(d["survival"], key=lambda r: -r["rate"])
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")

    fl = d["dollar_flows"]
    yrs = fl["years"]

    # --- chart 1: survival ---------------------------------------------------
    surv_rows = [{"label": r["format"], "value": round(100 * r["rate"], 1),
                  "note": f"{r['still_open']:,} of {r['cohort']:,}",
                  "slot": 1 if r["format"] == "Dollar Store" else
                          (2 if r["format"] == "Grocery (Small)" else 6)}
                 for r in surv]
    c_surv = charts.bar_chart(surv_rows, suffix="%", note_key="note")

    # --- chart 2: stock by format -------------------------------------------
    ctx = d["context"]
    picks = ["Dollar Store", "Supermarket", "Super Store", "Grocery (Small)",
             "Grocery (Medium)", "Grocery (Large)"]
    s_ctx = [{"name": f, "values": ctx[f]["stock"], "slot": i + 1}
             for i, f in enumerate(picks)]
    c_ctx = charts.line_chart(ctx["Dollar Store"]["years"], s_ctx, y_label="active stores")

    # --- chart 3: openings vs closings --------------------------------------
    s_flow = [{"name": "opened", "values": fl["new"], "slot": 1},
              {"name": "closed", "values": fl["departed"], "slot": 2}]
    c_flow = charts.line_chart(yrs, s_flow, y_label="stores per year",
                               annotate=[{"year": 2024, "text": "2024"}])

    # --- chart 4: brands -----------------------------------------------------
    bpick = ["Dollar General", "Dollar Tree", "Family Dollar", "99 Cents Only"]
    s_br = [{"name": b, "values": d["brands"][b]["stock"], "slot": i + 1}
            for i, b in enumerate(bpick) if b in d["brands"]]
    c_br = charts.line_chart(d["brands"]["Dollar General"]["years"], s_br,
                             y_label="active stores")

    # --- chart 5: dollar-only ZIPs ------------------------------------------
    z = d["dollar_only_zip"]
    s_z = [{"name": "ZIPs, dollar store but no grocery",
            "values": [r["dollar_only"] for r in z], "slot": 2}]
    c_z = charts.line_chart([r["yr"] for r in z], s_z, y_label="ZIP codes")

    vol = {v["format"]: v for v in d["volatility"]}
    churn_rows = [{"label": f, "value": round(vol[f]["churn"], 2),
                   "slot": 1 if f == "Dollar Store" else 6}
                  for f in ["Dollar Store", "Super Store", "Supermarket",
                            "Combination Grocery/Other", "Grocery (Medium)",
                            "Convenience Store", "Grocery (Small)"] if f in vol]
    c_churn = charts.bar_chart(churn_rows, suffix="x")

    spike = d["spike_2024"][:4]
    spike_tbl = "".join(f"<tr><td>{s['brand']}</td><td>{s['n']:,}</td></tr>" for s in spike)

    html = f"""<title>The dollar store did not out-grow the grocery store. It out-lived it.</title>
<style>{CSS}</style>
<main>
<h1>The dollar store did not out-grow the grocery store. It out-lived it.</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service historical
authorization records · {d['headline']['dollar_2025']:,} dollar stores accepted SNAP at the end of 2025</p>

<div class="ledger">
  <div><b>{100*ds['rate']:.0f}%</b><span>of dollar stores authorized 2008–2012 are still authorized today</span></div>
  <div><b>{100*sg['rate']:.1f}%</b><span>of small grocers from the same cohort are</span></div>
  <div><b>{d['dollar_only_zip'][-1]['dollar_only']:,}</b><span>ZIP codes now have a dollar store and no grocery of any size</span></div>
</div>

<p>Everyone knows dollar stores grew. The interesting part is <em>how</em>. Take every store that
first entered the SNAP program between 2008 and 2012, and ask how many are still in it at the end
of 2025.</p>

<figure>{c_surv}
<figcaption>Share of the 2008–2012 entry cohort still authorized at the end of 2025. Counts are
stores, not authorization spells, so a store that lapsed and returned is counted once.</figcaption></figure>

<p>A dollar store from that cohort is <strong>{d['survival_gap']['multiple']}× more likely</strong> to
still be operating than a small grocer from the same years. Small grocery is the extreme case:
{sg['still_open']:,} survivors from {sg['cohort']:,} entrants. Ninety-five percent are gone.</p>

<p>This is not the shape people usually assume. The story is generally told as dollar stores opening
aggressively, and they do open steadily — but on that measure they are not even unusual. Supermarket
openings are steadier year to year than dollar store openings. What is unusual is that dollar stores
essentially never close.</p>

<figure>{c_churn}
<figcaption>Closures between 2009 and 2023 as a multiple of average active stock. Small grocery
turned over more than three times its entire population; dollar stores shed about one store in
seven.</figcaption></figure>

<h2>Fifteen years of one direction</h2>
<p>The result compounds. Roughly {d['metronome']['mean_new']:,.0f} new dollar store authorizations a
year against about {d['metronome']['mean_closed']:,.0f} closures produces a line that only goes up.</p>

<figure>{c_flow}{charts.legend(s_flow)}
<figcaption>Dollar store openings and closures per year. The two lines cross for the first time in
2024.</figcaption></figure>

<p>Set against the grocery formats, the crossing is hard to miss. Dollar stores passed every
individual grocery format years ago and are now the second most common kind of SNAP retailer in the
country, behind convenience stores only.</p>

<figure>{c_ctx}{charts.legend(s_ctx)}
<figcaption>Active SNAP authorizations by store format. Convenience stores are omitted for scale —
there are {d['context']['Dollar Store']['stock'][-1]:,} dollar stores against roughly 119,000
convenience stores.</figcaption></figure>

<h2>2024 is the first break in the pattern</h2>
<p>Closures jumped from a few hundred a year to <strong>{fl['departed'][yrs.index(2024)]:,}</strong>
in 2024 — and this is one place the data lines up with events that made the news.</p>

<table><thead><tr><th>Brand</th><th>Stores leaving SNAP in 2024</th></tr></thead>
<tbody>{spike_tbl}</tbody></table>

<p>Dollar Tree spent 2024 closing Family Dollar locations, and 99 Cents Only liquidated entirely
that spring. Both show up here as authorization endings, which is a useful check: when something
verifiable happens in the retail world, this dataset sees it.</p>

<figure>{c_br}{charts.legend(s_br)}
<figcaption>Active SNAP authorizations by dollar-store brand. 99 Cents Only goes to zero in
2024.</figcaption></figure>

<h2>Where this actually matters</h2>
<p>Growth in the aggregate is not the same as growth where it counts. The sharper question is how
often a dollar store is the <em>only</em> thing there.</p>

<figure>{c_z}
<figcaption>ZIP codes containing at least one SNAP-authorized dollar store and no supermarket,
superstore, or grocery store of any size.</figcaption></figure>

<p>In 2008 that described {z[0]['dollar_only']:,} ZIP codes. By 2024 it described
<strong>{z[-1]['dollar_only']:,}</strong> — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of every
ZIP code that has a dollar store at all. Nationally there are now
{d['headline']['dollar_2025']:,} dollar stores against {d['headline']['all_grocery_2025']:,}
grocery stores of every size combined.</p>

<div class="caveat">
<h3>What this data can and cannot say</h3>
<p>These are <strong>SNAP authorizations</strong>, not stores. A retailer that closes and one that
merely stops accepting SNAP look identical here, so "left the program" is the honest reading of
every exit.</p>
<p>Nothing here measures floor space, sales, or what is actually on the shelves. A dollar store and
a supermarket count as one record each. USDA's own classification is by stocking breadth, and the
2016 stocking-standards rule changed that bar mid-series — which matters more for grocery formats
than for dollar stores.</p>
<p>Store-level SNAP redemption dollars are not public: <em>Food Marketing Institute v. Argus
Leader</em> (2019) closed that under FOIA Exemption 4. We can see where retailers are, never how much
each transacts.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025 (retailers authorized at any point
in the window). Analysis covers 611,164 stores with usable coordinates. A store counts as active in a
year if its authorization covered 31 December. Code and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)/1000:.0f} KB)")
    print(f"  survival gap: {d['survival_gap']['multiple']}x")
    print(f"  dollar-only ZIPs: {z[0]['dollar_only']:,} -> {z[-1]['dollar_only']:,}")


if __name__ == "__main__":
    main()
