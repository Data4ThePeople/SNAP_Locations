# Day 6 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 6 of the series (post5, the
synthesis). Companion files: `reports/day0-page-meta.md` through
`day5-page-meta.md` and `reports/visualization-page-meta.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post5/post5.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
Twenty years, one pattern
```

## 2. Page subtitle

```
Dollar stores did not push anyone out — they were already there. What the places losing their stores have in common is not what arrived, but how small they are.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-6.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-6-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states on a dark ground showing twenty years of SNAP retail turnover. Bright blue dots mark the 87,719 stores authorized since 2006, densest along the eastern seaboard and in California; grey dots mark the 37,264 authorized in 2006 and still authorized now, and the 25,138 that have left. Text on the map reads: The Stores That Stayed. Day 6. Chain share of all SNAP stores: 39% to 50%.
```

Short version if the field is tight:

```
Dot map of US SNAP retail turnover since 2006: 87,719 stores authorized since then, 37,264 there throughout, 25,138 gone.
```

## 4. Meta title

47 characters — will not truncate.

```
Twenty Years, One Pattern: What SNAP Data Shows
```

## 5. Meta description

154 characters.

```
The obvious explanation is wrong. Dollar stores did not push pharmacies and grocers out — they were already there. What these places share is being small.
```

## 6. Meta keywords

```
food deserts, dollar stores, store closures, rural food access, SNAP retailers, pharmacy deserts, retail consolidation, chain stores
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Twenty years, one pattern",
  "description": "The obvious explanation is wrong. Dollar stores did not push pharmacies and grocers out — they were already there. What these places share is being small.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 6,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["food deserts", "dollar stores", "store closures", "rural food access", "SNAP retailers", "pharmacy deserts", "retail consolidation", "chain stores"],
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

Six images, in page order. The charts' alt text states the numbers, not just
the shape, so a screen reader gets the same facts a sighted reader does.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: chains went from 39% to 50% of every SNAP retailer in the country between 2006 and 2025. 976 ZIP codes lost their last SNAP-authorized chain pharmacy since 2021. 6,488 is the median population of those that now have no grocery store of any size.
```

### `images/01-twenty-year-arc.png` (1161×688) — the arc

```
Line chart of SNAP-authorized stores by format across the 976 ZIP codes that lost their last chain pharmacy, 2006 to 2025. Grocery of every size falls from 5,301 to 4,425. Dollar stores climb from 494 to 2,054, a rise of 316%. Pharmacies peak at 1,192 in 2016 and fall to zero by 2025. In 2006 these places had about ten times as many grocery stores as dollar stores; today grocery leads by about two to one.
```

### `images/02-presence-vs-control.png` (1087×540) — presence against the control

```
Bar chart comparing what ZIP codes have in 2025: those that lost their last chain pharmacy against the 7,367 that kept one. Dollar stores are present in 83.3% of the loss group and 81.4% of the control. Convenience stores 96.8% against 97.8%. Dollar or convenience 98.6% against 98.3%. No grocery of any size 7.4% against 3.0%. Title: What each group of ZIP codes has in 2025.
```

### `images/03-growth-vs-control.png` (1476×563) — growth against the control

```
Bar chart of store-count change from 2021 to 2025 in ZIP codes that lost their last chain pharmacy against those that kept one. Dollar stores grew 2.6% where the pharmacy went, against 5.7% where it stayed. Convenience stores grew 4.9% against 3.5%. If dollar stores were moving into vacated ground the first comparison would run the other way.
```

### `images/04-median-population.png` (1461×500) — how small these places are

```
Bar chart of median 2020 census population by ZIP code group. ZIP codes that lost their last chain pharmacy have a median of 14,364 residents, against 26,583 where the pharmacy survived. Among the loss group that has also lost every grocery store, the median is 6,488. Title: Median 2020 census population of the ZIP code.
```

### `images/05-small-zip-share.png` (1447×564) — share below population thresholds

```
Bar chart of the share of ZIP codes below population thresholds, by group. Among those that lost their last chain pharmacy, 34.6% have fewer than ten thousand residents and 12.6% fewer than five thousand. Among those that kept a pharmacy, 10.7% and 2.9%. Roughly a third against a tenth, and one in eight against one in thirty-five.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The 39% → 50% chain share is the one-number summary of the whole series and
  appears in no other post. It is also the Day 6 card stat in the Day 0
  announcement, which still matches the pipeline.
- The control group is the spine of this piece: 7,367 ZIP codes that had a
  chain pharmacy in 2021 and kept one. Do not drop the comparison from any
  chart caption in layout — without it the numbers read as substitution, which
  is exactly what the section disproves.
- This post carries figures from Days 3 and 5 by reference (fuel-chain
  survival, the Murphy USA margin, the Walgreens authorization-to-store
  ratio). If those posts are rebuilt, re-check them here.
- Day 6 is the last chapter of the story; Day 7 is an epilogue. The subtitle
  and the closing paragraph both say so, and the Day 7 page opens by counting
  "the six chapters before this one".
