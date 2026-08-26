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
    ru = d["rural"]
    mix = d["ownership_mix"]
    den, tl = d["density"], d["total_loss"]
    s2 = d["series"].get("post2", {})
    entry_pct = abs(round(100 * (s2["drivers"]["new_after"] / s2["drivers"]["new_before"] - 1))) \
        if s2 else 55
    surv = d["series"].get("post1", {}).get("survival", [])
    dollar_surv = round(100 * next((r["rate"] for r in surv
                                    if r["format"] == "Dollar Store"), 0.782))

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{mix['chain']['share_2006']:.0f}% → {mix['chain']['share_2025']:.0f}%",
          "label": "chains' share of every SNAP retailer in the country, 2006 to 2025"},
         {"value": f"{grp['lost']:,}",
          "label": "ZIP codes lost their last SNAP-authorized chain pharmacy since 2021"},
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
        title="Dollar and convenience stores grew. Grocery and pharmacy did not.",
        subtitle="SNAP-authorized stores across the 976 pharmacy-loss ZIP codes")

    fmix, twn, gt = d["mix"], d["towns"], d["grocer_test"]
    fig(2, "mix-2006-2025",
        "Share of SNAP-authorized stores by format across the "
        f"{grp['lost']:,} pharmacy-loss ZIP codes, 2006 against 2025.",
        figures.pies_png,
        [{"title": y,
          "slices": [{"label": "convenience", "value": fmix[y]["convenience"], "slot": 3},
                     {"label": "grocery", "value": fmix[y]["grocery"], "slot": 4},
                     {"label": "chain pharmacy", "value": fmix[y]["pharmacy"], "slot": 2},
                     {"label": "dollar", "value": fmix[y]["dollar"], "slot": 1}]}
         for y in ("2006", "2025")],
        title="Grocery and pharmacy were half of this retail. Now they are under a third.",
        subtitle=f"share of SNAP-authorized stores, {grp['lost']:,} pharmacy-loss ZIP codes")

    sp = d["spread"]

    def _box(k, lab, slot):
        s = sp[k]
        return {"label": f"{lab}   {s['n']:,}", "slot": slot,
                **{q: s[q] for q in ("p10", "p25", "median", "p75", "p90")}}

    fig(3, "pharmacy-size",
        "ZIP code population (2020 census) for the ZIP codes that lost their last chain pharmacy "
        "against those that kept one.",
        figures.box_png,
        [_box("lost_pharmacy", "lost pharmacy", 2), _box("kept_pharmacy", "kept pharmacy", 0)],
        title="Smaller places lost their chain pharmacy",
        subtitle="ZIP code population, 2020 census")

    fig(4, "grocery-size",
        "ZIP code population (2020 census) for the ZIP codes that lost their last grocery store of "
        "any size against those that kept one.",
        figures.box_png,
        [_box("lost_grocer", "lost grocer", 2), _box("kept_grocer", "kept grocer", 0)],
        title="And far smaller places lost their grocery store",
        subtitle="ZIP code population, 2020 census")

    md = f"""# Twenty years, one pattern

*SNAP-authorized retailers, 2006–2025, with 2020 census population by ZCTA. The last chapter; an epilogue follows.*

**{mix['chain']['share_2006']:.0f}% → {mix['chain']['share_2025']:.0f}%** chains' share of every SNAP retailer in the country, 2006 to 2025.
**{grp['lost']:,}** ZIP codes lost their last SNAP-authorized chain pharmacy since 2021.
**{den['lost_no_grocery']['median_pop']:,}** median population of those that now have no grocery at all.

![Headline figures](images/00-key-figures.png)

---

We are nearing the end of our coverage of the history of retail SNAP authorizations. Today is the
penultimate chapter — the one where everything comes together — before tomorrow's closing piece, which
looks forward to where we could be headed.

This is the first time we have devoted so much time to one topic. Maybe you are ready to move on to
things that feel more relevant to you: the war, gas prices, inflation, labor data. There's no shame in
that, and we can see it in the open and click stats on this series against those other topics.

But let's be real. This is food we are talking about. Try going a day without it and see what else
matters to you. The people we are writing this for don't have the luxury of reading it. They are
thinking about where their next meal comes from, or how to feed their family tonight. How many other
problems wouldn't be problems if we could just feed Americans properly? We will never know until we
fix the food problem. That is why we have devoted eight days to it.

Those of us who don't have to worry about where our next meal comes from are the ones with the power
to end food insecurity for others. We just have to make it our problem. Step one is getting educated
about how this all works. So stick with us. We are almost there.

---

To connect all the dots, let's go back to where we left off yesterday — the **{grp['lost']:,} ZIP
codes** that lost their last SNAP-authorized chain pharmacy between 2021 and 2025. For these ZIP
codes, here is the trend of authorized SNAP food stores over twenty years.

![{figs["twenty-year-arc"]['caption']}](images/{figs["twenty-year-arc"]['file']})

Dollar stores went from {arc['dollar'][0]:,} to {arc['dollar'][-1]:,} — **{dollar_pct:+}%**.
Convenience stores went from {arc['conv'][0]:,} to {arc['conv'][-1]:,}, up {ac['conv_pct']:.1f}%.
Grocery of every size went the other way, {arc['groc'][0]:,} down to {arc['groc'][-1]:,}, a fall of
{abs(ac['groc_pct']):.1f}%. Pharmacies peaked at {ac['drug_peak']:,} in {ac['drug_peak_year']} and are
now at zero.

Look at what that does to the mix. In 2006 convenience and grocery were essentially level in these
places, and grocery outnumbered dollar stores by roughly ten to one. Today convenience outnumbers
grocery by nearly two to one, and grocery leads dollar by only about two to one. Two formats that
began level, and diverged. The direction of travel is unambiguous.

## USDA's assumptions don't hold up against reality

It's worth pausing on the stark contrast between what these places had in 2006 and what they have now.
To make it hit home, here is the mix in two pictures.

![{figs["mix-2006-2025"]['caption']}](images/{figs["mix-2006-2025"]['file']})

Look at the compression in grocery stores and chain pharmacies. Together those two were
**{fmix['2006']['groc_drug_pct']:.0f}%** of all the SNAP-authorized food retail in these ZIP codes in
2006 — more than half. Today they are **{fmix['2025']['groc_drug_pct']:.0f}%**. The total number of
stores went up over those twenty years, from {fmix['2006']['total']:,} to {fmix['2025']['total']:,}.
There is more retail here than there was. There is just less of the kind that sells a week of
groceries.

Which means these ZIP codes have more places to shop offering a narrower selection of food. We keep
harping on this because of the dissonance between the theory USDA cooked up in its Thrifty Food Plan —
a way, on paper, for a family of four to eat a healthy diet on about $229 a week — and the access
those families actually have to a store where that diet can be bought. If anything comes
out of this series, let it be the wake-up call USDA needs: get out of the spreadsheets and into the
real stores of the vulnerable Americans it claims to support.

That is the aggregate. Here is what it looks like in one place. {twn[0]['city']},
{twn[0]['state']} — a ZIP code of {twn[0]['pop']:,} people — had {twn[0]['then']['groc']} grocery
stores, {twn[0]['then']['pharmacy']} chain pharmacy, {twn[0]['then']['dollar']} dollar stores and
{twn[0]['then']['conv']} convenience stores in 2006. Today it has {twn[0]['now']['conv']} convenience
stores and {twn[0]['now']['dollar']} dollar stores, and neither a grocery store nor a chain pharmacy.

{twn[6]['city']}, {twn[6]['state']} is smaller — {twn[6]['pop']:,} people — and had one of each in
2006: a grocery store, a chain pharmacy, a dollar store, a convenience store. It now has
{twn[6]['now']['conv']} convenience stores and {twn[6]['now']['dollar']} dollar stores. Twice as many
food retailers as it had, and not one of them sells a week of groceries. {twn[5]['city']},
{twn[5]['state']}, population {twn[5]['pop']:,}, had the same four and is down to a single convenience
store and a single dollar store. {twn[2]['city']}, {twn[2]['state']} has {twn[2]['pop']:,} residents,
{twn[2]['now']['conv']} convenience stores and {twn[2]['now']['dollar']} dollar store.

Eight ZIP codes in this group had all four formats in 2006 and have neither a grocery store nor a
chain pharmacy today. They are not exotic places. They are in Ohio, Pennsylvania, West Virginia, Michigan and
Arkansas.

## The dollar stores did not do this

Before we move on, we wanted to check one thing. Did the surge in dollar stores and convenience
stores push the grocers out? Or did these formats come to the rescue, filling a void that was already
forming?

The answer is that we cannot blame the dollar stores for the demise of the grocers. Nationally,
**{gt['lost_last_grocery']['total']:,} ZIP codes** had a grocery store in 2006 and have none today.
**{gt['lost_last_grocery']['never_pct']:.0f}% of them never had a dollar store at all** —
{gt['lost_last_grocery']['never_dollar']:,} places that lost their grocery with nothing of the sort in
town to blame.

Where dollar stores did arrive, grocery held up better, not worse. Take every ZIP code that had a
grocery store in 2006: the ones that gained a dollar store since are up
{gt['with_dollar']['pct']:.1f}% in grocery stores, and the ones that did not are down
{abs(gt['without_dollar']['pct']):.1f}%. That is not proof the dollar store helps — these chains open
where the customers already are, and that alone would produce the same pattern — but it is the
opposite of what pushing someone out looks like.

If anything, it very much appears access to food in these places could have been a good deal worse
had the smaller formats not come to town. They did not take the grocery store. They are just most of
what is standing now that it has gone.

## What these places actually have in common

So if the dollar store did not do it, what did? The distinguishing feature of these places is not
what arrived. It is how small they are.

Start with the pharmacies. The ZIP codes that lost their last chain pharmacy have a median population
of **{sp['lost_pharmacy']['median']:,}**. The ones that kept theirs, **{sp['kept_pharmacy']['median']:,}**.
The two overlap — plenty of large ZIP codes lost a pharmacy — but the whole distribution sits lower.

![{figs["pharmacy-size"]['caption']}](images/{figs["pharmacy-size"]['file']})

Now the grocery stores, where it is not a shift but a chasm. The ZIP codes that lost their last
grocery store of any size have a median population of **{sp['lost_grocer']['median']:,}**. Half of
them fall between {sp['lost_grocer']['p25']:,} and {sp['lost_grocer']['p75']:,} people. Half of the
ones that kept a grocery store fall between {sp['kept_grocer']['p25']:,} and
{sp['kept_grocer']['p75']:,}. A grocery store needs more people under it than a pharmacy does, and it
goes first when they are not there.

![{figs["grocery-size"]['caption']}](images/{figs["grocery-size"]['file']})

The two charts are not drawn from the same pool, which is worth saying plainly. The pharmacy one
starts from ZIP codes that had a chain pharmacy in 2021 — a bar that already requires a certain number
of people. The grocery one starts from any ZIP code that had a grocery store in 2006, and only
{gt['lost_grocery_ever_had_rx_pct']:.0f}% of the ones that lost theirs ever had a chain pharmacy at
all. A place can be far too small for a Walgreens and still have had a grocery store.

[[CLOSING PARAGRAPH FOR THIS SECTION — Eric]]

## What is at stake

In **{tl['no_grocery']}** of these ZIP codes the only SNAP-authorized food retail left is a dollar store
or a convenience store. In **{tl['no_snap_retail_at_all']}** there is no SNAP-authorized retailer of any
kind. A household with an EBT card in those places is choosing among shelf-stable groceries, or driving.

That is the part of this that should be hard to sit with. Nothing here was done to these places. No one
decided they should have less. Each closure was, on its own terms, a rational decision by someone
reading their own numbers — and the sum of all of them is a town of six thousand with a dollar store
and nothing else. A competitor can be regulated. A merger can be blocked. There is no equivalent move
against arithmetic that stops working below a certain population.

That is where the measurement ends. It leaves a question about policy that this data cannot settle on its
own, and a rule that changes the answer in a few months. Both are taken up in the epilogue that follows
this piece.

## Limits

Every figure here counts **SNAP authorizations**, not storefronts. For the pharmacy chains those are nearly the same thing: Walgreens held 7,800 authorizations at the end of 2024 against the 8,454 US stores its own annual report counted four months earlier. For independents they are not the same, and this series does not treat them as such.

**The town examples count chain pharmacies only**, the same brand list the rest of this series uses.
A town shown here without a pharmacy may still have an independent one; this data cannot see it, for
the coverage reason set out in Day 5. The same goes for a grocery store that is not SNAP-authorized.

The control group is ZIP codes that had a chain pharmacy in 2021 and kept one. It is not a matched
sample: the two groups differ in population, which is the finding rather than a nuisance. Read the
comparison as descriptive, not causal.

Counties are classified by their **2023 Rural-Urban Continuum Code**, as in Day 4. A ZIP code does not
nest inside a county, so each is assigned the modal county of the stores recorded in it; one straddling
the metro line goes to whichever side holds more of them.

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
