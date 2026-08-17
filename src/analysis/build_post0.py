"""Render reports/post0.html from reports/data/post0.json."""
import json

from analysis import palette
from analysis.report_css import CSS, HEAD
from config import ROOT

DATA = ROOT / "reports" / "data" / "post0.json"
OUT = ROOT / "reports" / "post0.html"

MAP_URL = "https://github.com/Data4ThePeople/SNAP_Locations"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(3, "light", verbose=False)
    palette.validate(3, "dark", verbose=False)
    ds, ch = d["dataset"], d["chapters"]

    rows = "".join(f"""
<li class="chapter">
  <div class="ch-day">Day {c['day']}</div>
  <div class="ch-body">
    <h3>{c['headline']}</h3>
    <p class="ch-topic">{c['topic']}</p>
    <p class="ch-stat"><b>{c['stat']['value']}</b> <span>{c['stat']['label']}</span></p>
    <p class="ch-why">{c['placement']}</p>
  </div>
</li>""" for c in ch)

    srcs = "".join(f"<li>{s}</li>" for s in d["sources"])

    extra = """
.chapter{display:flex;gap:1.2rem;padding:1.4rem 0;border-top:1px solid var(--rule);list-style:none}
.chapter:first-child{border-top:2px solid var(--ink)}
.ch-day{flex:0 0 4.2rem;font-family:var(--mono,monospace);font-size:.8rem;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);padding-top:.35rem}
.ch-body{flex:1;min-width:0}
.ch-body h3{margin:0 0 .35rem;font-size:1.12rem;line-height:1.3;text-wrap:balance}
.ch-topic{margin:0 0 .55rem;color:var(--ink-2)}
.ch-stat{margin:0 0 .55rem;font-family:var(--mono,monospace);font-size:.85rem}
.ch-stat b{color:var(--s1);font-size:1.05rem;margin-right:.5rem}
.ch-stat span{color:var(--ink-3)}
.ch-why{margin:0;font-size:.92rem;color:var(--ink-3);border-left:2px solid var(--rule);
  padding-left:.8rem}
ol.chapters,ul.chapters{padding:0;margin:1.6rem 0}
.plain li{margin:.25rem 0}
"""

    html = f"""{HEAD}<title>Twenty years of SNAP retailers, mapped — and what we found in it</title>
<style>{CSS}{extra}</style>
<main>
<h1>Twenty years of SNAP retailers, mapped — and what we found in it</h1>
<p class="sub">Every store authorized to accept SNAP anywhere in the United States,
{ds['first_year']}–{ds['last_year']} · {ds['stores']:,} stores · an interactive map, and seven days of
analysis built on it</p>

<div class="ledger">
  <div><b>{ds['stores']:,}</b><span>stores authorized to accept SNAP at some point in the last twenty years</span></div>
  <div><b>{ds['active_2025']:,}</b><span>still authorized at the end of {ds['last_year']}</span></div>
  <div><b>{ds['last_year'] - ds['first_year'] + 1}</b><span>years you can move through, one at a time</span></div>
</div>

<p>SNAP is the largest food assistance program in the country. To use it you need a store that accepts it. USDA publishes a record of every store ever approved to do so, going back twenty years. It is a remarkable file: <strong>{ds['stores']:,} stores</strong>. Each one has a location, a store type, and the dates its approval started and ended.</p>

<p>We have turned that file into a map you can explore, and then spent seven pieces working out what it
says.</p>

<h2>The map</h2>

<p>It is a single web page. Nothing to install, nothing to sign into.</p>

<ul class="plain">
<li><strong>Filter by store type.</strong> All {ds['formats']} of USDA's categories — supermarkets,
superstores, convenience stores, dollar stores, farmers' markets and the rest.</li>
<li><strong>Filter by retailer.</strong> {ds['brands']} chains are named, so you can clear the map and bring back only the ones you want. Turn everything off, then switch on Kroger and Giant Eagle. Now you are looking at two companies against an empty country.</li>
<li><strong>Move through time.</strong> One year at a time, {ds['first_year']} to {ds['last_year']}.
The map redraws for the stores authorized on 31 December of that year.</li>
</ul>

<p><a href="{MAP_URL}">The map, the pipeline that builds it, and every figure in this series.</a></p>

<h2>One thing to understand before reading anything else</h2>

<p>This file records <strong>authorizations, not storefronts</strong>. A store leaving the data means
its authorization ended. That usually means the store closed, but it can also mean the store is still
open and simply stopped accepting SNAP.</p>

<p>While it's tempting to conflate the change in authorizations with the change in storefronts, don't fall into that trap. They are not the same. The good news is that more research can be done to find the change in storefronts, if that is what you are after. In the coming days, anytime we use this data to gain some insight into storefront closures or openings, we will check these counts against publicly available data to see how well they match up. Usually that is a company's own reported store count, or the Census Bureau's count of business locations. We recommend you do the same, which is easier than it sounds — it simply requires asking your AI agent of choice to perform this cross check.</p>

<p>And where we could not make that match work, we say so and make no claim. That is why some obvious-looking findings are missing from these pieces.</p>

<h2>Seven days, seven parts of one story.</h2>

<p>Each piece stands alone, but the argument builds from one to the next. The first six are the story. The last is an epilogue about what it means for policy.</p>

<ol class="chapters">{rows}</ol>

<h2>What we are not claiming</h2>

<p>This data has no prices, no floor space, and no sales. It has no idea what is on a shelf. A dollar store and a supermarket each count as one record. It also does not know whether anyone has a car. That is often what decides whether a store ten miles away is a quick errand or out of reach.</p>

<p>So this series is about <strong>where the stores are and what kind they are</strong>. That is a real and useful question. It is not the same as asking whether people are fed.</p>

<div class="caveat">
<h3>Sources</h3>
<ul class="plain">{srcs}</ul>
<p>Every figure in every piece is produced by a script with assertions in it, not by a query typed once.
The pipeline matches the map we shipped. The store counts add up exactly across all nineteen pairs of years. Both are checked on every run.</p>
</div>

<footer>
Source: USDA FNS SNAP Retailer Locator Historical Data, {ds['first_year'] - 1}–{ds['last_year']}.
{ds['stores']:,} stores, {ds['spells']:,} authorization spells, of which {ds['multi_spell']:,} stores
hold more than one. {ds['mappable']:,} have coordinates good enough to map. Code, pipeline and
verification: <a href="{MAP_URL}">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    for c in ch:
        print(f"  Day {c['day']}  [{c['slug']}]  {c['headline'][:60]}")


if __name__ == "__main__":
    main()
