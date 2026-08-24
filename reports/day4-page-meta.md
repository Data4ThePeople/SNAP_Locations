# Day 4 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 4 of the series (post3, rebuilt
around geography: growth by Rural-Urban Continuum Code). Companion files:
`reports/day0-page-meta.md` through `day3-page-meta.md` and
`reports/visualization-page-meta.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post3/post3.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
Super stores for some, dollar stores for the rest
```

## 2. Page subtitle

```
Twenty years of SNAP data show grocery growth obeying a single variable: how close you live to a metro area. 46.3 million Americans live on the wrong side of that line.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-4.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-4-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states showing non-metropolitan America's food retail in 2025: 11,689 dollar stores in violet scattered across rural counties, against just 6,171 big grocery stores — super stores and supermarkets — in grey. Metro-county stores appear only as a faint backdrop. Text on the map reads: The Stores That Stayed. Day 4. Nonmetro America, 2025.
```

Short version if the field is tight:

```
Dot map of nonmetro America in 2025: 11,689 dollar stores in violet against 6,171 big grocery stores in grey.
```

## 4. Meta title

49 characters — will not truncate.

```
Super Stores for Some, Dollar Stores for the Rest
```

## 5. Meta description

155 characters.

```
Big-format grocery growth happened almost entirely in metro counties. Where 46 million nonmetro Americans live, the big stores left and dollar stores came.
```

## 6. Meta keywords

```
rural food access, food deserts, rural-urban continuum codes, super stores, supermarkets, dollar stores, SNAP retailers, rural America
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Super stores for some, dollar stores for the rest",
  "description": "Big-format grocery growth happened almost entirely in metro counties. Where 46 million nonmetro Americans live, the big stores left and dollar stores came.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 4,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["rural food access", "food deserts", "rural-urban continuum codes", "super stores", "supermarkets", "dollar stores", "SNAP retailers", "rural America"],
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

### `images/00-key-figures.png` (1720×459) — headline figures

```
Three headline figures: a +33% change in metro super stores since 2006, while in nonmetro counties they fell 5%. 46.3 million Americans live in nonmetro counties. +286% nonmetro dollar store growth — the only format still growing on every rung of the rural-urban ladder.
```

### `images/01-metro-vs-nonmetro.png` (1282×688) — the divergence

```
Line chart of authorized super stores and supermarkets, indexed to 100 in 2006, split into metropolitan and non-metropolitan counties. The metro lines climb to 133 for super stores and 112 for supermarkets by 2025. The nonmetro lines drift down to about 95 and 93, with a sharp step down for nonmetro super stores in 2020 — the Kmart liquidation. Title: Metro America gained big stores. Nonmetro America lost them.
```

### `images/02-metro-1m-share.png` (1277×435) — the million-plus metros' share

```
Bar chart of the share of each format's net 2006–2025 change that landed in counties belonging to metro areas of a million people or more: 74% for super stores and 95% for supermarkets. Title: The million-person metros took almost all of the growth.
```

### `images/03-rucc-gradient.png` (1347×688) — growth by rural-urban code

```
Line chart of percent change in authorized stores from 2006 to 2025 across the nine Rural-Urban Continuum Codes, from code 1, metro areas of a million or more, to code 9, fully rural and remote. Dollar stores run nearly flat around +280 to +350% on every rung. Convenience stores slope from +105% down to +20%. Super stores and supermarkets start modestly positive and turn negative outside metro counties. Small grocery is negative everywhere, worst at the two extremes near −52%. Title: Dollar stores grow everywhere. Everything else grows where people are.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The growth disclaimer near the top ("growth means SNAP-authorized stores")
  is live text and load-bearing — do not drop it in layout.
- The labor-force paragraph references the earlier D4TP structural-decline
  piece; link it there if a link slot is available.
- The Day 4 card and email line now carry the geography stat ("+33% vs −5%",
  metro against nonmetro super stores since 2006), regenerated from the same
  rucc data this post uses. The Day 0 page-meta alt text matches.
