"""Assemble reports/post5/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post5.json"
# Shared figures come from the fuel chapter's own output so the two pieces
# cannot disagree about a number they both quote.
FUEL = ROOT / "reports" / "data" / "post6.json"
DIR = ROOT / "reports" / "post5"
IMG = DIR / "images"


def main():
    d = json.loads(SRC.read_text())
    d6 = json.loads(FUEL.read_text()) if FUEL.exists() else {}
    _fs = {r["segment"]: r for r in d6["survival"]}
    # Keyed by post 6's segment names, without defaults: a rename should break
    # the build rather than publish a stale number.
    f_ff = _fs["chains that sell fuel"]["rate"]
    f_do = _fs["dollar stores"]["rate"]
    f_mult = d6["stock_change"]["chains that sell fuel"]["multiple"]
    _f = d6["stock_change"]["chains that sell fuel"]
    f_pct = round(100 * (_f["y2025"] / _f["y2006"] - 1))
    dollar_pct = round(100 * (d["arc"]["dollar"][-1] / d["arc"]["dollar"][0] - 1))
    f_unb = _fs["single-owner stores"]["rate"]
    _mu = d6["fuel_margin"]["companies"]["Murphy USA"]
    f_pre, f_post = _mu["pre_mean"], _mu["post_mean"]
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
         {"value": f"{dollar_pct:+}%",
          "label": "change in dollar stores in those same ZIP codes since 2006"},
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
        ylabel="SNAP-authorized stores",
        title="Dollar stores rose as everything else fell",
        subtitle="SNAP-authorized stores across the 976 pharmacy-loss ZIP codes")

    fig(2, "presence-vs-control",
        "What each group of ZIP codes has in 2025.",
        figures.table_png, ["In 2025, the ZIP has...", "Lost pharmacy", "Kept pharmacy"],
        [[p["label"], f"{p['lost_pct']}%", f"{p['kept_pct']}%"] for p in pres],
        highlight_row=len(pres) - 1,
        title="These places look like the control group",
        subtitle="share of ZIP codes with each kind of store, 2025")

    fig(3, "growth-vs-control",
        "Change in store counts 2021 to 2025, in ZIP codes that lost their last chain pharmacy "
        "against those that kept one.",
        figures.hbar_png, [
            {"label": "dollar, lost pharmacy", "value": gr["lost"]["dollar_pct"], "slot": 2},
            {"label": "dollar, kept pharmacy", "value": gr["kept"]["dollar_pct"], "slot": 0},
            {"label": "convenience, lost pharmacy", "value": gr["lost"]["conv_pct"], "slot": 2},
            {"label": "convenience, kept pharmacy", "value": gr["kept"]["conv_pct"], "slot": 0}],
        suffix="%",
        title="Dollar stores grew slower where the pharmacy left",
        subtitle="change in store counts, 2021 to 2025")

    fig(4, "median-population",
        "Median 2020 census population of the ZIP code (ZCTA), by group.",
        figures.hbar_png, [
            {"label": "lost pharmacy", "value": den["lost"]["median_pop"], "slot": 2},
            {"label": "kept pharmacy", "value": den["kept"]["median_pop"], "slot": 0},
            {"label": "lost, and no grocery left",
             "value": den["lost_no_grocery"]["median_pop"], "slot": 2}],
        title="What these places share is being small",
        subtitle="median ZIP code population, 2020 census")

    fig(5, "small-zip-share",
        "Share of ZIP codes below population thresholds, by group.",
        figures.hbar_png, [
            {"label": "lost pharmacy, under 10k", "value": den["lost"]["under_10k_pct"], "slot": 2},
            {"label": "kept pharmacy, under 10k", "value": den["kept"]["under_10k_pct"], "slot": 0},
            {"label": "lost pharmacy, under 5k", "value": den["lost"]["under_5k_pct"], "slot": 2},
            {"label": "kept pharmacy, under 5k", "value": den["kept"]["under_5k_pct"], "slot": 0}],
        suffix="%",
        title="A third have fewer than ten thousand people",
        subtitle="share of ZIP codes below each population line")

    md = f"""# The pharmacy left. The grocery left. Two formats stayed.

*SNAP-authorized retailers, 2006–2025, with 2020 census population by ZCTA. The last in this series.*

**{grp['lost']:,}** ZIP codes lost their last SNAP-authorized chain pharmacy since 2021.
**{dollar_pct:+}%** change in dollar stores in those same ZIP codes since 2006.
**{den['lost_no_grocery']['median_pop']:,}** median population of those that now have no grocery at all.

![Headline figures](images/00-key-figures.png)

---

The five earlier pieces each followed one format. Dollar stores almost never leave the program. Small
grocers left in numbers, and mostly stopped being replaced. Pharmacy chains held flat for years and
then collapsed. Read on their own they are unrelated retail stories.

They are not unrelated in the places where they land. Take the **{grp['lost']:,} ZIP codes** that lost their last SNAP-authorized chain pharmacy between 2021 and 2025. Now look at every other kind of food store in those same places, over twenty years.

![{figs["twenty-year-arc"]['caption']}](images/{figs["twenty-year-arc"]['file']})

Dollar stores went from {arc['dollar'][0]:,} to {arc['dollar'][-1]:,} — **{dollar_pct:+}%**.
Grocery of every size went from {arc['groc'][0]:,} to {arc['groc'][-1]:,}, down
{abs(ac['groc_pct']):.0f}%. Pharmacies peaked at {ac['drug_peak']:,} in {ac['drug_peak_year']} and are
now at zero. In 2006 these places had roughly ten times as many grocery stores as dollar stores. Today
grocery outnumbers dollar by about two to one, and the direction of travel is unambiguous.

## The obvious explanation is wrong

The natural reading is substitution: dollar stores squeezed the others out. It is worth stating plainly
that the data does not support it, because it is the interpretation everyone reaches for first —
including me.

Three tests, all using a control group of the {grp['kept']:,} ZIP codes that had a chain pharmacy in
2021 and still have one. Without that comparison, every number here looks like one store pushing out another. Dollar stores grew almost everywhere, so you need a control group to see anything at all.

**First: presence is identical.** Dollar and convenience stores are no more common where the pharmacy
went than where it stayed.

![{figs["presence-vs-control"]['caption']}](images/{figs["presence-vs-control"]['file']})

**Second: growth was slower, not faster.** If dollar stores were moving into vacated ground you would
expect the opposite.

![{figs["growth-vs-control"]['caption']}](images/{figs["growth-vs-control"]['file']})

**Third, and decisive: the dollar stores were already there.** Of the {seq['base']:,} ZIP codes,
**{seq['had_before_pct']}%** already had a dollar store in 2021, before the pharmacy left. Only
{seq['arrived_after']} — {seq['arrived_after_pct']}% — gained their first one afterwards. Nobody moved in
to fill a gap. They were neighbours for years.

The timing does not work either. Pharmacy authorizations were flat from 2016 to 2021, then fell off after 2022. That tracks opioid lawsuits, drug pricing, and Rite Aid's bankruptcy. Dollar stores opened at a near-constant rate for sixteen years, through all of it.

## What these places actually have in common

The distinguishing feature is not what arrived. It is how small they are.

![{figs["median-population"]['caption']}](images/{figs["median-population"]['file']})

Median population in a ZIP that lost its pharmacy is **{den['lost']['median_pop']:,}**, against
**{den['kept']['median_pop']:,}** where the pharmacy survived. And among those that have also lost every
grocery store, the median is **{den['lost_no_grocery']['median_pop']:,} people**.

![{figs["small-zip-share"]['caption']}](images/{figs["small-zip-share"]['file']})

A third of the pharmacy-loss ZIPs have fewer than ten thousand residents, against a tenth of the
control. One in eight has fewer than five thousand.

That is the thread. **A supermarket needs volume. A chain pharmacy needs prescription volume. A dollar store needs neither.** Its whole model is a small box, few staff, a narrow range, and no fresh food to spoil. That is exactly why it works in a town of six thousand where a grocery store cannot.

And it is not the only format built that way. The gas station chapter found a second one, and it lasts just as well. **{f_ff}% of convenience chains that sell fuel** from the 2008–2012 group were still authorized in 2025. For dollar stores it was {f_do}%. That is a gap of well under one point. Those chains also added {f_pct:+}% over the twenty years. So naming only dollar stores would leave out half the answer.

Read that way, the pieces in this series stop being coincidences. They become one story told from several angles.

- Small grocery's collapse was a collapse in **new stores**. Sign-ups fell {entry_pct}%. The 2018 stocking rule asks every store for a fixed amount of inventory, which is a large demand on a small shop and no demand at all on a big one. In USDA's own categories the fall sorted by exactly that: new sign-ups dropped 58% for small grocers, while the largest grocery category grew 8%.
- Dollar stores' advantage was never fast opening. It was that **{dollar_surv}% stay** — a format cheap
  enough to survive where others cannot.
- Fuel-forward convenience chains match that staying power, and after 2020 they gained something dollar
  stores did not: fuel margins roughly doubled and stayed there. Murphy USA's went from {f_pre} to
  {f_post} cents a gallon.
- Pharmacies were removed by forces of their own, but they were removed **from the thinnest markets
  first**.

No one pushed anyone out. Several separate pressures pushed the same way. The formats left standing were the ones with the lowest cost per location: the dollar store and the gas station. They arrived at the same place from opposite ends of retail. That is harder to fix than a rival would be. If one competitor were driving this, there would be a competitor to regulate.

## What is at stake

In **{tl['no_grocery']}** of these ZIP codes the only SNAP-authorized food retail left is a dollar store
or a convenience store. In **{tl['no_snap_retail_at_all']}** there is no SNAP-authorized retailer of any
kind. A household with an EBT card in those places is choosing among shelf-stable groceries, or driving.

There is a second cost this data cannot measure, and it should not go unsaid. For many people a pharmacist is the easiest health professional to reach. They check a drug interaction, take a blood pressure, answer a question that would otherwise need an appointment. When the last pharmacy in a small town closes, that goes too. These records count SNAP
authorizations; they say nothing about prescriptions or clinical advice, and the pharmacy desert
literature is the place to look for that. But it is the same buildings and the same towns.

That is where the measurement ends. It leaves a question about policy that this data cannot settle on its
own, and a rule that changes the answer in a few months. Both are taken up in the epilogue that follows
this piece.

## Limits

Every figure here counts **SNAP authorizations**, not storefronts. For the pharmacy chains those are nearly the same thing. Walgreens' authorizations run at 0.97 of its own reported store count. For independents they are not the same, and this series does not treat them as such.

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
table P1) population by ZCTA. Analysis uses 656,868 stores with usable coordinates; a store counts as
active in a year if an authorization covered 31 December. Fuel-chain survival and margin figures are from
the gas station chapter. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post5.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post5.html", DIR / "post5-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post5.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
