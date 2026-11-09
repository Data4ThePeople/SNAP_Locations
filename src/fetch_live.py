"""Snapshot USDA's live SNAP retailer locator feed.

The historical file stops at Dec 31, 2025. The live feed behind USDA's retailer
locator lists every store authorized on the day it was last refreshed, and USDA
overwrites it in place with no archive. So each pull is saved, gzipped and
tracked in git, under the feed's own refresh date rather than the download date:
a later pull of an unchanged feed lands on the same file and is skipped.

The pull is rejected, and nothing is written, if:
  - the feed's refresh time changes while paging (a half-old, half-new list),
  - the rows received differ from the feed's own count,
  - any Record_ID appears twice.

    python src/fetch_live.py
"""
import csv
import gzip
import io
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from config import RAW

LAYER = ("https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/"
         "snap_retailer_location_data/FeatureServer/0")
LIVE_DIR = RAW / "live"
FIELDS = ["Record_ID", "Store_Name", "Store_Type", "Store_Street_Address",
          "Additonal_Address", "City", "State", "Zip_Code", "County",
          "Latitude", "Longitude"]
PAGE = 2000


def _get(url, params):
    q = urllib.parse.urlencode({**params, "f": "json"})
    req = urllib.request.Request(f"{url}?{q}", headers={"User-Agent": "Data4ThePeople SNAP research"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    if "error" in d:
        raise SystemExit(f"ABORT: feed returned an error: {d['error']}")
    return d


def refreshed_at():
    ms = _get(LAYER, {})["editingInfo"]["dataLastEditDate"]
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def snapshot_path(ts):
    return LIVE_DIR / f"snap-live-{ts:%Y-%m-%d}.csv.gz"


def fetch() -> None:
    ts = refreshed_at()
    out = snapshot_path(ts)
    if out.exists():
        print(f"Feed refreshed {ts:%Y-%m-%d %H:%M} UTC; already saved as {out.name}. Skipping.")
        return

    expected = _get(f"{LAYER}/query", {"where": "1=1", "returnCountOnly": "true"})["count"]
    print(f"Feed refreshed {ts:%Y-%m-%d %H:%M} UTC, {expected:,} rows. Paging...")
    rows, offset = [], 0
    while True:
        d = _get(f"{LAYER}/query", {
            "where": "1=1", "outFields": ",".join(FIELDS), "returnGeometry": "false",
            "orderByFields": "ObjectId", "resultOffset": offset, "resultRecordCount": PAGE,
        })
        feats = d.get("features", [])
        rows += [f["attributes"] for f in feats]
        offset += len(feats)
        if not feats or not d.get("exceededTransferLimit"):
            break

    if refreshed_at() != ts:
        raise SystemExit("ABORT: the feed was refreshed while paging. Nothing written; run again.")
    if len(rows) != expected:
        raise SystemExit(f"ABORT: received {len(rows):,} rows, feed reports {expected:,}. Nothing written.")
    ids = [r["Record_ID"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"ABORT: {len(ids) - len(set(ids)):,} duplicate Record_IDs. Nothing written.")

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: r["Record_ID"]))
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    # mtime=0 so the same rows always gzip to the same bytes.
    with open(out, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue().encode("utf-8"))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(rows):,} rows)")


if __name__ == "__main__":
    fetch()
    sys.exit(0)
