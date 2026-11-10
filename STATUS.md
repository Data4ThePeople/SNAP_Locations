# Status

Project: SNAP_Locations
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: post 8, stores that left SNAP in 2026 and what the stocking rule has not touched yet (slug set at 2a; posts 0 to 7 in `reports/` were published before this file existed)
Step: 1
Since: 2026-11-09

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | | Reopened for the November 5, 2026 live-feed layer and a static map of 2026 exits |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |

## Stale

None. No later step had been confirmed under this file.

## Log

- 2026-11-09 Step 1 reopened (`/step back 1`). Reason: the stocking rule took effect November 4, 2026, and USDA's live retailer feed (refreshed November 5) is newer than the historical file, which ends December 31, 2025. Adding a November 5, 2026 layer to the map and a static map of stores that left SNAP in 2026.
- 2026-11-09 Built the November 5, 2026 map step from the live feed (`fetch_live.py`, `load_live.py`, `export_map.py`) and the static map of 2026 exits (`analysis/left_2026.py`). Wrote `DATASETS.md`; own tie-out 24 of 24 in `TIEOUT.md`. Rebuilt `dist/snap-map.html` held back from git until Eric approves, because Pages serves it live.
- 2026-11-09 Independent tie-out found: (1) historical ZIPs lose leading zeros, so the 2026 same-address test missed 442 replacements in New England, NJ and VI; fixed by padding, convenience exits not replaced 14,888 -> 14,684 (12.5%); (2) the map's "opened and closed between Dec 31sts" count mixed live-only stores in (33,786); now 14,520 (2.2%), and 31,135 more left before Dec 31, 2006; (3) the out-of-US geocode list was misdescribed (37 Guam, 1 Caracas, 1 Tibet); (4) wording on the static map and map note tightened. Own tie-out now 26 of 26.
- 2026-11-09 Eric approved pushing the rebuilt `dist/snap-map.html` live. Updated `reports/visualization-page-meta.md` for the November 5, 2026 step: years to 2006–2026, store count 673,325 (661,456 historical plus 11,869 live-only), never-shown count corrected from 45,704 (7.0%) to 14,520 (2.2%) plus 31,135 before Dec 31, 2006, live feed added as a source, 20 formats, bundle size 8.61MB.
- 2026-11-09 Eric opened post 8: a map of 2026 exits, charts drilling into convenience stores, a stocking-rule update, and the point that the rule's effect is likely not in the numbers yet. Built `src/analysis/post8_left2026.py` (7 charts in `reports/post8/images/`, data in `reports/data/post8.json`), research brief `reports/research/stocking-rule-2026-11.md`, own tie-out `src/tieout_post8.py` 72 of 72. Exit test moved into `left_2026.exits()`; output unchanged.
- 2026-11-09 Independent tie-out of post 8: every count matched except 2026 new convenience stores (8,151 vs 8,149; state-envelope approximation on 2 live-only stores). Six rounded values off by 0.1 because averages were taken of rounded rates; fixed (unrounded mean, halves up; Grocery (Large) 2026 now 6.4%, Grocery (Medium) average 4.3%). Fixed: lag check now counts stores (1,192) and moves them out of the base too (still 11.6%); chart labels (trend subtitle names the address test, states chart says "highest share", "All states and territories", new-store chart discloses older IDs, map note names territories); research brief page cites (25086 not 25087), senators wording, and an over-certain sentence. Disclosed in DATASETS.md: inclusive end date, replaced share fell to 14.3% in 2026 from 25% to 37% (before the address test 14.6% vs 9.0% average), Lucky prefix catching 1,164 unrelated convenience stores, fuel banners mid-name not resolving to unknown. Own tie-out now 82 of 82.
- 2026-11-10 Added USDA's regulatory impact and small-business analyses (docket FNS-2025-0018-0236 and -0235, downloaded by Eric) to the research brief. Added the gap above earlier years to `post8_left2026.py`: 7,362 convenience exits above the 2019–2025 average rate (5,072 above the highest year; 6,600 before the address test; 6,245 lag-adjusted). Own tie-out 85 of 85.
