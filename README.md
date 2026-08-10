# SNAP Retailer Locations

Maps SNAP-authorized retailers nationally, classified by format and ownership,
for any date from 2006 to 2025.

```bash
pip install -r requirements.txt
python src/pipeline.py          # fetch -> load -> classify -> verify (~2 min)
python src/snapshot.py 2025-12-31
python src/snapshot.py 2012-06-30 --by=format
```

## Source

One static file: USDA's [SNAP Retailer Locator Historical
Data](https://www.fns.usda.gov/snap/retailer/historical-data), 703,441 rows
covering 2005–2025.

The live ArcGIS locator is deliberately **not** used. It collapses the taxonomy
into 8 coarse types — fusing large/medium/small grocery into one bucket — while
this file carries the full 17-type taxonomy plus authorization dates. Using one
source means the current map and every historical year share one taxonomy
instead of reconciling two.

The tradeoff: ~12,000 entities exist only in the live feed and are absent here —
all 8,423 Restaurant Meals Program locations (restaurants accepting SNAP) and
roughly 3,600 farmers-market entities.

FNS was renamed FNA on 2026-06-01 and `fns.usda.gov` URLs are migrating, so the
zip is cached locally rather than re-fetched.

## The data is spells, not stores

703,441 rows resolve to **661,456 stores**. 37,941 Record IDs carry multiple
rows because authorizations lapse and resume:

```
Record ID 888299  Depot Food Store Inc
  auth=2009-04-22 end=2019-09-12
  auth=2019-09-20 end=2019-12-01
  auth=2020-06-23 end=2022-12-27
  auth=2024-11-20 end=(active)
```

So `dim_store` is one row per store and `fact_spell` one row per spell. A store
is active on date `D` if any spell covers `D`. Counting rows instead of stores
overstates retailer counts by ~6%.

## Two classification axes

USDA encodes store **format**, never **ownership**, so the two are modeled
separately — letting you ask for "independent supermarkets" rather than picking
one axis up front.

**format** — USDA's type, with Dollar Store split out of the Combination
Grocery/Other bucket (23% of retailers and the fastest-growing segment).

**ownership** — `chain` / `independent` / `unknown`, derived from store names via
the hand-curated `data/brands.csv`, since naive normalization shatters 7-Eleven
into three brands and splits `DOLLARTREE` from `DOLLAR TREE`.

Two deliberate `unknown` cases, rather than forcing a guess:

- **Generic names.** `FOOD MART` appears 184 times, but those are unrelated
  independents sharing a name, not a chain.
- **Fuel banners.** `SHELL`, `BP`, and `CITGO` identify the fuel supplier, not
  the store operator; those sites are overwhelmingly franchisee-owned. Calling
  them "chain" would inflate chain counts.

Unresolved names held by ≤4 stores nationally are treated as independent. Name
frequency is computed over all 661,456 stores, never per snapshot, so labels
don't drift between map versions.

## Current snapshot (2025-12-31)

| Format | Stores | | Ownership | Stores |
|---|---:|---|---|---:|
| Convenience Store | 117,057 | | chain | 123,604 |
| Dollar Store | 37,362 | | independent | 89,873 |
| Combination Grocery/Other | 21,338 | | unknown | 35,615 |
| Super Store | 20,465 | | | |
| Supermarket | 19,538 | | **Total** | **249,092** |
| Grocery (Medium) | 11,509 | | | |
| Grocery (Small) | 7,989 | | | |
| Grocery (Large) | 4,001 | | | |

Crossing the axes shows why they're separate: **Grocery (Large) is 2,929
independent vs. 164 chain.** USDA's "Large Grocery Store" is an independent-grocer
category, not a chain-supermarket one.

## Limitations

- **Store-level redemption dollars are not obtainable.** *Food Marketing
  Institute v. Argus Leader* (SCOTUS, 2019) closed this under FOIA Exemption 4.
  You can map where retailers are, never how much each transacts.
- **The taxonomy is not stable over 20 years.** FNS tightened stocking standards
  ~2016–2018; Small Grocery Store falls 14,255 (2010) → 7,539 (2021), partly
  reclassification rather than closures. Annotate this on time-series charts.
- **Snapshots before 2006 are refused.** The archive only contains retailers
  authorized within the last 20 years, so earlier dates are incomplete by
  construction.
- **0.65% of stores lack coordinates** (`geocode_missing`); filter before mapping.
- **Do not deduplicate by address.** 145,993 addresses carry multiple records.
  Some are successors at one storefront, but others are genuinely concurrent —
  1979 W 25th St, Cleveland has 144 records because it is the West Side Market.

## Layout

```
src/config.py     paths, constants, connect()
src/fetch.py      download + cache the zip
src/load.py       CSV -> dim_store + fact_spell, with data-quality flags
src/brands.py     name normalization + crosswalk matching
src/classify.py   derive format, ownership, brand
src/snapshot.py   as_of(date) -> active stores; entry point for every map version
src/verify.py     27 regression checks against figures measured from the source
data/brands.csv   hand-curated crosswalk (source, not output — edit this to improve coverage)
```

To improve ownership coverage, add patterns to `data/brands.csv` and re-run
`python src/classify.py`. Find the biggest gaps with:

```sql
SELECT name_norm, max(name_freq) f FROM dim_store
WHERE chain_category IS NULL AND name_freq > 4
GROUP BY 1 ORDER BY f DESC LIMIT 50;
```
