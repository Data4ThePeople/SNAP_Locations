# Day 5 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 5 of the series (post4, the chain
pharmacy collapse). Companion files: `reports/day0-page-meta.md` through
`day4-page-meta.md` and `reports/visualization-page-meta.md`.

Corrected November 10, 2026: ZIP codes are now padded to 5 digits, which adds places
in New England, New Jersey and the Virgin Islands. Numbers below are the corrected ones;
the live page carries a correction note at the top.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post4/post4.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below.

---

## 1. Page title (H1)

```
The one chain format that did not work
```

## 2. Page subtitle

```
Dollar stores and gas stations kept growing. Chain pharmacies fell 24.3% in four years — because a pharmacy sets neither the price it is paid nor the price it pays. 1,068 ZIP codes lost their last one.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-5.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-5-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states on a dark ground showing SNAP-authorized chain pharmacies. Amber dots mark the 6,181 that left the program since 2016, densest across the Northeast, the mid-Atlantic and California; grey dots mark the 14,828 still authorized. Text on the map reads: The Stores That Stayed. Day 5. Chain pharmacies.
```

Short version if the field is tight:

```
Dot map of US chain pharmacies: 6,181 that left SNAP since 2016 in amber, against 14,828 still authorized in grey.
```

## 4. Meta title

50 characters — will not truncate. Leads with "chain pharmacies" rather than
the H1's phrasing, which is distinctive on the page but says nothing a reader
would search for.

```
Chain Pharmacies: The One Format That Did Not Work
```

## 5. Meta description

152 characters.

```
Chain pharmacies fell 24.3% in four years while dollar stores and gas stations grew. A pharmacy sets neither the price it is paid nor the price it pays.
```

## 6. Meta keywords

```
chain pharmacies, pharmacy closures, pharmacy benefit managers, drug wholesalers, Rite Aid bankruptcy, pharmacy deserts, SNAP retailers, food access
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "The one chain format that did not work",
  "description": "Chain pharmacies fell 24.3% in four years while dollar stores and gas stations grew. A pharmacy sets neither the price it is paid nor the price it pays.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 5,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["chain pharmacies", "pharmacy closures", "pharmacy benefit managers", "drug wholesalers", "Rite Aid bankruptcy", "pharmacy deserts", "SNAP retailers", "food access"],
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
Three headline figures: a 24.3% fall in authorized drug chain stores between 2021 and 2025. 5,054 drug chain authorizations ended over 2022 to 2025. 1,068 ZIP codes lost their last SNAP-authorized chain pharmacy since 2021.
```

### `images/01-drug-chain-arc.png` (1158×688) — the arc

```
Line chart of chain pharmacies holding an active SNAP authorization on 31 December of each year, 2006 to 2025. The line climbs steeply through 2012, plateaus just above 20,000 from 2013 to 2021, then falls sharply to 14,828 by 2025. A dashed vertical marker at 2021 is labelled "collapse begins". Title: Chain pharmacies held flat, then fell off a cliff.
```

### `images/02-chain-table.png` (1087×488) — the Big 3

```
Table of peak and current SNAP authorizations for the three big pharmacy chains. Walgreens peaked at 9,388 in 2013 and stands at 7,453, down 20.6%. CVS peaked at 8,173 in 2020 and stands at 7,201, down 11.9%. Rite Aid peaked at 3,184 in 2010 and stands at 2, down 99.9%. Duane Reade is counted with Walgreens and Longs Drugs with CVS. Title: Peak and current count, chain by chain.
```

### `images/03-states.png` (1310×809) — where they were

```
Bar chart of the largest state falls in authorized chain drug stores, 2021 to 2025, among states with at least 150 in 2021. Bars run leftward from zero. Pennsylvania is worst at −54.9%, from 1,041 stores to 470, followed by Michigan −47.1%, Oregon −41.3%, California −37.2%, New York −36.9%, Washington −34.3%, Ohio −32.9% and West Virginia −32.5%. Title: Where the pharmacies were.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The author discloses in the body that he ran a chain of more than twenty
  independent pharmacies and analysed drug pricing at 46brooklyn Research and
  3 Axis Advisors. If the page template has an author-bio slot, that belongs
  there as well — a reader who meets the disclosure mid-piece may wonder why it
  was not flagged sooner.
- Two outbound links in the body, to `46brooklyn.com` and `3axisadvisors.com`.
  Keep them live; they are the source for the reimbursement argument.
- The Day 5 card in the Day 0 announcement carries "chain pharmacies peaked at
  20,341 and stand at 14,828", which still matches the pipeline. No change
  needed there.
- Duane Reade is counted with Walgreens and Longs Drugs with CVS, since both
  have been banners of those chains since 2010 and 2008. That is why the table
  has three rows and why Walgreens reads -20.6% rather than -19.4%.
- The share of purchasing a pharmacy must make through its primary wholesaler
  is stated as "a majority" rather than a percentage on purpose: the figure
  comes from the author's own contracts, not a public source.
