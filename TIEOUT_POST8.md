# Tie-out, post 8

Recomputed by `src/tieout_post8.py` from `data/raw/hist.csv` and `data/raw/live/snap-live-2026-11-05.csv.gz`. `mappable`, `format`, `ownership` and `brand` are read from `dim_store`.

| Item | Built | Recomputed | Result |
|---|---|---|---|
| Convenience 2019: base, left, % | {'base': 113173, 'left': 9293, 'pct': 8.2} | {'base': 113173, 'left': 9293, 'pct': 8.2} | match |
| All other stores 2019: % | 4.5 | 4.5 | match |
| New convenience 2019: count, % | (10101, 8.9) | (10101, 8.9) | match |
| Convenience 2020: base, left, % | {'base': 109302, 'left': 5440, 'pct': 5.0} | {'base': 109302, 'left': 5440, 'pct': 5.0} | match |
| All other stores 2020: % | 2.6 | 2.6 | match |
| New convenience 2020: count, % | (11278, 10.3) | (11278, 10.3) | match |
| Convenience 2021: base, left, % | {'base': 112406, 'left': 7466, 'pct': 6.6} | {'base': 112406, 'left': 7466, 'pct': 6.6} | match |
| All other stores 2021: % | 2.7 | 2.7 | match |
| New convenience 2021: count, % | (11711, 10.4) | (11711, 10.4) | match |
| Convenience 2022: base, left, % | {'base': 113365, 'left': 6563, 'pct': 5.8} | {'base': 113365, 'left': 6563, 'pct': 5.8} | match |
| All other stores 2022: % | 2.6 | 2.6 | match |
| New convenience 2022: count, % | (11926, 10.5) | (11926, 10.5) | match |
| Convenience 2023: base, left, % | {'base': 115021, 'left': 6898, 'pct': 6.0} | {'base': 115021, 'left': 6898, 'pct': 6.0} | match |
| All other stores 2023: % | 3.2 | 3.2 | match |
| New convenience 2023: count, % | (12083, 10.5) | (12083, 10.5) | match |
| Convenience 2024: base, left, % | {'base': 116404, 'left': 6139, 'pct': 5.3} | {'base': 116404, 'left': 6139, 'pct': 5.3} | match |
| All other stores 2024: % | 3.5 | 3.5 | match |
| New convenience 2024: count, % | (12233, 10.5) | (12233, 10.5) | match |
| Convenience 2025: base, left, % | {'base': 118983, 'left': 8204, 'pct': 6.9} | {'base': 118983, 'left': 8204, 'pct': 6.9} | match |
| All other stores 2025: % | 4.6 | 4.6 | match |
| New convenience 2025: count, % | (9032, 7.6) | (9032, 7.6) | match |
| Convenience 2026: base, left, % | {'base': 117055, 'left': 14684, 'pct': 12.5} | {'base': 117055, 'left': 14684, 'pct': 12.5} | match |
| All other stores 2026: % | 5.5 | 5.5 | match |
| New convenience 2026: count, % | (8151, 7.0) | (8151, 7.0) | match |
| New convenience 2026 without older IDs: count, % | (6480, 5.5) | (6480, 5.5) | match |
| Convenience 2019–2025 average | 6.3 | 6.3 | match |
| Convenience 2019 before address test: left, %, replaced, replaced share | (12386, 10.9, 3093, 25.0) | (12386, 10.9, 3093, 25.0) | match |
| Convenience 2020 before address test: left, %, replaced, replaced share | (8145, 7.5, 2705, 33.2) | (8145, 7.5, 2705, 33.2) | match |
| Convenience 2021 before address test: left, %, replaced, replaced share | (10699, 9.5, 3233, 30.2) | (10699, 9.5, 3233, 30.2) | match |
| Convenience 2022 before address test: left, %, replaced, replaced share | (9700, 8.6, 3137, 32.3) | (9700, 8.6, 3137, 32.3) | match |
| Convenience 2023 before address test: left, %, replaced, replaced share | (10129, 8.8, 3231, 31.9) | (10129, 8.8, 3231, 31.9) | match |
| Convenience 2024 before address test: left, %, replaced, replaced share | (9793, 8.4, 3654, 37.3) | (9793, 8.4, 3654, 37.3) | match |
| Convenience 2025 before address test: left, %, replaced, replaced share | (11050, 9.3, 2846, 25.8) | (11050, 9.3, 2846, 25.8) | match |
| Convenience 2026 before address test: left, %, replaced, replaced share | (17131, 14.6, 2447, 14.3) | (17131, 14.6, 2447, 14.3) | match |
| Convenience before address test, 2019–2025 average | 9.0 | 9.0 | match |
| All other 2019–2025 average | 3.4 | 3.4 | match |
| Ownership chain: 2026 | {'base': 40540, 'left': 1565, 'pct': 3.9} | {'base': 40540, 'left': 1565, 'pct': 3.9} | match |
| Ownership chain: 2019–2025 average | 2.1 | 2.1 | match |
| Ownership independent: 2026 | {'base': 51003, 'left': 9290, 'pct': 18.2} | {'base': 51003, 'left': 9290, 'pct': 18.2} | match |
| Ownership independent: 2019–2025 average | 9.0 | 9.0 | match |
| Ownership unknown: 2026 | {'base': 25512, 'left': 3829, 'pct': 15.0} | {'base': 25512, 'left': 3829, 'pct': 15.0} | match |
| Ownership unknown: 2019–2025 average | 7.0 | 7.0 | match |
| Chains with 1,000+ convenience stores | ['7-Eleven', 'Circle K', 'Speedway', "Casey's", 'QuikTrip', 'Wawa', 'Murphy USA'] | ['7-Eleven', 'Circle K', 'Speedway', "Casey's", 'QuikTrip', 'Wawa', 'Murphy USA'] | match |
| 7-Eleven: 2025 %, 2026 % | (5.3, 5.5) | (5.3, 5.5) | match |
| Circle K: 2025 %, 2026 % | (2.3, 2.9) | (2.3, 2.9) | match |
| Speedway: 2025 %, 2026 % | (3.6, 5.6) | (3.6, 5.6) | match |
| Casey's: 2025 %, 2026 % | (1.0, 0.8) | (1.0, 0.8) | match |
| QuikTrip: 2025 %, 2026 % | (0.0, 0.7) | (0.0, 0.7) | match |
| Wawa: 2025 %, 2026 % | (0.6, 0.8) | (0.6, 0.8) | match |
| Murphy USA: 2025 %, 2026 % | (0.4, 1.9) | (0.4, 1.9) | match |
| Top 15 states by 2026 rate | ['NY', 'LA', 'CT', 'MS', 'TX', 'AR', 'AL', 'NJ', 'FL', 'GA', 'IN', 'PA', 'OK', 'ID', 'SC'] | ['NY', 'LA', 'CT', 'MS', 'TX', 'AR', 'AL', 'NJ', 'FL', 'GA', 'IN', 'PA', 'OK', 'ID', 'SC'] | match |
| NY: 2026 %, average % | (21.4, 10.1) | (21.4, 10.1) | match |
| LA: 2026 %, average % | (20.3, 9.3) | (20.3, 9.3) | match |
| CT: 2026 %, average % | (19.3, 9.1) | (19.3, 9.1) | match |
| MS: 2026 %, average % | (17.6, 11.0) | (17.6, 11.0) | match |
| TX: 2026 %, average % | (17.4, 6.5) | (17.4, 6.5) | match |
| AR: 2026 %, average % | (17.2, 9.3) | (17.2, 9.3) | match |
| AL: 2026 %, average % | (16.0, 8.1) | (16.0, 8.1) | match |
| NJ: 2026 %, average % | (16.0, 8.4) | (16.0, 8.4) | match |
| FL: 2026 %, average % | (15.7, 6.9) | (15.7, 6.9) | match |
| GA: 2026 %, average % | (15.7, 8.2) | (15.7, 8.2) | match |
| IN: 2026 %, average % | (13.4, 4.5) | (13.4, 4.5) | match |
| PA: 2026 %, average % | (13.3, 5.6) | (13.3, 5.6) | match |
| OK: 2026 %, average % | (13.1, 6.0) | (13.1, 6.0) | match |
| ID: 2026 %, average % | (11.9, 3.5) | (11.9, 3.5) | match |
| SC: 2026 %, average % | (11.7, 6.3) | (11.7, 6.3) | match |
| Grocery (Small): 2026 %, average % | (24.4, 10.6) | (24.4, 10.6) | match |
| Specialty (Seafood): 2026 %, average % | (15.4, 8.2) | (15.4, 8.2) | match |
| Specialty (Bakery): 2026 %, average % | (13.2, 8.1) | (13.2, 8.1) | match |
| Convenience Store: 2026 %, average % | (12.5, 6.3) | (12.5, 6.3) | match |
| Specialty (Meat/Poultry): 2026 %, average % | (12.5, 6.1) | (12.5, 6.1) | match |
| Grocery (Medium): 2026 %, average % | (12.2, 4.3) | (12.2, 4.3) | match |
| Grocery (Large): 2026 %, average % | (6.4, 3.0) | (6.4, 3.0) | match |
| Combination Grocery/Other: 2026 %, average % | (5.8, 5.0) | (5.8, 5.0) | match |
| Farmers' Market: 2026 %, average % | (3.6, 7.3) | (3.6, 7.3) | match |
| Supermarket: 2026 %, average % | (2.4, 1.5) | (2.4, 1.5) | match |
| Dollar Store: 2026 %, average % | (1.7, 1.1) | (1.7, 1.1) | match |
| Super Store: 2026 %, average % | (1.5, 1.4) | (1.5, 1.4) | match |
| Store types with 1,000+ | ['Combination Grocery/Other', 'Convenience Store', 'Dollar Store', "Farmers' Market", 'Grocery (Large)', 'Grocery (Medium)', 'Grocery (Small)', 'Specialty (Bakery)', 'Specialty (Meat/Poultry)', 'Specialty (Seafood)', 'Super Store', 'Supermarket'] | ['Combination Grocery/Other', 'Convenience Store', 'Dollar Store', "Farmers' Market", 'Grocery (Large)', 'Grocery (Medium)', 'Grocery (Small)', 'Specialty (Bakery)', 'Specialty (Meat/Poultry)', 'Specialty (Seafood)', 'Super Store', 'Supermarket'] | match |
| Map: convenience exits shown in lower 48 | 14,586 | 14,586 | match |
| Q4 convenience stores with end dates, 2022–2025 | {'2022': 3423, '2023': 3428, '2024': 3195, '2025': 2157} | {'2022': 3423, '2023': 3428, '2024': 3195, '2025': 2157} | match |
| Q4 shortfall and adjusted 2026 rate | (1192, 11.6) | (1192, 11.6) | match |

## Words

| Text on the output | Source | Verdict |
|---|---|---|
| Every chart: "left SNAP" (never "closed") | Authorization records; memory rule and DATASETS.md | supported |
| Every rate subtitle: "% of ... authorized on December 31 of the year before" | Base in DATASETS.md exit test; recomputed above | supported |
| Trend and new-store titles: "between January 1 and November 5" | Exit window Dec 31 to Nov 5 in DATASETS.md; live feed refresh date | supported |
| Trend and new-store marker: "live list" at 2026 | DATASETS.md: 2026 reads Nov 5 from the live feed, earlier years from the file | supported |
| Map title: "Convenience stores that left SNAP so far in 2026" | Exit test, Dec 31, 2025 to Nov 5, 2026 | supported |
| Map subtitle: "no new authorization at the same address" | Address test in DATASETS.md | supported |
| Map note: "Count includes Alaska, Hawaii and the territories; the map shows the lower 48" | Shown count recomputed above | supported |
| Trend subtitle: "excludes exits replaced at the same address" | Exit test in DATASETS.md | supported |
| State chart title: "highest share"; first row "All states and territories" | Ranked by 2026 rate; base includes territories | supported |
| New-store subtitle: "still authorized November 5"; "2026 includes 1,671 stores with older IDs (5.5% without them)" | DATASETS.md post 8 breakdowns; recomputed above | supported |
| Map key: "still in SNAP" (convenience stores on the Nov 5 list) | Ground layer: live_store convenience rows on the map | supported |
| Ownership rows: Chain, Independent, Owner unknown | dim_store ownership; DATASETS.md curated brands (independent = name on 4 or fewer stores) | supported |
| Legend: "2019–2025 average" | Simple mean of seven yearly rates, DATASETS.md post 8 breakdowns | supported |
| State chart: "states with 500 or more" | Threshold recomputed above | supported |
| Store-type chart: "types with 1,000 or more" | Threshold recomputed above | supported |
| Chain chart: "Largest convenience chains" (1,000 or more stores on Dec 31, 2025) | Recomputed above; threshold not printed on the chart | partly supported |
| Map source line: USDA Food and Nutrition Administration, historical data and live feed | DATASETS.md credit lines | supported |
