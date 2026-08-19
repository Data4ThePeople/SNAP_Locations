# Day 0 page — titles, meta, schema and alt text

Copy blocks for the Prismic page that announces the series (post0, "The Stores
That Stayed"). This is **not** the visualization page — that page has its own
copy in `reports/visualization-page-meta.md` — and not the launch email, which
is `reports/email-day0.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every number here is checked
against the pipeline (`reports/data/post0.json`); if the posts are rebuilt,
re-check the figures in the alt text below against `reports/post0/post0.md`.

---

## 1. Page title (H1)

```
The Stores That Stayed
```

## 2. Page subtitle

```
Twenty years of SNAP retailers, mapped. Every store authorized to accept SNAP anywhere in the United States, 2006–2025 — 661,456 of them. An interactive map, and seven days of analysis built on it.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-0.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-0-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states on a dark ground, every SNAP-authorized store in 2025 drawn as a blue dot — dense east of the Mississippi and along the coasts, sparse across the interior West. Text on the map reads: The Stores That Stayed. The Map. 249,083 stores in 2025.
```

Short version if the field is tight:

```
Dot map of 249,083 SNAP-authorized US stores in 2025, drawn as blue dots on a dark map of the lower 48.
```

## 4. Meta title

50 characters — will not truncate.

```
The Stores That Stayed: 20 Years of SNAP Retailers
```

## 5. Meta description

147 characters.

```
Twenty years of SNAP retailers, mapped — 661,456 stores, 2006–2025. An interactive map, and seven days of analysis on what stayed, what left, and why.
```

## 6. Meta keywords

```
SNAP retailers, food stamp stores, USDA SNAP data, food access, grocery store closures, dollar stores, The Stores That Stayed
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "The Stores That Stayed",
  "alternativeHeadline": "Twenty years of SNAP retailers, mapped",
  "description": "Twenty years of SNAP retailers, mapped — 661,456 stores, 2006–2025. An interactive map, and seven days of analysis on what stayed, what left, and why.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 0,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["SNAP retailers", "food stamp stores", "USDA SNAP data", "food access", "grocery store closures", "dollar stores", "The Stores That Stayed"],
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

Eight images, in page order. The seven day cards are pictures of text, so their
alt text carries that text — headline plus the key figure. If a card is ever
retitled, regenerate the cards and update the matching alt text from
`reports/post0/cards.md`, which is built from the same data.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: 661,456 stores authorized to accept SNAP at some point in the last twenty years. 249,083 still authorized at the end of 2025. 20 years you can move through, one at a time.
```

### `images/day-1.png` (1720×537) — Day 1 card

```
Series card for Day 1 — One in four of the smallest grocery stores is gone. Key figure: a 25% fall in the number of small grocery businesses, by the Census Bureau's count.
```

### `images/day-2.png` — Day 2 card

```
Series card for Day 2 — Dollar store domination. Key figure: up 307% since 2006, the steepest growth of any store format.
```

### `images/day-3.png` — Day 3 card

```
Series card for Day 3 — Convenience stores thrived. Most of their owners did not. Key figure: 14.2% of single-owner convenience stores lasted thirteen years, against 78.7% of the fuel-selling chains.
```

### `images/day-4.png` — Day 4 card

```
Series card for Day 4 — The bigger the store, the better it did, unless it belonged to a chain. Key figure: 78% of chain super stores kept their SNAP authorization; 46% of independent ones did.
```

### `images/day-5.png` — Day 5 card

```
Series card for Day 5 — The one chain format that did not work. Key figure: chain pharmacies peaked at 20,341 and stand at 14,828.
```

### `images/day-6.png` — Day 6 card

```
Series card for Day 6 — Twenty years, one pattern. Key figure: chains went from 39% to 50% of every SNAP retailer in the country, 2006 to 2025.
```

### `images/day-7.png` — Day 7 card

```
Series card for Day 7 — In November, the rules change for the stores that are left. Key figure: the small stores the rule hits hardest are 71% of SNAP retailers and 11% of SNAP spending, by USDA's own accounting.
```

## Notes

- The key figures also appear in the page as live text directly above the
  image, so a reader with images off still gets the three numbers. Keep it
  that way — same reasoning as the launch email.
- The cards are 1720px wide and scale poorly on phones. If the page ever needs
  a mobile-first variant, use the text block from `reports/post0/cards.md`
  instead, as the email does.
