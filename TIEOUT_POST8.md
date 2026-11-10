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
| Split restricted: 2026, average, rise in points | ({'base': 28508, 'left': 4314, 'pct': 15.1}, 6.2, 8.9) | ({'base': 28508, 'left': 4314, 'pct': 15.1}, 6.2, 8.9) | match |
| Split other_states: 2026, average, rise in points | ({'base': 88426, 'left': 10338, 'pct': 11.7}, 6.3, 5.4) | ({'base': 88426, 'left': 10338, 'pct': 11.7}, 6.3, 5.4) | match |
| Split nyc: 2026, average, rise in points | ({'base': 3580, 'left': 1092, 'pct': 30.5}, 14.1, 16.4) | ({'base': 3580, 'left': 1092, 'pct': 30.5}, 14.1, 16.4) | match |
| Split rest_of_ny: 2026, average, rise in points | ({'base': 3675, 'left': 462, 'pct': 12.6}, 6.5, 6.1) | ({'base': 3675, 'left': 462, 'pct': 12.6}, 6.5, 6.1) | match |
| Restriction states list | ['FL', 'IA', 'ID', 'IN', 'LA', 'NE', 'OK', 'TX', 'UT', 'WV'] | ['FL', 'IA', 'ID', 'IN', 'LA', 'NE', 'OK', 'TX', 'UT', 'WV'] | match |
| Gap not_replaced: vs average, vs highest year | (7362, 5072) | (7362, 5072) | match |
| Gap before_address_test: vs average, vs highest year | (6600, 4320) | (6600, 4320) | match |
| Gap not_replaced_lag_adjusted: vs average, vs highest year | (6245, 3978) | (6245, 3978) | match |
| Net change 2019: Dec 31, Nov 5, net | (245088, 242048, -3040) | (245088, 242048, -3040) | match |
| Net change 2020: Dec 31, Nov 5, net | (239745, 244685, 4940) | (239745, 244685, 4940) | match |
| Net change 2021: Dec 31, Nov 5, net | (244283, 247633, 3350) | (244283, 247633, 3350) | match |
| Net change 2022: Dec 31, Nov 5, net | (247327, 251489, 4162) | (247327, 251489, 4162) | match |
| Net change 2023: Dec 31, Nov 5, net | (250757, 253548, 2791) | (250757, 253548, 2791) | match |
| Net change 2024: Dec 31, Nov 5, net | (252100, 255227, 3127) | (252100, 255227, 3127) | match |
| Net change 2025: Dec 31, Nov 5, net | (254811, 250511, -4300) | (254811, 250511, -4300) | match |
| Net change 2026: Dec 31, Nov 5, net | (249083, 235892, -13191) | (249083, 235892, -13191) | match |
| Exits 2019: left, left before address test, base | (15224, 19696, 245088) | (15224, 19696, 245088) | match |
| Exits 2020: left, left before address test, base | (8872, 12660, 239745) | (8872, 12660, 239745) | match |
| Exits 2021: left, left before address test, base | (11089, 15656, 244283) | (11089, 15656, 244283) | match |
| Exits 2022: left, left before address test, base | (10056, 14578, 247327) | (10056, 14578, 247327) | match |
| Exits 2023: left, left before address test, base | (11215, 15849, 250757) | (11215, 15849, 250757) | match |
| Exits 2024: left, left before address test, base | (10826, 16081, 252100) | (10826, 16081, 252100) | match |
| Exits 2025: left, left before address test, base | (14493, 19069, 254811) | (14493, 19069, 254811) | match |
| Exits 2026: left, left before address test, base | (21923, 26129, 249083) | (21923, 26129, 249083) | match |
| 2026 exits vs 2019-2025 average: % above (subtitle "88% more") | 88 | 88 | match |
| Exit waterfall start and end | (11682, 21923) | (11682, 21923) | match |
| Exit waterfall Independent convenience: average, 2026, change | (4576, 9290, 4714) | (4576, 9290, 4714) | match |
| Exit waterfall Other convenience: average, 2026, change | (2567, 5394, 2827) | (2567, 5394, 2827) | match |
| Exit waterfall Grocery, any size: average, 2026, change | (1460, 3610, 2150) | (1460, 3610, 2150) | match |
| Exit waterfall All other stores: average, 2026, change | (3079, 3629, 550) | (3079, 3629, 550) | match |
| Entries 2019: all, at exit address, ratio, ratio before address test | (16656, 4469, 1.25, 1.18) | (16656, 4469, 1.25, 1.18) | match |
| Entries 2020: all, at exit address, ratio, ratio before address test | (17600, 3777, 0.64, 0.72) | (17600, 3777, 0.64, 0.72) | match |
| Entries 2021: all, at exit address, ratio, ratio before address test | (19006, 4562, 0.77, 0.82) | (19006, 4562, 0.77, 0.82) | match |
| Entries 2022: all, at exit address, ratio, ratio before address test | (18740, 4517, 0.71, 0.78) | (18740, 4517, 0.71, 0.78) | match |
| Entries 2023: all, at exit address, ratio, ratio before address test | (18640, 4609, 0.8, 0.85) | (18640, 4609, 0.8, 0.85) | match |
| Entries 2024: all, at exit address, ratio, ratio before address test | (19208, 5257, 0.78, 0.84) | (19208, 5257, 0.78, 0.84) | match |
| Entries 2025: all, at exit address, ratio, ratio before address test | (14769, 4556, 1.42, 1.29) | (14769, 4556, 1.42, 1.29) | match |
| Entries 2026: all, at exit address, ratio, ratio before address test | (12938, 4160, 2.5, 2.02) | (12938, 4160, 2.5, 2.02) | match |
| Entries 2026: older-ID live-only, ratio without them | (2273, 3.15) | (2273, 3.15) | match |
| Rate independent_convenience 2019 | {'base': 52195, 'left': 6026, 'pct': 11.5} | {'base': 52195, 'left': 6026, 'pct': 11.5} | match |
| Rate independent_convenience 2020 | {'base': 49138, 'left': 3707, 'pct': 7.5} | {'base': 49138, 'left': 3707, 'pct': 7.5} | match |
| Rate independent_convenience 2021 | {'base': 50051, 'left': 5091, 'pct': 10.2} | {'base': 50051, 'left': 5091, 'pct': 10.2} | match |
| Rate independent_convenience 2022 | {'base': 49776, 'left': 4287, 'pct': 8.6} | {'base': 49776, 'left': 4287, 'pct': 8.6} | match |
| Rate independent_convenience 2023 | {'base': 49982, 'left': 3990, 'pct': 8.0} | {'base': 49982, 'left': 3990, 'pct': 8.0} | match |
| Rate independent_convenience 2024 | {'base': 50851, 'left': 3900, 'pct': 7.7} | {'base': 50851, 'left': 3900, 'pct': 7.7} | match |
| Rate independent_convenience 2025 | {'base': 52343, 'left': 5031, 'pct': 9.6} | {'base': 52343, 'left': 5031, 'pct': 9.6} | match |
| Rate independent_convenience 2026 | {'base': 51003, 'left': 9290, 'pct': 18.2} | {'base': 51003, 'left': 9290, 'pct': 18.2} | match |
| Rate chain_convenience 2019 | {'base': 35821, 'left': 871, 'pct': 2.4} | {'base': 35821, 'left': 871, 'pct': 2.4} | match |
| Rate chain_convenience 2020 | {'base': 36369, 'left': 358, 'pct': 1.0} | {'base': 36369, 'left': 358, 'pct': 1.0} | match |
| Rate chain_convenience 2021 | {'base': 37825, 'left': 555, 'pct': 1.5} | {'base': 37825, 'left': 555, 'pct': 1.5} | match |
| Rate chain_convenience 2022 | {'base': 38870, 'left': 608, 'pct': 1.6} | {'base': 38870, 'left': 608, 'pct': 1.6} | match |
| Rate chain_convenience 2023 | {'base': 40057, 'left': 1273, 'pct': 3.2} | {'base': 40057, 'left': 1273, 'pct': 3.2} | match |
| Rate chain_convenience 2024 | {'base': 40227, 'left': 751, 'pct': 1.9} | {'base': 40227, 'left': 751, 'pct': 1.9} | match |
| Rate chain_convenience 2025 | {'base': 40683, 'left': 1265, 'pct': 3.1} | {'base': 40683, 'left': 1265, 'pct': 3.1} | match |
| Rate chain_convenience 2026 | {'base': 40540, 'left': 1565, 'pct': 3.9} | {'base': 40540, 'left': 1565, 'pct': 3.9} | match |
| Rate nyc_small 2019 | {'base': 4922, 'left': 638, 'pct': 13.0} | {'base': 4922, 'left': 638, 'pct': 13.0} | match |
| Rate nyc_small 2020 | {'base': 4600, 'left': 567, 'pct': 12.3} | {'base': 4600, 'left': 567, 'pct': 12.3} | match |
| Rate nyc_small 2021 | {'base': 4313, 'left': 745, 'pct': 17.3} | {'base': 4313, 'left': 745, 'pct': 17.3} | match |
| Rate nyc_small 2022 | {'base': 4223, 'left': 634, 'pct': 15.0} | {'base': 4223, 'left': 634, 'pct': 15.0} | match |
| Rate nyc_small 2023 | {'base': 4323, 'left': 532, 'pct': 12.3} | {'base': 4323, 'left': 532, 'pct': 12.3} | match |
| Rate nyc_small 2024 | {'base': 4341, 'left': 501, 'pct': 11.5} | {'base': 4341, 'left': 501, 'pct': 11.5} | match |
| Rate nyc_small 2025 | {'base': 4552, 'left': 646, 'pct': 14.2} | {'base': 4552, 'left': 646, 'pct': 14.2} | match |
| Rate nyc_small 2026 | {'base': 4624, 'left': 1368, 'pct': 29.6} | {'base': 4624, 'left': 1368, 'pct': 29.6} | match |
| Rate us_small_outside_nyc 2019 | {'base': 117048, 'left': 9875, 'pct': 8.4} | {'base': 117048, 'left': 9875, 'pct': 8.4} | match |
| Rate us_small_outside_nyc 2020 | {'base': 112690, 'left': 5734, 'pct': 5.1} | {'base': 112690, 'left': 5734, 'pct': 5.1} | match |
| Rate us_small_outside_nyc 2021 | {'base': 115704, 'left': 7598, 'pct': 6.6} | {'base': 115704, 'left': 7598, 'pct': 6.6} | match |
| Rate us_small_outside_nyc 2022 | {'base': 116809, 'left': 6625, 'pct': 5.7} | {'base': 116809, 'left': 6625, 'pct': 5.7} | match |
| Rate us_small_outside_nyc 2023 | {'base': 118617, 'left': 7097, 'pct': 6.0} | {'base': 118617, 'left': 7097, 'pct': 6.0} | match |
| Rate us_small_outside_nyc 2024 | {'base': 120038, 'left': 6283, 'pct': 5.2} | {'base': 120038, 'left': 6283, 'pct': 5.2} | match |
| Rate us_small_outside_nyc 2025 | {'base': 122829, 'left': 8517, 'pct': 6.9} | {'base': 122829, 'left': 8517, 'pct': 6.9} | match |
| Rate us_small_outside_nyc 2026 | {'base': 120418, 'left': 15263, 'pct': 12.7} | {'base': 120418, 'left': 15263, 'pct': 12.7} | match |
| Counties newly at zero | ['31085', '35021'] | ['31085', '35021'] | match |
| Counties down to one | ['13101', '38065', '48155', '50009'] | ['13101', '38065', '48155', '50009'] | match |
| Counties halved (to 2+) | ['08047', '18171', '38011', '48345'] | ['08047', '18171', '38011', '48345'] | match |
| Counties with 0 and 1 store, Dec 31 and Nov 5 | (21, 22, 35, 37) | (21, 22, 35, 37) | match |
| County Harding County, New Mexico: Dec 31, Nov 5 | (1, 0) | (1, 0) | match |
| County Hayes County, Nebraska: Dec 31, Nov 5 | (1, 0) | (1, 0) | match |
| County Oliver County, North Dakota: Dec 31, Nov 5 | (3, 1) | (3, 1) | match |
| County Echols County, Georgia: Dec 31, Nov 5 | (2, 1) | (2, 1) | match |
| County Essex County, Vermont: Dec 31, Nov 5 | (2, 1) | (2, 1) | match |
| County Foard County, Texas: Dec 31, Nov 5 | (2, 1) | (2, 1) | match |
| County Bowman County, North Dakota: Dec 31, Nov 5 | (4, 2) | (4, 2) | match |
| County Gilpin County, Colorado: Dec 31, Nov 5 | (4, 2) | (4, 2) | match |
| County Motley County, Texas: Dec 31, Nov 5 | (4, 2) | (4, 2) | match |
| County Warren County, Indiana: Dec 31, Nov 5 | (4, 2) | (4, 2) | match |
| Places top 10 (place, left, base, %) | [('New York City', 1368, 4624, 29.6), ('Harris County, TX', 518, 2092, 24.8), ('Los Angeles County, CA', 497, 3380, 14.7), ('Cook County, IL', 250, 1601, 15.6), ('Philadelphia County, PA', 249, 1031, 24.2), ('Wayne County, MI', 177, 1322, 13.4), ('Dallas County, TX', 163, 933, 17.5), ('Tarrant County, TX', 126, 735, 17.1), ('Miami Dade County, FL', 115, 489, 23.5), ('Bexar County, TX', 102, 788, 12.9)] | [('New York City', 1368, 4624, 29.6), ('Harris County, TX', 518, 2092, 24.8), ('Los Angeles County, CA', 497, 3380, 14.7), ('Cook County, IL', 250, 1601, 15.6), ('Philadelphia County, PA', 249, 1031, 24.2), ('Wayne County, MI', 177, 1322, 13.4), ('Dallas County, TX', 163, 933, 17.5), ('Tarrant County, TX', 126, 735, 17.1), ('Miami Dade County, FL', 115, 489, 23.5), ('Bexar County, TX', 102, 788, 12.9)] | match |
| NYC share of US exits and of US stores (conv + small grocery) | (8.2, 3.7) | (8.2, 3.7) | match |
| NYC share of US Convenience Store exits | 7.4 | 7.4 | match |
| NYC share of US Grocery (Small) exits | 14.2 | 14.2 | match |
| NYC map: stores still in SNAP (five boroughs, Nov 5 universe) | 7,510 | 7,510 | match |
| NYC map: convenience and small groceries that left | 1,368 | 1,368 | match |

## Words

| Text on the output | Source | Verdict |
|---|---|---|
| Splits chart: "limit states had a SNAP soda or candy purchase restriction in effect in 2026" | Chrisinger and White, Health Affairs Scholar 4(10) qxag275, Oct 2026: ten states implemented during Jan 2025 to Jun 2026; IA, NE, WV blocked Jun 22, 2026 | supported; AR and MT targeted mid-2026 starts are unconfirmed and sit in the comparison group (DATASETS.md) |
| Splits chart: "New York City" | historical file County field: New York, Kings, Queens, Bronx, Richmond | matches |
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
