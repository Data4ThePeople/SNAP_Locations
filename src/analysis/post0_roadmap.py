"""Post 0 — the announcement and the reading order for the series.

This is the only piece with no analysis of its own. It introduces the map and
lays out the five chapters and the epilogue. Every number it quotes is read from the chapter that
established it, so the announcement cannot drift from the pieces it advertises.

The reading order is deliberately NOT the order the chapters were written in.
The argument builds: establish the loss, then the two formats that filled the
gap, then the newest loss, then the synthesis.

    Day 1  small grocery      post2   what went away, and how much of it is real
    Day 2  dollar stores      post1   the format that replaced it in count
    Day 3  gas stations       post6   the second format that endures, and why
    Day 4  every format       post3   the rule the first three were exceptions to
    Day 5  pharmacies         post4   the newest loss, and the highest stakes
    Day 6  synthesis          post5   the thread through all five
    Day 7  epilogue           post7   what it means for policy, and a prediction

Day 4 sits where it does deliberately. The first three chapters each follow one
small format; Day 4 puts every format on one scale, which turns them from three
observations into two rules and their exceptions. It has to come after them —
the payoff is recognising formats you have already met — and before Day 5,
which is the one chain format that lost anyway.

post3 was ORIGINALLY a Walmart chapter and was cut, then rebuilt on a different
question. The Walmart piece asked whether the losses limit anyone's access,
which is a different question needing data this source does not have, and which
measured properly came out mostly negative: SNAP households live CLOSER to
supermarkets than average. That analysis survives in census_access.py and its
one durable finding — the rural tail — belongs in post7, where the benefit
formula already assumes a store that may not be nearby.

Chapter numbers in the JSON are reading-order positions. The `slug` field keeps
the link back to the file that holds the chapter, because renaming the analysis
scripts would break every cross-reference in the repository.
"""
import json

from config import ROOT

OUT = ROOT / "reports" / "data"

# (day, slug, subject, one-line topic, why it sits here)
#
# The headline is NOT listed here. It is read from the published piece at build
# time, because a copy of it here is a copy that can drift — and did: three
# titles changed during editing and these cards went on advertising the old ones
# until someone compared them by hand.
# `subject` is the short label used in the reading-order table, where a full
# headline would overflow the column.
CHAPTERS = [
    (1, "post2", "Small grocery",
     "What happened to the small neighborhood grocery store, and how much of the "
     "drop is stores closing versus stores leaving the program.",
     "Start with the loss. It is the change everything else in the series responds "
     "to, and it forces the one distinction the whole series depends on: these "
     "records count authorizations, not buildings."),
    (2, "post1", "Dollar stores",
     "The steadiest trend in the data: sixteen years of near-constant dollar store "
     "openings, and a survival rate no other format comes close to.",
     "Having established what went away, look at what grew in its place. The "
     "surprise is not the growth. It is that they almost never leave the program."),
    (3, "post6", "Gas stations",
     "Splitting the convenience store category by who runs the store, and the fuel "
     "margins that made the gas station newly profitable after 2020.",
     "Dollar stores are only half the answer. The chains that sell fuel endure at "
     "the same rate, for a reason that shows up in company filings. Almost nobody "
     "else in the category does."),
    (4, "post3", "Every format",
     "Every store type on a single scale: which ones kept their SNAP "
     "authorization, split by size and by whether a chain owned them.",
     "The keystone. The first three chapters each followed one format and each "
     "needed its own explanation. This one shows they were the same two rules all "
     "along — and that the formats that won were not breaking the rule about size, "
     "they were beating it with a rule about chains."),
    (5, "post4", "Pharmacies",
     "The collapse of the chain pharmacy, which happened faster and more recently "
     "than any other change in the data.",
     "The newest change, and the one with consequences beyond food. It also sets "
     "up the final chapter, which is built on the places this collapse hit."),
    (6, "post5", "The thread",
     "The places where all of these trends land at once, what they have in common, "
     "and the explanation that turns out to be wrong.",
     "The synthesis, and the last chapter of the story. It tests the obvious "
     "reading — that one format pushed the others out — against a control group, "
     "and finds something harder to act on."),
    (7, "post7", "Epilogue",
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
    for n in range(1, 8):
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
    p3_own = g("post3", "by_ownership", default={}) or {}
    p3_sv = g("post3", "survival", default={}) or {}

    # One headline number per chapter, pulled from that chapter's output.
    stats = {
        # Each card carries the number that proves its own title, not simply the
        # biggest number in the piece. Day 1 is titled "one in four", so it shows
        # the census figure rather than SNAP's 46%.
        "post2": {"value": f"{abs(g('post2','cbp','cbp_under10_pct', default=24.9)):.0f}%",
                  "label": "fall in the number of small grocery businesses, by the "
                           "Census Bureau's count"},
        "post1": {"value": f"{100*p1_surv['Dollar Store']['rate']:.0f}%",
                  "label": "of dollar stores authorized in 2008-2012 are still "
                           "authorized today"},
        "post6": {"value": f"{p6_surv['single-owner stores']['rate']}%",
                  "label": "of single-owner convenience stores lasted thirteen years, "
                           f"against {p6_surv['chains that sell fuel']['rate']}% of the "
                           "chains"},
        # Not the 78% chain-survival figure, striking as it is: Day 2's card
        # already carries a 78%, and two cards showing the same number a few
        # inches apart reads as a mistake rather than as a coincidence.
        "post3": {"value": f"{p3_sv['Super Store']['rate']/p3_sv['Grocery (Small)']['rate']:.0f}x",
                  "label": "likelier a super store kept its SNAP authorization than a "
                           "small grocery. A dollar store did better than both"},
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

    def headline(slug):
        """The piece's own H1, read from what was published."""
        md = ROOT / "reports" / slug / f"{slug}.md"
        if not md.exists():
            raise SystemExit(f"{md} is missing — build the pieces before the roadmap")
        first = md.read_text().split("\n", 1)[0].lstrip("#").strip()
        if not first:
            raise SystemExit(f"{md} has no title on its first line")
        return first

    out = {
        "chapters": [{"day": d, "slug": s, "subject": sub, "headline": headline(s),
                      "topic": t, "placement": w, "stat": stats.get(s, {})}
                     for d, s, sub, t, w in CHAPTERS],
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
