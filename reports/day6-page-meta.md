# Day 6 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 6 of the series (post5, the last
chapter). Companion files: `reports/day0-page-meta.md` through
`day5-page-meta.md` and `reports/visualization-page-meta.md`.

Corrected November 10, 2026: ZIP codes are now padded to 5 digits, which adds places
in New England, New Jersey and the Virgin Islands. Numbers below are the corrected ones;
the live page carries a correction note at the top.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post5/post5.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
Twenty years drive two Americas further apart
```

## 2. Page subtitle

```
Grocery and pharmacy were more than half the food retail in these places. They are under a third now — and the towns that lost a grocery store have a median population of 1,984.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-6.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-6-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states on a dark ground. A faint grey field shows the 63,497 SNAP-authorized grocery stores open today, dense along both coasts and around cities. Brighter blue dots mark the 2,680 grocery stores that stood in 2006 in the 2,387 ZIP codes that now have none — scattered across the Plains and interior West, where little grey surrounds them. Text on the map reads: The Stores That Stayed. Day 6. 2,387 ZIP codes lost their last grocery store.
```

Short version if the field is tight:

```
Dot map of the lower 48: 2,680 grocery stores in blue that stood where 2,387 ZIP codes now have none, over a faint grey field of the 63,497 open today.
```

## 4. Meta title

45 characters — will not truncate.

```
Twenty Years Drive Two Americas Further Apart
```

## 5. Meta description

148 characters.

```
Grocery and pharmacy were half the food retail in these ZIP codes and are now under a third. The places that lost a grocery store have 1,984 people.
```

## 6. Meta keywords

```
food deserts, rural food access, grocery store closures, dollar stores, pharmacy deserts, SNAP retailers, geographic inequality, Thrifty Food Plan
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Twenty years drive two Americas further apart",
  "description": "Grocery and pharmacy were half the food retail in these ZIP codes and are now under a third. The places that lost a grocery store have 1,984 people.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 6,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["food deserts", "rural food access", "grocery store closures", "dollar stores", "pharmacy deserts", "SNAP retailers", "geographic inequality", "Thrifty Food Plan"],
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

Five images, in page order. The charts' alt text states the numbers, not just
the shape, so a screen reader gets the same facts a sighted reader does.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: grocery and chain pharmacy fell from 51% to 30% of the food retail in these ZIP codes between 2006 and 2025. 2,387 ZIP codes had a grocery store of any size in 2006 and have none today. 1,984 is the median population where the last grocery store went, against 15,612 where it stayed.
```

### `images/01-twenty-year-arc.png` (1259×688) — the arc

```
Line chart of SNAP-authorized stores by format across the 1,068 ZIP codes that lost their last chain pharmacy, 2006 to 2025. Convenience stores rise from 5,707 to 8,768. Grocery of every size falls from 5,567 to 4,662. Dollar stores climb from 497 to 2,138. Chain pharmacies peak at 1,291 in 2016 and fall to zero. Title: Dollar and convenience stores grew. Grocery and pharmacy did not.
```

### `images/02-mix-2006-2025.png` (1421×620) — the mix, then and now

```
Two donut charts comparing the format mix in the same ZIP codes. In 2006, across 12,707 stores: convenience 45%, grocery 44%, chain pharmacy 7%, dollar 4%. In 2025, across 15,568 stores: convenience 56%, grocery 30%, dollar 14%, and no chain pharmacies at all. Title: Grocery and pharmacy were half of this retail. Now they are under a third.
```

### `images/03-pharmacy-size.png` (1410×676) — pharmacy, by ZIP size

```
Box plot of ZIP code population for the 876 ZIP codes that had a chain pharmacy in 2006 and have none today, against the 5,834 that still have one. The losers' median is 15,391 and their middle half runs 8,142 to 26,214. The keepers' median is 28,057, middle half 17,863 to 40,352. Whiskers mark the 10th and 90th percentiles. Title: Smaller places lost their chain pharmacy.
```

### `images/04-grocery-size.png` (1396×676) — grocery, by ZIP size

```
Box plot of ZIP code population for the 2,340 ZIP codes that had a grocery store in 2006 and have none today, against the 14,357 that still have one. The losers' median is 1,984 and their middle half runs 972 to 3,883. The keepers' median is 15,612, middle half 5,796 to 29,858. The two barely overlap. Title: And far smaller places lost their grocery store.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The hero keys the middle headline figure: the grocery stores that stood, in
  2006, in the 2,387 ZIP codes with none today, over a faint field of every
  grocery store open now. The blue reads in the interior because those ZIP
  codes are small and far apart, which is the piece's finding drawn on a map.
  Regenerate with `python -m analysis.hero 6`.
- The four named towns — Mount Clemens MI, Glassport PA, Yorkville OH,
  Whitesville WV — are checkable by anyone who lives there. They count chain
  pharmacies only, and grocery means a SNAP-authorized store in one of USDA's
  five grocery formats; a specialty shop or farmers' market does not count.
- Both size charts start from 2006, the earliest year in the data, so they ask
  the same question of each format. That is why the pharmacy count is 876
  rather than the 1,068 the rest of the piece uses — different window, stated in
  the body.
- The closing section names **yesterday evening's Nvidia earnings release**.
  That only works if the post goes out the morning after Nvidia reports.
  Confirm before scheduling; otherwise cut the word "yesterday evening's".
- The $229 weekly figure is the Thrifty Food Plan for a family of four, FY2026.
