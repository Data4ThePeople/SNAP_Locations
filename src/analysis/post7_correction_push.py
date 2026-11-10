"""Push the November 10, 2026 correction to post 7 (/p/stocking-rule) as a
Migration Release draft.

Post 7 predates the posts/<slug>/POST.md process, and its live page carries
two edits Eric made in Prismic. Rebuilding it from markdown would drop those
and change the slice layout, so this patches the live document instead:

  - every corrected number, swapped in place (same character length, so the
    rich-text spans stay valid)
  - the three chart images and the hero, re-uploaded from the rebuilt files
  - a highlighted correction blurb at the top
  - updated_date and the schema's dateModified set to the correction date

Input: the live document as served on the page (saved by fetching
https://www.data4thepeople.com/p/stocking-rule and decoding its Nuxt payload).

Run with the Prismic tool's own Python, from the repo root:
    ~/.claude/tools/prismic/.venv/bin/python src/analysis/post7_correction_push.py LIVE_JSON [--publish]
Without --publish it prints every change and uploads nothing.
"""
import copy
import json
import sys
import time
from pathlib import Path

TOOL = Path.home() / ".claude" / "tools" / "prismic"
sys.path.insert(0, str(TOOL))
import to_prismic as tp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DOC_ID = "apDQ3RMAACcAL8Yk"
UID = "stocking-rule"
DATE = "2026-11-10"
NEW = json.loads((ROOT / "reports" / "data" / "post7.json").read_text())["worst_case"]
CONV = NEW["stages"]["conv"]

# Published August 28 -> corrected. Each pair is the same length.
SWAPS = [
    ("5.3 million", f"{CONV['population']/1e6:.1f} million"),
    ("5.2 million", None),                      # lower-48 population, filled below
    ("109,791", f"{NEW['stores_by_group']['conv']:,}"),
    ("232,165", f"{NEW['stores_total']:,}"),
    ("2,871", f"{CONV['zips_to_zero']:,}"),
    ("2,782", None),                            # lower-48 ZIP count, filled below
    ("19,074", None),                           # lower-48 ZIPs kept, filled below
    ("1,051", f"{NEW['median']['zeroed']['median_pop']:,}"),
    ("8,343", f"{NEW['median']['kept']['median_pop']:,}"),
]


def lower48():
    """The map's own counts, read from the rebuilt markdown's map alt text."""
    import re
    md = (ROOT / "reports" / "post7" / "post7.md").read_text()
    kept = re.search(r"Faint grey marks the ([\d,]+) ZIP codes", md).group(1)
    gone = re.search(r"There are ([\d,]+) pink dots", md).group(1)
    pop = re.search(r"home to ([\d.]+ million) Americans", md).group(1)
    return kept, gone, pop


def correction_text():
    return (f"An earlier version of this post left out "
            f"{NEW['stores_total'] - 232165:,} SNAP stores in New England, New Jersey and the "
            f"U.S. Virgin Islands. USDA's file lists some ZIP codes without their leading zero, "
            f"and our count dropped those stores. We fixed the error. The post now counts "
            f"{NEW['stores_total']:,} SNAP-authorized stores, not 232,165, and "
            f"{NEW['stores_by_group']['conv']:,} convenience stores, not 109,791. The number of "
            f"ZIP codes that would have no SNAP retailer if convenience stores left rose from "
            f"2,871 to {CONV['zips_to_zero']:,}, and the people living in them from 5.3 million "
            f"to {CONV['population']/1e6:.1f} million. The charts and map are updated. The "
            f"smallest ZIP codes would still be hit hardest.")


def bands_alt():
    parts = []
    for i, b in enumerate(NEW["bands"]):
        lab = "Under 1,000 people" if i == 0 else b["band"]
        parts.append(f"{lab}: {b['pct']}%" + (", or " if i == 0 else ", ")
                     + f"{b['zeroed']:,} of {b['zips']:,}.")
    return ("Horizontal bar chart of the share of ZIP codes that would be left with no "
            "SNAP-authorized retailer if every convenience store gave up its authorization, "
            "by 2020 census population. " + " ".join(parts)
            + " Title: It lands almost entirely on the smallest places.")


def main():
    live, publish = Path(sys.argv[1]), "--publish" in sys.argv
    doc = json.loads(live.read_text())
    assert doc["id"] == DOC_ID and doc["uid"] == UID
    data = copy.deepcopy(doc["data"])

    kept, gone, pop48 = lower48()
    fill = {"5.2 million": pop48, "2,782": gone, "19,074": kept}
    swaps = [(o, n if n else fill[o]) for o, n in SWAPS]
    for o, n in swaps:
        assert len(o) == len(n), (o, n)
    changes = []

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("url", "id", "edit"):
                    continue
                x[k] = walk(v, f"{path}.{k}")
            return x
        if isinstance(x, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(x)]
        if isinstance(x, str):
            y = x
            for o, n in swaps:
                y = y.replace(o, n)
            if y != x:
                changes.append((path, x, y))
            return y
        return x

    data = walk(data, "")

    # Alt text that describes the picture, not just its numbers.
    sl = data["slices"]
    sl[14]["primary"]["image"]["alt"] = bands_alt()
    sl[12]["primary"]["image"]["alt"] = sl[12]["primary"]["image"]["alt"].replace(
        "the Plains and the rural East", "the Plains, the rural East and New England").replace(
        " scattered thickly across", " scattered across")
    for f in ("featured_image", "meta_image"):
        data[f]["alt"] = data[f]["alt"].replace(
            "the northern Plains and the rural East", "the northern Plains, the rural East and New England"
        ).replace(" on a dark ground", "")
    for a in [sl[14]["primary"]["image"]["alt"], sl[12]["primary"]["image"]["alt"], data["featured_image"]["alt"]]:
        assert len(a) < 500, (len(a), a)

    data["updated_date"] = DATE
    data["schema"] = data["schema"].replace(
        '"dateModified": "2026-08-28T08:00:00-04:00"', '"dateModified": "2026-11-10T13:00:00-05:00"')

    # Images: re-upload the rebuilt files; strip Content API-only keys from all.
    imgs = {1: "reports/post7/images/00-key-figures.png",
            12: "reports/post7/images/01-worst-case-map.png",
            14: "reports/post7/images/02-worst-case-bands.png"}
    hero = "reports/assets/heroes/day-7.png"
    blocks = [{"type": "image", "_src": src, "alt": sl[i]["primary"]["image"]["alt"]}
              for i, src in imgs.items()]
    blocks.append({"type": "image", "_src": hero, "alt": data["featured_image"]["alt"]})
    tp.load_dotenv()
    cache = ROOT / "reports" / "post7" / ".prismic-assets.json"
    tp.upload_assets(blocks, ROOT, cache, dry_run=not publish)
    for (i, _), b in zip(imgs.items(), blocks):
        sl[i]["primary"]["image"] = {"id": b["id"], "alt": b["alt"], "copyright": None,
                                     "dimensions": b["dimensions"]}
    hb = blocks[-1]
    for f in ("featured_image", "meta_image"):
        data[f] = {"id": hb["id"], "alt": hb["alt"], "copyright": None,
                   "dimensions": hb["dimensions"]}

    def clean_image(im):
        return {k: im[k] for k in ("id", "alt", "copyright", "dimensions") if k in im}

    for s in sl:
        s.pop("id", None)
        s.setdefault("slice_label", None)
        if "image" in s["primary"] and isinstance(s["primary"]["image"], dict):
            s["primary"]["image"] = clean_image(s["primary"]["image"])
    a = data.get("author_details") or {}
    if a.get("id"):
        data["author_details"] = {"link_type": "Document", "id": a["id"]}
    data = {k: v for k, v in data.items() if v is not None}

    # The correction, highlighted, at the very top.
    blurb = {"slice_type": "highlited_page_blurb", "slice_label": None,
             "variation": "default", "version": "initial", "items": [],
             "primary": {"title": "Correction, November 10, 2026",
                         "content": [{"type": "paragraph", "text": correction_text(),
                                      "spans": [], "direction": "ltr"}]}}
    gap = {"slice_type": "spacer", "slice_label": None, "variation": "default",
           "version": "initial", "items": [], "primary": {"spacer_value": "20px"}}
    data["slices"] = [blurb, gap] + sl

    print(f"{len(changes)} text fields changed:")
    for p, o, n in changes:
        import difflib
        sm = difflib.SequenceMatcher(None, o, n)
        diffs = [f"{o[i1:i2]!r}->{n[j1:j2]!r}" for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
        print(f"  {p}: {', '.join(diffs)}")
    print("\ncorrection blurb:\n  " + correction_text())
    print(f"\n{len(data['slices'])} slices (was {len(doc['data']['slices'])})")
    out = ROOT / "reports" / "post7" / "prismic-correction.json"
    body = {"uid": UID, "title": data["page_title"], "data": data}
    out.write_text(json.dumps(body, indent=1))
    print(f"wrote {out}")

    if not publish:
        print("dry run: nothing uploaded or sent")
        return
    import requests
    r = requests.put(f"{tp.MIGRATION_API}/{DOC_ID}",
                     headers={**tp.headers(), "Content-Type": "application/json"},
                     json=body, timeout=120)
    time.sleep(tp.RATE_LIMIT_SECONDS)
    if r.status_code >= 300:
        sys.exit(f"update failed ({r.status_code}): {r.text[:600]}")
    print(f"updated draft {DOC_ID} in the Migration Release")


if __name__ == "__main__":
    main()
