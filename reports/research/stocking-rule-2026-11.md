# Stocking rule: what we know as of November 9, 2026

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
- From the regulatory impact analysis (docket FNS-2025-0018-0236, verified for
  post 7): about 5,000 stores denied, about 4,500 expected to restock and
  reapply. **The time frame of the 5,000 is not verified;** the RIA returned
  403 this time.

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

- Regulatory impact analysis: https://www.regulations.gov/document/FNS-2025-0018-0236
- USDA rule page: https://www.fna.usda.gov/snap/retailer/stocking-standards-rule
  (403 for us; the independent check reported it loaded once and said stores
  that fall short "will be withdrawn" with no delay mentioned. Not confirmed.)
- USDA September guidance PDF (above)
- CSP Daily News, Nov. 4: https://www.cspdailynews.com/company-news/rule-take-effect-nov-4-could-prevent-food-stamp-use-convenience-stores
- NACS, Oct. 28: https://www.convenience.org/stay-current/news/2026/october/28/28
