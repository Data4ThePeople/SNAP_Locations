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
    z, ctx, gap, cen = d["dollar_only_zip"], d["context"], d["survival_gap"], d["chain_census"]
    sp, lap = d["spike_2024"], d["lapse"]
    fl = d["dollar_flows"]
    # Active on 31 December 2025; the largest single format in the file.
    conv_2025 = 117_055
    stock, yrs = ctx["Dollar Store"]["stock"], ctx["Dollar Store"]["years"]
    growth = stock[-1] / stock[0]
    growth_pct = round(100 * (growth - 1))
    lap_sg = next(r for r in lap if r["format"] == "Grocery (Small)")
    mix = d["ownership_mix"]
    m_ds, m_sg, m_cv = mix["Dollar Store"], mix["Grocery (Small)"], mix["Convenience Store"]

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
        title="For these chains, an authorization really is a store",
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
        "ZIP codes with a SNAP-authorized dollar store and no supermarket, superstore, or "
        "grocery store of any size.",
        figures.line_png, [r["yr"] for r in z],
        [{"name": "ZIP codes", "values": [r["dollar_only"] for r in z], "slot": 2}],
        ylabel="ZIP codes with a dollar store and no grocery",
        title="More places now have a dollar store and nothing else")

    md = f"""# Dollar stores cracked the code small grocers could not

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

## This time, an authorization is a store

Yesterday we had to be careful: when a small grocer leaves the SNAP file, the records cannot say
whether it closed or just stopped taking EBT. Dollar stores are a different case. Nearly all of them
belong to a handful of public chains — Dollar General, Dollar Tree, Family Dollar — and those
companies tell their investors exactly how many stores they run. So set the SNAP authorization
counts at the end of 2025 against the companies' own reported store counts:

![{figs["chain-census"]['caption']}](images/{figs["chain-census"]['file']})

Essentially every Dollar General and Dollar Tree in the country takes SNAP. Because the two counts
line up, we can read store openings and closings for these chains straight out of the SNAP file —
something yesterday's data could not give us. Keep that in mind through everything that follows: for
dollar stores, authorization counts are store counts.

## They grew enormously

Dollar stores went from {stock[0]:,} SNAP-authorized stores in {yrs[0]} to {stock[-1]:,} in
{yrs[-1]}. That is a **{growth_pct:+}%** change, while every grocery format either shrank or stood
still.

![{figs["growth"]['caption']}](images/{figs["growth"]['file']})

They are now the second most common kind of SNAP retailer in the country, behind only convenience
stores. There are {d['headline']['dollar_2025']:,} of them against
{d['headline']['all_grocery_2025']:,} grocery stores of every size combined.

## They kept their authorizations

Growth is the easy part of the story. The harder question is what happened to the stores that were
already there. Take every retailer that joined SNAP between 2008 and 2012, and ask how many are still
in the program at the end of 2025.

![{figs["retention"]['caption']}](images/{figs["retention"]['file']})

**{100*ds['rate']:.0f}% of dollar stores are still authorized. Meanwhile, just {100*sg['rate']:.1f}% of small grocers are.** A dollar store from those years is **{gap['multiple']}× more likely** to still be in the
program.

And since an authorization here is a store, those stores are still open. That says something about
the economics. These are public companies, and they do close stores that stop working. In 2024 dollar store endings jumped from a few hundred a year to {fl['departed'][fl['years'].index(2024)]:,} — Dollar Tree shutting Family Dollar locations ({sp[0]['n']}) and 99 Cents Only liquidating ({sp[1]['n']}). So the survival rate is not a company failing to notice. When a listed retailer culls that hard the moment the numbers stop working, and still has {100*ds['rate']:.0f}% of a cohort trading thirteen years later, the fair read is that these stores pay.

## More of the country has one and nothing else

Growth in total is not the same as growth where it matters. The sharper question is how often a dollar store is the *only* option nearby. So count the ZIP codes that have a dollar store and no grocery store of any size — no supermarket, no superstore, no large, medium or small grocer.

![{figs["dollar-only-zips"]['caption']}](images/{figs["dollar-only-zips"]['file']})

In {z[0]['yr']} that described {z[0]['dollar_only']:,} ZIP codes. By {z[-1]['yr']} it described
**{z[-1]['dollar_only']:,}** — {100*z[-1]['dollar_only']/z[-1]['with_dollar']:.0f}% of every ZIP code
that has a dollar store at all, up from {100*z[0]['dollar_only']/z[0]['with_dollar']:.0f}%. In one ZIP
code in four, the dollar store is not one option among several. It is the option.

## What it adds up to

Dollar stores ended up on both sides of a line everyone else has to choose.

They are **small where small pays**: a box that makes money in a town of a few thousand people, where a supermarket cannot. And they are **big where big pays**: a chain that works out how to clear USDA's stocking bar once, then spreads the cost of doing it across twenty thousand stores.

Small grocers only ever get the first half. {m_sg['independent']:.0f}% of them are independent and {m_sg['chain']:.0f}% belong to a chain. Same small box, no big company behind it.

Put the two halves together and the growth stops being surprising. It is no wonder dollar stores have outgrown every grocery format in the country.

But hold on to the second half. Why is that bar low enough for a small box to clear? Partly because someone else fought to keep it there. The 2016 stocking rule would have raised it sharply. It was rolled back in May 2017 — by the **convenience store** industry, lobbying hard for its members. Dollar stores never led that campaign. They just got the benefit.

Which is where we go next: the country's **{conv_2025:,} convenience stores**, the single largest group
in this data, and how they have thrived without anything like the chain concentration dollar stores
enjoy. Only {m_cv['chain']:.0f}% of them belong to a chain at all.

**Tomorrow: the convenience store.**

## Limits

Nothing here measures floor space, sales, or what is on the shelves. A dollar store and a supermarket
each count as one record.

**The chain-store check is what licenses closure language, and only for these chains.** For an
independent store an ended authorization may mean the shop closed or may mean it stopped taking EBT.
{100*lap_sg['rate']:.1f}% of small grocers lost their authorization and later regained it, median gap
{lap_sg['median_gap_days']} days — those were open the whole time.

The 2024 closures above were both announced by the companies and widely reported at the time, which is a useful check on the file: when something real happens in retail, these records catch it.

Store-level SNAP spending is not public. A 2019 Supreme Court case put those figures under a FOIA
exemption, so we can see where authorized stores are but never how much any one of them takes in.

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
