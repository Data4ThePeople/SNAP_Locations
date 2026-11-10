"""Epilogue — what the benefit assumes, and what changes in November 2026.

Split out of post 5, which had grown two sections that do a different job from
the rest of the series. Everything before this point is measurement. This piece
is the policy consequence, and it rests on two things the SNAP retailer file
cannot see:

  1. What is on a shelf. The authorization record has no assortment, so the
     question "can the Thrifty Food Plan basket be bought here?" is posed and
     explicitly left unanswered. No estimate is made.
  2. What has not happened yet. The stocking rule's compliance date is
     November 4, 2026, so the predictions here are stated before the fact and
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

from analysis.post4_pharmacy import DRUG_BRANDS
from config import ROOT

OUT = ROOT / "reports" / "data"

# Every external fact this piece uses, with its source. Kept as data so the
# rendered prose cannot drift from what was actually verified.
POLICY = {
    "tfp": {
        "reevaluated": 2021,
        "previous": 2006,
        "directive": "Agriculture Improvement Act of 2018 (2018 Farm Bill)",
        "effective": "October 1, 2021",
        "reference_family": "a man and a woman 20 to 50 years old, a child 6 to 8, "
                           "and a child 9 to 11",
        "seafood_weekly_cost": 12.80,
        "seafood_note": "most expensive category; the plan assumes low-cost choices "
                        "and names tilapia or canned tuna as examples",
        "url": "https://www.fna.usda.gov/cnpp/thrifty-food-plan-2021",
        "source": "Thrifty Food Plan, 2021 (USDA FNS-916, August 2021)",
    },
    "old_standard": {
        "varieties_per_category": 3,
        "categories": 4,
        "units_per_variety": 3,
        "total_varieties": 12,
        "total_items": 36,
        "perishable_items": 6,
        "perishable_categories": 2,
        # NOT a rule USDA wrote. This is the pre-2014-Farm-Bill standard that
        # section 765 ordered FNS to keep applying until it widened the
        # definition of "variety" — the codified CFR text said seven varieties
        # throughout, and the 36 units are the appropriations fallback that was
        # actually enforced.
        "url": "https://www.govinfo.gov/app/details/PLAW-115publ31",
        "source": "the pre-2014 standard, applied under section 765 of the "
                  "Consolidated Appropriations Act, 2017 (P.L. 115-31) and the "
                  "same provision in every later agriculture appropriations act",
    },
    # The chain from statute to enforcement, each link checked against the
    # Statutes at Large and the Federal Register. Three things here are easy to
    # get wrong and were: the rider blocked "variety" and BREADTH of stock but
    # never depth; there was no 2017 or 2018 replacement rule, only the 2016
    # rule's implementation deadline; and the rider never lapsed — it is in the
    # FY2026 act, and USDA satisfied its condition instead.
    # Set this to the day the post goes out. "N days out" is computed from it,
    # so the figure is reproducible instead of changing on every rebuild.
    "post_date": "2026-08-29",
    # The variety question, as it actually stands. Written after a fact-check
    # overturned the first draft of this section: the rule DOES define variety,
    # in detail, and it resolves the obvious cases (different cuts of meat are
    # one variety; cream and milk are two). No evidence was found that draft
    # guidance exists or keeps changing — the docket has had no activity since
    # the rule published. The real, documented problem is that the promised
    # guidance never came and USDA's own retailer pages still teach the old
    # standard.
    "variety": {
        "citation": "7 CFR 278.1(b)(1)(ii)(C)-(E)",
        "url": "https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-C/part-278/section-278.1",
        # The two pages a retailer or inspector actually opens for the standard
        # itself. Both still carried the pre-rule numbers and USDA's own
        # not-up-to-date banner when checked on August 27, 2026.
        "stale_pages": ["https://www.fna.usda.gov/snap/retailer/eligible",
                        "https://www.fna.usda.gov/snap/retailer/staple-foods"],
        "cuts_of_meat": "different cuts of meat",
        "cream": "Cream is a separate main ingredient from milk",
        "whole_grain": "may contain any amount of whole grain",
        "usda_protein_example": "chicken breast, ground beef, frozen salmon filets, "
                                "canned tuna, eggs, peanut butter, and lentils",
        "usda_grain_example": "sourdough bread, corn tortillas, whole grain spaghetti, "
                              "quick-cook oats, brown rice, pearled barley, and white flour",
        "guidance_promised": "We will update our website with guidance for retailers soon.",
        "guidance_promised_date": "May 8, 2026",
        "stale_banner": "Attention: Some content on this page is not up to date.",
        "stale_pages_say": "a minimum of 36 staple food items, three varieties per "
                           "category, and that chocolate milk and regular milk count "
                           "as one variety",
        "docket_quiet_since": "May 8, 2026",
        # The page carrying the promise stamps its own last-updated date at
        # the foot, which makes the claim checkable by any reader in one
        # click. Quoted in the page's own format rather than the house one.
        "page_updated_stamp": "Page updated: May 08, 2026",
        "page_updated_checked": "August 27, 2026",
        "source": "91 FR 25082 regulatory text; fns.usda.gov/snap/retailer/eligible and "
                  "/staple-foods, both still carrying the pre-rule standard and a "
                  "not-up-to-date banner as of August 27, 2026",
    },
    "industry": {
        "nacs_day_one": "raises more questions than it answers",
        "nacs_august": "USDA has not published detailed guidance to help retailers "
                       "understand how products will be categorized and enforced",
        "nacs_disputes": "could create confusion for both retailers and inspectors, "
                         "increasing the likelihood of disputes during compliance reviews",
        "nacs_ask": "delay enforcement until six months after formal guidance is released",
        "nacs_day_one_url": "https://www.convenience.org/stay-current/news/2026/"
                            "may/8/usda-releases-complex-overhaul-of-snap-stocking-requirements",
        "nacs_august_url": "https://www.convenience.org/stay-current/news/2026/"
                           "august/10/what-convenience-retailers-need-to-know-about-snap",
        "senate_sponsor": "Sen. Jim Justice (R-WV)",
        "senate_vote": "10-11",
        "senate_vote_date": "August 6, 2026",
        "cstores_snap": 118000,
        "cstore_sqft": 3600,
        "source": "NACS, 8 May and August 10, 2026; Senate Agriculture Committee markup, "
                  "August 6, 2026",
    },
    "history": {
        "directive_act": "Agricultural Act of 2014",
        "directive_cite": "Pub. L. 113-79, section 4002(a)",
        "directive_date": "February 7, 2014",
        "directive_codified": "7 U.S.C. 2012(o)(1)(A)",
        "rule_2016_cite": "81 FR 90675",
        "rule_2016_published": "December 15, 2016",
        "rule_2016_effective": "January 17, 2017",
        "rule_2016_existing_stores": "January 17, 2018",
        "rider_cite": "section 765 of the Consolidated Appropriations Act, 2017 "
                      "(P.L. 115-31)",
        "rider_date": "May 5, 2017",
        "rider_blocked": "variety and breadth of stock",
        "rider_latest": "section 726 of Division B of P.L. 119-37",
        "rider_latest_date": "November 12, 2025",
        "proposed_2025_cite": "90 FR 46081",
        "proposed_2025_date": "September 25, 2025",
        # Every URL below was resolved and read, not inferred from a citation
        # pattern. The two Federal Register documents came from the FR API by
        # docket, and the three public laws from govinfo by PLAW id.
        "directive_url": "https://www.govinfo.gov/app/details/PLAW-113publ79",
        "rule_2016_url": "https://www.federalregister.gov/documents/2016/12/15/2016-29837/enhancing-retailer-standards-in-the-supplemental-nutrition-assistance-program-snap",
        "rider_url": "https://www.govinfo.gov/app/details/PLAW-115publ31",
        "rider_latest_url": "https://www.govinfo.gov/app/details/PLAW-119publ37",
        "proposed_2025_url": "https://www.federalregister.gov/documents/2025/09/25/2025-18624/updated-staple-food-stocking-standards-for-retailers-in-the-supplemental-nutrition-assistance",
        "source": "Statutes at Large and the Federal Register, verified against "
                  "govinfo",
    },
    "new_standard": {
        "varieties_per_category": 7,
        "categories": 4,
        "perishable_categories": 3,
        "total_varieties": 28,
        "units_per_variety": 3,
        "total_items": 84,
        "perishable_items": 9,
        "category_names": "dairy, fruits or vegetables, grains, and protein",
        "published": "May 8, 2026",
        "effective": "July 7, 2026",
        "compliance": "November 4, 2026",
        "docket": "FNS-2025-0018",
        "directive": "Agricultural Act of 2014",
        "blocked": "the same seven-variety expansion was blocked by Congress in 2017",
        "citation": "91 FR 25082",
        "url": "https://www.federalregister.gov/documents/2026/05/08/2026-09137/updated-staple-food-stocking-standards-for-retailers-in-the-supplemental-nutrition-assistance",
        "usda_page": "https://www.fna.usda.gov/snap/retailer/stocking-standards-rule",
        "source": "Updated Staple Food Stocking Standards for Retailers in the "
                  "Supplemental Nutrition Assistance Program, final rule, "
                  "91 FR 25082 (May 8, 2026)",
    },
    # Every figure below is from the RIA filed in the docket as a supporting
    # document, NOT from the Federal Register notice — the notice carries the
    # totals but none of the store-level projections. Docket FNS-2025-0018,
    # document FNS-2025-0018-0236, "SNAP Retailer Stocking RIA - 3.19.26".
    #
    # Two corrections live here, both caught by reading the RIA rather than the
    # notice:
    #  - Cost was 262 dollars, which is the SEPTEMBER 2025 PROPOSED rule. The
    #    final rule revised small-retailer cost up to 407 in year one and 482
    #    over five years.
    #  - The 5,000 figure is DENIALS, not permanent losses. USDA "expect[s] that
    #    most of these retailers will likely invest in stock to meet the new
    #    standards and apply for reauthorization", and budgets for 4,500
    #    reauthorizations. The projected net permanent loss is therefore about
    #    500, and any claim that 5,000 stores will be lost misreads the source.
    "impact": {
        "stores_denied": 5000,
        "reauthorizations_expected": 4500,
        "net_permanent_loss": 500,
        "baseline_annual_denials": 2000,
        "baseline_denial_rate_pct": 3.5,
        "new_denial_rate_pct": 5.0,
        "stores_needing_varieties": 99_192,
        "small_firms": 188_512,
        "large_firms": 80_705,
        "cost_year_one_small": 407,
        "cost_five_years_small": 482,
        "cost_year_one_large": 24,
        "cost_retailers_total_musd": 77,
        "cost_government_musd": 4,
        # USDA's own justification for why the losses would not matter. This is
        # the argument the rest of the series is a response to.
        "small_share_of_redemptions_pct": 11,
        "small_share_of_retailers_pct": 71,
        "large_share_of_redemptions_pct": 74,
        "large_share_of_retailers_pct": 15,
        "rfa_finding": "no significant economic impact on a substantial number of "
                       "small entities",
        "url": "https://www.regulations.gov/document/FNS-2025-0018-0236",
        "docket_url": "https://www.regulations.gov/docket/FNS-2025-0018",
        "source": "USDA regulatory impact analysis for the final rule, docket "
                  "FNS-2025-0018 document 0236 (March 19, 2026)",
    },
    "need_for_access": {
        "citation": "7 CFR 278.1",
        "factors": "how close the store came to compliance, distance to the next "
                   "authorized store, local vehicle access, operating hours, and "
                   "violation history",
        "catchall": "any other factors which the FNS officer in charge considers "
                    "pertinent",
        "methodology_published": False,
        "url": "https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-C/part-278/section-278.1",
        "source": "SNAP retailer eligibility regulations; FRAC analysis",
    },
    "positions": [
        {"who": "FMI – The Food Industry Association", "represents": "supermarkets",
         "stance": "supports"},
        {"who": "National Grocers Association", "represents": "independent supermarkets",
         "stance": "supports"},
        {"who": "NACS, NATSO and SIGMA", "represents": "convenience and fuel retailers", "stance": "opposes",
         "note": "filed jointly on November 24, 2025; called compliance unworkable for "
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
    # The closing cites congressional stock trading. One source, deliberately:
    # the Times investigation is defined by committee assignment rather than by
    # party and states its bipartisan finding outright, which is what the text
    # claims. A ProPublica piece was cited here too and was dropped — it is an
    # investigation of one administration's appointees, so it neither supported
    # "elected officials of both parties" nor kept the piece free of a partisan
    # frame the rest of it does not have.
    "trading": {
        "nyt_url": "https://www.nytimes.com/interactive/2022/09/13/us/politics/"
                   "congress-members-stock-trading-list.html",
        # Not quoted in the text — the closing links the investigation rather
        # than citing its numbers. Kept as the record of what it found.
        "nyt_members": 97,
        "nyt_trades": 3700,
        "nyt_years": "2019-2021",
        "nyt_source": "\"These 97 Members of Congress Reported Trades in Companies "
                      "Influenced by Their Committees,\" The New York Times, "
                      "September 13, 2022",
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
    mult = round(im["stores_denied"] / im["baseline_annual_denials"], 1)
    print(f"   {im['stores_denied']:,} denials vs {im['baseline_annual_denials']:,} "
          f"baseline = {mult}x; {im['reauthorizations_expected']:,} reauthorizations "
          f"expected, so net permanent loss ~{im['net_permanent_loss']:,}")
    print(f"   {im['stores_needing_varieties']:,} stores must add varieties; "
          f"${im['cost_year_one_small']} year one for a small retailer")
    print(f"   small stores: {im['small_share_of_retailers_pct']}% of retailers, "
          f"{im['small_share_of_redemptions_pct']}% of redemptions")
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
    # ------------------------------------------------------------ worst case
    # What the map looks like if the three formats most exposed to the stocking
    # standard gave up their authorizations. This is NOT a forecast — USDA's own
    # projection is a net loss of about 500 stores. It is the ceiling: the most
    # that could be lost if the variety definition lands as strictly as it can.
    # Staged, because the stages are the argument: convenience is the format
    # experts think is genuinely at risk, and the dollar store is the tail.
    from analysis import panel as _panel, rucc as _rucc
    from analysis.post5_synthesis import zcta_population as _zpop
    from collections import Counter as _C
    con = _panel.build()
    _pop = _zpop()
    _lookup, _ = _rucc.load()
    _DRUG = ",".join(f"'{b}'" for b in DRUG_BRANDS)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE cur AS
        SELECT DISTINCT p.record_id, lpad(trim(p.zip_code), 5, '0') AS zip, p.state, p.county,
               CASE WHEN p.format = 'Convenience Store' THEN 'conv'
                    WHEN p.format = 'Dollar Store' THEN 'dollar'
                    WHEN p.brand IN ({_DRUG}) THEN 'rx' ELSE 'other' END AS grp
        FROM panel p JOIN fact_spell f ON f.record_id = p.record_id AND NOT f.date_anomaly
        WHERE f.auth_date <= DATE '2025-12-31'
          AND (f.end_date IS NULL OR f.end_date >= DATE '2025-12-31')
          AND p.zip_code IS NOT NULL AND length(trim(p.zip_code)) BETWEEN 3 AND 5""")
    con.execute("CREATE OR REPLACE TEMP TABLE zpop (zip VARCHAR, pop BIGINT)")
    con.executemany("INSERT INTO zpop VALUES (?, ?)", list(_pop.items()))
    stores = {g: int(n) for g, n in
              con.execute("SELECT grp, count(*) FROM cur GROUP BY 1").fetchall()}
    base_zips, = con.execute("SELECT count(DISTINCT zip) FROM cur").fetchone()
    stages = {}
    for key, keep in (("conv", "grp <> 'conv'"),
                      ("conv_rx", "grp NOT IN ('conv','rx')"),
                      ("all", "grp = 'other'")):
        zz = [r[0] for r in con.execute(
            f"""SELECT DISTINCT zip FROM cur
                WHERE zip NOT IN (SELECT zip FROM cur WHERE {keep})""").fetchall()]
        stages[key] = {"zips_to_zero": len(zz),
                       "population": sum(_pop[z] for z in zz if z in _pop)}
    # The scenario the piece actually models: convenience stores give up
    # authorization, dollar stores and chain pharmacies do not. Everything
    # published below is computed against this and nothing else.
    KEEP = "grp <> 'conv'"
    zeroed = {r[0] for r in con.execute(
        f"""SELECT DISTINCT zip FROM cur
            WHERE zip NOT IN (SELECT zip FROM cur WHERE {KEEP})""").fetchall()}
    zc = {}
    for z, st, ct, n in con.execute(
            "SELECT zip, state, county, count(*) FROM cur GROUP BY 1,2,3").fetchall():
        k = _lookup(st, ct)
        if k:
            zc.setdefault(z, _C())[k] += n
    metro = sum(1 for z in zeroed if z in zc and zc[z].most_common(1)[0][0] <= 3)
    nonmetro = sum(1 for z in zeroed if z in zc and zc[z].most_common(1)[0][0] > 3)
    states = [{"state": s, "lost": int(l), "total": int(tt),
               "pct": round(100 * l / tt, 1)}
              for s, l, tt in con.execute(f"""
        WITH z AS (SELECT DISTINCT zip, state FROM cur),
             k AS (SELECT DISTINCT zip FROM cur WHERE {KEEP})
        SELECT z.state, count(*) FILTER (WHERE k.zip IS NULL), count(*)
        FROM z LEFT JOIN k USING(zip) GROUP BY 1
        HAVING count(*) >= 100 ORDER BY 2 DESC""").fetchall()]
    # By ZIP population, which is the thread the whole series pulls on. The
    # state ranking is still computed above but is not charted: it mostly
    # measures how rural a state is, and says it less clearly than this does.
    bands = [{"band": b, "zips": int(tt), "zeroed": int(z), "population": int(pp or 0),
              "pct": round(100 * z / tt, 1)}
             for b, tt, z, pp in con.execute(f"""
        WITH z AS (SELECT DISTINCT zip FROM cur),
             k AS (SELECT DISTINCT zip FROM cur WHERE {KEEP}),
             b AS (SELECT z.zip, p.pop, k.zip IS NULL AS zeroed,
                          CASE WHEN p.pop < 1000 THEN 'under 1,000'
                               WHEN p.pop < 2500 THEN '1,000 to 2,500'
                               WHEN p.pop < 5000 THEN '2,500 to 5,000'
                               WHEN p.pop < 10000 THEN '5,000 to 10,000'
                               WHEN p.pop < 25000 THEN '10,000 to 25,000'
                               ELSE '25,000 and up' END AS band,
                          CASE WHEN p.pop < 1000 THEN 1 WHEN p.pop < 2500 THEN 2
                               WHEN p.pop < 5000 THEN 3 WHEN p.pop < 10000 THEN 4
                               WHEN p.pop < 25000 THEN 5 ELSE 6 END AS ord
                   FROM z LEFT JOIN k USING(zip) JOIN zpop p ON p.zip = z.zip)
        SELECT band, count(*), count(*) FILTER (WHERE zeroed),
               sum(pop) FILTER (WHERE zeroed)
        FROM b GROUP BY band, ord ORDER BY ord""").fetchall()]
    med = {}
    for lab, w in (("zeroed", "k.zip IS NULL"), ("kept", "k.zip IS NOT NULL")):
        r = con.execute(f"""
            WITH z AS (SELECT DISTINCT zip FROM cur),
                 k AS (SELECT DISTINCT zip FROM cur WHERE {KEEP})
            SELECT count(*), median(p.pop) FROM z LEFT JOIN k USING(zip)
            JOIN zpop p ON p.zip = z.zip WHERE {w}""").fetchone()
        med[lab] = {"n": int(r[0]), "median_pop": int(r[1])}
    print("\n   by ZIP population:")
    for b in bands:
        print(f"     {b['band']:18} {b['zeroed']:>5,} of {b['zips']:>6,}  ({b['pct']:5.1f}%)")
    print(f"     median population — left with nothing {med['zeroed']['median_pop']:,}, "
          f"keeps a retailer {med['kept']['median_pop']:,}")
    check("the smallest ZIP codes are hit far hardest",
          bands[0]["pct"] > 10 * bands[-1]["pct"])

    out["worst_case"] = {
        "bands": bands, "median": med,
        "stores_total": sum(stores.values()), "stores_by_group": stores,
        "stores_at_risk": sum(v for k, v in stores.items() if k != "other"),
        "stores_remaining": stores.get("other", 0),
        "base_zips": int(base_zips), "stages": stages,
        "zeroed_metro": metro, "zeroed_nonmetro": nonmetro,
        "zeroed_nonmetro_pct": round(100 * nonmetro / (metro + nonmetro), 1),
        "states": states,
    }
    import datetime as _dt
    _pd = _dt.date.fromisoformat(POLICY["post_date"])
    _imp = _dt.date(2026, 11, 4)
    out["policy"]["days_to_implementation"] = (_imp - _pd).days
    out["policy"]["days_since_rule"] = (_pd - _dt.date(2026, 5, 8)).days
    print(f"\n   {out['policy']['days_to_implementation']} days from "
          f"{POLICY['post_date']} to the 4 November implementation date")

    w = out["worst_case"]
    print("\nWorst case: the three exposed formats give up authorization")
    print(f"   {w['stores_at_risk']:,} of {w['stores_total']:,} stores "
          f"({100*w['stores_at_risk']/w['stores_total']:.1f}%) would go")
    for k, lab in (("conv", "convenience only"), ("conv_rx", "+ chain pharmacies"),
                   ("all", "+ dollar stores")):
        s = stages[k]
        print(f"   {lab:20} {s['zips_to_zero']:>6,} ZIPs to zero, "
              f"{s['population']:>12,} people")
    print(f"   of the {len(zeroed):,} zeroed ZIPs, {w['zeroed_nonmetro_pct']}% are nonmetro")
    check("worst case removes more than half of all authorized stores",
          w["stores_at_risk"] > w["stores_total"] / 2)
    # The staging is the argument: the dollar store is what makes it a disaster.
    check("dollar stores more than double the ZIPs left with nothing",
          stages["all"]["zips_to_zero"] > 2 * stages["conv_rx"]["zips_to_zero"])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "post7.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'post7.json'}")
    if FAILURES:
        raise SystemExit("FAILED: " + ", ".join(FAILURES))
    print("all checks passed")


if __name__ == "__main__":
    main()
