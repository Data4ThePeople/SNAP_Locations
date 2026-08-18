# Visualization page — titles, meta and schema

Copy blocks for the Prismic page that carries the interactive map and the
methodology. This is **not** post 0 (the series announcement) — that page has
its own copy.

Fill the three placeholders before publishing: `[[slug]]`, `[[PRISMIC HERO URL]]`,
and the two timestamps. Everything else is final.

---

## 1. Page title (H1)

```
Every Store That Accepted SNAP, 2006–2025
```

## 2. Page subtitle

```
An interactive map of all 661,456 retailers USDA authorized to accept food stamps over twenty years — by store type, by chain, and by the year each one arrived or left. The companion to our series, The Stores That Stayed.
```

## 3. Hero image

| file | dimensions | use |
|---|---|---|
| `reports/assets/snap-map-hero.png` | 1680×1080 | Prismic hero |
| `reports/assets/snap-map-og.png` | 1200×628 | social card (1.91:1) |

Rendered from the published bundle at its default state — 2025, colored by
owner — so the counts and colors match what a reader actually sees.

**Hero alt text:**

```
Dot map of 249,083 SNAP-authorized stores across the United States in 2025, chains in blue and independents in orange, dense east of the Mississippi and along the coasts, sparse across the interior West.
```

Short version if the field is tight:

```
Dot map of 249,083 SNAP-authorized US stores in 2025, chains in blue and independents in orange.
```

## 4. Meta title

44 characters — will not truncate.

```
SNAP Retailer Map: 661,456 Stores, 2006–2025
```

## 5. Meta description

156 characters.

```
An interactive map of every store USDA authorized to accept SNAP from 2006 to 2025 — 661,456 retailers by type, chain, and year. Free, sourced, reproducible.
```

## 6. Meta keywords

```
SNAP retailers, food stamp map, USDA SNAP data, food access, grocery store closures, dollar stores
```

## 7. Schema

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Article",
      "headline": "Every Store That Accepted SNAP, 2006–2025",
      "description": "An interactive map of every store USDA authorized to accept SNAP from 2006 to 2025 — 661,456 retailers by type, chain, and year. Free, sourced, reproducible.",
      "image": "[[PRISMIC HERO URL]]?auto=format,compress",
      "datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
      "dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]",
      "articleSection": "Visualization",
      "isPartOf": { "@type": "CreativeWorkSeries", "name": "The Stores That Stayed" },
      "inLanguage": "en-US",
      "isAccessibleForFree": true,
      "keywords": ["SNAP retailers", "food stamp map", "USDA SNAP data", "food access", "grocery store closures", "dollar stores"],
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
    },
    {
      "@type": "Dataset",
      "name": "SNAP-Authorized Retailers, United States, 2006–2025",
      "description": "Every retail location USDA's Food and Nutrition Service authorized to accept SNAP benefits between 2006 and 2025, mapped by year. Derived from the SNAP Retailer Locator Historical Data by resolving 703,441 authorization spells into 661,456 distinct stores, of which 656,868 carry coordinates that validate against US, state and territory borders. A store is counted as active in a year if an authorization covered 31 December of that year; 45,704 stores (7.0%) opened and closed between two such dates and never appear. Each store carries USDA's own store-type category (18 values), a hand-checked retailer match (289 chains grouped into 13 parent companies), and an inferred owner class (chain, independent, or unknown). Fuel brands are classed as unknown rather than chain, because a fuel supply contract says nothing about who owns the store. No prices, sales, floor space, or redemption volumes are included; SNAP redemption figures are not public.",
      "url": "https://www.data4thepeople.com/p/[[slug]]/",
      "license": "https://www.data4thepeople.com/terms-of-use",
      "isAccessibleForFree": true,
      "temporalCoverage": "2006/2025",
      "spatialCoverage": { "@type": "Place", "name": "United States" },
      "keywords": ["SNAP retailers", "food stamp map", "USDA SNAP data", "food access", "grocery store closures", "dollar stores"],
      "variableMeasured": [
        "Store count authorized on 31 December, by year (count of stores)",
        "Store format, USDA category, 18 values (categorical)",
        "Retailer brand, 289 matched chains (categorical)",
        "Parent company, 13 groups (categorical)",
        "Ownership class: chain, independent, or unknown (categorical)",
        "Store location, latitude and longitude in decimal degrees (WGS 84)",
        "Authorization start and end date (ISO 8601 date)"
      ],
      "creator": {
        "@type": "Organization",
        "name": "Data 4 The People",
        "url": "https://data4thepeople.com"
      },
      "isBasedOn": [
        {
          "@type": "Dataset",
          "name": "USDA FNS SNAP Retailer Locator Historical Data",
          "description": "USDA's Food and Nutrition Service publishes every retail location it has authorized to accept SNAP benefits, with street address, coordinates, USDA store type, and the start and end dates of each authorization. The 2005–2025 historical file is used in full; records before 2006 are excluded because coverage in the first year is incomplete.",
          "url": "https://www.fns.usda.gov/snap/retailer/historicaldata",
          "license": "https://www.usda.gov/policies-and-links",
          "creator": {
            "@type": "Organization",
            "name": "USDA Food and Nutrition Service",
            "url": "https://www.fns.usda.gov"
          }
        }
      ]
    }
  ]
}
```

---

## Embed code

The embeddable file is the standalone bundle, **not** `web/index.html` — that
one fetches its data at runtime and the data directory is not published.

```html
<iframe
  src="https://data4thepeople.github.io/SNAP_Locations/dist/snap-map.html"
  title="SNAP Retailers, 2006–2025"
  width="100%"
  height="1200"
  style="width:100%;height:1200px;border:0;display:block"
  loading="lazy"
  allow="fullscreen"
  allowfullscreen></iframe>
```

- **Height is fixed at 1200px, width is fluid.** The layout is a flex column at
  `height:100%`, so the map area absorbs whatever height it is given. A
  percentage height collapses it.
- **`allow="fullscreen"` is required.** There is a fullscreen button in the map
  controls; without the attribute it fails silently.
- **Do not add `sandbox`** unless it includes `allow-scripts`. The map needs
  scripts and WebGL.
- The responsive breakpoint is **830px of container width**, not viewport width.
  Above it the map sits beside two lists; below it the controls stack and the
  lists become tabs.
- First load is 8.45MB. Everything is inlined, so it is one request and then it
  caches. The only network dependency after that is the CARTO basemap.

## Notes

- The USDA license URL in the schema (`usda.gov/policies-and-links`) returns 403
  to automated requests but resolves normally in a browser. It is bot-blocking,
  not a dead link — worth swapping if a validator complains.
- The alt text covers the hero image only. The interactive map is a WebGL canvas
  of 249,083 dots and is not reachable by a screen reader; the methodology
  section carries the underlying numbers in text, which is the current mitigation.
