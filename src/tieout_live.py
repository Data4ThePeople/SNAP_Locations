"""Tie out every number on the November 2026 map step and the 2026 exits map.

Recomputed in pandas from the raw files (data/raw/hist.csv and the live
snapshot gzip), not from fact_spell or live_store, then compared with what the
build wrote: web/data/meta.json and reports/data/left_2026.json. Two inputs
are taken from dim_store because recomputing them would mean re-running the
classifier: `mappable` (the geocode flags) and `format` (USDA type plus the
dollar-store split). Writes TIEOUT.md and exits non-zero on any mismatch.

    python src/tieout_live.py
"""
import gzip
import json
import re
import sys
from datetime import date

import pandas as pd

from config import CSV_PATH, ROOT, connect
from fetch_live import LIVE_DIR

ROWS = []

# Every label and sourced claim on the two outputs, checked against its source.
WORDS = [
    ("Static map title: \"Stores that left SNAP so far in 2026\"",
     "Exit test in DATASETS.md, Dec 31, 2025 to Nov 5, 2026", "supported"),
    ("Static map subtitle: \"authorized December 31, 2025, not on USDA's list November 5, 2026, no new authorization at the same address\"",
     "Historical file end date; live feed dataLastEditDate 2026-11-05 21:00 UTC; address test in DATASETS.md", "supported"),
    ("Static map key: \"still in SNAP\"", "Ground layer is the Nov 5, 2026 map step, defined in DATASETS.md", "supported"),
    ("Static map note: \"Counts are national; the map shows the lower 48\"", "Shown count recomputed above", "supported"),
    ("Static map note: \"exits where a different authorization appeared at the same address\"",
     "Address test in DATASETS.md; recomputed above", "supported"),
    ("Static map note: source credits USDA Food and Nutrition Administration, historical data and live feed",
     "DATASETS.md credit lines", "supported"),
    ("Map About note: \"N stores (P%) opened and closed between two Dec 31sts and never appear\"",
     "Recomputed above from raw spells", "supported"),
    ("Map About note: \"Stores without usable coordinates are excluded\"", "DATASETS.md missing and misplaced geocodes", "supported"),
    ("Map slider label: \"Nov 5, 2026\"", "Live feed refresh date", "supported"),
    ("Map About note: last step is USDA's live list that day, not a Dec 31 count",
     "DATASETS.md, live feed: no authorization dates, one-day list", "supported"),
    ("Map About note: matched stores keep their historical format", "load_live.py; DATASETS.md", "supported"),
    ("Map About note: stores not in the historical file carry USDA's broader live types, \"size not given\", \"type not given\"",
     "Live feed's 8 types; DATASETS.md mapping", "supported"),
    ("Map About note: Restaurant Meals sites and farmers-market entries the historical file never carried are left out",
     "Counts above (8,565 and 3,709); DATASETS.md", "supported"),
    ("Map subtitle: \"Authorized retailers, 2006–2026\"", "Snapshots Dec 31, 2006 to Nov 5, 2026", "supported"),
]


def tie(item, built, recomputed, where):
    ok = built == recomputed
    ROWS.append((item, built, recomputed, "match" if ok else "MISMATCH", where))


def norm(s):
    return re.sub(r"[^A-Z0-9]+", " ", str(s).upper().strip()).strip() if isinstance(s, str) else ""


def main():
    meta = json.loads((ROOT / "web/data/meta.json").read_text())
    left = json.loads((ROOT / "reports/data/left_2026.json").read_text())
    snap = date.fromisoformat(meta["live"]["date"])

    h = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8-sig")
    h["rid"] = h["Record ID"].astype("int64")
    h["auth"] = pd.to_datetime(h["Authorization Date"].str.strip(), format="%m/%d/%Y", errors="coerce")
    h["end"] = pd.to_datetime(h["End Date"].str.strip().replace("", None), format="%m/%d/%Y", errors="coerce")
    h["addr"] = (h["Street Number"].fillna("") + " " + h["Street Name"].fillna("")).map(norm)
    # The historical file drops leading zeros from ZIPs; the live feed does not.
    h["zip5"] = h["Zip Code"].fillna("").str.strip().str[:5].str.zfill(5)

    with gzip.open(LIVE_DIR / f"snap-live-{snap}.csv.gz", "rt", encoding="utf-8") as fh:
        lv = pd.read_csv(fh, dtype=str)
    lv["rid"] = lv["Record_ID"].astype("int64")
    lv["addr"] = lv["Store_Street_Address"].map(norm)
    lv["zip5"] = lv["Zip_Code"].fillna("").str[:5]

    con = connect(read_only=True)
    ds = con.execute("SELECT record_id rid, mappable, format FROM dim_store").df().set_index("rid")
    con.close()

    def active(d):
        d = pd.Timestamp(d)
        m = (h["auth"] <= d) & (h["end"].isna() | (h["end"] >= d))
        return set(h.loc[m, "rid"])

    hist_ids = set(h["rid"])
    mappable = set(ds.index[ds["mappable"]])

    # --- map step: Nov 5, 2026 ------------------------------------------------
    rmp = lv["Store_Type"].eq("Restaurant Meals Program")
    mkt_new = lv["Store_Type"].eq("Farmers and Markets") & ~lv["rid"].isin(hist_ids)
    kept = lv[~rmp & ~mkt_new]
    on_map = kept[~kept["rid"].isin(hist_ids) | kept["rid"].isin(mappable)]
    # Live-only coordinates: every row has them and none fall outside the US
    # windows in this snapshot (checked in verify_map.py), so all are mappable.
    tie("Live feed rows", 248175, len(lv), "fetch_live.py output")
    tie("Restaurant Meals Program rows dropped", 8565, int(rmp.sum()), "DATASETS.md")
    tie("Live-only farmers-market rows dropped", 3709, int(mkt_new.sum()), "DATASETS.md")
    tie("Stores on the map, Nov 5, 2026", meta["per_year_totals"]["2026"], len(on_map), "map count line")
    tie("Live-only stores on the map", meta["live"]["only_in_live"],
        int((~on_map["rid"].isin(hist_ids)).sum()), "map About note")
    tie("Slider label", "Nov 5, 2026", meta["labels"][-1], "map year label")
    # Mappable historical stores on no Dec 31 2006-2025 and not in the feed.
    on_any = set()
    for y in range(2006, 2026):
        on_any |= active(f"{y}-12-31")
    never = mappable - on_any - set(on_map["rid"])
    last_end = h.groupby("rid")["end"].max()
    before = {r for r in never if pd.notna(last_end.get(r)) and last_end[r] < pd.Timestamp("2006-12-31")}
    tie("Stores that opened and closed between Dec 31sts", meta["excluded_shortlived_count"],
        len(never) - len(before), "map About note")
    tie("Stores that left before Dec 31, 2006", meta["excluded_before_first"], len(before), "meta only")
    # Live-only: the live type, except a dollar-chain name becomes Dollar Store.
    from brands import normalize, resolve
    lo_conv = on_map[~on_map["rid"].isin(hist_ids) & on_map["Store_Type"].eq("Convenience Store")]
    dollar = sum(resolve(normalize(n or ""), s, "Convenience Store")[1] == "dollar"
                 for n, s in zip(lo_conv["Store_Name"].fillna(""), lo_conv["State"]))
    conv_live = int(on_map["rid"].map(ds["format"]).eq("Convenience Store").sum()) + len(lo_conv) - dollar
    tie("Convenience stores on the map, Nov 5, 2026",
        meta["format_by_year"][meta["formats"].index("Convenience Store")][-1], conv_live, "format panel")

    # --- 2026 exits -----------------------------------------------------------
    base_ids = active("2025-12-31") & mappable
    base = h[h["rid"].isin(base_ids)].drop_duplicates("rid").set_index("rid")
    gone = base[~base.index.isin(set(lv["rid"]))].copy()
    newc = lv[~lv["rid"].isin(base_ids) & ~rmp]
    keys = set(zip(newc["addr"], newc["zip5"]))
    gone["replaced"] = [a != "" and (a, z) in keys for a, z in zip(gone["addr"], gone["zip5"])]
    gone["format"] = gone.index.map(ds["format"])
    conv = gone["format"].eq("Convenience Store")
    t = left["totals"]
    cv = next(r for r in left["by_format"] if r["format"] == "Convenience Store")
    tie("Stores authorized Dec 31, 2025 (mappable)", t["base"], len(base), "left_2026.json")
    tie("Exits, all formats", t["left"], len(gone), "left_2026.json")
    tie("Exits replaced at same address", t["replaced"], int(gone["replaced"].sum()), "static map note: 3,755")
    tie("Exits not replaced, all formats", t["left_not_replaced"], int((~gone["replaced"]).sum()),
        "static map note: nationally")
    tie("Convenience stores, Dec 31, 2025", cv["base"],
        int(base.index.map(ds["format"]).to_series().eq("Convenience Store").sum()), "left_2026.json")
    tie("Convenience exits", cv["left"], int(conv.sum()), "chat summary")
    tie("Convenience exits not replaced", cv["left_not_replaced"], int((conv & ~gone["replaced"]).sum()),
        "static map key: convenience")
    tie("Other exits not replaced", t["left_not_replaced"] - cv["left_not_replaced"],
        int((~conv & ~gone["replaced"]).sum()), "static map key: other")
    lo = gone[~gone["replaced"]]
    lon, lat = lo["Longitude"].astype(float), lo["Latitude"].astype(float)
    in48 = lon.between(-125.0, -66.5) & lat.between(24.0, 49.5)
    tie("Exits shown in lower 48", left["shown_lower48"], int(in48.sum()), "static map note: shown")
    tie("Convenience share not replaced, 2026 (%)", cv["pct_left_not_replaced"],
        round(100 * int((conv & ~gone["replaced"]).sum()) / cv["base"], 1), "chat summary")

    # --- earlier years, historical file on both ends --------------------------
    for row in left["baseline_years"]:
        a, b = row["from"], row["to"]
        A_ids = active(a) & mappable
        B_ids = active(b)
        A = h[h["rid"].isin(A_ids)].drop_duplicates("rid").set_index("rid")
        N = h[h["rid"].isin(B_ids - A_ids)]
        nk = set(zip(N["addr"], N["zip5"]))
        G = A[~A.index.isin(B_ids)]
        rep = pd.Series([x != "" and (x, z) in nk for x, z in zip(G["addr"], G["zip5"])], index=G.index)
        c = G.index.map(ds["format"]).to_series(index=G.index).eq("Convenience Store")
        tie(f"{row['year']} convenience exits not replaced", row["conv_left_not_replaced"],
            int((c & ~rep).sum()), "chat summary baseline")

    lines = ["# Tie-out", "",
             f"Recomputed by `src/tieout_live.py` from `data/raw/hist.csv` and "
             f"`data/raw/live/snap-live-{snap}.csv.gz`. `mappable` and `format` are read from "
             "`dim_store`.", "",
             "| Item | Built | Recomputed | Result | Where it appears |", "|---|---:|---:|---|---|"]
    fmt = lambda v: f"{v:,}" if isinstance(v, int) else str(v)
    lines += [f"| {i} | {fmt(b)} | {fmt(r)} | {s} | {w} |" for i, b, r, s, w in ROWS]
    lines += ["", "## Words", "",
              "| Text on the output | Source | Verdict |", "|---|---|---|"]
    lines += [f"| {t} | {s} | {v} |" for t, s, v in WORDS]
    (ROOT / "TIEOUT.md").write_text("\n".join(lines) + "\n")
    bad = [r for r in ROWS if r[3] != "match"]
    for r in ROWS:
        print(f"  [{r[3]:8}] {r[0]}: built {fmt(r[1])}, recomputed {fmt(r[2])}")
    print(f"\n{len(ROWS) - len(bad)} of {len(ROWS)} match. Wrote TIEOUT.md")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
