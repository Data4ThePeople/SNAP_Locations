"""Assemble reports/post1/ — markdown text, PNG figures, and the HTML archive.

Four figures, matching build_post1.py. See that module's docstring for the
correction on who actually got the 2016 stocking rule rolled back.
"""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post1.json"
DIR = ROOT / "reports" / "post1"
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
        return p

    surv = sorted(d["survival"], key=lambda r: -r["rate"])
    ds = next(r for r in surv if r["format"] == "Dollar Store")
    sg = next(r for r in surv if r["format"] == "Grocery (Small)")
    ss = next(r for r in surv if r["format"] == "Super Store")
    z, ctx, gap, cen = d["dollar_only_zip"], d["context"], d["survival_gap"], d["chain_census"]
    lap = d["lapse"]
    # Active on 31 December 2025; the largest single format in the file.
    conv_2025 = 117_055
    stock, yrs = ctx["Dollar Store"]["stock"], ctx["Dollar Store"]["years"]
    growth = stock[-1] / stock[0]
    growth_pct = round(100 * (growth - 1))
    lap_sg = next(r for r in lap if r["format"] == "Grocery (Small)")
    mix = d["ownership_mix"]
    m_cv = mix["Convenience Store"]

    picks = ["Dollar Store", "Supermarket", "Grocery (Medium)", "Grocery (Small)", "Super Store"]
    s_ctx = [{"name": "dollar stores" if p == "Dollar Store"
              else p.replace("Grocery ", "").strip("()").lower(),
              "values": ctx[p]["stock"], "slot": 2 if p == "Dollar Store" else 3 + i % 4}
             for i, p in enumerate(picks) if p in ctx]

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{growth_pct:+}%",
          "label": f"change in SNAP-authorized dollar stores since {yrs[0]}"},
         {"value": f"{100*ds['rate']:.0f}%",
          "label": "of dollar stores authorized in 2008-2012 are still authorized today"},
         {"value": f"{100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}%",
          "label": "of ZIP codes with a dollar store have no grocery store at all, "
                   f"up from {100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}% in {z[0]['yr']}"}])

    fig(1, "chain-census",
        "SNAP authorizations at the end of 2025 against each company's most recently reported "
        "store count, early 2025 to February 2026.",
        figures.table_png, ["Chain", "SNAP-authorized", "Reported stores", "Ratio"],
        [[c["brand"], f"{c['authorized']:,}", f"{c['reported']:,}", f"{c['ratio']:.2f}"]
         for c in cen],
        title="The SNAP counts match the companies' own, almost exactly",
        subtitle="SNAP authorizations, 31 Dec 2025 · company counts, early 2025 to Feb 2026")

    fig(2, "growth", "Stores authorized on 31 December of each year, by format.",
        figures.line_png, yrs, s_ctx, ylabel="stores authorized on 31 December",
        title="Dollar stores passed every grocery format")

    fig(3, "retention",
        "Share of the 2008–2012 entry cohort still authorized at the end of 2025. Counts are "
        "stores, not authorization spells, so a store that lapsed and returned is counted once.",
        figures.hbar_png,
        [{"label": r["format"], "value": 100 * r["rate"],
          "slot": 2 if r["format"] == "Dollar Store"
          else (1 if r["format"] == "Grocery (Small)" else 0)} for r in surv], suffix="%",
        title="Dollar stores stayed. Small grocers did not.",
        subtitle="share of the 2008-2012 cohort still authorized in 2025")

    fig(4, "dollar-only-zips",
        "ZIP codes with a SNAP-authorized dollar store and no grocery store. Grocery store here "
        "means any of USDA's grocery formats: supermarket, super store, or a large, medium, or "
        "small grocery store.",
        figures.line_png, [r["yr"] for r in z],
        [{"name": "ZIP codes", "values": [r["dollar_only"] for r in z], "slot": 2}],
        ylabel="ZIP codes with a dollar store and no grocery",
        title="More places now have a dollar store and no grocery store")

    ds_sp = d["dollar_only_split"]
    fig(5, "dollar-only-split",
        f"The {ds_sp['joined']:,} ZIP codes that joined the list between 2008 and 2024, split by "
        "whether an authorized grocery was ever there — checked on every 31 December in the "
        "window.",
        figures.hbar_png,
        [{"label": "never had an authorized grocery", "value": ds_sp["new_never"], "slot": 2},
         {"label": "had one — it left SNAP by 2024", "value": ds_sp["new_lost"], "slot": 1}],
        title="Most of these places never had an authorized grocery",
        subtitle=f"the {ds_sp['joined']:,} ZIP codes that joined the list, 2008-2024")

    dst = d["dollar_only_states"]
    tx = next(r for r in dst if r["state"] == "TX")
    pa = next(r for r in dst if r["state"] == "PA")
    fig(6, "dollar-only-states",
        "The walk from 2008 to 2024 for the ten states that added the most: the ZIP codes that "
        "left the list, the arrivals that never had an authorized grocery in the window, and the "
        "arrivals where a grocery left SNAP.",
        figures.table_png,
        ["State", "2008", "Left\nthe list", "New dollar\nstore, never\na grocery",
         "Grocery\nleft SNAP", "2024"],
        [[r["state"], f"{r['y2008']:,}", f"−{r['exited']:,}", f"+{r['new_never']:,}",
          f"+{r['new_lost']:,}", f"{r['y2024']:,}"] for r in dst],
        width=9.4,
        title="How each state got from 2008 to 2024",
        subtitle="dollar-store-only ZIP codes: start, movements, end",
        note="Left the list: nearly always because a grocery became authorized there. New dollar "
             "store, never a grocery: a dollar store arrived; the ZIP had no authorized grocery "
             "at any point, 2008–2024. Grocery left SNAP: the ZIP had an authorized grocery at "
             "some point and it left the program — some of these had a dollar store all along, "
             "most gained one too.")

    md = f"""# Dollar store domination

*SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records.
{d['headline']['dollar_2025']:,} dollar stores authorized at the end of 2025, against
{d['headline']['all_grocery_2025']:,} grocery stores of every size.*

**{growth_pct:+}%** change in SNAP-authorized dollar stores since {yrs[0]}.
**{100*ds['rate']:.0f}%** of dollar stores authorized in 2008–2012 are still authorized today.
**{100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}%** of ZIP codes with a dollar store have no
grocery of any size, up from {100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}% in {z[0]['yr']}.

![Headline figures](images/00-key-figures.png)

---

Yesterday's piece ended on a question. Small grocery is a small format that could not make the numbers
work. The dollar store is a small format too — same small box, narrow range, few staff. It did the
opposite.

## This time, an authorization is very nearly a store

Yesterday we had to be careful: when a small grocer leaves the SNAP file, the records cannot say
whether it closed or just stopped taking EBT. Dollar stores are a different case. Nearly all of them
belong to a handful of public chains — Dollar General, Dollar Tree, Family Dollar — and those
companies tell their investors exactly how many stores they run. So set the SNAP authorization
counts at the end of 2025 against the companies' own reported store counts:

![{figs["chain-census"]['caption']}](images/{figs["chain-census"]['file']})

Essentially every Dollar General and Dollar Tree in the country takes SNAP. Because the two counts
line up this closely, store openings and closings for these chains show through the SNAP file almost
one for one — something yesterday's data could not give us. We cannot say the two counts are the
same thing, but we hold very high conviction that they move together. Keep that in mind through
everything that follows: for dollar stores, authorization counts track store counts.

## They grew enormously

Dollar stores went from {stock[0]:,} SNAP-authorized stores in {yrs[0]} to {stock[-1]:,} in
{yrs[-1]}. That is a **{growth_pct:+}%** change, while no grocery format managed even a tenth of
that.

![{figs["growth"]['caption']}](images/{figs["growth"]['file']})

They are now the second most common kind of SNAP retailer in the country, behind only convenience
stores. There are {d['headline']['dollar_2025']:,} of them against
{d['headline']['all_grocery_2025']:,} grocery stores of every size combined.

## They kept their authorizations

But dollar stores didn't just have growth — they had growth and longevity. Take every retailer that
joined SNAP between 2008 and 2012, and ask how many are still in the program at the end of 2025. No
other format touches the dollar store.

![{figs["retention"]['caption']}](images/{figs["retention"]['file']})

**{100*ds['rate']:.0f}% of dollar stores are still authorized. Meanwhile, just {100*sg['rate']:.1f}% of small grocers are.** A dollar store from those years is **{gap['multiple']}× more likely** to still be in the
program. Even more impressive, dollar stores outlasted the super stores — the supercenters with more
scale in a single store than any other format — which kept {100*ss['rate']:.0f}% of theirs.

## The growth in dollar store concentration

You have likely heard the saying that there are three things that matter in real estate: location,
location, and location. Location matters just as much in data analysis — a national total says
little about anyone's lived experience.

So we asked the location question that piqued our curiosity: how has the number of ZIP codes with a
dollar store but no grocery store changed over the history of the data? The answer is in the chart
below:

![{figs["dollar-only-zips"]['caption']}](images/{figs["dollar-only-zips"]['file']})

In {z[0]['yr']}, there were just {z[0]['dollar_only']:,} ZIP codes with a dollar store and no
grocer. By {z[-1]['yr']} that had risen to **{z[-1]['dollar_only']:,}**. Put another way: of all
the ZIP codes that have a dollar store, the share with no grocer went from
{100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}% to
{100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}%. That means if you live in one of these
ZIP codes, cannot travel beyond it, and are on SNAP, you are buying your food at a dollar store or
a convenience store.

We initially made the mistake of reading this as a bad thing. But good and bad are relative
concepts. Included in those {z[-1]['dollar_only']:,} ZIP codes are towns that in {z[0]['yr']} had
no SNAP-authorized grocer and no dollar store — some had nothing but a gas-station convenience
store that took SNAP. For a town like that, the dollar store opening is a very good thing,
providing considerably more food options than a gas station carries.

So we did the math. Of the ZIP codes that joined this list between {z[0]['yr']} and {z[-1]['yr']},
{100*ds_sp['new_never']/ds_sp['joined']:.0f}% never had a grocer that accepted SNAP to begin with,
while {100*ds_sp['new_lost']/ds_sp['joined']:.0f}% had one at some point and it left the program:

![{figs["dollar-only-split"]['caption']}](images/{figs["dollar-only-split"]['file']})

The mix differs by state. Here is the walk from 2008 to 2024 for the ten states that added the
most — each starts with the ZIP codes it had, loses a few that left the list, and adds the two
kinds of arrivals:

![{figs["dollar-only-states"]['caption']}](images/{figs["dollar-only-states"]['file']})

Take Pennsylvania, the top row. It started {z[0]['yr']} with {pa['y2008']:,} ZIP codes that had a
dollar store and no authorized grocer. {pa['exited']} of those left the list — almost always the
good way, a grocery store becoming authorized there. Then {pa['new_never']:,} ZIP codes joined when
a dollar store opened somewhere that never had an authorized grocer, and {pa['new_lost']:,} more
joined where a grocery left SNAP. Net it out and Pennsylvania ends {z[-1]['yr']} at
{pa['y2024']:,}.

Texas leans hardest toward arrival: {tx['new_never']:,} of its new ZIP codes never had an
authorized grocery, against {tx['new_lost']:,} where a grocery left SNAP. Illinois leans the other
way — it is the only state on the list where groceries leaving SNAP outnumber dollar stores
arriving where none was.

## What it adds up to

Dollar stores ended up on both sides of a line everyone else has to choose.

They are **small where small pays**: a box that makes money in a town of a few thousand people, where a supermarket cannot. And they are **big where big pays**: a chain that works out how to clear USDA's stocking bar once, then spreads the cost of doing it across twenty thousand stores.

Put the two halves together and the growth stops being surprising. It is no wonder dollar stores have outgrown every grocery format in the country.

But hold on to the second half. Why is that bar low enough for a small box to clear? Partly because someone else fought to keep it there. The 2016 stocking rule would have raised it sharply. It was rolled back in May 2017 — by the **convenience store** industry, lobbying hard for its members. Dollar stores never led that campaign. They just got the benefit.

Which is where we go next: the country's **{conv_2025:,} convenience stores**, the single largest group
in this data, and how they have thrived without anything like the chain concentration dollar stores
enjoy. Only {m_cv['chain_2025']:.0f}% of them belong to a chain at all.

**Tomorrow: the convenience store.**

## Limits

Nothing here measures floor space, sales, or what is on the shelves. A dollar store and a supermarket
each count as one record.

**The chain-store check is what licenses closure language, and only for these chains.** For an
independent store an ended authorization may mean the shop closed or may mean it stopped taking EBT.
{100*lap_sg['rate']:.1f}% of small grocers lost their authorization and later regained it, median gap
{lap_sg['median_gap_days']} days — those were open the whole time.

Store-level SNAP spending is not public. A 2019 Supreme Court case put those figures under a FOIA
exemption, so we can see where authorized stores are but never how much any one of them takes in.

In the ZIP code split, "a grocery left SNAP" means exactly that — its authorization ended. The
store itself may still trade without SNAP. And ZIP codes are places, not people: many of the ZIP
codes that gained their first authorized store are lightly populated, so counts of places do not
translate directly into counts of shoppers.

Company store counts are from early 2025 to early 2026 and are compared against authorizations at the
end of 2025, so the ratios are close, not exact.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025, covering retailers authorized at
any point in the window. Analysis uses 656,868 stores with usable coordinates. A store counts as active
in a year if an authorization covered 31 December. Company store counts from Dollar General and Dollar
Tree investor releases; Family Dollar via trade press. The 2017 rollback is Section 765 of P.L. 115-31.
Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post1.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post1.html", DIR / "post1-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post1.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
