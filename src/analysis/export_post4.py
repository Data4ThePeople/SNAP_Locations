"""Assemble reports/post4/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post4.json"
DIR = ROOT / "reports" / "post4"
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

    ch, ind, z, st, br = d["chain"], d["independent"], d["zips"], d["states"], d["brands"]
    ends, yrs = d["endings"], d["chain"]["years"]
    end_years = sorted(ends.keys())
    wal = d["census"][0]
    ended_2022_plus = sum(sum(v.values()) for k, v in ends.items() if int(k) >= 2022)

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{ch['2021_to_latest_pct']}%",
          "label": "fall in authorized drug chain stores, 2021 to 2025"},
         {"value": f"{ended_2022_plus:,}",
          "label": "drug chain authorizations ended 2022-2025"},
         {"value": f"{z['lost']:,}",
          "label": "ZIP codes lost their last SNAP-authorized drug store since 2021"}])

    fig(1, "drug-chain-arc",
        "Drug chain stores with an active SNAP authorization on 31 December of each year.",
        figures.line_png, yrs,
        [{"name": "drug chains", "values": ch["stock"], "slot": 1}],
        ylabel="active SNAP authorizations",
        annotate=[{"year": 2018, "text": "stocking rule"},
                  {"year": 2021, "text": "collapse begins"}],
        title="Chain pharmacies held flat, then fell off a cliff",
        subtitle="stores authorized on 31 December")

    bpick = [b for b in ["Walgreens", "CVS", "Rite Aid", "Duane Reade"] if b in br]
    fig(2, "by-chain",
        "Active SNAP authorizations by pharmacy chain.",
        figures.line_png, yrs,
        [{"name": b, "values": br[b]["stock"], "slot": i + 1} for i, b in enumerate(bpick)],
        ylabel="active authorizations",
        title="Three companies drive the whole decline",
        subtitle="stores authorized on 31 December, by chain")

    fig(3, "chain-table",
        "Peak and current SNAP authorizations by pharmacy chain.",
        figures.table_png, ["Chain", "Peak", "Year", "2025", "Change"],
        [[b, f"{v['peak']:,}", str(v["peak_year"]), f"{v['latest']:,}", f"{v['pct']:+.1f}%"]
         for b, v in sorted(br.items(), key=lambda kv: -kv[1]["peak"]) if v["peak"] >= 200],
        highlight_row=2,
        title="Peak and current count, chain by chain",
        subtitle="SNAP-authorized stores")

    fig(4, "endings-per-year",
        "Drug chain SNAP authorizations ending each year.",
        figures.hbar_png,
        [{"label": y, "value": sum(ends[y].values()), "slot": 2 if int(y) >= 2022 else 0}
         for y in end_years],
        title="The break lands after 2022",
        subtitle="drug chain authorizations ending each year")

    fig(5, "endings-table",
        "Drug chain authorizations ending each year, by company.",
        figures.table_png, ["Year", "Total", "Rite Aid", "Walgreens", "CVS"],
        [[y, f"{sum(ends[y].values()):,}", f"{ends[y].get('Rite Aid',0):,}",
          f"{ends[y].get('Walgreens',0):,}", f"{ends[y].get('CVS',0):,}"] for y in end_years],
        highlight_row=len(end_years) - 1,
        title="Which company left, and when",
        subtitle="authorizations ending each year, by company")

    fig(6, "states",
        "Largest percentage falls in authorized drug stores, 2021 to 2025, among states with "
        "at least 150 in 2021.",
        figures.hbar_png,
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": abs(r["pct"]),
          "slot": 2 if r["state"] == "PA" else 0} for r in st[:8]], suffix="%",
        title="Where the pharmacies were",
        subtitle="largest falls in authorized drug stores, 2021 to 2025")

    md = f"""# Rite Aid went from 1,523 SNAP-authorized stores to 2

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
Drug chains peaked at {ch['peak']:,} in {ch['peak_year']} and stand at {ch['latest']:,}.*

**{ch['2021_to_latest_pct']}%** fall in authorized drug chain stores, 2021 to 2025.
**{ended_2022_plus:,}** drug chain authorizations ended 2022–2025.
**{z['lost']:,}** ZIP codes lost their last SNAP-authorized drug store since 2021.

![Headline figures](images/00-key-figures.png)

---

USDA files drug stores in the same category as dollar stores. It is called "Combination Grocery/Other." The bucket holds stores that mainly sell general goods but also sell food. The two have moved
in opposite directions, and the pharmacy side has fallen off a cliff in the last four years.

![{figs["drug-chain-arc"]['caption']}](images/{figs["drug-chain-arc"]['file']})

The shape matters. Drug chains peaked at **{ch['peak']:,} in {ch['peak_year']}** and then did almost
nothing for five years: down {abs(ch['peak_to_2021_pct'])}% by 2021. Then they lost
**{abs(ch['2021_to_latest_pct'])}%** in four years.

That timing rules out the explanation that fits other small-format retailers. USDA's stocking rules changed in 2018. Pharmacies face the same inventory test as everyone else. The drug chains passed it easily. Their decline starts three years later, and it has a much
more mundane cause.

## It is three companies

The decline is not spread across the industry. Split the same total by chain and three names carry all of it:

![{figs["by-chain"]['caption']}](images/{figs["by-chain"]['file']})

Here is each chain at its peak and today:

![{figs["chain-table"]['caption']}](images/{figs["chain-table"]['file']})

Rite Aid is not a decline, it is a disappearance: **{br['Rite Aid']['peak']:,}** stores at its
{br['Rite Aid']['peak_year']} peak, {br['Rite Aid']['stock'][yrs.index(2024)]:,} as recently as 2024,
and **{br['Rite Aid']['latest']}** at the end of 2025. The company filed its second Chapter 11 in two
years on 5 May 2025 and closed its last 89 stores on 3 October, ending 63 years of business.

Walgreens is down {abs(br['Walgreens']['pct']):.0f}% from its {br['Walgreens']['peak_year']} peak,
having announced 1,200 closures in October 2024 before being taken private by Sycamore Partners. CVS is
down {abs(br['CVS']['pct']):.0f}% from {br['CVS']['peak_year']} — a smaller percentage, but
{br['CVS']['peak'] - br['CVS']['latest']:,} fewer stores, after roughly 900 closures between 2022 and
2024 and 271 more announced for 2025.

## When they left

Count the authorizations that ended each year and the break is obvious: The baseline is a couple of hundred a
year. Then 2022 arrives.

![{figs["endings-per-year"]['caption']}](images/{figs["endings-per-year"]['file']})

Split the same years by company and you can see who left when:

![{figs["endings-table"]['caption']}](images/{figs["endings-table"]['file']})

This is the most externally checkable finding in this series. Every one of these moves was announced by the company and covered in the trade press. The authorization records line up with them. When a retailer's own filings and USDA's paperwork tell the same story, the paperwork can
be trusted for the cases where no filing exists.

It also means closure language is defensible here in a way it is not for independent grocers. In 2024
Walgreens had {wal['authorized_2024']:,} SNAP authorizations. It reported operating about {wal['reported']:,} US stores. That is a ratio of {wal['ratio']}. For this chain, authorization is effectively a
store census, so an ending is a closed store.

## What this data cannot tell you about independent pharmacies

It would be natural to ask next how independent pharmacies fared. These records cannot answer that, and
it is worth being explicit about why rather than reporting a number that looks like an answer.

A pharmacy appears in this dataset only if it is **SNAP-authorized**, which requires stocking staple
foods. Most independent pharmacies do not. Trade sources put the national count of independent community
pharmacies near {ind['national_estimate']:,}; this dataset contains **{ind['latest']}** of them — about
{100*ind['coverage']:.1f}%. The visible ones are the unusual subset that double as food retailers.

And they are not spread evenly. New York accounts for **{100*ind['ny_share_latest']:.0f}%** of the 2025
count, up from {100*ind['ny_share_first']:.0f}% in 2006 — the small pharmacy-plus-bodega is a distinctly
New York retail form. Worse for any trend claim, the two halves move in opposite directions: New York
went from {ind['ny'][0]} to {ind['latest_ny']} while the rest of the country went from
{ind['ex_ny_first']} to {ind['ex_ny_latest']}. A national line through that averages a rise and a fall
and describes neither.

So there is no independent-pharmacy finding here. What the chains show above is solid because their SNAP
authorization is close to a store census; for independents, this source is the wrong instrument.

## Where the stores were

The losses are concentrated, and the map follows Rite Aid's footprint.

![{figs["states"]['caption']}](images/{figs["states"]['file']})

Pennsylvania — Rite Aid's home state — lost {abs(st[0]['delta']):,} of {st[0]['then']:,},
{abs(st[0]['pct']):.0f}%. Michigan lost {abs(st[1]['delta']):,}. California lost the most in absolute
terms.

Nationally, **{z['lost']:,} ZIP codes** that had at least one SNAP-authorized chain pharmacy in 2021 had
none by 2025. Only {z['gained']} gained one. That is the part that matters for people. In a neighbourhood with no grocery store, a pharmacy is often where a SNAP household buys food. It is also where they fill prescriptions.

## Limits

These records count **SNAP authorizations**, not pharmacies. A drug store that stops accepting EBT but
keeps trading looks the same as one that closes. For Walgreens the two are nearly equivalent — hence the
census check above — but that logic does not transfer to independents.

CVS is left out of the store-count check on purpose. About 1,700 of its pharmacies sit inside Target stores, and Target's own authorization covers those. So CVS's count here is lower than its real footprint. Rite Aid is left out for the opposite reason — its store count was moving so fast in 2024–25
that any single-date comparison is unstable.

A SNAP authorization says nothing about whether a pharmacy fills prescriptions. Nothing here measures prescription counts or pharmacy access. The ZIP-code count above covers chain pharmacies
only, for the coverage reason set out earlier.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Corporate events from company filings and contemporaneous trade press. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post4.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post4.html", DIR / "post4-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post4.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
