"""Push the November 10, 2026 ZIP-code corrections to posts 1, 4 and 5 as
Migration Release drafts.

The three posts kept only 5-digit ZIP codes. USDA's file stores ZIPs as
numbers, so ZIPs that start with a zero (New England, New Jersey, the Virgin
Islands) came through as 3 or 4 digits and were dropped. `panel.py` now pads
them, and the posts' scripts were rerun.

These posts predate posts/<slug>/POST.md and carry Eric's hand-written alt
text and meta, so, like post7_correction_push.py, this patches each live
document in place:

  - every corrected number swapped in one pass (so a new value is never
    swapped again), with rich-text spans shifted when the length changes
  - only the charts whose data changed are re-uploaded
  - a highlighted correction blurb at the top
  - updated_date and the schema's dateModified set to the correction date

Input: a folder holding each live document, decoded from the page payload
as <slug>.json.

Run with the Prismic tool's own Python, from the repo root:
    ~/.claude/tools/prismic/.venv/bin/python src/analysis/zip_correction_push.py LIVE_DIR [--publish]
"""
import copy
import json
import re
import sys
import time
from pathlib import Path

TOOL = Path.home() / ".claude" / "tools" / "prismic"
sys.path.insert(0, str(TOOL))
import to_prismic as tp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-11-10"
TITLE = "Correction, November 10, 2026"
CAUSE = ("USDA's file lists some ZIP codes without their leading zero, so our ZIP code "
         "counts left out places in New England, New Jersey and the U.S. Virgin Islands. "
         "We fixed the error.")

d1 = json.loads((ROOT / "reports/data/post1.json").read_text())
d4 = json.loads((ROOT / "reports/data/post4.json").read_text())
d5 = json.loads((ROOT / "reports/data/post5.json").read_text())
sp1, z4, sp5 = d1["dollar_only_split"], d4["zips"], d5["spread"]
gt5, mix5, ac5 = d5["grocer_test"], d5["mix"], d5["arc_change"]


def c(n):
    return f"{n:,}"


POSTS = {
    "dollar-store-domination": {
        "doc": "aobmvhIAACwAykmX", "n": 1,
        # (old, new); a bare number matches only as a whole number
        "swaps": [("675", c(sp1["start"])), ("4,024", c(sp1["end"])),
                  ("203", c(sp1["exited"])), ("3,552", c(sp1["joined"])),
                  ("2,115", c(sp1["new_never"])), ("1,437", c(sp1["new_lost"]))],
        "images": {14: "03-dollar-only-zips.png", 16: "04-dollar-only-split.png"},
        "hero": None,
        "blurb": (f"{CAUSE} ZIP codes with a dollar store and no grocery store now number "
                  f"{c(sp1['start'])} in 2008, not 675, and {c(sp1['end'])} in 2024, not "
                  f"4,024. The other figures for those ZIP codes and two charts are updated. "
                  f"The count still rose in every period shown."),
    },
    "chain-pharmacies": {
        "doc": "ao3ZzRIAACcA-L6j", "n": 4,
        "swaps": [("976", c(z4["lost"])), ("45", c(z4["gained"])),
                  ("16.7%", f"{z4['rate_nonmetro']}%"), ("10.8%", f"{z4['rate_metro']}%")],
        "images": {1: "00-key-figures.png"},
        "hero": None,
        "blurb": (f"{CAUSE} The number of ZIP codes that lost their last SNAP-authorized chain "
                  f"pharmacy since 2021 is now {c(z4['lost'])}, not 976. In nonmetro ZIP codes "
                  f"the share is now {z4['rate_nonmetro']}%, and in metro ones "
                  f"{z4['rate_metro']}%, not 16.7% and 10.8%. Nonmetro places were still more "
                  f"likely to lose their last chain pharmacy."),
    },
    "diverging-two-americas": {
        "doc": "apApTxMAACcALqHP", "n": 5,
        "swaps": [("2,267", c(gt5["lost_last_grocery"]["total"])),
                  ("1,955", c(sp5["lost_grocer"]["median"])),
                  ("15,716", c(sp5["kept_grocer"]["median"])),
                  ("976", c(d5["groups"]["lost"])),
                  ("972", c(d5["density"]["lost"]["zips_matched"])),
                  ("494", c(mix5["2006"]["dollar"])), ("2,054", c(mix5["2025"]["dollar"])),
                  ("+316%", f"+{round(100 * (mix5['2025']['dollar'] / mix5['2006']['dollar'] - 1))}%"),
                  ("5,447", c(mix5["2006"]["convenience"])), ("8,413", c(mix5["2025"]["convenience"])),
                  ("54.5%", f"{ac5['conv_pct']}%"),
                  ("5,301", c(mix5["2006"]["grocery"])), ("4,425", c(mix5["2025"]["grocery"])),
                  ("16.5%", f"{-ac5['groc_pct']}%"), ("1,192", c(ac5["drug_peak"])),
                  ("12,118", c(mix5["2006"]["total"])), ("14,892", c(mix5["2025"]["total"])),
                  ("40%", f"{round(gt5['lost_last_grocery']['never_pct'])}%"),
                  ("919", c(gt5["lost_last_grocery"]["never_dollar"])),
                  ("2.5%", f"{gt5['with_dollar']['pct']}%"),
                  ("5.3%", f"{-gt5['without_dollar']['pct']}%"),
                  ("16,082", c(sp5["lost_pharmacy"]["median"])),
                  ("28,703", c(sp5["kept_pharmacy"]["median"])),
                  ("956", c(sp5["lost_grocer"]["p25"])), ("3,740", c(sp5["lost_grocer"]["p75"])),
                  ("5,717", c(sp5["kept_grocer"]["p25"])), ("30,308", c(sp5["kept_grocer"]["p75"])),
                  ("814", c(sp5["lost_pharmacy"]["n"])), ("5,247", c(sp5["kept_pharmacy"]["n"])),
                  ("8,559", c(sp5["lost_pharmacy"]["p25"])), ("27,178", c(sp5["lost_pharmacy"]["p75"])),
                  ("18,560", c(sp5["kept_pharmacy"]["p25"])), ("41,147", c(sp5["kept_pharmacy"]["p75"])),
                  ("2,232", c(sp5["lost_grocer"]["n"])), ("13,223", c(sp5["kept_grocer"]["n"])),
                  ("2,546", None)],  # hero alt: 2006 grocery stores in those ZIPs; pass --hero6, read off the rebuilt day-6.png
        "images": {1: "00-key-figures.png", 8: "01-twenty-year-arc.png",
                   12: "02-mix-2006-2025.png", 18: "03-pharmacy-size.png",
                   20: "04-grocery-size.png"},
        "hero": "day-6.png",
        "blurb": (f"{CAUSE} The number of ZIP codes that lost their last grocery store is now "
                  f"{c(gt5['lost_last_grocery']['total'])}, not 2,267, and the number that lost "
                  f"their last chain pharmacy is {c(d5['groups']['lost'])}, not 976. The other "
                  f"figures for those ZIP codes, the charts and the map are updated. The "
                  f"pattern is the same: smaller places were more likely to lose their grocery "
                  f"store and their chain pharmacy."),
    },
}


def swap_text(text, spans, table):
    """Replace every whole-number match in one pass; shift spans to fit."""
    pat = re.compile(r"(?<![\d,.])(" + "|".join(re.escape(o) for o in
                     sorted(table, key=len, reverse=True)) + r")(?![\d]|[.,]\d)")
    out, delta, pos, edits = [], 0, 0, []
    for m in pat.finditer(text):
        new = table[m.group(1)]
        out.append(text[pos:m.start()])
        out.append(new)
        edits.append((m.start(), m.end(), len(new) - (m.end() - m.start())))
        pos = m.end()
    out.append(text[pos:])
    if not edits:
        return text, spans
    if spans:
        for s in spans:
            for k in ("start", "end"):
                shift = 0
                for a, b, dl in edits:
                    if s[k] >= b or (k == "end" and s[k] > a):
                        shift += dl
                s[k] += shift
    return "".join(out), spans


def patch(slug, cfg, live_dir, publish):
    doc = json.loads((live_dir / f"{slug}.json").read_text())
    assert doc["id"] == cfg["doc"], (doc["id"], cfg["doc"])
    data = copy.deepcopy(doc["data"])
    table = dict(cfg["swaps"])
    for o, n in table.items():
        assert n is not None, o
    changes = []

    def walk(x, path):
        if isinstance(x, dict):
            if isinstance(x.get("text"), str) and "spans" in x:
                new, _ = swap_text(x["text"], x["spans"], table)
                if new != x["text"]:
                    changes.append((path, x["text"], new))
                    x["text"] = new
                return x
            for k, v in list(x.items()):
                if k in ("url", "id", "edit", "link_type"):
                    continue
                if isinstance(v, str):
                    new, _ = swap_text(v, None, table)
                    if new != v:
                        changes.append((f"{path}.{k}", v, new))
                        x[k] = new
                else:
                    walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        return x

    walk(data, "")
    data["updated_date"] = DATE
    data["schema"] = re.sub(r'"dateModified": "[^"]+"',
                            '"dateModified": "2026-11-10T14:00:00-05:00"', data["schema"])

    sl = data["slices"]
    for i in cfg["images"]:
        assert len(sl[i]["primary"]["image"]["alt"]) < 500
    blocks = [{"type": "image", "_src": f"reports/post{cfg['n']}/images/{fn}",
               "alt": sl[i]["primary"]["image"]["alt"]} for i, fn in cfg["images"].items()]
    if cfg["hero"]:
        blocks.append({"type": "image", "_src": f"reports/assets/heroes/{cfg['hero']}",
                       "alt": data["featured_image"]["alt"]})
    cache = ROOT / "reports" / f"post{cfg['n']}" / ".prismic-assets.json"
    tp.upload_assets(blocks, ROOT, cache, dry_run=not publish)

    def img(b):
        return {"id": b["id"], "alt": b["alt"], "copyright": None, "dimensions": b["dimensions"]}

    for (i, _), b in zip(cfg["images"].items(), blocks):
        sl[i]["primary"]["image"] = img(b)
    if cfg["hero"]:
        data["featured_image"] = img(blocks[-1])
        data["meta_image"] = img(blocks[-1])

    def clean_image(im):
        return {k: im[k] for k in ("id", "alt", "copyright", "dimensions") if k in im}

    for f in ("featured_image", "meta_image"):
        if isinstance(data.get(f), dict) and data[f].get("id"):
            data[f] = clean_image(data[f])
    for s in sl:
        s.pop("id", None)
        s.setdefault("slice_label", None)
        if isinstance(s["primary"].get("image"), dict):
            s["primary"]["image"] = clean_image(s["primary"]["image"])
    a = data.get("author_details") or {}
    if a.get("id"):
        data["author_details"] = {"link_type": "Document", "id": a["id"]}
    data = {k: v for k, v in data.items() if v is not None}

    blurb = {"slice_type": "highlited_page_blurb", "slice_label": None,
             "variation": "default", "version": "initial", "items": [],
             "primary": {"title": TITLE,
                         "content": [{"type": "paragraph", "text": cfg["blurb"],
                                      "spans": [], "direction": "ltr"}]}}
    gap = {"slice_type": "spacer", "slice_label": None, "variation": "default",
           "version": "initial", "items": [], "primary": {"spacer_value": "20px"}}
    data["slices"] = [blurb, gap] + sl

    print(f"\n=== {slug} ({cfg['doc']}): {len(changes)} fields changed")
    import difflib
    for p, o, n in changes:
        sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
        diffs = [f"{o[max(0, i1 - 12):i2]!r}->{n[max(0, j1 - 12):j2]!r}"
                 for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
        print(f"  {p}: " + "; ".join(diffs))
    print(f"  blurb: {cfg['blurb']}")
    print(f"  {len(data['slices'])} slices (was {len(doc['data']['slices'])})")
    body = {"uid": slug, "title": data["page_title"], "data": data}
    (ROOT / "reports" / f"post{cfg['n']}" / "prismic-correction.json").write_text(
        json.dumps(body, indent=1))
    if not publish:
        return
    import requests
    r = requests.put(f"{tp.MIGRATION_API}/{cfg['doc']}",
                     headers={**tp.headers(), "Content-Type": "application/json"},
                     json=body, timeout=120)
    time.sleep(tp.RATE_LIMIT_SECONDS)
    if r.status_code >= 300:
        sys.exit(f"{slug}: update failed ({r.status_code}): {r.text[:600]}")
    print(f"  updated draft {cfg['doc']} in the Migration Release")


def main():
    live_dir, publish = Path(sys.argv[1]), "--publish" in sys.argv
    swaps = dict(POSTS["diverging-two-americas"]["swaps"])
    if swaps["2,546"] is None:
        swaps["2,546"] = sys.argv[sys.argv.index("--hero6") + 1]
        POSTS["diverging-two-americas"]["swaps"] = list(swaps.items())
    tp.load_dotenv()
    for slug, cfg in POSTS.items():
        patch(slug, cfg, live_dir, publish)
    if not publish:
        print("\ndry run: nothing uploaded or sent")


if __name__ == "__main__":
    main()
