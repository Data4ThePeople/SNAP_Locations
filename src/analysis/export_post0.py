"""Assemble reports/post0/ — markdown text, PNG figures, and the HTML archive."""
import json
import shutil

from analysis import figures
from config import ROOT

SRC = ROOT / "reports" / "data" / "post0.json"
DIR = ROOT / "reports" / "post0"
IMG = DIR / "images"
MAP_URL = "https://github.com/Data4ThePeople/SNAP_Locations"


def main():
    d = json.loads(SRC.read_text())
    IMG.mkdir(parents=True, exist_ok=True)
    ds, ch = d["dataset"], d["chapters"]
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

    print("figures:")
    fig(0, "key-figures", "Headline figures.", figures.ledger_png,
        [{"value": f"{ds['stores']:,}",
          "label": "stores authorized to accept SNAP at some point in the last twenty years"},
         {"value": f"{ds['active_2025']:,}",
          "label": f"still authorized at the end of {ds['last_year']}"},
         {"value": f"{ds['last_year'] - ds['first_year'] + 1}",
          "label": "years you can move through, one at a time"}])

    # Short subject labels, not full headlines: table_png does not wrap, and a
    # 70-character headline would run past its column.
    fig(1, "reading-order",
        "The seven pieces in reading order, with the headline figure of each.",
        figures.table_png, ["Day", "Subject", "Headline figure"],
        [[f"Day {c['day']}", c["subject"], f"{c['stat']['value']}"] for c in ch],
        title="Read them in this order",
        subtitle="the argument builds from one piece to the next")

    chapter_md = "\n".join(f"""
### Day {c['day']} — {c['headline']}

{c['topic']}

**{c['stat']['value']}** — {c['stat']['label']}

> {c['placement']}
""" for c in ch)

    srcs = "\n".join(f"- {s}" for s in d["sources"])

    md = f"""# Twenty years of SNAP retailers, mapped — and what we found in it

*Every store authorized to accept SNAP anywhere in the United States, {ds['first_year']}–{ds['last_year']}.
{ds['stores']:,} stores. An interactive map, and seven days of analysis built on it.*

**{ds['stores']:,}** stores authorized to accept SNAP at some point in the last twenty years.
**{ds['active_2025']:,}** still authorized at the end of {ds['last_year']}.
**{ds['last_year'] - ds['first_year'] + 1}** years you can move through, one at a time.

![Headline figures](images/00-key-figures.png)

---

SNAP is the largest food assistance program in the country. To use it you need a store that accepts it. USDA publishes a record of every store ever approved to do so, going back twenty years. It is a remarkable file: **{ds['stores']:,} stores**. Each one has a location, a store type, and the dates its approval started and ended.

We have turned that file into a map you can explore, and then spent seven pieces working out what it says.

## The map

It is a single web page. Nothing to install, nothing to sign into.

- **Filter by store type.** All {ds['formats']} of USDA's categories — supermarkets, superstores,
  convenience stores, dollar stores, farmers' markets and the rest.
- **Filter by retailer.** {ds['brands']} chains are named, so you can clear the map and bring back only the ones you want. Turn everything off, then switch on Kroger and Giant Eagle. Now you are looking at two companies against an empty country.
- **Move through time.** One year at a time, {ds['first_year']} to {ds['last_year']}. The map redraws
  for the stores authorized on 31 December of that year.

[The map, the pipeline that builds it, and every figure in this series.]({MAP_URL})

## One thing to understand before reading anything else

This file records **authorizations, not storefronts**. A store leaving the data means its authorization
ended. That usually means the store closed, but it can also mean the store is still open and simply
stopped accepting SNAP.

The two look identical here. That one gap shapes the whole series, and we handle it the same way every time. Where a claim depends on stores actually closing, we check it against a source outside this data. Usually that is a company's own reported store count, or the Census Bureau's count of business locations. The census counts a store whether or not it takes EBT.

Where we could not check it, we say so and make no claim. That is why some obvious-looking findings are missing from these pieces.

## Seven days, one argument

Each piece stands alone. But they are built to be read in order, and that order is not the order we wrote them in. It is the order in which the argument builds. The first six are the story. The last is an epilogue about what it means for policy.

![{figs["reading-order"]['caption']}](images/{figs["reading-order"]['file']})
{chapter_md}
## What we are not claiming

This data has no prices, no floor space, and no sales. It has no idea what is on a shelf. A dollar store and a supermarket each count as one record. It also does not know whether anyone has a car. That is often what decides whether a store ten miles away is a quick errand or out of reach.

So this series is about **where the stores are and what kind they are**. That is a real and useful question. It is not the same as asking whether people are fed.

## Sources

{srcs}

Every figure in every piece is produced by a script with assertions in it, not by a query typed once. The pipeline matches the map we shipped. The store counts add up exactly across all nineteen pairs of years. Both are checked on every run.

---

*Source: USDA FNS SNAP Retailer Locator Historical Data, {ds['first_year'] - 1}–{ds['last_year']}.
{ds['stores']:,} stores, {ds['spells']:,} authorization spells, of which {ds['multi_spell']:,} stores hold
more than one. {ds['mappable']:,} have coordinates good enough to map. Code, pipeline and verification:
[Data4ThePeople/SNAP_Locations]({MAP_URL}).*
"""
    (DIR / "post0.md").write_text(md)
    shutil.copy(ROOT / "reports" / "post0.html", DIR / "post0-archive.html")
    shutil.copy(SRC, DIR / "data.json")
    print(f"\nwrote {DIR}/post0.md ({len(md)//1000} KB), {len(figs)} images, "
          f"html archive, data.json")


if __name__ == "__main__":
    main()
