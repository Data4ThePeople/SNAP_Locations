"""Render reports/post4.html from reports/data/post4.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS
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
        annotate=[{"year": 2018, "text": "stocking rule"}, {"year": 2021, "text": "collapse begins"}])

    bpick = ["Walgreens", "CVS", "Rite Aid", "Duane Reade"]
    s_br = [{"name": b, "values": br[b]["stock"], "slot": i + 1}
            for i, b in enumerate(bpick) if b in br]
    c_br = charts.line_chart(yrs, s_br, y_label="active authorizations")

    end_years = sorted(ends.keys())
    tot = [sum(ends[y].values()) for y in end_years]
    c_end = charts.bar_chart(
        [{"label": y, "value": tot[i], "slot": 2 if int(y) >= 2022 else 0}
         for i, y in enumerate(end_years)])

    end_tbl = "".join(
        f"<tr><td>{y}</td><td>{sum(ends[y].values()):,}</td>"
        f"<td>{ends[y].get('Rite Aid', 0):,}</td><td>{ends[y].get('Walgreens', 0):,}</td>"
        f"<td>{ends[y].get('CVS', 0):,}</td></tr>" for y in end_years)

    c_ind = charts.line_chart(
        yrs, [{"name": "independent pharmacies", "values": ind["stock"], "slot": 3}],
        y_label="active authorizations")

    c_st = charts.bar_chart(
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": abs(r["pct"]),
          "slot": 2 if r["state"] == "PA" else 0} for r in st[:8]], suffix="%")

    brand_tbl = "".join(
        f"<tr><td>{b}</td><td>{v['peak']:,}</td><td>{v['peak_year']}</td>"
        f"<td>{v['latest']:,}</td><td>{v['pct']:+.1f}%</td></tr>"
        for b, v in sorted(br.items(), key=lambda kv: -kv[1]["peak"]) if v["peak"] >= 200)

    wal = d["census"][0]

    html = f"""<title>Rite Aid went from 1,523 SNAP-authorized stores to 2</title>
<style>{CSS}</style>
<main>
<h1>Rite Aid went from 1,523 SNAP-authorized stores to 2</h1>
<p class="sub">SNAP-authorized retailers, 2006–2025 · USDA Food and Nutrition Service authorization
records · drug chains peaked at {ch['peak']:,} in {ch['peak_year']} and stand at {ch['latest']:,}</p>

<div class="ledger">
  <div><b>{ch['2021_to_latest_pct']}%</b><span>fall in authorized drug chain stores, 2021 to 2025</span></div>
  <div><b>{sum(sum(v.values()) for k, v in ends.items() if int(k) >= 2022):,}</b><span>drug chain authorizations ended 2022–2025</span></div>
  <div><b>{z['lost']:,}</b><span>ZIP codes lost their last SNAP-authorized drug store since 2021</span></div>
</div>

<p>USDA files drug stores in the same category as dollar stores — "Combination Grocery/Other," a
bucket for retailers whose main business is general merchandise but which also sell food. The two
have moved in opposite directions, and the pharmacy side has fallen off a cliff in the last four
years.</p>

<figure>{c_chain}
<figcaption>Drug chain stores with an active SNAP authorization on 31 December of each
year.</figcaption></figure>

<p>The shape matters. Drug chains peaked at <strong>{ch['peak']:,} in {ch['peak_year']}</strong> and
then did almost nothing for five years: down {abs(ch['peak_to_2021_pct'])}% by 2021. Then they lost
<strong>{abs(ch['2021_to_latest_pct'])}%</strong> in four years.</p>

<p>That timing rules out the explanation that fits other small-format retailers. USDA's stocking
standards changed in 2018, and pharmacies are authorized under the same inventory test as everyone
else — but drug chains sailed through it. Their decline starts three years later, and it has a much
more mundane cause.</p>

<h2>It is three companies</h2>

<figure>{c_br}{charts.legend(s_br)}
<figcaption>Active SNAP authorizations by pharmacy chain.</figcaption></figure>

<table><thead><tr><th>Chain</th><th>Peak</th><th>Year</th><th>2025</th><th>Change</th></tr></thead>
<tbody>{brand_tbl}</tbody></table>

<p>Rite Aid is not a decline, it is a disappearance: <strong>{br['Rite Aid']['peak']:,}</strong> stores
at its {br['Rite Aid']['peak_year']} peak, {br['Rite Aid']['stock'][yrs.index(2024)]:,} as recently as
2024, and <strong>{br['Rite Aid']['latest']}</strong> at the end of 2025. The company filed its second
Chapter 11 in two years on 5 May 2025 and closed its last 89 stores on 3 October, ending 63 years of
business.</p>

<p>Walgreens is down {abs(br['Walgreens']['pct']):.0f}% from its {br['Walgreens']['peak_year']} peak,
having announced 1,200 closures in October 2024 before being taken private by Sycamore Partners. CVS
is down {abs(br['CVS']['pct']):.0f}% from {br['CVS']['peak_year']} — a smaller percentage, but
{br['CVS']['peak'] - br['CVS']['latest']:,} fewer stores, after roughly 900 closures between 2022 and
2024 and 271 more announced for 2025.</p>

<h2>When they left</h2>
<p>Authorizations ending per year makes the break unmistakable. The baseline is a couple of hundred a
year. Then 2022 arrives.</p>

<figure>{c_end}
<figcaption>Drug chain SNAP authorizations ending each year.</figcaption></figure>

<table><thead><tr><th>Year</th><th>Total</th><th>Rite Aid</th><th>Walgreens</th><th>CVS</th></tr></thead>
<tbody>{end_tbl}</tbody></table>

<p>This is the most externally checkable finding in this series. Every one of these movements was
announced by the company and covered in the trade press at the time, and the authorization records
line up with them. When a retailer's own filings and USDA's paperwork tell the same story, the
paperwork can be trusted for the cases where no filing exists.</p>

<p>It also means closure language is defensible here in a way it is not for independent grocers. In
2024 Walgreens had {wal['authorized_2024']:,} SNAP authorizations against roughly
{wal['reported']:,} US stores it reported operating — a ratio of {wal['ratio']}. For this chain,
authorization is effectively a store census, so an ending is a closed store.</p>

<h2>The independents were already going</h2>
<p>Independent pharmacies are a much smaller population, and their decline started years earlier and
never reversed.</p>

<figure>{c_ind}
<figcaption>Independently owned pharmacies with an active SNAP authorization, identified by store
name.</figcaption></figure>

<p>They peaked at {ind['peak']} in {ind['peak_year']} and stand at {ind['latest']} —
<strong>{ind['pct']}%</strong>. Unlike the chains, their fall does overlap the 2018 stocking change,
and it kept going. Two cautions: these are small absolute numbers, so percentages move easily; and
identifying them by store name misses any pharmacy trading under its owner's surname, so treat
{ind['peak']} as a floor and the direction as the finding.</p>

<h2>Where the stores were</h2>
<p>The losses are concentrated, and the map follows Rite Aid's footprint.</p>

<figure>{c_st}
<figcaption>Largest percentage falls in authorized drug stores, 2021 to 2025, among states with at
least 150 in 2021. Labels show the count then and now.</figcaption></figure>

<p>Pennsylvania — Rite Aid's home state — lost {abs(st[0]['delta']):,} of
{st[0]['then']:,}, {abs(st[0]['pct']):.0f}%. Michigan lost {abs(st[1]['delta']):,}. California lost the
most in absolute terms.</p>

<p>Nationally, <strong>{z['lost']:,} ZIP codes</strong> that had at least one SNAP-authorized drug
store in 2021 had none by 2025. Only {z['gained']} gained one. That is the part with consequences for
people: a pharmacy is often where a SNAP household buys food in a neighbourhood with no grocery
store, and it is where they fill prescriptions.</p>

<div class="caveat">
<h3>Limits</h3>
<p>These records count <strong>SNAP authorizations</strong>, not pharmacies. A drug store that stops
accepting EBT but keeps trading looks the same as one that closes. For Walgreens the two are nearly
equivalent — hence the census check above — but that logic does not transfer to independents.</p>
<p>CVS is deliberately left out of the census comparison: roughly 1,700 of its pharmacies operate
inside Target stores and are covered by Target's own authorization, so its authorization count
understates its footprint. Rite Aid is left out for the opposite reason — its store count was moving
so fast in 2024–25 that any single-date comparison is unstable.</p>
<p>A pharmacy's SNAP authorization says nothing about whether it dispenses prescriptions, and nothing
here measures prescription volume or pharmacy access as such.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 611,164 stores with
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
