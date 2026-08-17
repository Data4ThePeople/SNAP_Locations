"""Render reports/post4.html from reports/data/post4.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post4.json"
OUT = ROOT / "reports" / "post4.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(4, "light", verbose=False)
    palette.validate(4, "dark", verbose=False)

    ch, ind, z, st = d["chain"], d["independent"], d["zips"], d["states"]
    yrs = ch["years"]
    br = d["brands"]
    ends = d["endings"]

    c_chain = charts.line_chart(
        yrs, [{"name": "drug chains", "values": ch["stock"], "slot": 1}],
        y_label="active SNAP authorizations",
        annotate=[{"year": 2018, "text": "stocking rule"}, {"year": 2021, "text": "collapse begins"}],
        title="Chain pharmacies held flat, then fell off a cliff",
        subtitle="stores authorized on 31 December")

    # The by-chain line and the aggregate endings bar are cut: each showed the
    # same split as the table beside it, less precisely, and the piece was two
    # figures over the limit.
    end_years = sorted(ends.keys())
    end_tbl = "".join(
        f"<tr><td>{y}</td><td>{sum(ends[y].values()):,}</td>"
        f"<td>{ends[y].get('Rite Aid', 0):,}</td><td>{ends[y].get('Walgreens', 0):,}</td>"
        f"<td>{ends[y].get('CVS', 0):,}</td></tr>" for y in end_years)

    o = ind

    c_st = charts.bar_chart(
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": abs(r["pct"]),
          "slot": 2 if r["state"] == "PA" else 0} for r in st[:8]], suffix="%",
        title="Where the pharmacies were",
        subtitle="largest falls in authorized drug stores, 2021 to 2025")

    brand_tbl = "".join(
        f"<tr><td>{b}</td><td>{v['peak']:,}</td><td>{v['peak_year']}</td>"
        f"<td>{v['latest']:,}</td><td>{v['pct']:+.1f}%</td></tr>"
        for b, v in sorted(br.items(), key=lambda kv: -kv[1]["peak"]) if v["peak"] >= 200)

    wal = d["census"][0]

    html = f"""{HEAD}<title>Rite Aid went from 1,523 SNAP-authorized stores to 2</title>
<style>{CSS}</style>
<main>
<h1>Rite Aid went from 1,523 SNAP-authorized stores to 2</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · drug chains peaked at {ch['peak']:,} in {ch['peak_year']} and stand at {ch['latest']:,}</p>

<div class="ledger">
  <div><b>{ch['2021_to_latest_pct']}%</b><span>fall in authorized drug chain stores, 2021 to 2025</span></div>
  <div><b>{sum(sum(v.values()) for k, v in ends.items() if int(k) >= 2022):,}</b><span>drug chain authorizations ended 2022–2025</span></div>
  <div><b>{z['lost']:,}</b><span>ZIP codes lost their last SNAP-authorized chain pharmacy since 2021</span></div>
</div>

<p>A drug store is not most people's idea of a grocery store. USDA files it as one anyway, in the
same category as the dollar store: "Combination Grocery/Other," for shops that mainly sell general
goods and also sell food. That filing is not a technicality. In a neighborhood with no supermarket,
the pharmacy is often where a SNAP household buys food.</p>

<p>Those stores are going away, and it happened fast.</p>

<figure>{c_chain}
<figcaption>Drug chain stores with an active SNAP authorization on 31 December of each
year.</figcaption></figure>

<p>Drug chains peaked at <strong>{ch['peak']:,} in {ch['peak_year']}</strong>. For the next five years
almost nothing happened: down {abs(ch['peak_to_2021_pct'])}% by 2021. Then they lost
<strong>{abs(ch['2021_to_latest_pct'])}%</strong> in four years.</p>

<p>That timing rules out the explanation that fits the other small formats in this series. USDA's
stocking rules changed in 2018, and pharmacies face the same inventory test as everyone else. They
passed it easily. This decline starts three years later, and the cause is far more ordinary.</p>

<h2>Three companies did all of it</h2>

<p>The industry did not shrink. Three companies did.</p>

<table><thead><tr><th>Chain</th><th>Peak</th><th>Year</th><th>2025</th><th>Change</th></tr></thead>
<tbody>{brand_tbl}</tbody></table>

<p>Rite Aid is not a decline. It is a disappearance: <strong>{br['Rite Aid']['peak']:,}</strong> stores
at its {br['Rite Aid']['peak_year']} peak, {br['Rite Aid']['stock'][yrs.index(2024)]:,} as recently as
2024, and <strong>{br['Rite Aid']['latest']}</strong> at the end of 2025. The company filed its second
Chapter 11 in two years on 5 May 2025 and closed its last 89 stores on 3 October, ending 63 years in
business.</p>

<p>Walgreens is down {abs(br['Walgreens']['pct']):.0f}% from its {br['Walgreens']['peak_year']} peak.
It announced 1,200 closures in October 2024, then was taken private by Sycamore Partners. CVS is down
{abs(br['CVS']['pct']):.0f}% from {br['CVS']['peak_year']} — a smaller share, but
{br['CVS']['peak'] - br['CVS']['latest']:,} fewer stores, after roughly 900 closures between 2022 and
2024 and 271 more announced for 2025.</p>

<p>Count the authorizations that ended each year and you can see who left when. The baseline is a
couple of hundred a year. Then 2022 arrives.</p>

<table><thead><tr><th>Year</th><th>Total</th><th>Rite Aid</th><th>Walgreens</th><th>CVS</th></tr></thead>
<tbody>{end_tbl}</tbody></table>

<p>This is the most checkable finding in the series. Every one of these moves was announced by the
company and written up in the trade press, and the authorization records line up with them.</p>

<p>That matters beyond this chapter. In 2024 Walgreens held {wal['authorized_2024']:,} SNAP
authorizations and reported operating about {wal['reported']:,} US stores — a ratio of {wal['ratio']}.
For a chain like this one, the authorization list is very close to a store census. So here, unlike
anywhere else in the series, we can say a store closed and mean it.</p>

<h2>{z['lost']:,} ZIP codes lost their last one</h2>

<p>The losses are not spread evenly. They track Rite Aid's footprint.</p>

<figure>{c_st}
<figcaption>Largest percentage falls in authorized drug stores, 2021 to 2025, among states with at
least 150 in 2021. Labels show the count then and now.</figcaption></figure>

<p>Pennsylvania — Rite Aid's home state — lost {abs(st[0]['delta']):,} of {st[0]['then']:,}, or
{abs(st[0]['pct']):.0f}%. Michigan lost {abs(st[1]['delta']):,}. California lost the most stores of any
state.</p>

<p>Nationally, <strong>{z['lost']:,} ZIP codes</strong> that had at least one SNAP-authorized chain
pharmacy in 2021 had none by 2025. Only {z['gained']} gained one.</p>

<p>That is the part that matters for people. In these places the pharmacy was the food store, and it
was also where prescriptions got filled. Both left on the same day.</p>

<h2>What it adds up to</h2>

<p>The other losses in this series were slow, and hard to pin on anyone. This one is neither. It took
four years, three companies did it, and each of them announced it as it happened.</p>

<p>It also hands us something the earlier chapters could not: a list of places. {z['lost']:,} ZIP codes
lost their last chain pharmacy in four years. Set that beside what came before — the small grocers that
went, the dollar stores and gas stations that stayed — and a question forms.</p>

<p>What happens in the neighborhoods where all of it lands at once? Do the formats that survive move in
when the others leave? Or do some places simply end up with less of everything? That is tomorrow, and
it is the last chapter.</p>

<div class="caveat">
<h3>Limits</h3>
<p>These records count <strong>SNAP authorizations</strong>, not pharmacies. A drug store that stops
accepting EBT but keeps trading looks the same here as one that closes. For Walgreens the two are
nearly the same thing — that is what the census check above establishes — but that logic does not carry
to anyone else.</p>
<p>Independent pharmacies are not in this story, and cannot be. A pharmacy shows up in these records
only if it is SNAP-authorized, which means stocking staple foods, and most independents do not. Trade
sources count about {o['national_estimate']:,} independent community pharmacies nationally. This
dataset holds <strong>{o['latest']}</strong> of them, or {100*o['coverage']:.1f}%. Nearly half sit in
New York, where the pharmacy that doubles as a corner grocery is a local retail form. Any national
trend drawn from {o['latest']} unusual stores would describe those stores, not the sector.</p>
<p>CVS is left out of the store-count check on purpose. About 1,700 of its pharmacies sit inside Target
stores, and Target's own authorization covers those, so CVS's count here is lower than its real
footprint. Rite Aid is left out for the opposite reason: its store count moved so fast in 2024–25 that
any single-date comparison is unstable.</p>
<p>A SNAP authorization says nothing about whether a pharmacy fills prescriptions. Nothing here
measures prescription counts or pharmacy access. The ZIP-code count above covers chain pharmacies only,
for the coverage reason set out just above.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Corporate events from company filings and contemporaneous trade press. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  drug chains {ch['peak']:,} ({ch['peak_year']}) -> {ch['latest']:,}")
    print(f"  Rite Aid {br['Rite Aid']['stock'][yrs.index(2024)]:,} (2024) -> "
          f"{br['Rite Aid']['latest']} (2025)")


if __name__ == "__main__":
    main()
