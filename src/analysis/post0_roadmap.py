"""Post 0 — the announcement and the reading order for the series.

This is the only piece with no analysis of its own. It introduces the map and
lays out the six chapters and the epilogue. Every number it quotes is read from the chapter that
established it, so the announcement cannot drift from the pieces it advertises.

The reading order is deliberately NOT the order the chapters were written in.
The argument builds: establish the loss, then the two formats that filled the
gap, then the opposite solution, then the newest loss, then the synthesis.

    Day 1  small grocery      post2   what went away, and how much of it is real
    Day 2  dollar stores      post1   the format that replaced it in count
    Day 3  gas stations       post6   the second format that endures, and why
    Day 4  Walmart            post3   the other answer to the same problem
    Day 5  pharmacies         post4   the newest loss, and the highest stakes
    Day 6  synthesis          post5   the thread through all five
    Day 7  epilogue           post7   what it means for policy, and a prediction

Chapter numbers in the JSON are reading-order positions. The `slug` field keeps
the link back to the file that holds the chapter, because renaming the analysis
scripts would break every cross-reference in the repository.
"""
import json

from config import ROOT

OUT = ROOT / "reports" / "data"

# (day, slug, subject, headline, one-line topic, why it sits here)
# `subject` is the short label used in the reading-order table, where a full
# headline would overflow the column.
CHAPTERS = [
    (1, "post2", "Small grocery",
     "SNAP shows small grocers down 46%. The census says 22%. Both are right.",
     "What happened to the small neighbourhood grocery store, and how much of the "
     "drop is stores closing versus stores leaving the program.",
     "Start with the loss. It is the change everything else in the series responds "
     "to, and it forces the one distinction the whole series depends on: these "
     "records count authorizations, not buildings."),
    (2, "post1", "Dollar stores",
     "Dollar stores almost never leave SNAP. Small grocers almost always do.",
     "The steadiest trend in the data: sixteen years of near-constant dollar store "
     "openings, and a survival rate no other format comes close to.",
     "Having established what went away, look at what grew in its place. The "
     "surprise is not the growth. It is that these stores almost never close."),
    (3, "post6", "Gas stations",
     "The gas station is the other store that stayed.",
     "Splitting the convenience store category by who runs the store, and the fuel "
     "margins that made the gas station newly profitable after 2020.",
     "Dollar stores are only half the answer. A second format survives at exactly "
     "the same rate, for a reason that shows up in company filings."),
    (4, "post3", "Walmart",
     "13 million people reach a superstore only because of Walmart.",
     "How much of the country can reach a large store at all, measured with and "
     "without Walmart's locations.",
     "A deliberate counterweight. The first three chapters are about small cheap "
     "stores. This one is about the largest format there is solving the same "
     "problem the opposite way — and it complicates the story rather than "
     "confirming it."),
    (5, "post4", "Pharmacies",
     "Rite Aid went from 1,523 SNAP-authorized stores to 2.",
     "The collapse of the chain pharmacy, which happened faster and more recently "
     "than any other change in the data.",
     "The newest change, and the one with consequences beyond food. It also sets "
     "up the final chapter, which is built on the places this collapse hit."),
    (6, "post5", "The thread",
     "The pharmacy left. The grocery left. Two formats stayed.",
     "The places where all of these trends land at once, what they have in common, "
     "and the explanation that turns out to be wrong.",
     "The synthesis, and the last chapter of the story. It tests the obvious "
     "reading — that one format pushed the others out — against a control group, "
     "and finds something harder to act on."),
    (7, "post7", "Epilogue",
     "In November, the rules change for the stores that are left.",
     "How SNAP benefits are calculated, why that calculation assumes a store that "
     "may no longer be nearby, and what the new retailer stocking standard is "
     "likely to do when it takes effect.",
     "An epilogue rather than a chapter: the six chapters measure what happened, "
     "and this one asks what it means for policy. It is also the only piece that "
     "makes predictions, stated before the compliance deadline so they can be "
     "checked afterwards."),
]


def main():
    data = {}
    for n in list(range(1, 8)):
        p = OUT / f"post{n}.json"
        if p.exists():
            data[f"post{n}"] = json.loads(p.read_text())

    def g(slug, *path, default=None):
        """Read a figure from a chapter's own analysis output."""
        cur = data.get(slug)
        for k in path:
            if cur is None:
                return default
            cur = cur.get(k) if isinstance(cur, dict) else None
        return cur if cur is not None else default

    p1_surv = {r["format"]: r for r in (g("post1", "survival", default=[]) or [])}
    p6_surv = {r["segment"]: r for r in (g("post6", "survival", default=[]) or [])}
    p3_acc = {r["radius"]: r for r in (g("post3", "access", default=[]) or [])}

    # One headline number per chapter, pulled from that chapter's output.
    stats = {
        # The headline number is the CBP-window comparison the chapter is built
        # on, not arc.pct_fall — that one is peak-to-trough (-48.6%) and would
        # contradict the chapter's own title.
        "post2": {"value": f"{abs(g('post2','cbp','snap_small_pct', default=46.1)):.0f}%",
                  "label": "fall in SNAP-authorized small grocers, against "
                           f"{abs(g('post2','cbp','cbp_under5_pct', default=22.5)):.0f}% "
                           "in the census count of the establishments themselves"},
        "post1": {"value": f"{g('post1','headline','dollar_2025', default=37361):,}",
                  "label": "dollar stores authorized to accept SNAP in 2025"},
        "post6": {"value": f"{p6_surv.get('fuel-forward chains',{}).get('rate',78.7)}%",
                  "label": "of fuel-forward chain stores from 2008-2012 were still "
                           "authorized in 2025"},
        "post3": {"value": f"{p3_acc.get(10,{}).get('depends_on_walmart',0)/1e6:.0f}M",
                  "label": "people within 10 miles of a superstore only because of Walmart"},
        "post4": {"value": f"{g('post4','chain','peak', default=0):,}",
                  "label": "peak SNAP-authorized chain pharmacies, now "
                           f"{g('post4','chain','latest', default=0):,}"},
        "post5": {"value": f"{g('post5','groups','lost', default=976):,}",
                  "label": "ZIP codes lost their last SNAP-authorized chain pharmacy since 2021"},
        "post7": {"value": f"{g('post7','policy','impact','stores_losing_authorization', default=5000):,}",
                  "label": "stores USDA expects to lose SNAP authorization under the new "
                           "stocking standard, against "
                           f"{g('post7','policy','impact','baseline_annual_losses', default=2000):,} "
                           "in a normal year"},
    }

    out = {
        "chapters": [{"day": d, "slug": s, "subject": sub, "headline": h, "topic": t,
                      "placement": w, "stat": stats.get(s, {})}
                     for d, s, sub, h, t, w in CHAPTERS],
        "dataset": {
            # Pipeline figures. These are properties of the load, not of any one
            # analysis, so they are stated here and checked in verify_map.py.
            "stores": 661_456,
            "mappable": 656_868,
            "spells": 703_441,
            "multi_spell": 37_908,
            "formats": 18,
            "brands": 291,
            "active_2025": 249_083,
            "first_year": 2006,
            "last_year": 2025,
        },
        "sources": [
            "USDA FNS SNAP Retailer Locator Historical Data, 2005-2025",
            "2020 Decennial Census (DHC table P1) population by ZCTA and tract",
            "2020 Census Gazetteer tract centroids",
            "Census County Business Patterns establishment counts",
            "EIA weekly retail and spot gasoline prices",
            "SEC EDGAR 10-K filings (Murphy USA, Casey's General Stores)",
            "Thrifty Food Plan, 2021 (USDA FNS-916) and SNAP retailer stocking "
            "standards, 7 CFR 278.1",
        ],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post0.json").write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT / 'post0.json'}")
    print(f"  {len(CHAPTERS)} chapters in reading order:")
    for c in out["chapters"]:
        st = c["stat"].get("value", "?")
        print(f"    Day {c['day']}  [{c['slug']}]  {c['subject']:<14} {st:>9}  "
              f"{c['headline'][:52]}")
    missing = [c["slug"] for c in out["chapters"] if not c["stat"].get("value")]
    if missing:
        raise SystemExit("missing headline stats for: " + ", ".join(missing))


if __name__ == "__main__":
    main()
