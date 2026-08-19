# Day 2 page — titles, meta, schema and alt text

Copy blocks for the Prismic page carrying Day 2 of the series (post1, dollar
stores). Companion files: `reports/day0-page-meta.md`, `reports/day1-page-meta.md`,
and `reports/visualization-page-meta.md`.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final. Every figure here matches
`reports/post1/post1.md` as generated; if the post is rebuilt, re-check the
numbers quoted in the alt text below. Image order follows the restructured
post: the chain-census table now leads the article.

---

## 1. Page title (H1)

```
Dollar store domination
```

## 2. Page subtitle

```
SNAP-authorized retailers, 2006–2025. USDA Food and Nutrition Service authorization records. 37,361 dollar stores authorized at the end of 2025, against 63,497 grocery stores of every size.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/heroes/day-2.png` | 1680×1080 | Prismic hero |
| `reports/assets/heroes/day-2-email.jpg` | 1200×771 | email / social card |

**Hero alt text:**

```
Dot map of the lower 48 states showing SNAP-authorized dollar stores, with national counts: 37,361 stores in 2025 drawn in green over the 9,181 of 2006 in grey, dense across the South and Midwest. Text on the map reads: The Stores That Stayed. Day 2. Dollar stores, 2006 to 2025.
```

Short version if the field is tight:

```
Dot map of SNAP-authorized dollar stores: 37,361 in 2025 in green over 9,181 in 2006 in grey.
```

## 4. Meta title

54 characters — will not truncate.

```
Dollar Stores Cracked the Code Small Grocers Could Not
```

## 5. Meta description

146 characters.

```
SNAP-authorized dollar stores grew 307% since 2006 and kept 78% of their stores for thirteen years. How the small-box chain beat the small grocer.
```

## 6. Meta keywords

```
dollar stores, Dollar General, Dollar Tree, SNAP retailers, food access, food deserts, grocery store closures
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Dollar store domination",
  "alternativeHeadline": "Dollar stores cracked the code small grocers could not",
  "description": "SNAP-authorized dollar stores grew 307% since 2006 and kept 78% of their stores for thirteen years. How the small-box chain beat the small grocer.",
  "image": "[[PRISMIC HERO URL]]?auto=format,compress",
  "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
  "articleSection": "Analysis",
  "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
  "position": 2,
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": ["dollar stores", "Dollar General", "Dollar Tree", "SNAP retailers", "food access", "food deserts", "grocery store closures"],
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

Seven images, in page order. The charts' alt text states the numbers, not just
the shape, so a screen reader gets the same facts a sighted reader does.

### `images/00-key-figures.png` (1720×422) — headline figures

```
Three headline figures: a +307% change in SNAP-authorized dollar stores since 2006. 78% of dollar stores authorized in 2008–2012 are still authorized today. 26% of ZIP codes with a dollar store have no grocery store at all, up from 8% in 2008.
```

### `images/01-chain-census.png` (1087×488) — the chain census

```
Table comparing SNAP authorizations at the end of 2025 with each company's most recently reported store count, early 2025 to February 2026. Dollar General: 20,997 authorized against 20,942 reported, ratio 1.00. Dollar Tree: 9,005 against 9,000, ratio 1.00. Family Dollar: 7,346 against 7,600, ratio 0.97. Title: The SNAP counts match the companies' own, almost exactly.
```

### `images/02-growth.png` (1161×687) — growth by format

```
Line chart of stores authorized on 31 December of each year, 2006 to 2025. Dollar stores climb steeply from 9,181 to 37,361, crossing every other line. Super stores and supermarkets hold flat near 20,000. Medium grocery holds near 11,000, and small grocery falls from about 14,000 to 8,000. Title: Dollar stores passed every grocery format.
```

### `images/03-retention.png` (1461×823) — cohort retention

```
Horizontal bar chart of the share of the 2008–2012 entry cohort still authorized in 2025, by format. Dollar Store, highlighted in orange: 78.2%. Super Store: 69.4%. Supermarket: 55%. Combination Grocery/Other: 42.9%. Grocery (Large): 33%. Convenience Store: 22.7%. Grocery (Medium): 17.6%. Grocery (Small), highlighted in blue: 4.5%. Title: Dollar stores stayed. Small grocers did not.
```

### `images/04-dollar-only-zips.png` (1158×687) — dollar-only ZIP codes

```
Line chart of ZIP codes that have a SNAP-authorized dollar store and no grocery store — no supermarket, super store, or large, medium, or small grocery store — from 2008 to 2024. The line rises steadily from 675 ZIP codes to 4,024. Title: More places now have a dollar store and no grocery store.
```

### `images/05-dollar-only-split.png` (1618×434) — how the ZIP codes joined

```
Horizontal bar chart splitting the 3,552 ZIP codes that joined the dollar-store-only list between 2008 and 2024. Never had an authorized grocery, in orange: 2,115. Had one that left SNAP by 2024, in blue: 1,437. Title: Most of these places never had an authorized grocery.
```

### `images/06-dollar-only-states.png` (1397×935) — the state walk

```
Table walking each of the ten states that added the most dollar-store-only ZIP codes from its 2008 count to its 2024 count: ZIP codes that left the list (nearly always because a grocery became authorized), new dollar stores in ZIPs that never had an authorized grocery, and arrivals where a grocery left SNAP. Pennsylvania: 25, minus 6, plus 125 never-had, plus 106 where a grocery left SNAP, ending at 250. Illinois: 18, minus 3, plus 93, plus 121, ending at 229 — the only state where groceries leaving SNAP outnumber arrivals. Texas: 90, minus 46, plus 173, plus 80, ending at 297. Ohio: 48, minus 9, plus 117, plus 85, ending at 241. New York: 26, minus 5, plus 111, plus 66, ending at 198. Missouri: 12, minus 6, plus 88, plus 73, ending at 167. Indiana: 22, minus 4, plus 90, plus 67, ending at 175. Kentucky: 26, minus 7, plus 88, plus 63, ending at 170. Michigan: 16, minus 4, plus 82, plus 61, ending at 155. North Carolina: 28, minus 5, plus 90, plus 44, ending at 157. Title: How each state got from 2008 to 2024.
```

## Notes

- The headline figures also appear as live text above the image on the page;
  keep both so the numbers survive images-off rendering.
- The chain-census table is the article's first chart by design: it establishes
  that dollar-store authorization counts track store counts almost one for one,
  which is the license for the closure language in the rest of the piece. Keep
  it first if sections are ever reordered.
- The +307% figure is the same one on the Day 2 card and in the launch email.
  If it changes upstream, those need the update too.
