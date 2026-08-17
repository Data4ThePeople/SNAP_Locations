"""Render reports/post1.html from reports/data/post1.json."""
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
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")

    fl = d["dollar_flows"]
    yrs = fl["years"]
    g_rate = 100 * next(r for r in d["lapse"]
                        if r["format"] == "Grocery (Small)")["rate"]

    # --- chart 1: survival ---------------------------------------------------
    surv_rows = [{"label": r["format"], "value": round(100 * r["rate"], 1),
                  "note": f"{r['still_open']:,} of {r['cohort']:,}",
                  "slot": 1 if r["format"] == "Dollar Store" else
                          (2 if r["format"] == "Grocery (Small)" else 0)}
                 for r in surv]
    c_surv = charts.bar_chart(surv_rows, suffix="%", note_key="note",
        title="Dollar stores stayed. Small grocers did not.",
        subtitle="share of the 2008-2012 cohort still authorized in 2025")

    # --- chart 2: stock by format -------------------------------------------
    ctx = d["context"]
    picks = ["Dollar Store", "Supermarket", "Super Store", "Grocery (Small)",
             "Grocery (Medium)", "Grocery (Large)"]
    s_ctx = [{"name": f, "values": ctx[f]["stock"], "slot": i + 1}
             for i, f in enumerate(picks)]
    c_ctx = charts.line_chart(ctx["Dollar Store"]["years"], s_ctx, y_label="active stores",
        title="Dollar stores passed every grocery format",
        subtitle="stores authorized on 31 December")

    # --- chart 3: openings vs closings --------------------------------------
    s_flow = [{"name": "opened", "values": fl["new"], "slot": 1},
              {"name": "closed", "values": fl["departed"], "slot": 2}]
    c_flow = charts.line_chart(yrs, s_flow, y_label="stores per year",
                               annotate=[{"year": 2024, "text": "2024"}],
        title="Openings ran far ahead of endings until 2024",
        subtitle="dollar store authorizations per year")

    # --- chart 4: brands -----------------------------------------------------
    bpick = ["Dollar General", "Dollar Tree", "Family Dollar", "99 Cents Only"]
    s_br = [{"name": b, "values": d["brands"][b]["stock"], "slot": i + 1}
            for i, b in enumerate(bpick) if b in d["brands"]]
    c_br = charts.line_chart(d["brands"]["Dollar General"]["years"], s_br,
                             y_label="active stores",
        title="99 Cents Only reaches zero in 2024",
        subtitle="stores authorized on 31 December, by brand")

    # --- chart 5: dollar-only ZIPs ------------------------------------------
    z = d["dollar_only_zip"]
    s_z = [{"name": "ZIPs, dollar store but no grocery",
            "values": [r["dollar_only"] for r in z], "slot": 2}]
    c_z = charts.line_chart([r["yr"] for r in z], s_z, y_label="ZIP codes",
        title="More ZIP codes have a dollar store and no grocery",
        subtitle="ZIP codes with a dollar store and no grocery of any size")

    vol = {v["format"]: v for v in d["volatility"]}
    churn_rows = [{"label": f, "value": round(vol[f]["churn"], 2),
                   "slot": 1 if f == "Dollar Store" else 0}
                  for f in ["Dollar Store", "Super Store", "Supermarket",
                            "Combination Grocery/Other", "Grocery (Medium)",
                            "Convenience Store", "Grocery (Small)"] if f in vol]
    c_churn = charts.bar_chart(churn_rows, suffix="x",
        title="Small grocery churned. Dollar stores barely did.",
        subtitle="authorizations ending 2009-2023, as a multiple of average stock")

    spike = d["spike_2024"][:4]
    spike_tbl = "".join(f"<tr><td>{s['brand']}</td><td>{s['n']:,}</td></tr>" for s in spike)

    lap = {r["format"]: r for r in d["lapse"]}
    lap_rows = [{"label": f, "value": round(100 * lap[f]["rate"], 1),
                 "slot": 1 if f == "Dollar Store" else 0}
                for f in ["Grocery (Medium)", "Grocery (Large)", "Convenience Store",
                          "Grocery (Small)", "Supermarket", "Super Store", "Dollar Store"]
                if f in lap]
    c_lap = charts.bar_chart(lap_rows, suffix="%",
        title="Some stores drop out, then come back",
        subtitle="share that lost authorization and later regained it")
    cen = d["chain_census"]
    cen_tbl = "".join(
        f"<tr><td>{c['brand']}</td><td>{c['authorized']:,}</td>"
        f"<td>{c['reported']:,}</td><td>{c['ratio']:.2f}</td></tr>" for c in cen)

    html = f"""{HEAD}<title>Dollar stores almost never leave SNAP. Small grocers almost always do.</title>
<style>{CSS}</style>
<main>
<h1>Dollar stores almost never leave SNAP. Small grocers almost always do.</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · {d['headline']['dollar_2025']:,} dollar stores were authorized at the end of 2025</p>

<div class="ledger">
  <div><b>{100*ds['rate']:.0f}%</b><span>of dollar stores authorized 2008–2012 are still authorized today</span></div>
  <div><b>{100*sg['rate']:.1f}%</b><span>of small grocers from the same cohort still are</span></div>
  <div><b>{d['dollar_only_zip'][-1]['dollar_only']:,}</b><span>ZIP codes have a dollar store and no grocery of any size</span></div>
</div>

<p>Everyone knows dollar stores grew. The sharper question is what happened to the stores that were already there. So take every retailer that joined SNAP between 2008 and 2012. Then ask how many are still in the program at the end of 2025. Here is that count, by format:</p>

<figure>{c_surv}
<figcaption>Share of the 2008–2012 entry cohort still authorized at the end of 2025. Counts are
stores, not authorization spells, so a store that lapsed and returned is counted once.</figcaption></figure>

<p>Small grocery is the extreme: {sg['still_open']:,} of {sg['cohort']:,} are still in the program.
A dollar store from those same years is <strong>{d['survival_gap']['multiple']}× more likely</strong>
to still be authorized.</p>

<h2>What an ended authorization actually means</h2>

<p>Before calling that a survival rate, be exact about what this data records. It tracks <em>authorizations</em>, not storefronts. When a record ends, the store might have closed. Or it might still be open and just no longer take EBT. Those are very different claims. The raw data cannot tell them apart.</p>

<p>Two checks narrow it. They point in opposite directions for chains and for independents.</p>

<p><strong>For the dollar chains, authorization is effectively a store census.</strong> Compare the
number of SNAP-authorized stores per brand against the number of stores each company reports
operating:</p>

<table><thead><tr><th>Brand</th><th>SNAP-authorized, 2025</th><th>Company-reported</th><th>Ratio</th></tr></thead>
<tbody>{cen_tbl}</tbody></table>

<p>Essentially every Dollar General and Dollar Tree in the country accepts SNAP. So for these
retailers the authorization record really is a store count, and an ending really does mean a closed
store. That is what licenses the closure language in the rest of this piece — but only for them.</p>

<p><strong>For independents, the opposite caution applies.</strong> Some stores drop out of the
program and come back, which proves they were open the whole time. Those cases are visible because
the store reappears:</p>

<figure>{c_lap}
<figcaption>Share of each format's stores that lost authorization and later regained it — direct
evidence of stores operating while unauthorized. Median gaps run from 9 days for superstores to 85
for convenience stores.</figcaption></figure>

<p>A small grocer is <strong>{d['lapse_gap']['multiple']}× more likely</strong> than a dollar store to
have dropped out and returned. And that {100*g_rate:.0f}% is only a floor: it counts stores that came
back. Any store that left the program and stayed open is invisible here.</p>

<p>So the honest reading of the headline chart is that it measures <em>program retention</em>, not
survival. For dollar stores those are nearly the same thing. For small grocers they are not, and the
gap between them is unknown — the resolution requires business-registry data rather than SNAP records,
which is where this series goes next.</p>

<h2>The pattern that produces the gap</h2>
<p>The story is usually told as dollar stores opening fast. They do open steadily. But on that measure they are not unusual at all. Supermarket openings actually vary less from year to year. What sets dollar stores apart is the other side of the ledger. This is how many stores each format shed:</p>

<figure>{c_churn}
<figcaption>Authorizations ending between 2009 and 2023, as a multiple of average active stock. Small
grocery cycled through more than three times its own population; dollar stores shed about one store in
seven.</figcaption></figure>

<p>About {d['metronome']['mean_new']:,.0f} dollar stores joined each year. Only about {d['metronome']['mean_closed']:,.0f} left. A gap that wide produces a line that goes one way:</p>

<figure>{c_flow}{charts.legend(s_flow)}
<figcaption>Dollar store authorizations beginning and ending each year. The two lines cross for the
first time in 2024.</figcaption></figure>

<p>Put next to the grocery formats, the result is stark. Dollar stores passed every single grocery format years ago. They are now the second most common SNAP retailer in the country. Only convenience stores beat them.</p>

<figure>{c_ctx}{charts.legend(s_ctx)}
<figcaption>Active SNAP authorizations by store format. Convenience stores are omitted for scale —
there are about 119,000 of them.</figcaption></figure>

<h2>2024 breaks the pattern</h2>
<p>Endings jumped from a few hundred a year to <strong>{fl['departed'][yrs.index(2024)]:,}</strong> in
2024. This is the one place we can check the data against events that were independently reported.</p>

<table><thead><tr><th>Brand</th><th>Authorizations ending in 2024</th></tr></thead>
<tbody>{spike_tbl}</tbody></table>

<p>Dollar Tree spent 2024 closing Family Dollar stores. 99 Cents Only shut down entirely that spring. Both show up here right on time. That is a useful check. When something real happens in retail, these records catch it.</p>

<figure>{c_br}{charts.legend(s_br)}
<figcaption>Active SNAP authorizations by dollar-store brand. 99 Cents Only goes to zero in
2024.</figcaption></figure>

<h2>Where it matters</h2>
<p>Growth in total is not the same as growth where it matters. The sharper question is how often a dollar store is the <em>only</em> option nearby.</p>

<figure>{c_z}
<figcaption>ZIP codes containing at least one SNAP-authorized dollar store and no supermarket,
superstore, or grocery store of any size.</figcaption></figure>

<p>In 2008 that described {z[0]['dollar_only']:,} ZIP codes. By 2024 it described
<strong>{z[-1]['dollar_only']:,}</strong> — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of every
ZIP code that has a dollar store at all. Across the country there are now {d['headline']['dollar_2025']:,} dollar stores. Grocery stores of every size combined come to {d['headline']['all_grocery_2025']:,}.</p>

<div class="caveat">
<h3>Limits</h3>
<p>Nothing here measures floor space, sales, or what is on the shelves. A dollar store and a supermarket each count as one record. USDA sorts stores by how much they stock, and a 2018 rule moved that bar partway through this series. That affects grocery formats far more than dollar stores. The next piece takes it up.</p>
<p>SNAP spending per store is not public. A 2019 Supreme Court case, <em>Food Marketing Institute v. Argus Leader</em>, put those figures under a FOIA exemption. So we can see where authorized stores are, but never how much any one of them takes in.</p>
<p>Company store counts are from early 2025 to early 2026. We compare them against authorizations at the end of 2025. So the ratios are close, not exact.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, covering retailers authorized at
any point in the window. Analysis uses 656,868 stores with usable coordinates. A store counts as
active in a year if an authorization covered 31 December. Company store counts: Dollar General and
Dollar Tree investor releases, Family Dollar via trade press. Code, data pipeline and verification:
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
