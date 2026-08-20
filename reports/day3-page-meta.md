# Day 3 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 3 of the series (post6, convenience
stores and gas stations). Companion files: `reports/day0-page-meta.md`,
`reports/day1-page-meta.md`, `reports/day2-page-meta.md`, and
`reports/visualization-page-meta.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post6/post6.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
Convenience stores thrived, but with an advantage few others had
```

## 2. Page subtitle

```
The convenience store looks like the format that beat the odds — huge, growing, and mostly independent. Split it open and the winners are the fuel-selling chains, riding a pump margin that doubled after 2020 and never came back down.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-3.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-3-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states showing SNAP-authorized convenience stores in 2025, with national counts: 40,540 chain stores in orange over 51,003 single-owner stores in grey, dense along the coasts, Texas and the Southeast. Text on the map reads: The Stores That Stayed. Day 3. Convenience stores, 2025.
```

Short version if the field is tight:

```
Dot map of SNAP-authorized convenience stores in 2025: 40,540 chain stores in orange, 51,003 single-owner stores in grey.
```

Note: the hero's chain/single-owner split is by inferred ownership and leaves
~25,000 unclassifiable stores undrawn; the post's own segments (fuel chains,
other chains, single-owner) are brand-based. The two counts are not meant to
reconcile with the body text.

## 4. Meta title

60 characters — at the truncation edge but should hold.

```
Convenience Stores Thrived, With an Advantage Few Others Had
```

## 5. Meta description

147 characters.

```
Fuel-selling convenience chains grew 258% and kept 78.7% of their stores, powered by fuel margins that doubled after 2020 and never came back down.
```

## 6. Meta keywords

```
convenience stores, gas stations, fuel margins, SNAP retailers, Wawa, Sheetz, Casey's, food access
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Convenience stores thrived, but with an advantage few others had",
  "description": "Fuel-selling convenience chains grew 258% and kept 78.7% of their stores, powered by fuel margins that doubled after 2020 and never came back down.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 3,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["convenience stores", "gas stations", "fuel margins", "SNAP retailers", "Wawa", "Sheetz", "Casey's", "food access"],
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

Four images, in page order. The charts' alt text states the numbers, not just
the shape, so a screen reader gets the same facts a sighted reader does.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: a +258% change in chains that sell fuel since 2006. 78.7% of their 2008–2012 stores are still authorized, against 14.2% for single-owner stores. +103% growth in Murphy USA's fuel margin per gallon after 2020.
```

### `images/01-growth-by-owner.png` (1255×688) — indexed growth

```
Line chart of stores authorized on 31 December of each year, indexed to 100 in 2006. Dollar stores, the benchmark, reach 407 by 2025. Chains that sell fuel track them closely, reaching 358. Other chains reach 263. Single-owner stores flatten after 2013 and end at 160. Title: Only the fuel chains kept pace with the dollar store.
```

### `images/02-fuel-margin.png` (1131×688) — fuel margins

```
Line chart of retail fuel margin in cents per gallon from company 10-K filings, 2016 to 2025. Casey's, in green, climbs from about 19 cents before 2020 to a plateau near 39. Murphy USA, in blue, climbs from about 13 cents to a plateau near 28. Both roughly double after 2020 and neither returns to its old range. Title: Fuel profit doubled after 2020 and stayed there.
```

### `images/03-survival-by-owner.png` (1405×564) — cohort survival

```
Horizontal bar chart of the share of stores first authorized 2008–2012 still authorized in 2025. Chains that sell fuel, highlighted in blue: 78.7%. Dollar stores: 78.2%. Other chains: 33.1%. Single-owner stores, highlighted in pink: 14.2%. Title: A chain store stays. A single-owner store usually does not.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The growth disclaimer near the top of the post ("growth means SNAP-authorized
  stores, not store counts") is live text and load-bearing — do not drop it in
  layout.
- The 1973 fuel-crisis line near the close is editorial ("in our view") and can
  link to existing D4TP fuel coverage if a link slot is available.
