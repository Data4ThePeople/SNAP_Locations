"""Epilogue — what the benefit assumes, and what changes in November 2026.

Split out of post 5, which had grown two sections that do a different job from
the rest of the series. Everything before this point is measurement. This piece
is the policy consequence, and it rests on two things the SNAP retailer file
cannot see:

  1. What is on a shelf. The authorization record has no assortment, so the
     question "can the Thrifty Food Plan basket be bought here?" is posed and
     explicitly left unanswered. No estimate is made.
  2. What has not happened yet. The stocking rule's compliance date is
     4 November 2026, so the predictions here are stated before the fact and
     designed to be checked against the same data afterwards.

Because so much of this rests on outside documents rather than the panel, the
external facts are collected in POLICY below with their sources attached, in one
place, rather than scattered through prose. Anything asserted in the rendered
piece should be traceable to an entry here or to a figure from another chapter's
JSON.

The panel contributes exactly two things, and both are read from the chapters
that established them rather than recomputed:

  - the 2018 precedent (post 2): when stocking standards last tightened, new
    authorizations roughly halved while exits stayed flat. This is the basis for
    predicting an entry collapse rather than a wave of closures.
  - the size gradient (post 2): when the standard last tightened, the fall in
    new sign-ups sorted by how much stock a format already carried — small
    grocery -58%, the largest grocery category +8%. This is the basis for
    predicting who a higher floor removes.

An earlier draft predicted the losses would fall on single stores rather than
chains, citing a chain/independent split inside one USDA category. That split
does not hold: the non-dollar chains in that category fell as far as the
independents, and they are Walgreens, CVS, Rite Aid, Big Lots and Fred's, so
their fall is entangled with a bankruptcy and a liquidation. A stocking rule
asks for stock, so the honest prediction is about stock.
"""
import json

from config import ROOT

OUT = ROOT / "reports" / "data"

# Every external fact this piece uses, with its source. Kept as data so the
# rendered prose cannot drift from what was actually verified.
POLICY = {
    "tfp": {
        "reevaluated": 2021,
        "previous": 2006,
        "directive": "Agriculture Improvement Act of 2018 (2018 Farm Bill)",
        "effective": "1 October 2021",
        "reference_family": "a man and a woman 20 to 50 years old, a child 6 to 8, "
                           "and a child 9 to 11",
        "seafood_weekly_cost": 12.80,
        "seafood_note": "most expensive category; the plan assumes low-cost choices "
                        "and names tilapia or canned tuna as examples",
        "source": "Thrifty Food Plan, 2021 (USDA FNS-916, August 2021)",
    },
    "old_standard": {
        "varieties_per_category": 3,
        "categories": 4,
        "units_per_variety": 3,
        "total_items": 36,
        "perishable_items": 6,
        "perishable_categories": 2,
        "source": "7 CFR 278.1 and the SNAP stocking standards rule effective "
                  "January 2018",
    },
    "new_standard": {
        "varieties_per_category": 7,
        "categories": 4,
        "perishable_categories": 3,
        "category_names": "dairy, fruits or vegetables, grains, and protein",
        "effective": "7 July 2026",
        "compliance": "4 November 2026",
        "docket": "FNS-2025-0018",
        "directive": "Agricultural Act of 2014",
        "blocked": "the same seven-variety expansion was blocked by Congress in 2017",
        "source": "Updated Staple Food Stocking Standards for Retailers in the "
                  "Supplemental Nutrition Assistance Program, final rule",
    },
    "impact": {
        "stores_losing_authorization": 5000,
        "baseline_annual_losses": 2000,
        "small_format_share_pct": 70,
        "cost_year_one": 262,
        "cost_five_years": 374,
        "rfa_finding": "no significant economic impact on a substantial number of "
                       "small entities",
        "source": "USDA regulatory impact analysis accompanying the final rule",
    },
    "need_for_access": {
        "citation": "7 CFR 278.1",
        "factors": "how close the store came to compliance, distance to the next "
                   "authorized store, local vehicle access, operating hours, and "
                   "violation history",
        "catchall": "any other factors which the FNS officer in charge considers "
                    "pertinent",
        "methodology_published": False,
        "source": "SNAP retailer eligibility regulations; FRAC analysis",
    },
    "positions": [
        {"who": "FMI – The Food Industry Association", "represents": "supermarkets",
         "stance": "supports"},
        {"who": "National Grocers Association", "represents": "independent supermarkets",
         "stance": "supports"},
        {"who": "NACS, NATSO and SIGMA", "represents": "convenience and fuel retailers", "stance": "opposes",
         "note": "filed jointly on 24 November 2025; called compliance unworkable for "
                 "small-format stores, singling out the grains and dairy categories"},
        {"who": "Food Research & Action Center", "represents": "anti-hunger advocacy",
         "stance": "opposes", "note": "on access grounds"},
        {"who": "Dollar General, Dollar Tree, Family Dollar", "represents": "dollar stores",
         "stance": "no public comment"},
    ],
    "dollar_general": {
        "stores": 21000,
        "produce_stores_low": 5000,
        "produce_stores_high": 7000,
        "ebt_delivery_stores": 16000,
        "note": "expanding SNAP acceptance to online delivery while selling fresh "
                "produce in fewer than one in three of its own stores, and slowing "
                "that rollout",
        "source": "company disclosures and trade press",
    },
    "precedent_2019": {
        "opposing_comments": 9000,
        "theme": "reduced SNAP household access to authorized stores and the creation "
                 "of food deserts",
        "source": "final rule preamble summarising comments on the 2019 proposal",
    },
}

FAILURES = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def main():
    d2 = json.loads((OUT / "post2.json").read_text())
    d5 = json.loads((OUT / "post5.json").read_text())
    d6 = json.loads((OUT / "post6.json").read_text())

    print("1. The 2018 precedent, from post 2")
    fl, dr = d2["flows"], d2["drivers"]
    entry_drop = round(100 * (dr["new_after"] / dr["new_before"] - 1), 1)
    exit_drop = round(100 * (dr["dep_after"] / dr["dep_before"] - 1), 1)
    print(f"   new authorizations {dr['new_before']:.0f} -> {dr['new_after']:.0f} "
          f"({entry_drop:+.1f}%)")
    print(f"   departures         {dr['dep_before']:.0f} -> {dr['dep_after']:.0f} "
          f"({exit_drop:+.1f}%)")
    check("the 2018 tightening shows as an entry collapse, not an exit spike",
          entry_drop < -30 and exit_drop > -30 and abs(entry_drop) > abs(exit_drop) * 2,
          f"entries {entry_drop:+.0f}% vs departures {exit_drop:+.0f}%")

    print("\n2. The size gradient, from post 2")
    eu = {r["store_type"]: r["pct"] for r in d2["entry_change_usda"]}
    for k in ("Small Grocery Store", "Convenience Store", "Medium Grocery Store",
              "Supermarket", "Large Grocery Store"):
        print(f"   {k:28} {eu[k]:>+6.1f}%")
    check("the fall sorted by how much stock a format already carried",
          eu["Small Grocery Store"] < eu["Medium Grocery Store"] - 30
          and eu["Large Grocery Store"] > -15)

    print("\n2b. The survival gradient, from post 6 (a different measure)")
    surv = {r["segment"]: r["rate"] for r in d6["survival"]}
    for k in ("chains that sell fuel", "other chains", "single-owner stores"):
        print(f"   {k:28} {surv[k]:>5.1f}%")
    check("survival is ordered by operator scale",
          surv["chains that sell fuel"] > surv["other chains"]
          > surv["single-owner stores"])

    print("\n3. The standard is more than doubling")
    o, n = POLICY["old_standard"], POLICY["new_standard"]
    print(f"   varieties per category  {o['varieties_per_category']} -> "
          f"{n['varieties_per_category']}")
    print(f"   categories needing a perishable  {o['perishable_categories']} -> "
          f"{n['perishable_categories']}")
    check("the variety requirement more than doubles",
          n["varieties_per_category"] >= 2 * o["varieties_per_category"],
          f"{o['varieties_per_category']} -> {n['varieties_per_category']}")
    check("the perishable requirement widens",
          n["perishable_categories"] > o["perishable_categories"])

    print("\n4. USDA's own forecast")
    im = POLICY["impact"]
    mult = round(im["stores_losing_authorization"] / im["baseline_annual_losses"], 1)
    print(f"   {im['stores_losing_authorization']:,} stores lose authorization vs "
          f"{im['baseline_annual_losses']:,} baseline = {mult}x")
    print(f"   compliance cost estimated at ${im['cost_year_one']} in year one")
    check("USDA projects a material increase in authorization losses", mult >= 2,
          f"{mult}x")
    POLICY["impact"]["multiple"] = mult

    print("\n5. Who took a position")
    for p in POLICY["positions"]:
        print(f"   {p['stance']:18} {p['who']} ({p['represents']})")
    stances = {p["stance"] for p in POLICY["positions"]}
    check("the record contains both support and opposition",
          {"supports", "opposes"} <= stances)
    check("the dollar chains are recorded as silent",
          any(p["stance"] == "no public comment" for p in POLICY["positions"]))

    out = {
        "policy": POLICY,
        "precedent": {"years": fl["years"], "new": fl["new"], "departed": fl["departed"],
                      "drivers": dr, "entry_pct": entry_drop, "exit_pct": exit_drop},
        "survival": d6["survival"],
        "entry_change_usda": d2["entry_change_usda"],
        "thin_markets": {"groups": d5["groups"], "density": d5["density"],
                         "total_loss": d5["total_loss"],
                         "presence": d5["presence"]},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post7.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post7.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("all checks passed")


if __name__ == "__main__":
    main()
