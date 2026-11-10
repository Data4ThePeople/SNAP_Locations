# Datasets

The map and the 2026 exit count use two USDA products, joined on Record_ID. The
historical file covers every Dec 31 from 2006 to 2025. The live feed adds one
more date, November 5, 2026. Two curated files in `data/` add brand and
ownership, and a Census boundary file draws the static map.

## SNAP Retailer Locator Historical Data, 2005-2025 (USDA Food and Nutrition Administration)

**What it is.** One row per authorization spell: a store's Record_ID, name,
address, coordinates, USDA store type, authorization date and end date. A store
whose authorization lapses and resumes has more than one row.

**Where it comes from.** `snap-retailer-locator-data2005-2025.zip` from
`fna.usda.gov/sites/default/files/resource-files/`, one CSV inside, no login.
Cached in `data/raw/` (not in git). FNS was renamed FNA on June 1, 2026 and its
URLs are moving, so `src/fetch.py` does not re-download once the CSV exists.

**Version and vintage.** Data through December 31, 2025. USDA publishes a new
file about once a year. As of November 8, 2026, no 2026 file was listed.

**Coverage.** All 50 states, DC and the territories. Only stores authorized at
some point in the 20-year window are included, so a snapshot before 2006 would
be missing stores that opened and closed earlier; `snapshot()` refuses those
dates. 703,441 rows resolve to 661,456 stores. Every value is an administrative
record, not an estimate. Restaurant Meals Program sites and about 3,700
farmers-market entities that appear in the live feed are not in this file.

**Changes over time.** USDA's store types are not stable. Small Grocery Store
falls from 14,255 (2010) to 7,539 (2021), partly from reclassification when
stocking standards tightened around 2016 to 2018, not only from exits.

**Suppressed, censored or masked values.** None. Redemption dollars per store
are not released (*Food Marketing Institute v. Argus Leader*, 2019).

**Missing data.** `1930-01-01` is USDA's code for an unknown authorization date.
4,542 stores have no coordinates. A blank end date means still authorized. A
store counts as authorized on a date if its authorization date is on or before
it and its end date is blank or on or after it, so a store whose end date is
December 31 is in that day's count and leaves after it.

**Revisions.** Each annual file replaces the last one. End dates can be filled
in after the fact. We pin the 2005-2025 file.

**Units and rounding.** Dates to the day. Coordinates in decimal degrees.

**Known quirks.** 40 stores are geocoded outside the US (37 Guam stores placed
in Israel, the Philippines, Mexico and Europe, a California Big Lots in
Caracas, and a "China, Texas" Dollar General in Tibet) and 6 fall in the wrong
state. ZIP codes are stored as numbers, so leading zeros are dropped: 48,413
stores have 4-digit ZIPs and 335 have 3-digit ZIPs, mostly in New England, New
Jersey and the Virgin Islands. We pad them back to 5 digits before comparing
with the live feed and before any ZIP-code count. Post 7 (August 28, 2026)
first kept only 5-digit ZIPs and left out 16,918 stores authorized on
December 31, 2025; it was corrected on November 10, 2026 (249,083 stores,
3,169 ZIP codes, 6.1 million people). The scripts for posts 1, 4 and 5 still
keep only 5-digit ZIPs; checking those posts is queued. `mappable` excludes all three groups: 656,868 of
661,456 stores. One address can carry many records at once (the West Side
Market in Cleveland has 144), so we never deduplicate by address. An exit in
this file is a lost authorization, not necessarily a store that closed.

**Uncertainty.** USDA publishes none. Geocodes are USDA's.

**License and attribution.** US government work, public domain. Credit: USDA
Food and Nutrition Administration.

## SNAP retailer locator live feed (USDA Food and Nutrition Administration)

**What it is.** The list behind USDA's online retailer locator: one row per
store authorized on the day the feed was last refreshed. It has Record_ID, name,
address, coordinates and one of 8 store types. It has no authorization or end
dates, so it shows only who is in SNAP on that one day.

**Where it comes from.** ArcGIS feature service
`services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0`,
public, no key. `src/fetch_live.py` pages through it and saves
`data/raw/live/snap-live-<refresh date>.csv.gz`, which is tracked in git.

**Version and vintage.** USDA overwrites the feed in place and keeps no archive,
so the saved file is the only copy of that day's list. The snapshot in use was
refreshed November 5, 2026 at 21:00 UTC, one day after the stocking standards
compliance date: 248,175 rows. The fetch is refused if the refresh time changes
while paging, if the row count differs from the feed's own count, or if any
Record_ID repeats.

**Coverage.** Same geography as the historical file. Of 248,175 rows:
224,032 have a Record_ID in the historical file; 8,565 are Restaurant Meals
Program sites; 3,709 are farmers-market entities with no historical Record_ID;
11,869 are other stores new to SNAP since December 31, 2025, or otherwise
absent from the historical file. The map leaves out the Restaurant Meals sites
and those 3,709 market entities, because the historical file has never carried
them and adding them for one date would look like growth.

**Changes over time.** One snapshot so far.

**Suppressed, censored or masked values.** None.

**Missing data.** No row in the November 5 snapshot lacks coordinates.

**Revisions.** The whole list is replaced at each refresh.

**Units and rounding.** Decimal-degree coordinates. Store type in 8 classes:
Convenience Store, Grocery Store, Supermarket, Super Store, Specialty Store,
Other, Farmers and Markets, Restaurant Meals Program.

**Known quirks.**
- The 8 types are coarser than the historical file's 17. "Grocery Store" hides
  small, medium and large. "Specialty Store" hides meat, bakery, seafood and
  produce. "Other" holds combination stores, dollar stores, delivery routes and
  co-ops.
- For a store in both sources, the live type disagrees with its historical type
  0.82% of the time (1,833 of 224,032). The map keeps the historical type.
- 2,273 stores kept on the map have no historical Record_ID even though their
  ID is lower than the file's highest one. They may be older authorizations the
  historical file never carried. They are counted as live-only.
- 1,075 stores in the feed have a Record_ID whose every historical spell has an
  end date. They are back in SNAP under the same ID.

**Uncertainty.** USDA publishes none. The feed is a list on one date, so a
store that left and returned between two snapshots does not show.

**License and attribution.** US government work, public domain. Credit: USDA
Food and Nutrition Administration.

## How the two sources are combined

**Map snapshot for November 5, 2026.** This is also the "still in SNAP" layer
under the static map of exits. A store with a historical Record_ID keeps
that file's format, ownership, brand and coordinates. A live-only store gets its
format from its live type: Convenience Store, Supermarket and Super Store map
directly; Other maps to Combination Grocery/Other; Grocery Store becomes
"Grocery (size not given)"; Specialty Store becomes "Specialty (type not
given)". The map note calls these stores "not in the historical file" rather
than "new", because 2,273 of them carry IDs lower than the file's highest. As
in the historical file, a store whose name matches a dollar chain
becomes Dollar Store whatever its type. Ownership and brand come
from `data/brands.csv`, as for every other store. An unresolved name counts as
independent if 4 or fewer stores carry it, counting historical and live-only
stores together. Historical labels are never recomputed, so no published number
moves. A live-only store is mappable if it has coordinates inside the US
windows and is not outside its own state's envelope, the test `load.py` applies.

**Stores that left SNAP in 2026.** A store left if it was authorized and
mappable on December 31, 2025 and its Record_ID is nowhere in the November 5
feed, under any type. If a store that was not authorized on December 31 shows
up in the feed at the same street line and 5-digit ZIP (upper-cased, each run
of punctuation or spaces collapsed to one space, ends trimmed, Restaurant Meals
sites ignored, historical ZIPs padded to 5 digits), the exit counts as
"replaced at the same address" and is not shown on the static map. The same
test runs on the historical file for 2019 to 2025, from December 31 of the year
before to November 5, so 2026 is compared with years measured the same way.

**Post 8 breakdowns.** Every rate in post 8 uses the exit test above: exits not
replaced at the same address, as a share of stores authorized and mappable on
December 31 of the year before. Ownership, brand and state are the historical
file's values for the store. "2019–2025 average" is the simple mean of the
seven unrounded yearly rates. Percentages are rounded to one decimal, halves
up. "All states and territories" and other national counts include Alaska,
Hawaii, Puerto Rico, Guam and the Virgin Islands. The state chart shows states with 500 or more convenience
stores on December 31, 2025; the store-type chart shows types with 1,000 or
more. New authorizations are stores present on November 5 that were not
authorized on the December 31 before, mappable, with format Convenience Store.
Returns under an old ID count in every year. In 2026 the count includes 1,671
live-only convenience stores whose IDs are lower than the historical file's
highest; without them the 2026 rate is 5.5% instead of 7.0%. The count is of
stores still authorized on November 5, not every store authorized in between.

**Fewer exits replaced in 2026.** The address test removes a smaller share of
convenience exits in 2026 (14.3%) than in 2019 to 2025 (25% to 37%). Street
and ZIP agree for 99.6% of stores found in both sources, so formatting does not
explain it. Before the address test, 14.6% of convenience stores left by
November 5, 2026, against a 2019 to 2025 average of 9.0% (range 7.5% to
10.9%). Post 8 reports the measure after the address test and discloses this
one.

**Gap above earlier years.** The number of 2026 convenience exits above what
earlier years' rates would give: 2026 exits minus the 2026 base (117,055 stores)
times the 2019 to 2025 rate, rounded to the nearest store, halves up. Against
the mean of the seven unrounded yearly rates, 14,684 exits against 7,322
expected, a gap of 7,362. Against the highest single year (2019, 8.2%), the gap
is 5,072. Before the address test, the gaps are 6,600 and 4,320. With the
recording lag adjustment below, they are 6,245 and 3,978. The gap is a count of
exits above the usual rate, not a count of exits caused by the stocking rule.

**Restriction states and New York City.** Same measure, convenience stores
only. "Limit states" are the ten states whose SNAP soda or candy purchase
restriction was in effect at some point between January 1 and November 5,
2026, per Chrisinger and White, *Health Affairs Scholar* 4(10), qxag275
(October 2026): Florida, Idaho, Indiana, Iowa, Louisiana, Nebraska, Oklahoma,
Texas, Utah and West Virginia. A court blocked the Iowa, Nebraska and West
Virginia waivers on June 22, 2026. Arkansas (targeted July 1, 2026) and Montana
(targeted September 30, 2026) stay in the comparison group because their start
could not be confirmed. The chart says "see methods" for these details. The comparison group is the other 40 states and DC;
territories are in neither. "Rise in points" is the unrounded 2026 rate minus
the mean of the seven unrounded earlier rates. New York City is the five
boroughs by the historical file's county field (New York, Kings, Queens, Bronx,
Richmond). The comparison shows where exits rose, not why.

**Recording lag check.** The historical file shows fewer convenience stores
with an end date in October to December 2025 (2,157) than the 2022 to 2024
average for those months (3,349). If the 1,192 difference were exits that
happened in 2025 but were recorded late, they would sit in both the 2026 base
and the 2026 exits. Taking them out of both, the 2026 convenience rate would be
11.6% instead of 12.5%. The file cannot tell which. The check is rough: it is
not filtered by the address test.

**What "left SNAP" means in post 8.** A store left if it was authorized and
mappable on December 31 of the year before, its Record_ID is gone from the list
by November 5, and no store that was not authorized on that December 31 shows
up at the same street address and ZIP by then. Every exit count, rate, map and
ranking in post 8 uses this test, in every year 2019 to 2026.

**Details of the exit test.** The street line is the historical file's Street
Number and Street Name joined by a space (Additional Address is not used),
compared with the live feed's Store_Street_Address. Normalization upper-cases
the text and turns every run of characters other than A to Z and 0 to 9 into
one space. A store's address is the one on its historical record. In
historical years, a store "shows up" if it is authorized on November 5 and was
not authorized on December 31. In 2026, a replacement can be any live-feed row
except Restaurant Meals sites (farmers-market entities and the few unmappable
rows included); limiting it to the map layer, as the new-store count does,
would add 36 exits. "Convenience Store" and "Grocery (Small)" are the derived
format: a store whose name matches a dollar chain is a Dollar Store whatever
USDA's type (with USDA's raw types, 2026 convenience would be 117,069 and
14,687 instead of 117,055 and 14,684). Bases are mappable stores only.

**Exits by year and the waterfall (post 8).** Exit counts use the test above,
all store types. The waterfall starts at the 2019 to 2025 average count of
exits and adds each store-type group's 2026 change from its own 2019 to 2025
average, ending at the 2026 count. Each group's average is rounded to a whole
store first, so the bars add up; the start is the sum of those rounded
averages. The groups do not overlap: independent convenience stores; other
convenience stores (chain or owner unknown); grocery stores of any size;
everything else.

**Exits for every new store (post 8).** The store universe on a date is the
map's: on a historical date, stores authorized and mappable in the historical
file; on November 5, 2026, the live feed's map layer. New authorizations are
stores in the universe on November 5 that were not authorized on the December 31 before
(historical years: authorized and mappable on November 5 in the historical
file; 2026: the live feed's map layer, so no Restaurant Meals sites and no
farmers-market entities the historical file never carried). A new store at the
street address and ZIP of a store that left is the other half of a
replacement, so it is left out, just as that exit is. The ratio is exits
divided by the remaining new stores, to two decimals, halves up. Counting every
exit and every new store instead gives 2.02 in 2026 against 0.72 to 1.29 in
2019 to 2025; that version equals the net change in the store count
(December 31, 2025 to November 5, 2026: 249,083 to 235,892). In 2026, 2,273
live-only stores carry IDs below the historical file's highest and may be older
authorizations; 1,829 of them count as new stores in the ratio. Without them,
the 2026 ratio is 3.15 instead of 2.50. New stores are counted only if still
authorized on November 5, in every year.

**Places (post 8).** Exits of convenience stores and small groceries in 2026,
counted by the historical file's county field, with New York City's five
boroughs counted as one place and every other county alone. Comparing a
five-county city with single counties favors the city; the chart says so.

**New York City trend and map.** "Convenience stores and small groceries" are
the historical file's Convenience Store and Grocery (Small) types, in the five
boroughs by the county field. Rates use the exit test above. The map's "still
in SNAP" layer is every store in the November 5 universe in the New York City
group, all types.

**Counties (post 8).** Stores are placed in counties by their coordinates, using
the Census Bureau's 2024 cartographic county boundaries
(`cb_2024_us_county_500k.zip` from `www2.census.gov/geo/tiger/GENZ2024/shp/`,
cached in `data/raw/`, public domain), not by USDA's county field, which has
errors (a store in Morrill, Nebraska is listed in Sioux County). Counts use the
store universe above; 50 states and DC only. About 360 stores on December 31
and 320 on November 5 fall outside every county polygon (mostly coastal
geocodes and territories) and are not counted. "Down to one" means 2 or more
stores on December 31 and exactly 1 on November 5. "Cut in half" means 2 or
more on December 31 and on November 5, with the November 5 count at or below
half. Stores are not filtered by state before placing, so territory stores
count among the unplaced. Each county also notes the
farmers-market entities on the November 5 list; they are outside the store
count but usable by shoppers. Harding County, New Mexico has no store left
but has one such entity.

**Limits of the comparison.** Earlier years use the historical file on both
dates. 2026 uses the file on one date and the live feed on the other. A store
that left between December 31 and November 5 in an earlier year shows up in the
file with an end date. In 2026 it shows up only by being absent from the feed.
The address test can find a match at a multi-tenant address that is not a
replacement, which makes "not replaced" counts lower, not higher.

## SNAP Data Tables: monthly state participation (USDA Food and Nutrition Service)

- **What:** people and households on SNAP each month, by state, with a "US Summary" sheet. One workbook per fiscal year, FY2019 to FY2026.
- **Where:** USDA FNS, SNAP Data Tables, https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap ("SNAP Monthly State Participation and Benefit Summary"). The site blocks scripted downloads, so Eric downloaded the files by hand. Copies are in `data/raw/snap_participation/FY19.xls` and `FY20.xlsx` to `FY26.xlsx`.
- **Version:** FY2026 data as of October 9, 2026. The latest month is July 2026; August and September 2026 show "--" (not yet reported). USDA marks all data as subject to revision.
- **Fields used:** total participation, persons. FY2020 to FY2026 are the "P-EBT/Other Excluded" versions, so pandemic school-meal benefits are not counted. FY2019 predates P-EBT. Total participation excludes disaster supplements.
- **Layout:** seven regional sheets (NERO, MARO, SERO, MWRO, SWRO, MPRO, WRO), each with one block per state: a state-name row, then one row per month. The "US Summary" sheet has the same layout for the nation, including territories.
- **Known issue:** a partial federal shutdown moved February 2019 benefits into January 2019, so USDA's February 2019 count (7.6 million people) is not a real drop. The chart starts in January 2020.
- **Used in post 8** (`src/analysis/post8_enrollment.py`, `reports/data/post8_enrollment.json`, `post8-enrollment.png`):
  - People on SNAP nationally each month, January 2020 to July 2026.
  - Percent change in people on SNAP from January 2025, July 2025 and December 2025 to July 2026, for the US Summary, groups of states by party control (below) and New York State. The post uses July 2025 to July 2026. The chart `post8-enrollment-change.png` groups states by party control of state government in 2026 (see the Ballotpedia section): Republican trifecta states -16.1%, US -13.2%, divided states -14.9%, Democratic trifecta states not counting New York City -10.1%, New York City -8.7% (from the OTDA file below). Each bar also prints the number of fewer people, July 2025 minus July 2026, rounded to the nearest 0.1 million or, under a million, the nearest thousand (Republican 2,545,699; US 5,511,740; divided 1,228,514; Democratic not counting NYC 1,564,460; NYC 155,393). Arizona is a divided state; without it that group fell 10.6%. Without Texas (-19.8%) and Florida (-22.1%), which the post describes as falling about 20%, Republican trifecta states fell 12.9%. With 2025 status instead (Virginia divided, not Democratic), the groups are -16.1%, -14.4% and -10.1%. 
  - The change for each state and DC from July 2025 to July 2026 is kept in the JSON for reference. Arizona's -50.8% is real, not a file error: the Center on Budget and Policy Priorities reports the same figure ("nearly 51 percent lower"), and Arizona's Department of Economic Security has tied it to verification and processing problems in putting the 2025 law in place.
  - Outside check: CBPP's SNAP Tracker reports a national drop of 5.5 million people (13 percent) from July 2025 to July 2026, with every state but Alaska down. Our figures match (5,511,740 people; Alaska +3.5%).
  - These are patterns next to the store exits. They do not show that falling enrollment caused any store to leave SNAP.

## SNAP Caseloads and Expenditures: Beginning 2002 (New York State OTDA)

- **What:** people and households on SNAP each month, by New York social services district. New York City is one district; the other 57 are counties.
- **Where:** data.ny.gov dataset `dq6j-8u8z`, pulled with `https://data.ny.gov/resource/dq6j-8u8z.csv?$limit=200000&$where=year>=2018` on November 10, 2026. Copy in `data/raw/snap_participation/ny-snap-caseloads-dq6j-8u8z.csv`.
- **Version:** through August 2026.
- **Fields used:** `year`, `month`, `district`, `total_snap_persons`.
- **Check against USDA:** the 58 districts summed equal USDA's New York State figure in every start and end month used (for example, 2,667,525 people in July 2026 in both).
- **Used in post 8:** percent change in people on SNAP in New York City and in the rest of New York State (all districts minus New York City), over the same months as the USDA figures. July 2026 is the end month so the city matches the national figures; the August 2026 city count is kept in the JSON for reference.

## Party control of state government (Ballotpedia)

- **What:** for each state and year, the party of the governor and of each legislative chamber, and whether one party holds all three (a trifecta).
- **Where:** Ballotpedia's "Party control of [state] state government" pages and "Historical and potential changes in trifectas", pulled for Eric's earlier analysis in the SUD_V3 project (`scripts/build_trifectas.py`, checked against Ballotpedia's yearly totals). The 2025 and 2026 rows are copied to `data/raw/ballotpedia/trifectas-2025-2026.csv`.
- **Fields used:** `state`, `year`, `trifecta` (R, D or divided).
- **Rules:** Nebraska's one-house legislature is nonpartisan, and Ballotpedia counts its trifecta by the governor's party (Republican). A year is the year officeholders served, so Virginia shows as divided in 2025 and Democratic in 2026. DC has no state government and is in no group; territories are left out.
- **2026 groups:** 23 Republican, 16 Democratic, 11 divided (Alaska, Arizona, Kansas, Kentucky, Michigan, Minnesota, Nevada, North Carolina, Pennsylvania, Vermont, Wisconsin).
- **Used in post 8:** the enrollment change chart groups states this way. It shows where enrollment fell more. It does not show that party control, or any one policy, caused it.

## County population estimates, Vintage 2025 (US Census Bureau)

- **What:** estimated population of every county on July 1, 2025.
- **Where:** https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv, downloaded November 10, 2026, to `data/raw/census/co-est2025-alldata.csv`.
- **Fields used:** `SUMLEV` (050 = county), `STATE` and `COUNTY` (joined as the five-digit GEOID used by the Census county boundaries), `POPESTIMATE2025`.
- **Used in post 8:** the 59 counties with zero or one SNAP store on November 5, 2026 (22 with none, 37 with one) were home to 77,601 people (13,974 in the counties with none). Listed in `reports/data/post8_beats.json` under `counties_zero_or_one_nov5`.

## Curated brand and parent-company files (Data 4 The People)

**What it is.** `data/brands.csv` maps normalized store names to a brand and a
category. `data/brand_groups.csv` maps brands to parent companies, bounded by
year, state and format. USDA records neither.

**Known quirks.** Fuel banners (Shell, BP, Citgo) are the fuel supplier, not the
operator, so a name that starts with one resolves to unknown. A banner later in
the name ("Hwy 72 Exxon") does not trigger the rule; of about 13,350
mappable convenience stores named that way, 12,476 are classed independent. The prefix pattern for the Lucky supermarket banner also catches
1,164 mappable convenience stores named LUCKY FOOD MART, LUCKY 7 and similar,
which are probably unrelated. They count as chain stores; removing them moves
the chain convenience exit rate for 2026 from 3.9% to 3.7%. Small real chains
below the name-count threshold (JR Food Store, 33 stores) can land in unknown. Voluntary alliances such as IGA resolve to
independent. Generic names such as FOOD MART stay unknown.

## 2020 cartographic boundary file, states, 1:20m (US Census Bureau)

**What it is.** State outlines, drawn under the dots on the static map.
`cb_2020_us_state_20m.zip` from `www2.census.gov/geo/tiger/GENZ2020/shp/`,
cached in `data/raw/`. Lower 48 only; Alaska, Hawaii and the territories are
cut by bounding box, and any count beside the map says how many points it
shows. Public domain.
