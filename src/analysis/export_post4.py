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
        label_ends=False,          # one series; the title already names it
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

    fig(3, "states",
        "Largest percentage falls in authorized chain drug stores, 2021 to 2025, among states with "
        "at least 150 in 2021.",
        figures.hbar_png,
        [{"label": f"{r['state']}  {r['then']:,}→{r['now']:,}", "value": r["pct"],
          "slot": 2 if r["state"] == "PA" else 0} for r in st[:8]], suffix="%",
        direction="left",
        title="Where the pharmacies were",
        subtitle="largest falls in authorized chain drug stores, 2021 to 2025")

    md = f"""# The one chain format that did not work

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Administration authorization records.
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

The answer has to do with what was happening behind the pharmacy counter. A pharmacy dispenses
prescriptions. But unlike a dollar store, which sets its own prices on its groceries and tchotchkes, a
pharmacy does not set the price of its prescriptions. That is done, effectively, by the pharmacy
benefit managers — the ginormous middlemen that adjudicate every pharmacy claim. When a pharmacy rings
up your prescription, the PBM's price comes back and tells them how much they will be reimbursed for
it. They have no control over this. They just take the price they get.

Years ago these prices weren't that bad, and pharmacies could make money at the prices they were
assigned. But over time the PBMs squeezed and squeezed reimbursement, pressuring pharmacy profit. I
spent years analyzing this at [46brooklyn Research](https://www.46brooklyn.com) and
[3 Axis Advisors](https://www.3axisadvisors.com) — if you really want to head down a rabbit hole, head
over there and read all about it. Small community pharmacies really started feeling the pain of
reimbursement pressure in the 2016 to 2018 time frame. It apparently took a few more years for that
pressure to make it to the much larger chains, and a few years after that for it to kill one off
altogether.

But if we only spoke of PBMs we would be underselling how terrible the pharmacy business really is. On
the other side of the fence is the pharmacy's wholesaler, a trade dominated by three monstrous
players. Go back to the dollar store and how it can set its prices. It also has control over its costs,
because if one vendor has a crappy price on a product, it can just buy it elsewhere. The dollar store
has some control over both sides of its gross margin equation. Now back to the pharmacy. The massive
wholesalers lock pharmacies into purchasing agreements that prevent them from shopping for the best
price on every drug. They can shop a bit — but only for a minority of their purchases. The majority
is required to come from their primary wholesaler. Sounds anti-competitive, doesn't it? But that's
U.S. health care. If you have size and a good team of lawyers, you can get away with just about
anything.

So pharmacy is really getting squeezed on both sides, by ginormous PBMs and massive wholesalers.
Community pharmacy has known this for years — and sadly, we can't identify community pharmacy from
this data source. But apparently chain pharmacies are now getting caught up in the carnage.

The chains say so themselves. Walgreens' 2024 annual report describes "ongoing prescription
reimbursement pressure," and names the cause: benefit managers and insurers "have consolidated over
recent years to create larger healthcare entities with greater bargaining power." Rite Aid's last annual
report before bankruptcy said it more bluntly. To join the restricted networks that Medicare Part D
plans run, "retail pharmacies generally are required to accept lower reimbursement rates."

In short, pharmacies are the polar opposite of the fuel-forward convenience store chains — the Wawas,
Casey's and Sheetzes of the world. In the early 2020s those gas stations benefited wildly from higher
margins in their core business, selling fuel. Meanwhile, at that exact same time, the chain pharmacies
got hit by lower margins in their core business, selling prescriptions. One thrived. The other is in
demise.

## The fall of the Big 3

If we look at the chains, three dominate the rest by store count: Walgreens, CVS and Rite Aid. The
table below shows the counts at which they peaked, the year they got there, and where they stood at
the end of 2025. All three are down. One is now gone. And the one that has relatively outperformed —
CVS — is the only one of the three that owns its own PBM. Likely not a coincidence.

![{figs["chain-table"]['caption']}](images/{figs["chain-table"]['file']})

Rite Aid is not a decline. It is a disappearance: **{br['Rite Aid']['peak']:,}** stores at its
{br['Rite Aid']['peak_year']} peak, {br['Rite Aid']['stock'][yrs.index(2024)]:,} as recently as 2024,
and **{br['Rite Aid']['latest']}** at the end of 2025. The company filed its second Chapter 11 in two
years on 5 May 2025 and closed its last 89 stores on 3 October, ending a run that began with a
single discount store in Scranton, Pennsylvania in 1962.

Walgreens and CVS are the slower version of the same story. Walgreens approved another 900 to 1,000
closures in October 2024, then was taken private by Sycamore Partners in August 2025. CVS closed
roughly 900 stores between 2022 and 2024, and 221 more in 2025. Every one of these moves was announced
by the company as it happened, and the authorization records line up with them — which makes this the
most checkable finding in the series.

## {z['lost']:,} ZIP codes lost their last chain pharmacy

But the losses are not spread evenly. They track Rite Aid's footprint.

![{figs["states"]['caption']}](images/{figs["states"]['file']})

Pennsylvania — Rite Aid's home state — lost {abs(st[0]['delta']):,} of {st[0]['then']:,} chain
pharmacies, or {abs(st[0]['pct']):.0f}%; Michigan lost {abs(st[1]['delta']):,}; California lost more
stores than any other state. Nationally, **{z['lost']:,} ZIP codes** that had at least one
SNAP-authorized chain pharmacy in 2021 had none by 2025, and only {z['gained']} went the other way.

The sharpest divide is in where those losses landed. **One in six nonmetro ZIP codes lost its last
chain pharmacy** — {z['rate_nonmetro']}%, against {z['rate_metro']}% of metro ones. Yet again,
nonmetro areas get the short end of the stick, driving American geographic inequality ever higher.

That is the part that matters for people. In many communities, losing a pharmacy isn't just losing
another food store option; it's also losing access to prescriptions, and to the pharmacist — a health
care provider — who was there to answer questions.

## What it adds up to

Let's not mince words — the chain pharmacy trend is bad. But what is more interesting is the reason
why it's so bad, as it gets to the rotten core of our nation's problems with all health care. And
when we dig further, we once again see this tale of two Americas. We have learned that as time
passes, people who live in rural areas have fewer places to buy food. The stores they do have carry
a limited inventory — enough to make ends meet but not enough to meet their nutritional needs. Without
proper nutrition, it follows that rural America could be more likely to get sick. And today we have
learned that they are more likely to have lost the pharmacy they are more likely to need.

This is the conundrum facing America today. Five chapters in, it's becoming quite obvious to me that
no one who has any control is doing anything to improve the quality of life for the "other side" of
America. Rather, we sit idly on the comfortable side, enjoying our plentiful supply of grocery
stores and pharmacies.

The good news is that now you know. You can completely disagree with my logic, you can decide not to
care about the America you don't see each day, or you can choose to do what you can to fix this
problem.

**Tomorrow: the pattern behind all five chapters — and the explanation most of us would reach for,
which the data says is wrong.**

## Limits

**The margin explanation is not measured here.** These records show the collapse and its timing, not
why. The squeeze is taken from the companies' own annual reports, quoted above, from the concentration
of drug distribution among three wholesalers, and from the author's own years running independent
pharmacies. That is testimony and industry structure, not measurement.

These records count **SNAP authorizations**, not pharmacies. A drug store that stops accepting EBT
but keeps trading looks the same here as one that closes. For Walgreens the two are nearly the same
thing — it held {wal['authorized_2024']:,} authorizations at the end of 2024 against the
{wal['reported']:,} US stores its own annual report counted four months earlier — but that logic
carries to no one else, and CVS in particular is undercounted here, because its pharmacies inside
Target stores sit under Target's own authorization.

**Duane Reade is counted with Walgreens, and Longs Drugs with CVS.** Walgreens bought Duane Reade in
April 2010 and CVS bought Longs in October 2008, so for most of this window they are signage rather
than competitors; listed separately, a store changing its sign would read as a store lost.

Independent pharmacies are not in this story, and cannot be. A pharmacy appears here only if it is
SNAP-authorized, which requires stocking staple foods, and most independents do not. Against the
{ind['national_estimate']:,} independent community pharmacies the National Community Pharmacists
Association counted in July 2025, this dataset holds **{ind['latest']}** stores whose names merely
suggest a pharmacy — {100*ind['coverage']:.1f}%, of which {ind['multi_store']} share a name with
another store and so are small chains, and nearly half sit in New York. Nothing about the sector can
be drawn from them.

Counties carry their **2023 Rural-Urban Continuum Code**, as in Day 4, and a ZIP code is assigned the
modal county of the stores inside it. Nothing here measures prescriptions, pharmacy access, nutrition
or health. Where this piece reasons from one of those to the next, it is reasoning, not measurement.

---

*Source: SNAP Retailer Locator Historical Data, 2005–2025, from USDA's Food and Nutrition Administration (the Food and Nutrition Service until June 2026). Analysis uses 656,868 stores with
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
