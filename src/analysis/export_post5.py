"""Assemble reports/post5/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post5.json"
DIR = ROOT / "reports" / "post5"
IMG = DIR / "images"


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = []

    def fig(n, slug, caption, fn, *a, **kw):
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs.append({"file": p.name, "caption": caption})
        print(f"  {p.name}")

    arc, ac = d["arc"], d["arc_change"]
    grp, pres, gr, seq = d["groups"], d["presence"], d["growth"], d["sequencing"]
    den, tl = d["density"], d["total_loss"]
    s2 = d["series"].get("post2", {})
    entry_pct = abs(round(100 * (s2["drivers"]["new_after"] / s2["drivers"]["new_before"] - 1))) \
        if s2 else 55
    surv = d["series"].get("post1", {}).get("survival", [])
    dollar_surv = round(100 * next((r["rate"] for r in surv
                                    if r["format"] == "Dollar Store"), 0.782))

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{grp['lost']:,}",
          "label": "ZIP codes lost their last SNAP-authorized chain pharmacy since 2021"},
         {"value": f"{ac['dollar_multiple']}x",
          "label": "growth in dollar stores in those same ZIP codes since 2006"},
         {"value": f"{den['lost_no_grocery']['median_pop']:,}",
          "label": "median population of those that now have no grocery at all"}])

    fig(1, "twenty-year-arc",
        f"SNAP-authorized stores by format across the {grp['lost']:,} ZIP codes that lost their "
        "last chain pharmacy between 2021 and 2025.",
        figures.line_png, arc["years"],
        [{"name": "convenience", "values": arc["conv"], "slot": 3},
         {"name": "grocery", "values": arc["groc"], "slot": 4},
         {"name": "dollar", "values": arc["dollar"], "slot": 1},
         {"name": "chain pharmacy", "values": arc["drug"], "slot": 2}],
        ylabel="SNAP-authorized stores")

    fig(2, "presence-vs-control",
        "What each group of ZIP codes has in 2025.",
        figures.table_png, ["In 2025, the ZIP has...", "Lost pharmacy", "Kept pharmacy"],
        [[p["label"], f"{p['lost_pct']}%", f"{p['kept_pct']}%"] for p in pres],
        highlight_row=len(pres) - 1)

    fig(3, "growth-vs-control",
        "Change in store counts 2021 to 2025, in ZIP codes that lost their last chain pharmacy "
        "against those that kept one.",
        figures.hbar_png, [
            {"label": "dollar, lost pharmacy", "value": gr["lost"]["dollar_pct"], "slot": 2},
            {"label": "dollar, kept pharmacy", "value": gr["kept"]["dollar_pct"], "slot": 0},
            {"label": "convenience, lost pharmacy", "value": gr["lost"]["conv_pct"], "slot": 2},
            {"label": "convenience, kept pharmacy", "value": gr["kept"]["conv_pct"], "slot": 0}],
        suffix="%")

    fig(4, "median-population",
        "Median 2020 census population of the ZIP code (ZCTA), by group.",
        figures.hbar_png, [
            {"label": "lost pharmacy", "value": den["lost"]["median_pop"], "slot": 2},
            {"label": "kept pharmacy", "value": den["kept"]["median_pop"], "slot": 0},
            {"label": "lost, and no grocery left",
             "value": den["lost_no_grocery"]["median_pop"], "slot": 2}])

    fig(5, "small-zip-share",
        "Share of ZIP codes below population thresholds, by group.",
        figures.hbar_png, [
            {"label": "lost pharmacy, under 10k", "value": den["lost"]["under_10k_pct"], "slot": 2},
            {"label": "kept pharmacy, under 10k", "value": den["kept"]["under_10k_pct"], "slot": 0},
            {"label": "lost pharmacy, under 5k", "value": den["lost"]["under_5k_pct"], "slot": 2},
            {"label": "kept pharmacy, under 5k", "value": den["kept"]["under_5k_pct"], "slot": 0}],
        suffix="%")

    md = f"""# The pharmacy left. The grocery left. The dollar store stayed.

*SNAP-authorized retailers, 2006–2025, with 2020 census population by ZCTA. The fifth and last in
this series.*

**{grp['lost']:,}** ZIP codes lost their last SNAP-authorized chain pharmacy since 2021.
**{ac['dollar_multiple']}×** growth in dollar stores in those same ZIP codes since 2006.
**{den['lost_no_grocery']['median_pop']:,}** median population of those that now have no grocery at all.

![Headline figures](images/00-key-figures.png)

---

The four earlier pieces each followed one format. Dollar stores almost never leave the program. Small
grocers left in numbers, and mostly stopped being replaced. Pharmacy chains held flat for years and
then collapsed. Read separately they are three unrelated retail stories.

They are not unrelated in the places where they land. Take the **{grp['lost']:,} ZIP codes** that lost
their last SNAP-authorized chain pharmacy between 2021 and 2025, and look at what has happened to every
other kind of food retailer in those same places over twenty years.

![{figs[1]['caption']}](images/{figs[1]['file']})

Dollar stores went from {arc['dollar'][0]:,} to {arc['dollar'][-1]:,} — **{ac['dollar_multiple']}×**.
Grocery of every size went from {arc['groc'][0]:,} to {arc['groc'][-1]:,}, down
{abs(ac['groc_pct']):.0f}%. Pharmacies peaked at {ac['drug_peak']:,} in {ac['drug_peak_year']} and are
now at zero. In 2006 these places had roughly ten times as many grocery stores as dollar stores. Today
grocery outnumbers dollar by about two to one, and the direction of travel is unambiguous.

## The obvious explanation is wrong

The natural reading is substitution: dollar stores squeezed the others out. It is worth stating plainly
that the data does not support it, because it is the interpretation everyone reaches for first —
including me.

Three tests, all using a control group of the {grp['kept']:,} ZIP codes that had a chain pharmacy in
2021 and still have one. Without that comparison every number here looks like substitution, because
dollar stores grew almost everywhere.

**First: presence is identical.** Dollar and convenience stores are no more common where the pharmacy
went than where it stayed.

![{figs[2]['caption']}](images/{figs[2]['file']})

**Second: growth was slower, not faster.** If dollar stores were moving into vacated ground you would
expect the opposite.

![{figs[3]['caption']}](images/{figs[3]['file']})

**Third, and decisive: the dollar stores were already there.** Of the {seq['base']:,} ZIP codes,
**{seq['had_before_pct']}%** already had a dollar store in 2021, before the pharmacy left. Only
{seq['arrived_after']} — {seq['arrived_after_pct']}% — gained their first one afterwards. Nobody moved in
to fill a gap. They were neighbours for years.

And the timing does not work either. Pharmacy authorizations were flat from 2016 to 2021 and fell off
after 2022, tracking opioid litigation, pharmacy reimbursement and Rite Aid's bankruptcy. Dollar store
openings ran at a near-constant rate for sixteen years, indifferent to all of it.

## What these places actually have in common

The distinguishing feature is not what arrived. It is how small they are.

![{figs[4]['caption']}](images/{figs[4]['file']})

Median population in a ZIP that lost its pharmacy is **{den['lost']['median_pop']:,}**, against
**{den['kept']['median_pop']:,}** where the pharmacy survived. And among those that have also lost every
grocery store, the median is **{den['lost_no_grocery']['median_pop']:,} people**.

![{figs[5]['caption']}](images/{figs[5]['file']})

A third of the pharmacy-loss ZIPs have fewer than ten thousand residents, against a tenth of the
control. One in eight has fewer than five thousand.

That is the thread. **A supermarket needs volume. A chain pharmacy needs prescription volume. A dollar
store needs neither.** Its whole model is a small box, a narrow assortment, few staff and no fresh
inventory to spoil — which is precisely why it works in a market of six thousand people where a grocery
store does not.

Read that way, the three stories in this series stop being coincidences and become the same story told
from three angles:

- Small grocery's collapse was an **entry** collapse — new authorizations fell {entry_pct}% — and the
  2018 depth-of-stock rule added a fixed cost that a chain absorbs and a single store cannot. Within
  USDA's own Combination Grocery/Other category, independents fell 64% while the dollar chains in that
  same category fell 5%.
- Dollar stores' advantage was never fast opening. It was that **{dollar_surv}% stay** — a format cheap
  enough to survive where others cannot.
- Pharmacies were removed by forces of their own, but they were removed **from the thinnest markets
  first**.

No one displaced anyone. Three different pressures pushed in the same direction, and the formats with
the lowest fixed costs were the ones left standing. That is harder to address than displacement would
be: if a competitor were driving this, there would be a competitor to regulate.

## What is at stake

In **{tl['no_grocery']}** of these ZIP codes the only SNAP-authorized food retail left is a dollar store
or a convenience store. In **{tl['no_snap_retail_at_all']}** there is no SNAP-authorized retailer of any
kind. A household with an EBT card in those places is choosing among shelf-stable groceries, or driving.

There is a second consequence this data cannot measure but which should not go unmentioned. A retail
pharmacy is, for many people, the most accessible health professional they have — the person who checks
an interaction, takes a blood pressure, gives advice that would otherwise require an appointment. When
the last pharmacy in a small town closes, that access goes with it. These records count SNAP
authorizations; they say nothing about prescriptions or clinical advice, and the pharmacy desert
literature is the place to look for that. But it is the same buildings and the same towns.

## Limits

Every retail figure counts **SNAP authorizations**, not storefronts. For the pharmacy chains those are
nearly the same thing — Walgreens' authorizations run at 0.97 of its own reported store count — but for
independents they are not, and this series does not treat them as such.

The control group is ZIP codes that had a chain pharmacy in 2021 and kept one. It is not a matched
sample: the two groups differ in population, which is the finding rather than a nuisance. Read the
comparison as descriptive, not causal.

Population is 2020 census by ZCTA, which approximates but does not exactly equal a ZIP code.
{den['lost']['zips_matched']:,} of the {grp['lost']:,} pharmacy-loss ZIPs matched a ZCTA.

Nothing here measures sales, floor space, assortment or prices. A dollar store and a supermarket each
count as one record, and the question of what is actually purchasable in these places needs a different
source.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, and 2020 Decennial Census (DHC,
table P1) population by ZCTA. Analysis uses 611,164 stores with usable coordinates; a store counts as
active in a year if an authorization covered 31 December. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post5.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post5.html", DIR / "post5-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post5.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
