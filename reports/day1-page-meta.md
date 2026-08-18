# Day 1 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 1 of the series (post2, small
grocery). Companion files: `reports/day0-page-meta.md` for the announcement
page and `reports/visualization-page-meta.md` for the map page.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post2/post2.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
One in four of the smallest grocery stores is gone
```

## 2. Page subtitle

```
SNAP-authorized retailers, 2006–2025, checked against Census County Business Patterns. 14,795 small grocery stores in 2012, 7,987 today.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-1.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-1-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states showing SNAP-authorized small grocery stores, with national counts: 12,957 that left SNAP since 2006 in coral, 690 authorized in 2006 and still authorized in grey, and 7,297 newly authorized since 2006 in grey. The departures cluster in the Northeast, California, Florida and Texas. Text on the map reads: The Stores That Stayed. Day 1. Small grocery.
```

Short version if the field is tight:

```
Dot map of small grocery stores in SNAP: 12,957 left since 2006, shown in coral against the stores that remain.
```

## 4. Meta title

50 characters — will not truncate.

```
One in Four of the Smallest Grocery Stores Is Gone
```

## 5. Meta description

158 characters.

```
Small grocery stores fell 25% by the Census Bureau's count and 46% in SNAP's own records. Where the gap comes from, and the stocking rule that may explain it.
```

## 6. Meta keywords

```
small grocery stores, SNAP retailers, grocery store closures, food access, USDA stocking requirements, corner stores, bodegas
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "One in four of the smallest grocery stores is gone",
  "description": "Small grocery stores fell 25% by the Census Bureau's count and 46% in SNAP's own records. Where the gap comes from, and the stocking rule that may explain it.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 1,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["small grocery stores", "SNAP retailers", "grocery store closures", "food access", "USDA stocking requirements", "corner stores", "bodegas"],
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
Three headline figures: a 25% fall in the number of small grocery businesses from 2012 to 2023, by the Census Bureau's count. A 46% fall in SNAP's own Small Grocery category over the same years. A 58% fall in the number of small grocers signing up for SNAP each year.
```

### `images/01-small-grocery-arc.png` (1255×688) — the arc

```
Line chart of small grocery stores with an active SNAP authorization on 31 December of each year, 2007 to 2025. The line rises to a peak of 14,795 stores in 2012, falls steeply through the late 2010s, bottoms at 7,611 in 2020, and ends at 7,987 in 2025. Title: Authorized small grocers fell by nearly half.
```

### `images/02-census-vs-snap.png` (1409×615) — census against SNAP

```
Horizontal bar chart of percentage change from 2012 to 2023, with bars growing leftward from a right-hand baseline to show declines. Census, all grocery: minus 6.7%. Census, under 5 staff: minus 22.5%. Census, under 10 staff: minus 24.9%. SNAP Small plus Medium: minus 25.9%. SNAP Small only: minus 46.1%. Title: The businesses fell a quarter. SNAP's Small category fell twice that.
```

### `images/03-size-ladder.png` (1087×645) — the size ladder

```
Table of the change in new SNAP sign-ups per year, 2012–13 average against 2018–19 average, by USDA store type. Small Grocery Store: minus 58%. Convenience Store: minus 42%. Combination Grocery/Other: minus 38%. Medium Grocery Store: minus 9%. Supermarket: minus 6%. Large Grocery Store: plus 8%. Title: The fall sorts by store size.
```

### `images/04-states.png` (1310×809) — the states

```
Horizontal bar chart of the eight states with the largest falls in authorized small grocers from 2012 to 2025, bars growing leftward to show declines. New York, highlighted: minus 64%, from 3,765 stores to 1,356. Illinois: minus 61.6%. Georgia: minus 58.2%. Maryland: minus 55.1%. New Jersey: minus 54.5%. Florida: minus 51.6%. Connecticut: minus 51%. Louisiana: minus 49.3%. Title: New York lost the most, by a wide margin.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The 25% / 46% / 58% trio is the same comparison set the Day 1 card and the
  launch email use. If any of the three changes upstream, the card, the email
  block and this file all need the update.
