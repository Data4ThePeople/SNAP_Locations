# Status

Project: SNAP_Locations
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: none yet (stocking-rule update to the map; posts 0 to 7 in `reports/` were published before this file existed)
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
