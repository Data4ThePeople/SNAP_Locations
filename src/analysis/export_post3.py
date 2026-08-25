"""Assemble reports/post3/ — markdown text, PNG figures, and the HTML archive.

Day 4 was rebuilt around geography: growth by USDA Rural-Urban Continuum Code.
The metro/nonmetro divergence for the big formats, the million-plus metros'
share of the growth, and the dollar store as the one format whose growth is
indifferent to county size. The earlier size-ladder and ownership cut still
lives in post3.json (ladder, survival, by_ownership) if it is ever wanted back.
"""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post3.json"
DIR = ROOT / "reports" / "post3"
IMG = DIR / "images"

# One row per RUCC code, worded so the chart teaches the ladder itself. "Town"
# stands in for ERS's "urban population of" and "near metro" for "adjacent to a
# metro area"; the caption carries the official phrasing.
RUCC_LABEL = {1: "1  metro of 1M+", 2: "2  metro 250k-1M", 3: "3  metro under 250k",
              4: "4  town of 20k+, near metro", 5: "5  town of 20k+, remote",
              6: "6  town of 5-20k, near metro", 7: "7  town of 5-20k, remote",
              8: "8  rural, near metro", 9: "9  rural, remote"}


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    figs = {}

    def fig(n, slug, caption, fn, *a, **kw):
        p = IMG / f"{n:02d}-{slug}.png"
        fn(p, *a, **kw)
        figs[slug] = {"file": p.name, "caption": caption}
        print(f"  {p.name}")

    ru = d["rucc"]
    F = ru["formats"]
    yrs = list(range(2006, 2026))
    pop_nm_m = ru["pop_nonmetro"] / 1e6

    def seg(fmt, which):        # yearly counts for metro / nonmetro
        return [F[fmt][which][str(y)] for y in yrs]

    def pchg(fmt, which):       # 2006 -> 2025 percent change for a segment
        s = F[fmt][which]
        return 100 * (s["2025"] / s["2006"] - 1)

    def code_chg(fmt, k):       # 2006 -> 2025 percent change for one RUCC code
        c = F[fmt]["by_code"][str(k)]
        return 100 * (c["2025"] / c["2006"] - 1)

    def share_1m(fmt):          # RUCC-1 share of the format's net change
        net = {k: F[fmt]["by_code"][str(k)]["2025"] - F[fmt]["by_code"][str(k)]["2006"]
               for k in range(1, 10)}
        return 100 * net[1] / sum(net.values())

    idx = lambda vals: [round(100 * v / vals[0], 1) for v in vals]

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{pchg('Super Store', 'metro'):+.0f}%",
          "label": "change in metro super stores since 2006. In nonmetro counties "
                   f"they fell {abs(pchg('Super Store', 'nonmetro')):.0f}%"},
         {"value": f"{pop_nm_m:.1f}M",
          "label": "Americans live in the nonmetro counties the big formats are leaving"},
         {"value": f"+{pchg('Dollar Store', 'nonmetro'):.0f}%",
          "label": "nonmetro dollar store growth — the only format still growing "
                   "on every rung of the rural-urban ladder"}])

    fig(1, "metro-vs-nonmetro",
        "Authorized super stores and supermarkets, indexed to 100 in 2006, in "
        "metropolitan against non-metropolitan counties (USDA Rural-Urban Continuum "
        "Codes; metro is codes 1-3).",
        figures.line_png, yrs,
        [{"name": "super stores — metro", "values": idx(seg("Super Store", "metro")), "slot": 1},
         {"name": "supermarkets — metro", "values": idx(seg("Supermarket", "metro")), "slot": 3},
         {"name": "supermarkets — nonmetro", "values": idx(seg("Supermarket", "nonmetro")), "slot": 5},
         {"name": "super stores — nonmetro", "values": idx(seg("Super Store", "nonmetro")), "slot": 2}],
        y_zero=False, ylabel="authorized stores, indexed to 2006 = 100",
        title="Metro America gained big stores. Nonmetro America lost them.")

    fig(2, "metro-1m-share",
        "Share of each format's net change in authorized stores, 2006-2025, that "
        "landed in counties belonging to metro areas of a million people or more.",
        figures.hbar_png,
        [{"label": "super stores", "value": share_1m("Super Store"), "slot": 1},
         {"label": "supermarkets", "value": share_1m("Supermarket"), "slot": 3}],
        suffix="%",
        title="The million-person metros took almost all of the growth",
        subtitle="share of net 2006-2025 change in metro-1M+ counties")

    fig(3, "rucc-gradient",
        "Percent change in authorized stores, 2006 to 2025, on each rung of the "
        "Rural-Urban Continuum. Each row is one code, from counties in metro areas "
        "of a million or more down to fully rural counties not adjacent to any "
        "metro area; the dashed rule separates metro from nonmetro. \"Town\" is "
        "ERS's \"urban population of\"; \"near metro\" is \"adjacent to a metro "
        "area\".",
        figures.dotrows_png, [RUCC_LABEL[k] for k in range(1, 10)],
        [{"name": "dollar stores", "values": [round(code_chg("Dollar Store", k), 1) for k in range(1, 10)], "slot": 2},
         {"name": "convenience", "values": [round(code_chg("Convenience Store", k), 1) for k in range(1, 10)], "slot": 4},
         {"name": "super stores", "values": [round(code_chg("Super Store", k), 1) for k in range(1, 10)], "slot": 1},
         {"name": "supermarkets", "values": [round(code_chg("Supermarket", k), 1) for k in range(1, 10)], "slot": 3},
         {"name": "small grocery", "values": [round(code_chg("Grocery (Small)", k), 1) for k in range(1, 10)], "slot": 7}],
        divider_after=3, subtitle="% change in authorized stores, 2006-2025",
        title="Dollar stores grow everywhere. Everything else grows where people are.")

    km = ru["kmart_2020"]

    md = f"""# Super stores for some, dollar and convenience stores for the rest

*SNAP-authorized retailers, 2006–2025, joined to USDA's Rural-Urban Continuum Codes.
{pop_nm_m:.1f} million Americans live in the non-metropolitan counties this piece is about.*

**{pchg('Super Store', 'metro'):+.0f}%** change in metro super stores since 2006; in nonmetro counties they fell {abs(pchg('Super Store', 'nonmetro')):.0f}%. **{pop_nm_m:.1f} million** Americans live in nonmetro counties. **+{pchg('Dollar Store', 'nonmetro'):.0f}%** nonmetro dollar store growth — the only format still growing on every rung of the rural-urban ladder.

![Headline figures](images/00-key-figures.png)

---

*As in the earlier pieces: anytime we refer to "growth" in this post, it is growth in
SNAP-authorized stores, not growth in store counts. See the Limits section for more on this.*

My analysis for today's post made me reflect on my own life. I'm specifically thinking about the
plethora of grocery options I have just minutes from my house in suburban Dayton, Ohio. There are a
Target, a Costco, and a Kroger down the street from me. Drive another few minutes and you'll pass a
Walmart and an Aldi. Another five minutes and there's a Trader Joe's. My weekly grocery trips
involve some ever-changing combination of visits to these stores to get the products my family
likes at the best price. There weren't always this many options. But large-format grocers have flocked to the
metropolitan area in which I live, providing an overabundance of fully stocked grocery stores for suburban Daytonians.

Most of you reading this can probably relate. But not everyone. If you are one of the
**{pop_nm_m:.1f} million Americans** living in a non-metropolitan county, how you shop for
groceries is likely very different — rather than having more options as time passes, you may have
fewer.

## The two grocery Americas

How do we know that? The data, of course. The chart below shows the change in the two largest store
formats — super stores and supermarkets — in metropolitan counties against non-metropolitan
counties, indexed to 100 in 2006.

![{figs["metro-vs-nonmetro"]['caption']}](images/{figs["metro-vs-nonmetro"]['file']})

In metro counties, super stores are up {pchg('Super Store', 'metro'):.0f}% and supermarkets
{pchg('Supermarket', 'metro'):.0f}%. In nonmetro counties both lines point the other way: down
{abs(pchg('Super Store', 'nonmetro')):.0f}% and {abs(pchg('Supermarket', 'nonmetro')):.0f}%. That
sharp step down in 2020 is the Kmart liquidation — {km['kmart']} nonmetro Kmart supercenters left
the program in a single year.

Reality is even more skewed than that chart lets on. It turns out that nearly three-quarters of all
net super store growth — and {share_1m('Supermarket'):.0f}% of net supermarket growth — happened in
the million-plus metros alone.

![{figs["metro-1m-share"]['caption']}](images/{figs["metro-1m-share"]['file']})

The more we analyze and write, the more we see common threads emerging across this country. Today's
finding is a complement to our deep dive into the structural decline of the labor force — an
extensive piece that tracked the decline in the labor force (and therefore, the economic engine) of
nonmetro counties and the simultaneous surge in the labor forces of large metro counties and their
surrounding suburbs (Austin, Nashville, Salt Lake City). When a county is in structural decline, it
makes sense that it would lose the larger-format grocery stores that need volume to make the
economics work. Two findings from two completely different databases, connected by Ockham's razor.

## What grows where the big stores don't

And so, what store formats are growing in nonmetro counties? You guessed it: dollar stores and
convenience stores.

The chart below needs one piece of setup. USDA's Rural-Urban Continuum Codes sort every county in
America onto a nine-rung ladder: code 1 is a county in a metro area of a million people or more,
codes 2 and 3 are smaller metros, and codes 4 through 9 step down through ever smaller and more
remote nonmetro counties, ending at code 9 — fully rural counties not adjacent to any metro area.
The chart walks that ladder top to bottom, one row per rung, and marks each format's twenty-year
growth on every one. The dollar store is the only format whose growth was indifferent to the size
of the county — the smallest counties grew at nearly the same pace as the largest ones.

![{figs["rucc-gradient"]['caption']}](images/{figs["rucc-gradient"]['file']})

Every other format fades as you read down the ladder. Convenience stores grew
{code_chg('Convenience Store', 1):.0f}% in the biggest metros but only
{code_chg('Convenience Store', 9):.0f}% in fully rural counties. The big formats flip negative the
moment you cross the metro line. Small grocery falls everywhere — steepest at the two extremes, the
big-city bodega and the only-store-in-town. Only the dollar store's dots hold their place on every
rung, a straight column at around +300%.

You are free to have your own views on these different store formats. But the data can help us
remove our views from our own lived experience and try to form them from how others live. What if I
lived in a small county, getting smaller by the day as its labor force shrank through aging, a
declining birth rate, and out-migration to the larger metro areas for better work? Maybe I had one grocery store years ago.
Maybe now it's gone. Maybe I can't get everything I would like to eat at a dollar store. But
calories are better than no calories. And so, I am grateful. The alternative is a long drive,
spending gas money I may not have — especially now, thanks to our self-inflicted fuel crisis.

## The questions this leaves

Where does this gravitational pull lead? Is it really a good strategy to let so much American land
become uninhabitable over time as it loses its workers and the stores that rely on them to make
their economics work? Should we really expect so many Americans to live off what they can buy at a
dollar store? What right do any of us who don't have to live this way have to criticize the
physical and mental health of those who do? And how can we ever expect the cost of health care to
decline — Medicaid and all the rest — if we can't provide people with access to the healthy foods
that USDA's economists blindly assume they can buy?

Those are just a few of the questions on my mind after studying this data. Feel free to add yours.

**Tomorrow: the mirror image of the fuel-forward chain convenience store — the one chain format
in structural decline, and the reason why.**

## Limits

**Growth here means authorized stores.** For super stores, supermarkets and dollar stores the
distinction is small — those chains' authorization counts track their reported store counts almost
exactly (see Day 2). For convenience stores a rising count can also mean wider EBT take-up among
stores that already existed, so read its gradient as the shape, not the level.

**Counties are classified by their current Rural-Urban Continuum Code** (the 2023 vintage;
Connecticut keeps its 2013 county codes because the 2023 file switched to planning regions). A
county keeps one code across the whole window, so within-county comparisons are consistent — but
"metro" means metro as defined today. 99.7% of active stores matched a coded county; the remainder
sit in territories and a few renamed county-equivalents. County populations are the 2020 census.

**A county is a coarse lens.** A metro county contains poor neighborhoods far from any supermarket,
and a rural county can have a town center with three grocers. The RUCC split measures the county's
relationship to a metro area, not any single household's drive to a store.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. USDA ERS Rural-Urban Continuum
Codes, 2023 (Connecticut: 2013), with 2020 census county populations. Analysis uses 656,868 stores
with usable coordinates; a store counts as active in a year if an authorization covered 31 December.
Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations](https://github.com/Data4ThePeople/SNAP_Locations).*
"""
    (DIR / "post3.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post3.html", DIR / "post3-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post3.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
