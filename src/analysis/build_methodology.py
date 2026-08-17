"""Short-form methodology for the visualization page.

This sits on the page that hosts the map embed, not inside the iframe and not in
post 0. It is deliberately brief and bulleted: the reader wants to know what a
dot means and what it does not mean, then get back to the map. Anyone who wants
the full treatment is pointed at the repository.

Every number is read from the pipeline and from the map's own meta.json rather
than typed in, for the reason the tool itself just demonstrated — the page used
to hardcode two counts and both drifted, one by a third.
"""
import json

from config import ROOT, connect

WEB_META = ROOT / "web" / "data" / "meta.json"
DIR = ROOT / "reports" / "methodology"
REPO = "https://github.com/Data4ThePeople/SNAP_Locations"

FAILURES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def figures():
    con = connect(read_only=True)
    q = lambda s: int(con.execute(s).fetchone()[0])
    m = json.loads(WEB_META.read_text())
    own = dict(con.execute("SELECT ownership, count(*) FROM dim_store "
                           "WHERE mappable GROUP BY 1").fetchall())
    f = {
        "spells": q("SELECT count(*) FROM fact_spell"),
        "stores": q("SELECT count(*) FROM dim_store"),
        "multi": q("SELECT count(*) FROM (SELECT record_id FROM fact_spell "
                   "GROUP BY 1 HAVING count(*) > 1)"),
        "mappable": q("SELECT count(*) FROM dim_store WHERE mappable"),
        "no_coords": q("SELECT count(*) FROM dim_store WHERE geocode_missing"),
        "offshore": q("SELECT count(*) FROM dim_store WHERE geocode_offshore"),
        "state_bad": q("SELECT count(*) FROM dim_store WHERE state_mismatch"),
        "on_map": m["count"],
        "never": m["excluded_shortlived_count"],
        "never_pct": m["excluded_shortlived_pct"],
        "formats": len(m["formats"]),
        "brands": len(m["brands"]) - 1,   # slot 0 is "no brand"
        "groups": len(m["groups"]),
        "y0": m["years"][0], "y1": m["years"][-1],
        "chain": int(own.get("chain", 0)),
        "independent": int(own.get("independent", 0)),
        "unknown": int(own.get("unknown", 0)),
    }
    f["dropped"] = f["stores"] - f["mappable"]
    return f


def main():
    f = figures()
    print("1. Figures read from the pipeline and the map payload")
    for k in ("stores", "spells", "mappable", "on_map", "never", "brands"):
        print(f"     {k:<10} {f[k]:>10,}")

    print("\n2. Consistency")
    check("coordinate drops account for the gap",
          f["no_coords"] + f["offshore"] + f["state_bad"] == f["dropped"],
          f"{f['no_coords']:,} + {f['offshore']} + {f['state_bad']} = {f['dropped']:,}")
    check("map count plus never-shown equals mappable",
          f["on_map"] + f["never"] == f["mappable"],
          f"{f['on_map']:,} + {f['never']:,} = {f['mappable']:,}")
    check("ownership buckets sum to mappable",
          f["chain"] + f["independent"] + f["unknown"] == f["mappable"])

    md = f"""# How this map was built

*A short version. Everything here is reproducible, and the full detail is linked
at the end.*

## Where the data comes from

- **USDA's SNAP Retailer Locator Historical Data**, covering {f['y0']}–{f['y1']}.
- It is a public file. USDA lists every store it has authorized to accept SNAP,
  with an address and the dates the authorization started and ended.
- We add nothing to it. Every dot on the map is a row USDA published.

## What one dot means

- A store that was **authorized on 31 December** of the year you have selected.
- Move the year slider and the map redraws for that date.
- **An authorization is not a storefront.** When a record ends, the store may have
  closed — or it may still be open and simply stopped taking EBT. The file cannot
  tell those apart, and neither can we.
- Because we use one date a year, **{f['never']:,} stores ({f['never_pct']}%) never
  appear at all**. They opened and closed between two 31 Decembers.

## How the file was cleaned

- {f['spells']:,} rows became **{f['stores']:,} stores**. {f['multi']:,} stores hold
  more than one authorization, because authorizations lapse and restart. Counting
  rows instead of stores would double-count them.
- We check every location against the borders of the US, its states and its
  territories. Three kinds of store fall out: {f['no_coords']:,} with no
  coordinates at all, {f['offshore']} placed outside the country, and
  {f['state_bad']} whose coordinates disagree with their own listed state.
- **{f['mappable']:,} stores** have a location good enough to map. Of those,
  **{f['on_map']:,}** appear on at least one year.

## The three ways a store is labelled

- **Store format** — USDA's own category, {f['formats']} of them, from supermarket
  to farmers' market. USDA assigns it and it never changes within a record.
- **Retailer** — we match store names to **{f['brands']} chains** using a
  hand-checked list, and group those into {f['groups']} parent companies. Matching
  is on whole words, so "Giant" never matches inside "Giants Deli".
- **Owner** — chain, independent, or unknown: {f['chain']:,} / {f['independent']:,} /
  {f['unknown']:,}. A gas-station brand on the sign counts as **unknown**, not a
  chain, because a fuel brand is a supply contract and says nothing about who owns
  the store.

## How we check our own work

- The map is rebuilt from the database on every run, and the code refuses to write
  it unless the counts match the database for all {f['y1'] - f['y0'] + 1} years.
- Store arrivals and departures have to add up exactly, every year, with nothing
  left over.
- Where a claim depends on stores really closing, we test it against a source
  outside this file — a company's own reported store count, or the Census Bureau's
  count of business locations, which counts a store whether or not it takes EBT.

## What this data cannot tell you

- Nothing about **prices, sales, floor space, or what is on the shelves**. A dollar
  store and a supermarket each count as one dot.
- Nothing about **how much SNAP money any store takes in**. A 2019 Supreme Court
  case put those figures beyond public reach.
- Nothing about **whether anyone has a car**, which is often what decides if a
  store two towns over is reachable at all.

## The long version

Every figure, the pipeline that builds the map, the brand list, and the checks
that have to pass before anything is published are all public:

**[{REPO.split('//')[1]}]({REPO})**
"""

    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "methodology.md").write_text(md)
    print(f"\nwrote {DIR / 'methodology.md'} ({len(md)//1000} KB)")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("all checks passed")


if __name__ == "__main__":
    main()
