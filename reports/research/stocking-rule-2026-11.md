# Stocking rule: what we know as of November 10, 2026

Sourced facts for the post's update section. Every item has a quote and a URL.
Items marked **not verified** could not be read at the source.

## The rule

- Final rule: "Updated Staple Food Stocking Standards for Retailers in the
  Supplemental Nutrition Assistance Program," 91 FR 25082, published May 8,
  2026. Effective July 7, 2026. "SNAP retailers must implement the provisions
  of this rule no later than November 4, 2026"
  Text read through the Federal Register API,
  https://www.federalregister.gov/api/v1/documents/2026-09137.json (raw text
  and full-text XML links). Page numbers below were checked against the XML.
- The standard: seven varieties in each of four staple categories (dairy;
  grains; protein; vegetables or fruits), three stocking units per variety,
  for 84 items, with perishables in at least three categories. The rule moves
  varieties per category from 3 to 7; the old floor of 36 items is 3 varieties
  x 4 categories x 3 units, the standard enforced before the rule. (Already verified for post 7, `src/analysis/post7_policy.py`,
  `POLICY["new_standard"]` and `POLICY["old_standard"]`.)
- "Butter and all jerky will be classified as accessory foods." (91 FR 25082)
- Plant-based dairy: "up to three distinct plant-based dairy alternative
  varieties that are each a substitute for a traditional dairy variety"
  can count. (91 FR 25084-85)
- Variety examples in the rule: "fresh tomatoes, 100% tomato juice, a can of
  diced tomatoes, and a jar of pasta sauce with tomatoes as the main
  ingredient all count as one 'tomato' variety" and "seasoned chicken breast
  is now a distinct variety from plain chicken breast." (91 FR 25083)

## How existing stores are checked (supports "not in the numbers yet")

- **Primary, 91 FR 25086:** "Current SNAP retailer locations authorized under
  criterion A will be assessed for compliance with the new stocking standards
  at reauthorization, which generally occurs within five years from the date
  of authorization and every five years thereafter."
- Same section: "180 days after this rule is published, new retailers or
  current SNAP retailers applying for authorization of a new store location
  will be assessed for compliance with the new stocking standards at
  authorization."
- Same section (91 FR 25086): "the Department may assess a retailer's eligibility for
  continued authorization at any time, as provided under current SNAP
  regulations at 7 CFR 278.1(j)."
- NACS (Aug. 10, 2026, trade group): "USDA inspectors can review stocking
  compliance during SNAP authorization reviews and other inspections."
  https://www.convenience.org/stay-current/news/2026/august/10/what-convenience-retailers-need-to-know-about-snap
- Delaware LIVE (Nov. 3, 2026): "Enforcement will not necessarily mean every
  existing store receives an inspection Wednesday."
  https://delawarelive.com/new-snap-stocking-rules-take-effect-wednesday-with-small-delaware-stores-facing-biggest-adjustment/

**What this supports.** The data snapshot is from November 5, one day after
the compliance date. Under the rule, existing stores are generally checked
when they come up for reauthorization, about once every five years, though
USDA may check any store at any time. So most existing stores had likely not
yet been assessed under the new standard by November 5. Some stores may have
left in anticipation of it; the data cannot say why any store left.

## What happens to a store that falls short

- 91 FR 25086: "Retailers who are denied authorization or reauthorization
  because they did not meet the staple foods stocking requirements will be
  required to wait six (6) months before applying for authorization again."
- 91 FR 25086: "Food items a retailer ordered or received up to 21 calendar
  days before the store visit will count towards meeting the stocking
  requirements as long as there is adequate documentation."
- Iowa Public Radio (Nov. 9, 2026) reports an appeals process for stores
  flagged as noncompliant (attributed to a source, not USDA).
  https://www.iowapublicradio.org/ipr-news/2026-11-09/snap-stocking-standards-food-security-federal-rules-department-of-agriculture-grocery-convenience-stores

## USDA's own estimate

- 91 FR 25087: "This rule will primarily affect small SNAP-authorized retailers
  (convenience stores, small grocery stores, and combination stores) who are
  currently authorized under Criterion A."
- Cost to current retailers: "approximately $77 million in the first year and
  about $1 to $2 million per year over the following four years." (91 FR 25087)

### Regulatory impact analysis (RIA)

"SNAP Retailer Stocking RIA - 3.19.26 CLEAN," docket document
FNS-2025-0018-0236, https://www.regulations.gov/document/FNS-2025-0018-0236 .
Eric downloaded it on Nov. 10, 2026; local copy in `reports/post8/` (not in
git). Page numbers are the PDF's own.

- Baseline denials (p. 16): "Roughly 2,000 do so annually under current
  standards, approximately 3.5 percent of those that apply or reapply."
- The 5,000 (p. 16): "during the transition to the new standards, an
  increased number of stores will likely lose authorization due to failure to
  meet the new stocking standard. ... We assume that more retailers may be
  denied under the new requirements, up to 5 percent. For the 99,192 stores
  that will need to add varieties, this amounts to around 5,000 stores that
  may be denied. We expect that most of these retailers will likely invest in
  stock to meet the new standards and apply for reauthorization."
- The 500 (p. 18): "The Department now assumes 10 percent of those denied may
  not reapply, or 500 stores."
- **Time frame.** The RIA does not give a period for the 5,000 in words. Its
  cost tables book all denial and reapplication costs in one year: "Total
  Federal Administrative Cost, 2027" (Table 8, p. 18), and government costs of
  $4 million in FY 2027 and $0 in FY 2028 to 2031 (Table 1, p. 2). FY 2027 runs
  October 1, 2026 to September 30, 2027. So USDA costed the denials as
  happening in FY 2027. That sits beside the rule's own statement that existing
  stores are assessed at reauthorization, about every five years (91 FR 25086).
- Effect on shoppers (p. 19): "the Department does not anticipate that many
  stores will leave the program due to this final rule."
- Exits expected (p. 2): "a few of these retailers may choose to exit the
  program rather than face the costs of compliance."
- Redemptions (p. 6, citing USDA's FY 2024 retailer dashboard): the small
  store types most affected make up "about 71 percent of SNAP-authorized
  retailers" but take "only about 11 percent of SNAP redemptions."
- Store visits (p. 10, note 9): "an FNS contractor making an unannounced visit
  to the store to capture photos of overall store inventory, aisles, store
  conditions and capture inventory counts on a survey form."
- Uncertainty (p. 19): denial estimates "are based on assumptions derived from
  current application and denial patterns. The actual values may be higher or
  lower than what is presented in this RIA."

### Regulatory flexibility analysis (small-business analysis)

"Regulatory Flexibility Analysis - Final Rule," docket document
FNS-2025-0018-0235. Eric downloaded it on Nov. 10, 2026; local copy in
`reports/post8/`. (FNS-2025-0018-0233 is an earlier version dated
September 25, 2025.)

- Stores in scope (p. 2): "Of the 60,335 combination stores, 119,688
  convenience stores, and 8,489 small grocery stores authorized under
  Criterion A to accept SNAP benefits in April 2025, almost all would fall
  under the Small Business Administration gross sales threshold."
- Share short of the new standard (p. 4): "53 % of small stores will not meet
  the new variety criteria," 99,192 of 188,512 small firms. By group, the share
  below 7 varieties: dairy 48%, protein 37%, grains 19%, fruits and vegetables
  17%. This is the share that would need to add items, not a forecast of exits.
- Source data (p. 3): STARS records for "121,294 currently authorized small
  SNAP-authorized firms which were authorized or reauthorized during calendar
  years 2022 to 2024," based on "the most recent store visit."
- Cost (pp. 5-7): about $15 a year in added stock for a store adding the
  average 5 varieties; "approximately $50 per year" for a store adding the
  most (13); about $400 in staff time per small store in the first year.
- Who may leave (p. 9): "stores may make the economic choice to opt out of
  SNAP. However, FNS anticipates that only those stores whose current SNAP
  redemptions are extremely low may make that choice."
- Lowest sellers (p. 8): 37,726 convenience stores fall in the bottom 30th
  percentile of SNAP redemptions; at the 10th percentile a convenience store
  redeemed "$3,350 in SNAP redemptions, 0.05% of Total Gross Sales" (2024).
- The 36-item floor (p. 2): "Under current law, (pursuant to annually repeated
  appropriations language since 2017), a store could stock as few as 36 food
  items."

## Guidance and the delay request

- USDA "did not issue official guidance to retailers until September 2026"
  (Iowa Public Radio, Nov. 9). The guidance PDF
  (`fna.snapRetailerNotice-StockingStandardsWebUpdates090426.pdf`) returned
  403: **contents not verified.** The FAQ and calculator are also not verified.
- Aug. 31: a letter on NACS, NATSO and SIGMA letterhead, signed by about 250
  companies (an independent count found about 247), asked USDA to defer
  enforcement until six months after guidance.
  https://nationalaglawcenter.org/wp-content/uploads/2026/09/retailers-snap-request-letter.pdf
- Iowa Public Radio (Nov. 9) says "a dozen Republican U.S. senators" warned
  the timeline was too fast, and separately that Sen. Chuck Grassley and other
  senators sent a letter in late September asking USDA "to delay enforcement
  for six months." It does not say all twelve signed. The letter: "If no delay is granted, tens of thousands of
  well-meaning retailers will be at risk of losing their SNAP authorization on
  day one." (Iowa Public Radio, Nov. 9)
- **No delay found.** Iowa Public Radio (Nov. 9) says the rule "went into
  effect Nov. 4" and does not report a USDA response to the delay requests. USDA's
  own pages returned 403, so a USDA statement after Nov. 4 is not verified.

## Not read (403 or not fetched)

- USDA rule page: https://www.fna.usda.gov/snap/retailer/stocking-standards-rule
  (403 for us; the independent check reported it loaded once and said stores
  that fall short "will be withdrawn" with no delay mentioned. Not confirmed.)
- USDA September guidance PDF (above)
- CSP Daily News, Nov. 4: https://www.cspdailynews.com/company-news/rule-take-effect-nov-4-could-prevent-food-stamp-use-convenience-stores
- NACS, Oct. 28: https://www.convenience.org/stay-current/news/2026/october/28/28
