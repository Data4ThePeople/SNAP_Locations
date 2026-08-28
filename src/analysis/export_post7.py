"""Assemble reports/post7/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures, panel
from config import ROOT

LADDER = ["Small Grocery Store", "Convenience Store", "Combination Grocery/Other",
          "Medium Grocery Store", "Supermarket", "Large Grocery Store"]

SRC = ROOT / "reports" / "data" / "post7.json"
DIR = ROOT / "reports" / "post7"
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

    P = d["policy"]
    tfp, o, n, im = P["tfp"], P["old_standard"], P["new_standard"], P["impact"]
    h = P["history"]
    wc = d["worst_case"]
    v, i = P["variety"], P["industry"]
    nfa, dg = P["need_for_access"], P["dollar_general"]
    trading = P["trading"]
    pre, tm = d["precedent"], d["thin_markets"]
    surv = {r["segment"]: r for r in d["survival"]}
    eu = {r["store_type"]: r for r in d["entry_change_usda"]}
    den, tl = tm["density"], tm["total_loss"]

    # One definition, three renderings: the PNG below, the live text in the
    # markdown, and the .ledger block build_post7 makes from that text. They
    # used to be written out separately and had drifted into saying different
    # things, and the longer hand-written values overflowed the HTML's columns.
    # The lead card is the piece's own finding rather than USDA's share of
    # retailers: people, not percentages. The conditional does the work of
    # keeping a ceiling from reading as a forecast, so it stays in the label.
    LEDGER = [
        {"value": f"{wc['stages']['conv']['population']/1e6:.1f} million",
         "label": "people whose ZIP code would have no SNAP retailer at all "
                  "if convenience stores drop out"},
        {"value": f"${im['cost_year_one_small']}",
         "label": "what USDA estimates it costs a small store to comply in the "
                  "first year"},
        {"value": n["compliance"].replace(", 2026", ""),   # "November 4, 2026" -> "November 4"
         "label": "the 2026 date by which every SNAP retailer has to meet it"},
    ]
    ledger_md = "\n".join(f"**{it['value']}** {it['label']}." for it in LEDGER)

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png, LEDGER)

    # ---- worst-case figures -------------------------------------------------
    from analysis import usmap
    from analysis.post4_pharmacy import DRUG_BRANDS
    _con = panel.build()
    _D = ",".join(f"'{b}'" for b in DRUG_BRANDS)
    _A = ("f.auth_date <= DATE '2025-12-31' AND "
          "(f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')")

    _con.execute(f"""CREATE OR REPLACE TEMP TABLE _wc AS
        SELECT DISTINCT p.record_id, p.zip_code AS zip, p.format,
               p.longitude AS lon, p.latitude AS lat
        FROM panel p JOIN fact_spell f
          ON f.record_id = p.record_id AND NOT f.date_anomaly
        WHERE {_A} AND p.zip_code IS NOT NULL AND length(p.zip_code) = 5""")

    # Convenience stores only. Chain pharmacies show no exposure to this rule
    # and adding them moves the count by 90 ZIP codes; dollar stores are the
    # tail, carried in prose rather than drawn as though it were the base case.
    _keep = ("zip IN (SELECT zip FROM _wc WHERE format <> 'Convenience Store')")

    def _zips(where):
        """One point per ZIP code, at the mean position of its stores.

        Mapping stores could not carry this: taking half the dots out of a
        232,000-dot field still leaves dots everywhere. Places is the unit the
        consequence is actually measured in, and it is a sparse enough field to
        read.
        """
        rows = _con.execute(f"""
            SELECT avg(lon), avg(lat) FROM _wc WHERE {where}
              AND lon BETWEEN {usmap.LO48[0]} AND {usmap.LO48[2]}
              AND lat BETWEEN {usmap.LO48[1]} AND {usmap.LO48[3]}
            GROUP BY zip""").fetchall()
        xy = usmap.albers([r[0] for r in rows], [r[1] for r in rows])
        return xy, len(rows)

    _kept_xy, _n_kept = _zips(_keep)
    _gone_xy, _n_gone = _zips(f"NOT ({_keep})")

    # The body quotes the dot count off the map, so it has to quote the
    # population of those same ZIP codes. The pipeline's 5.3 million belongs to
    # all 2,871 nationally; the map draws the lower 48, and pairing the two
    # would attribute the national population to a smaller set of dots.
    from analysis.post5_synthesis import zcta_population
    _pop = zcta_population()
    _gone_zips = [r[0] for r in _con.execute(f"""
        SELECT DISTINCT zip FROM _wc WHERE NOT ({_keep})
          AND lon BETWEEN {usmap.LO48[0]} AND {usmap.LO48[2]}
          AND lat BETWEEN {usmap.LO48[1]} AND {usmap.LO48[3]}""").fetchall()]
    _gone_pop = sum(_pop[z] for z in _gone_zips if z in _pop)
    assert len(_gone_zips) == _n_gone, (len(_gone_zips), _n_gone)
    print(f"  mapped: {_n_gone:,} ZIP codes, {_gone_pop:,} people "
          f"(national {wc['stages']['conv']['zips_to_zero']:,} / "
          f"{wc['stages']['conv']['population']:,})")
    fig(1, "worst-case-map",
        f"Dot map of the lower 48, one dot per ZIP code. Faint grey marks the {_n_kept:,} "
        f"ZIP codes that would still have a SNAP-authorized retailer if every convenience "
        f"store gave up its authorization; pink marks the {_n_gone:,} that would have none, "
        f"scattered across the interior and the rural East.",
        figures.map_pair_png,
        [{"title": "", "xy": _kept_xy, "color": figures.MUTED,
          # figures.MUTED is the series' context grey and is contrast-checked
          # against this ground; the hand-picked darker grey it replaced was
          # near-invisible. The pink still reads as figure because it is the
          # only chromatic layer and sits at nearly twice the dot size.
          # 19,074 grey dots against 2,782 pink: at equal weight the grey wins
          # on count alone. Grey is dimmed and shrunk, pink enlarged and set
          # opaque, so the ground stays legible without becoming the figure.
          "layers": [{"xy": _kept_xy, "color": "#4d565e", "size": 1.3, "alpha": 0.85},
                     {"xy": _gone_xy, "color": figures.S[4], "size": 3.6, "alpha": 1.0}],
          "keys": [{"label": f"{_n_kept:,} ZIP codes keep a SNAP retailer",
                    "color": figures.MUTED},
                   {"label": f"{_n_gone:,} would have none", "color": figures.S[4]}]}],
        width=6.6,
        title="The places that would be left with no SNAP retailer",
        subtitle="one dot per ZIP code, lower 48",
        note=f"not a forecast — the ceiling, if every convenience store gave up its SNAP "
             f"authorization · lower 48 shown, {wc['stages']['conv']['zips_to_zero']:,} "
             f"ZIP codes nationally")

    fig(2, "worst-case-bands",
        "Share of ZIP codes that would be left with no SNAP-authorized retailer, by the ZIP code's "
        "2020 census population, if every convenience store gave up its SNAP authorization.",
        figures.hbar_png,
        [{"label": f"{b['band']}   {b['zeroed']:,} of {b['zips']:,}", "value": b["pct"], "slot": 2}
         for b in wc["bands"]],
        suffix="%",
        title="It lands almost entirely on the smallest places",
        subtitle="share of ZIP codes left with no SNAP retailer if convenience stores "
                 "drop from SNAP program, by population")

    md = f"""# Sizing the risk to SNAP of the imminent stocking rule changes

*An epilogue. A stocking standard twelve years in the making, the guidance that still has not
arrived, and a map of who would bear the risk if it goes wrong.*

{ledger_md}

![Headline figures](images/00-key-figures.png)

---

This is an epilogue. Seven days over twenty years of data left us with one finding: your experience of
America depends very much on where you live. Yes, we knew that already. But we spent the week steeped
in what it does to the most foundational thing people need each day: healthy food.

Now we look forward. The path of least resistance is for this to get worse. But this post is about
something narrower — one specific rule change, months away, that could severely impair food access in
nonmetro areas.

It is a risk, not a certainty. It's like Y2K. Maybe the rule lands and nothing happens. Or maybe
SNAP-authorized retail gets cut by a third. The scary part is that we don't know.

## Stocking rule — background

The rule that lands in November was written twelve years ago, and the story of why it took twelve
years is most of the reason to pay attention to it.

Congress raised the bar itself. Section 4002 of the
**[{h['directive_act']}]({h['directive_url']})**, signed {h['directive_date']}, rewrote the definition
of a retail food store so that a store had to offer "a variety of at least 7 foods" in each of the four
staple categories ({n['category_names']}), "including perishable foods in at least 3 of the
categories." Before that the statute named no number at all; the floor of three varieties was USDA's
own regulation, not an act of Congress.

USDA wrote the matching rule two years later. *[Enhancing Retailer Standards in
SNAP]({h['rule_2016_url']})* published {h['rule_2016_published']} at **{h['rule_2016_cite']}**,
effective {h['rule_2016_effective']}, with existing stores given until
{h['rule_2016_existing_stores']} to comply. Seven varieties in each of four categories, three stocking
units of each, a perishable food in three categories: 84 units in all.

Then Congress blocked its own instruction. [Section 765 of the Consolidated Appropriations Act,
2017]({h['rider_url']}) (P.L. 115-31), signed {h['rider_date']}, barred the department from spending
any money to "implement, administer, or enforce the 'variety' requirements" of that rule.

But read the rest of the sentence and it is not a repeal. It is a condition. The prohibition holds
*until* the Secretary "amends the definition of the term 'variety' ... to increase the number of items
that qualify as acceptable varieties in each staple food category." Until then, USDA was ordered to
apply the standard in force the day before the 2014 Farm Bill passed.

That fallback has governed every SNAP retailer for the nine years since, and it is the one still in
force this morning: **{o['varieties_per_category']} varieties** in each of four categories,
{o['units_per_variety']} stocking units of each — **{o['total_items']} units** — with a perishable food
in {o['perishable_categories']} categories rather than three. The regulation on the books said
something else the whole time. The codified text still read seven varieties; the
{o['total_items']}-unit floor is what the rider made USDA actually enforce.

And the rider never went away. It has ridden every agriculture appropriations act since, including the
one signed {h['rider_latest_date']} that funds the government through this fiscal year, where it sits
at [{h['rider_latest']}]({h['rider_latest_url']}). What changed is that USDA finally met its condition.
It proposed a new framework for what counts as a distinct variety on {h['proposed_2025_date']}
([{h['proposed_2025_cite']}]({h['proposed_2025_url']})), and finalized it on {n['published']} at
**[{n['citation']}]({n['url']})** — effective {n['effective']}, with every authorized retailer required
to implement by **{n['compliance']}**.

So the thing arriving in November is not really a new stocking standard. It is the 2014 standard,
released. The unit count is not even new: USDA's 2016 rule computed the same
{n['total_items']} units this one does. Nine years of argument were about a single word, and the rule
that ends it is a rule about what "variety" means.

## What's a food?

We are **{P['days_to_implementation']} days** from implementation day. You would think that after
twelve years between the statute and its arrival, the details would be settled.

Give USDA its due: on the central question, they are. The rule defines a distinct variety at length
([{v['citation']}]({v['url']})), in a default rule plus three carve-out groups. Foods differ if they come from a
different plant, a different animal, or a different main ingredient. Different cuts of the same animal
are not separate varieties — the rule says so in as many words, listing "{v['cuts_of_meat']}" among
the things that do not count. So hamburger and steak are one protein, not two. Milk and cream are two,
because the rule states that "{v['cream']}." Shredded wheat and a loaf of bread are two, because
breakfast cereals and bread are named separately. USDA even published a worked answer for a compliant
protein shelf: {v['usda_protein_example']}.

So, your local Shell station is not going to have to stock goat meat.

Then, where is the problem? Two places.

**First, the framework has holes in the categories a small store lives on.** The rule makes "bread" a variety
and never says what bread is. Are tortillas bread? Bagels? Pita? It matters, because USDA's own worked
example for grains — {v['usda_grain_example']} — only reaches seven if corn tortillas are *not* bread.
The rule does not say. It then splits bread into whole grain and non-whole grain and defines whole
grain as products that "{v['whole_grain']}" — no threshold, no labeling test. Whether a store gets one
bread variety or two turns on reading an ingredient list against a standard with no number in it.
Where instant oatmeal, granola and muesli sit between raw grain, breakfast cereal and accessory food is
unstated. Whether oat milk and oat yogurt are one variety or two is unstated. Sandwiches made at a
commissary rather than in the store are unstated, and that was the question retailers raised most on an
industry webinar this month.

**Second, the guidance that would answer all of it has not arrived.** On the day the rule published,
[USDA's own page]({n['usda_page']}) said: "{v['guidance_promised']}" That was
{v['guidance_promised_date']}. Scroll to the bottom of [that page]({n['usda_page']}) and, as of last
night, it still reads *{v['page_updated_stamp']}*. Nothing has followed — no FAQ, no variety list, no policy memo, and no
further document in [the docket]({im['docket_url']}) in the {P['days_since_rule']} days since.

Meanwhile the two pages a store owner or a field inspector opens for the standard itself —
[retailer eligibility]({v['stale_pages'][0]}) and [staple foods]({v['stale_pages'][1]}) — still
describe the old rule. They still say {v['stale_pages_say']}, a statement the new rule reverses. Both
carry USDA's own banner: "{v['stale_banner']}"

The industry has noticed. On publication day the convenience store association said the rule
"[{i['nacs_day_one']}]({i['nacs_day_one_url']})." Three months later:
"[{i['nacs_august']}]({i['nacs_august_url']})." Its general counsel warned that the complexity
"{i['nacs_disputes']}." The association is circulating a letter asking USDA to {i['nacs_ask']}; an
amendment from {i['senate_sponsor']} to force that delay failed {i['senate_vote']} on
{i['senate_vote_date']}.

So roughly {i['cstores_snap']:,} convenience stores are {P['days_to_implementation']} days from a
compliance review against a standard whose reference material still describes the rule it replaced.

## Model the risk

Clear as mud, right? Look how many words it took us to answer a simple question — what's a food? And on
the parts a small store actually has to get right, we still have no answer. As such, we figured it
would be appropriate to just go ahead and model out the worst case scenario.

Please note: this is not a forecast. It is a modeled scenario. As we have written, all models are wrong. Some are
useful. This one is useful because we can see WHO bears the most risk if such a scenario were to
manifest.

Start with the format the evidence points at. Convenience stores are
**{wc['stores_by_group']['conv']:,} of the {wc['stores_total']:,}** SNAP-authorized stores in the
country — {100*wc['stores_by_group']['conv']/wc['stores_total']:.0f}% of them. They are the format the
rule's own preamble singles out, the one whose trade association is asking Congress for a delay, and
the one with the least room in a {i['cstore_sqft']:,}-square-foot box — where the perishable
requirement bites hardest. So take them out, and see where the cuts hurt the most.

The map below shows this. There are {_n_gone:,} pink dots on this map, representing the {_n_gone:,}
ZIP codes that would be left with no SNAP retailers if their convenience stores opted out of the SNAP
program. These ZIP codes are home to {_gone_pop/1e6:.1f} million Americans — {wc['stages']['conv']['population']/1e6:.1f} million
nationally, once you count Alaska, Hawaii and the stores we cannot place on a map.

![{figs["worst-case-map"]['caption']}](images/{figs["worst-case-map"]['file']})

Note that the dots rarely touch large cities. Instead the risk lies in the interior and the rural
East — the same geographic inequality finding we have stumbled upon throughout this entire series.

This next bar chart hammers this home directly. In ZIP codes with fewer than a thousand people,
**{wc['bands'][0]['pct']:.0f}%** would be left with no SNAP retailer at all. In ZIP codes above
twenty-five thousand, **{wc['bands'][-1]['pct']:.1f}%** would. The median ZIP code left with no SNAP
retailer holds {wc['median']['zeroed']['median_pop']:,} people; the median one that keeps at least one
SNAP retailer holds {wc['median']['kept']['median_pop']:,}.

![{figs["worst-case-bands"]['caption']}](images/{figs["worst-case-bands"]['file']})

This is the point of the model — it shows us that even if we don't end up with the worst case
scenario, we are likely to end up with greater geographic inequality.

## Accountability is patriotism?

No matter how much territory we cover, we keep coming back to one thing that is sorely missing —
accountability.

First, government is failing our American brothers and sisters living in more remote territories.
Don't blame capitalism. Capitalism is a tool — no different from a hammer, or AI. Without intervention
it leads to inequality, and that is just the way of things. But it doesn't have to be. Government sets
the rules of the game, and it can set them to unleash the benefits of capitalism for all. We have
drifted so far from that we now have not only an abdication of the responsibility, but elected
officials [of both parties]({trading['nyt_url']}) using their power to enrich themselves from this
broken system.

But there is another question here. I wonder how many elected officials know about the ambiguity in
this stocking regulation, or the risk their most vulnerable constituents face if it doesn't get ironed
out in a way that keeps retailers from dropping out of SNAP. Ignorance is not an excuse for inaction.
All this data is accessible at a moment's notice. It boils down to awareness, and there are only so
many moments in a day. If our lawmakers are focused on what stock to trade next, that is time taken
away from protecting Americans from hidden risks like this one.

So what can we do? Of course this is my own opinion, and my own frustration with a lack of
accountability that is spreading across America like a plague. But we will commit to tracking this
USDA database as it updates, and identifying the changes in SNAP retailers after this ruling hits, so
we all have the facts on how this plays out. And we will keep calling out lack of accountability when
we see it. If this resonates with you, share it with a friend. The more people that expect more from
those in power, the more likely we are to collectively drive the accountability Americans so sorely
need.

## Limits

**The {wc['stages']['conv']['population']/1e6:.1f} million is everyone who lives there, not everyone on SNAP.**
It is the 2020 census population of those ZIP codes; this file cannot see who uses the program. The map
draws the lower 48, which holds {_n_gone:,} of the {wc['stages']['conv']['zips_to_zero']:,} ZIP codes —
the rest are in Alaska and Hawaii or have no usable coordinates.

**This data cannot see inside a store.** Whether a given convenience store already clears the standard,
or could for less than USDA's estimate, is not knowable from an authorization file; that needs
shelf-level audit data such as NEMS-S. It is why this is a ceiling and not an estimate.

**The worst case is arithmetic, not a forecast.** It says nothing about how likely a format is to leave.
The "need for access" pathway at [{nfa['citation']}]({nfa['url']}) gives USDA wide discretion, and an
effort to protect rural stores could hold the count near the agency's own projection of
about {im['net_permanent_loss']:,}. That would be a good outcome and we would report it as one.

**We describe effects, not motives.** USDA's stated purpose is nutrition, and nothing here claims
otherwise. Note too that fewer stores does not by itself cut benefits, which are set against the
[Thrifty Food Plan]({tfp['url']}) price; any effect would run through households finding the program
harder to use, which this data cannot observe. The compliance-cost and store-loss figures are USDA's
own — we have not independently estimated either.

---

*Sources: [{tfp['source']}]({tfp['url']}). [{o['source']}]({o['url']}).
[{n['source']}]({n['url']}) (docket {n['docket']}, effective {n['effective']}, compliance
{n['compliance']}), and the [proposed rule]({h['proposed_2025_url']}) that preceded it at
{h['proposed_2025_cite']}. [{h['directive_act']}]({h['directive_url']}), {h['directive_cite']}, and the
2016 rule it produced at [{h['rule_2016_cite']}]({h['rule_2016_url']}). The rider in current law at
[{h['rider_latest']}]({h['rider_latest_url']}). Variety definition and need-for-access pathway at
[{nfa['citation']}]({nfa['url']}). [{im['source']}]({im['url']}). Trade association positions from
published statements by FMI and the National Grocers Association, the joint comments of NACS, NATSO and
SIGMA filed November 24, 2025, and NACS on
[{n['published']}]({i['nacs_day_one_url']}) and [August 10, 2026]({i['nacs_august_url']}).
{dg['source']}. {trading['nyt_source']}. Store-count and survival
figures from [SNAP Retailer Locator Historical
Data](https://www.fna.usda.gov/snap/retailer-locator/data), 2005–2025, published by USDA's Food and
Nutrition Administration — the Food and Nutrition Service until it was renamed on June 1, 2026 — using
656,868 stores with usable coordinates. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post7.md").write_text(md)
    # The archive is written by build_post7 from this markdown. Copying
    # reports/post7.html here copied whatever the LAST build produced, which
    # is how a stale draft ended up shipped as this chapter's archive.
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post7.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
