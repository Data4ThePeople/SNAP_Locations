# Day 7 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 7 of the series (post7, the
epilogue). Companion files: `reports/day0-page-meta.md` through
`day6-page-meta.md` and `reports/visualization-page-meta.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post7/post7.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
Sizing the risk to SNAP of the imminent stocking rule changes
```

## 2. Page subtitle

```
An epilogue. A stocking standard twelve years in the making, the guidance that still has not arrived, and a map of who would bear the risk if it goes wrong.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-7.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-7-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states on a dark ground, one dot per ZIP code. A faint grey field shows the ZIP codes that would still have a SNAP-authorized retailer if every convenience store gave up its authorization, clustering into cities. Pink dots mark the ZIP codes that would have none, scattered across the interior West, the northern Plains and the rural East. Text on the map reads: The Stores That Stayed. Day 7. ZIP codes left with no SNAP retailer 2,871. If the convenience stores go.
```

Short version if the field is tight:

```
Dot map of the lower 48 showing, in pink, the 2,871 ZIP codes that would be left with no SNAP retailer at all if every convenience store gave up its authorization.
```

## 4. Meta title

Deliberately not the H1. Its only job is to survive a search result, so it front-loads
the term people search and stays clear of the ~60-character display cut.

47 characters — will not truncate.

```
The Imminent Stocking Rule and the Risk to SNAP
```

## 5. Meta description

157 characters.

```
A new SNAP stocking standard takes effect November 4. Model the scenario and 2,871 ZIP codes, home to 5.3 million people, would have no SNAP retailer at all.
```

## 6. Meta keywords

```
SNAP stocking standards, SNAP retailers, food access, convenience stores, rural food access, USDA rulemaking, 7 CFR 278.1, staple foods, food deserts
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Sizing the risk to SNAP of the imminent stocking rule changes",
  "description": "A new SNAP stocking standard takes effect November 4. Model the scenario and 2,871 ZIP codes, home to 5.3 million people, would have no SNAP retailer at all.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 7,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["SNAP stocking standards", "SNAP retailers", "food access", "convenience stores", "rural food access", "USDA rulemaking", "7 CFR 278.1", "staple foods", "food deserts"],
  "author": {
    "@type": "Person",
    "name": "Eric Pachman",
    "url": "https://www.data4thepeople.com/authors/eric-pachman"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Data 4 The People",
    "url": "https://data4thepeople.com"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://www.data4thepeople.com/p/[[slug]]/"
  }
}
```

## 8. In-body images and alt text

Three images, in page order. The charts' alt text states the numbers, not just
the shape, so a screen reader gets the same facts a sighted reader does.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: 5.3 million people live in a ZIP code that would have no SNAP retailer at all if convenience stores drop out. $407 is what USDA estimates it costs a small store to comply in the first year. November 4 is the 2026 date by which every SNAP retailer has to meet the new standard.
```

### `images/01-worst-case-map.png` (1615×1060) — the places left with no SNAP retailer

```
Dot map of the lower 48, one dot per ZIP code. Faint grey marks the 19,074 ZIP codes that would still have a SNAP-authorized retailer if every convenience store gave up its authorization. Pink marks the 2,782 that would have none, scattered thickly across the interior, the Plains and the rural East while cities stay grey. Title: The places that would be left with no SNAP retailer. A note says this is a ceiling rather than a forecast, and that 2,871 ZIP codes are affected nationally.
```

### `images/02-worst-case-bands.png` (1547×694) — by ZIP code population

```
Horizontal bar chart of the share of ZIP codes that would be left with no SNAP-authorized retailer if every convenience store gave up its authorization, by 2020 census population. Under 1,000 people: 49.8%, or 1,310 of 2,628. 1,000 to 2,500: 22.8%, 924 of 4,061. 2,500 to 5,000: 9.1%, 305 of 3,335. 5,000 to 10,000: 5.6%, 167 of 2,999. 10,000 to 25,000: 1.3%, 58 of 4,338. 25,000 and up: 0.1%, 5 of 4,558. Title: It lands almost entirely on the smallest places.
```

## Notes

- The hero keys the chapter's own finding and uses the same unit as its map:
  one dot per ZIP code, pink for the places left with no SNAP retailer at all
  if convenience stores give up authorization. It replaces an earlier frame
  built on 157,889 "small formats", a figure the piece no longer contains —
  it models convenience stores alone. Dots are the lower 48 and the keyed
  count is national, per the series convention stated in the corner note.
  Regenerate with `python -m analysis.hero 7`.
- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- **Two numbers differ on purpose and should not be "corrected" to match.** The
  map key reads 2,782 ZIP codes while the body says 2,871. The map draws the
  lower 48; the count is national. The gap is Alaska, Hawaii and stores without
  usable coordinates, and it is stated in the map's corner note and again in
  Limits.
- **The post is dated August 29, 2026** in the pipeline (`POLICY["post_date"]`
  in `src/analysis/post7_policy.py`), and two figures are computed from it: the
  67 days to the November 4 compliance date, and the 113 days since the rule
  published. If the publication date moves, change `post_date` and rebuild, or
  both numbers will be wrong.
- Every rule, statute and regulation in the body is linked to its primary
  source — 19 links, each resolved rather than inferred. The Federal Register
  documents came from the FR API by docket, the public laws from govinfo, and
  7 CFR 278.1 was confirmed against the eCFR API. Two links return 403 to
  automated checkers but are correct: the New York Times interactive (paywall)
  and regulations.gov (blocks non-browser clients).
- **USDA links point at `fna.usda.gov`, not `fns.usda.gov`.** The Food and
  Nutrition Service was renamed the Food and Nutrition Administration on
  June 1, 2026. The old host still redirects, but the canonical URLs have moved
  and the data download page is now `/snap/retailer-locator/data`.
- The closing section is Eric's. The only editorial additions are the two
  citation links and the sentence attributing the count of 97 members to the
  Times; a check in the pipeline pins "nearly a fifth" to 97 of 535.
- This is the last chapter. `post0_roadmap.py` reads the first line of
  `reports/post7/post7.md` for the roadmap card headline, so the H1 above
  propagates to the series index on rebuild.
