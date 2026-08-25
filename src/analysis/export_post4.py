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
    pr = d["peers"]
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
          "label": "ZIP codes lost their last SNAP-authorized chain pharmacy since 2021"}])

    fig(1, "drug-chain-arc",
        "Drug chain stores with an active SNAP authorization on 31 December of each year.",
        figures.line_png, yrs,
        [{"name": "drug chains", "values": ch["stock"], "slot": 1}],
        ylabel="active SNAP authorizations",
        annotate=[{"year": 2021, "text": "collapse begins"}],
        title="Chain pharmacies held flat, then fell off a cliff",
        subtitle="stores authorized on 31 December")

    # The by-chain line chart and the aggregate endings bar are both cut: each
    # one showed the same split as the table beside it, less precisely, and the
    # piece was two figures over the limit.
    fig(2, "chain-table",
        "Peak and current SNAP authorizations by pharmacy chain.",
        figures.table_png, ["Chain", "Peak", "Year", "2025", "Change"],
        [[b, f"{v['peak']:,}", str(v["peak_year"]), f"{v['latest']:,}", f"{v['pct']:+.1f}%"]
         for b, v in sorted(br.items(), key=lambda kv: -kv[1]["peak"]) if v["peak"] >= 200],
        highlight_row=2,
        title="Peak and current count, chain by chain",
        subtitle="SNAP-authorized stores")

    fig(3, "endings-table",
        "Drug chain authorizations ending each year, by company.",
        figures.table_png, ["Year", "Total", "Rite Aid", "Walgreens", "CVS"],
        [[y, f"{sum(ends[y].values()):,}", f"{ends[y].get('Rite Aid',0):,}",
          f"{ends[y].get('Walgreens',0):,}", f"{ends[y].get('CVS',0):,}"] for y in end_years],
        highlight_row=len(end_years) - 1,
        title="Which company left, and when",
        subtitle="authorizations ending each year, by company")

    fig(4, "states",
        "Largest percentage falls in authorized drug stores, 2021 to 2025, among states with "
        "at least 150 in 2021.",
        figures.hbar_png,
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": r["pct"],
          "slot": 2 if r["state"] == "PA" else 0} for r in st[:8]], suffix="%",
        direction="left",
        title="Where the pharmacies were",
        subtitle="largest falls in authorized drug stores, 2021 to 2025")

    md = f"""# The one chain format that did not work

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
Drug chains peaked at {ch['peak']:,} in {ch['peak_year']} and stand at {ch['latest']:,}.*

**{ch['2021_to_latest_pct']}%** fall in authorized drug chain stores, 2021 to 2025.
**{ended_2022_plus:,}** drug chain authorizations ended 2022–2025.
**{z['lost']:,}** ZIP codes lost their last SNAP-authorized chain pharmacy since 2021.

![Headline figures](images/00-key-figures.png)

---

A drug store is not most people's idea of a grocery store. USDA files it as one anyway, in the same
category as the dollar store: "Combination Grocery/Other," for shops that mainly sell general goods
and also sell food. That filing is not a technicality. Think of the last time you walked into a chain
pharmacy: the food is not a shelf by the register, it is aisles of it — cereal, pasta, canned goods,
snacks, a cooler of milk and frozen meals. The selection has far more in common with a dollar store
than with a convenience store. So when a fully stocked grocery store is not available, or is simply
too far away, the pharmacy offers our nation's most vulnerable people another place to buy food.

But a pharmacy is not a dollar store, and it is not a convenience store. Its economics are far
different. Trust me — I spent a few years running more than twenty of them. And the main difference is
what made this next chart break sharply down in the early part of this decade.

![{figs["drug-chain-arc"]['caption']}](images/{figs["drug-chain-arc"]['file']})

Drug chains peaked at **{ch['peak']:,} in {ch['peak_year']}**. For the next five years almost nothing
happened: down {abs(ch['peak_to_2021_pct'])}% by 2021. Then they lost
**{abs(ch['2021_to_latest_pct'])}%** in four years. Over those same four years the dollar store chains
rose {pr['dollar']['pct']}%, and the fuel-forward convenience chains {pr['fuel_forward']['pct']}%.

What gives? Why did the pharmacy chain format collapse this decade, while its closest competitors in
food retail carried on growing?

## The business behind the counter

Think back to Day 3, and the convenience store attached to a fuel pump. It is a small chain store with
a second business running behind it, and after 2020 that second business got much better: Murphy USA's
margin on a gallon of fuel rose 103%. The store rode it up.

A pharmacy is built to the same shape, and that is where the resemblance ends. Its second business
fills prescriptions, and it is squeezed at both ends at once. The shop at the front sells toothpaste
and snacks. The business behind it sets neither of the two prices that decide what that work earns.
What a prescription pays is set by the companies that manage drug benefits for insurers, the pharmacy
benefit managers, and it has been going one way for years.
What the drugs cost to buy is set at the other end, by the three wholesalers that handle more than 90%
of drug distribution in this country. Reimbursement on one side, cost of goods on the other, and
almost no control over the gross margin in between.

The chains say so themselves. Walgreens' 2024 annual report describes "ongoing prescription
reimbursement pressure," and names the cause: benefit managers and insurers "have consolidated over
recent years to create larger healthcare entities with greater bargaining power." Rite Aid's last annual
report before bankruptcy said it more bluntly. To join the restricted networks that Medicare Part D
plans run, "retail pharmacies generally are required to accept lower reimbursement rates."

Any independent pharmacist reading this already knows how true that is; it is the daily arithmetic of
the job. What this data adds is that the chains were not immune to the same dynamic.

That is the whole difference. Being small and being part of a chain are advantages in what it costs to
run a store. Neither one does anything about the margin on what the store sells. Two formats built to
the same shape, and the direction of the margin behind the counter is the only thing separating them —
one expanding, one contracting. That was enough.

## Three companies did all of it

The industry did not shrink. Three companies did.

![{figs["chain-table"]['caption']}](images/{figs["chain-table"]['file']})

Rite Aid is not a decline. It is a disappearance: **{br['Rite Aid']['peak']:,}** stores at its
{br['Rite Aid']['peak_year']} peak, {br['Rite Aid']['stock'][yrs.index(2024)]:,} as recently as 2024,
and **{br['Rite Aid']['latest']}** at the end of 2025. The company filed its second Chapter 11 in two
years on 5 May 2025 and closed its last 89 stores on 3 October, ending a run that began with a
single discount store in Scranton, Pennsylvania in 1962.

Walgreens is down {abs(br['Walgreens']['pct']):.0f}% from its {br['Walgreens']['peak_year']} peak. It
approved another 900 to 1,000 closures in October 2024 — 1,200 to 1,300 counting stores approved
earlier and not yet shut — and in August 2025 it was taken private by Sycamore Partners. CVS is down
{abs(br['CVS']['pct']):.0f}% from {br['CVS']['peak_year']} — a smaller share, but
{br['CVS']['peak'] - br['CVS']['latest']:,} fewer stores, after roughly 900 closures between 2022 and
2024 and a further 271 announced for 2025, of which 221 happened.

Count the authorizations that ended each year and you can see who left when. The baseline is a couple
of hundred a year. Then 2022 arrives.

![{figs["endings-table"]['caption']}](images/{figs["endings-table"]['file']})

This is the most checkable finding in the series. Every one of these moves was announced by the company
and written up in the trade press, and the authorization records line up with them.

That matters beyond this chapter. In 2024 Walgreens held {wal['authorized_2024']:,} SNAP
authorizations against the {wal['reported']:,} US stores its own annual report counts — a ratio of
{wal['ratio']}. The two dates are four months apart and Walgreens was closing stores between them, so
the real figure is a little higher than that. For a chain like this one, the authorization list is
very close to a store census. So here, unlike anywhere else in the
series, we can say a store closed and mean it.

## {z['lost']:,} ZIP codes lost their last one

The losses are not spread evenly. They track Rite Aid's footprint.

![{figs["states"]['caption']}](images/{figs["states"]['file']})

Pennsylvania — Rite Aid's home state — lost {abs(st[0]['delta']):,} of {st[0]['then']:,}, or
{abs(st[0]['pct']):.0f}%. Michigan lost {abs(st[1]['delta']):,}. California lost the most stores of any
state.

Nationally, **{z['lost']:,} ZIP codes** that had at least one SNAP-authorized chain pharmacy in 2021 had
none by 2025. Only {z['gained']} gained one.

That is the part that matters for people. In these places the pharmacy was the food store, and it was
also where prescriptions got filled. Both left on the same day.

## What it adds up to

The other losses in this series were slow, and hard to pin on anyone. This one is neither. It took four
years, three companies did it, and each of them announced it as it happened.

It also hands us something the earlier chapters could not: a list of places. {z['lost']:,} ZIP codes
lost their last chain pharmacy in four years. Set that beside what came before — the small grocers that
went, the dollar stores and gas stations that stayed — and a question forms.

What happens in the neighborhoods where all of it lands at once? Do the formats that survive move in
when the others leave? Or do some places simply end up with less of everything? That is tomorrow, and
it is the last chapter.

## Limits

**The margin explanation is not measured here.** These records show the collapse and its timing; they
say nothing about why. The squeeze is taken from the companies' own annual reports, quoted above, from
the fact that all three describe the same pressure, from the concentration of drug distribution among
three wholesalers, and from the author's own years running independent pharmacies. That is testimony
and industry structure, not a measurement. Nothing in this dataset can confirm or refute it.

These records count **SNAP authorizations**, not pharmacies. A drug store that stops accepting EBT but
keeps trading looks the same here as one that closes. For Walgreens the two are nearly the same thing —
that is what the census check above establishes — but that logic does not carry to anyone else.

Independent pharmacies are not in this story, and cannot be. A pharmacy shows up in these records only
if it is SNAP-authorized, which means stocking staple foods, and most independents do not. The
National Community Pharmacists Association counted {ind['national_estimate']:,} independent community
pharmacies nationally in July 2025. This dataset holds **{ind['latest']}** stores whose names suggest a
pharmacy, or {100*ind['coverage']:.1f}% — and not even all of those are independent: {ind['multi_store']}
of them share a name with at least one other store, so they are small regional chains. Nearly half sit in New York,
where the pharmacy that doubles as a corner grocery is a local retail form. Any national trend drawn
from {ind['latest']} unusual stores would describe those stores, not the sector.

CVS is left out of the store-count check on purpose. About 1,700 of its pharmacies sit inside Target
stores, and Target's own authorization covers those, so CVS's count here is lower than its real
footprint. Rite Aid is left out for the opposite reason: its store count moved so fast in 2024–25 that
any single-date comparison is unstable.

A SNAP authorization says nothing about whether a pharmacy fills prescriptions. Nothing here measures
prescription counts or pharmacy access. The ZIP-code count above covers chain pharmacies only, for the
coverage reason set out just above.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. Analysis uses 656,868 stores with
usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Corporate events and reimbursement language from company 10-K filings (Walgreens Boots Alliance FY2024, Rite Aid FY2023, CVS Health FY2025) and contemporaneous trade press. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post4.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post4.html", DIR / "post4-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post4.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
