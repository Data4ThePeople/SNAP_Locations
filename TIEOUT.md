# Tie-out

Recomputed by `src/tieout_live.py` from `data/raw/hist.csv` and `data/raw/live/snap-live-2026-11-05.csv.gz`. `mappable` and `format` are read from `dim_store`.

| Item | Built | Recomputed | Result | Where it appears |
|---|---:|---:|---|---|
| Live feed rows | 248,175 | 248,175 | match | fetch_live.py output |
| Restaurant Meals Program rows dropped | 8,565 | 8,565 | match | DATASETS.md |
| Live-only farmers-market rows dropped | 3,709 | 3,709 | match | DATASETS.md |
| Stores on the map, Nov 5, 2026 | 235,892 | 235,892 | match | map count line |
| Live-only stores on the map | 11,869 | 11,869 | match | map About note |
| Slider label | Nov 5, 2026 | Nov 5, 2026 | match | map year label |
| Convenience stores on the map, Nov 5, 2026 | 108,075 | 108,075 | match | format panel |
| Stores authorized Dec 31, 2025 (mappable) | 249,083 | 249,083 | match | left_2026.json |
| Exits, all formats | 26,129 | 26,129 | match | left_2026.json |
| Exits replaced at same address | 3,764 | 3,764 | match | static map note: 3,755 |
| Exits not replaced, all formats | 22,365 | 22,365 | match | static map note: nationally |
| Convenience stores, Dec 31, 2025 | 117,055 | 117,055 | match | left_2026.json |
| Convenience exits | 17,131 | 17,131 | match | chat summary |
| Convenience exits not replaced | 14,888 | 14,888 | match | static map key: convenience |
| Other exits not replaced | 7,477 | 7,477 | match | static map key: other |
| Exits shown in lower 48 | 22,191 | 22,191 | match | static map note: shown |
| Convenience share not replaced, 2026 (%) | 12.7 | 12.7 | match | chat summary |
| 2019 convenience exits not replaced | 9,293 | 9,293 | match | chat summary baseline |
| 2020 convenience exits not replaced | 5,440 | 5,440 | match | chat summary baseline |
| 2021 convenience exits not replaced | 7,466 | 7,466 | match | chat summary baseline |
| 2022 convenience exits not replaced | 6,563 | 6,563 | match | chat summary baseline |
| 2023 convenience exits not replaced | 6,898 | 6,898 | match | chat summary baseline |
| 2024 convenience exits not replaced | 6,139 | 6,139 | match | chat summary baseline |
| 2025 convenience exits not replaced | 8,204 | 8,204 | match | chat summary baseline |

## Words

| Text on the output | Source | Verdict |
|---|---|---|
| Static map title: "Stores that left SNAP so far in 2026" | Exit test in DATASETS.md, Dec 31, 2025 to Nov 5, 2026 | supported |
| Static map subtitle: "authorized December 31, 2025, not on USDA's list November 5, 2026" | Historical file end date; live feed dataLastEditDate 2026-11-05 21:00 UTC | supported |
| Static map key: "still in SNAP" | Ground layer is live_store rows kept on the map | supported |
| Static map note: "exits where a different authorization appeared at the same address" | Address test in DATASETS.md; recomputed above | supported |
| Static map note: "Source: USDA SNAP retailer data" | DATASETS.md, both USDA sections | supported |
| Map slider label: "Nov 5, 2026" | Live feed refresh date | supported |
| Map About note: last step is USDA's live list that day, not a Dec 31 count | DATASETS.md, live feed: no authorization dates, one-day list | supported |
| Map About note: matched stores keep their historical format | load_live.py; DATASETS.md | supported |
| Map About note: new stores carry USDA's broader live types, "size not given", "type not given" | Live feed's 8 types; DATASETS.md mapping | supported |
| Map About note: Restaurant Meals sites and farmers-market entries the historical file never carried are left out | Counts above (8,565 and 3,709); DATASETS.md | supported |
| Map subtitle: "Authorized retailers, 2006–2026" | Snapshots Dec 31, 2006 to Nov 5, 2026 | supported |
