"""Push the November 11, 2026 update to the map page (/p/snap-retailer-map) as
a Migration Release draft.

The live page still describes the map as 2006-2025 and says 45,704 stores
(7.0%) never appear because they opened and closed between two December 31sts.
That figure also counted 31,135 stores that left SNAP before the first step;
the right count for the stated reason is 14,520 (2.2%). The map now ends on a
November 5, 2026 step drawn from USDA's live list.

This patches the live document in place, so Eric's Prismic edits stay:
  - title, subtitle, meta title and description, schema, iframe title
  - the method notes that the new step changes, and the 45,704 correction
  - a highlighted update note at the top

Every number comes from the published bundle (dist/snap-map.html) or
reports/visualization-page-meta.md.

    ~/.claude/tools/prismic/.venv/bin/python src/analysis/map_page_update_push.py LIVE_JSON [--publish]
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
DOC_ID = "aoOeoxIAACwAxLGU"
UID = "snap-retailer-map"
DATE = "2026-11-11"
MODIFIED = "2026-11-11T14:00:00-05:00"


def bundle_meta():
    s = (ROOT / "dist" / "snap-map.html").read_text()
    g = lambda k: re.search(r'"' + k + r'"\s*:\s*([\d.]+)', s).group(1)  # noqa: E731
    return {k: g(k) for k in ("count", "mappable", "excluded_shortlived_count",
                              "excluded_shortlived_pct", "excluded_before_first",
                              "only_in_live")}


def meta_block(md, heading):
    sec = md.split(heading, 1)[1]
    return re.search(r"```(?:json)?\n(.*?)\n```", sec, re.S).group(1)


def main():
    live, publish = Path(sys.argv[1]), "--publish" in sys.argv
    doc = json.loads(live.read_text())
    assert doc["id"] == DOC_ID and doc["uid"] == UID
    d = copy.deepcopy(doc["data"])
    m = bundle_meta()
    md = (ROOT / "reports" / "visualization-page-meta.md").read_text()

    n_live = int(m["only_in_live"])
    n_hist_shown = int(m["count"]) - n_live
    never, pct = int(m["excluded_shortlived_count"]), m["excluded_shortlived_pct"]
    before = int(m["excluded_before_first"])
    total = 661456 + n_live
    assert total == int(re.search(r"all ([\d,]+) retailers", md).group(1).replace(",", ""))
    assert int(m["mappable"]) - never - before == n_hist_shown

    changes = []

    def setf(path, old, new):
        changes.append((path, old, new))
        return new

    d["page_title"] = setf("page_title", d["page_title"],
                           d["page_title"].replace("2006–2025", "2006–2026"))
    d["page_subtitle"] = setf("page_subtitle", d["page_subtitle"],
                              d["page_subtitle"].replace("661,456", f"{total:,}"))
    d["meta_title"] = setf("meta_title", d["meta_title"], meta_block(md, "## 4. Meta title"))
    d["meta_description"] = setf("meta_description", d["meta_description"],
                                 meta_block(md, "## 5. Meta description"))
    schema = meta_block(md, "## 7. Schema")
    hero = d["featured_image"]["url"].split("?")[0]
    schema = (schema.replace("[[PRISMIC HERO URL]]", hero)
              .replace('"datePublished": "[[YYYY-MM-DDTHH:MM:SS-04:00]]"',
                       '"datePublished": "2026-08-17T20:00:00-04:00"')
              .replace('"dateModified": "[[YYYY-MM-DDTHH:MM:SS-04:00]]"',
                       f'"dateModified": "{MODIFIED}"')
              .replace("https://www.data4thepeople.com/p/[[slug]]/",
                       "https://www.data4thepeople.com/p/snap-retailer-map"))
    assert "[[" not in schema
    json.loads(schema)
    d["schema"] = setf("schema", d["schema"], schema)
    d["updated_date"] = DATE

    sl = d["slices"]
    # iframe title
    pre = sl[0]["primary"]["html_content"][0]
    pre["text"] = setf("iframe", pre["text"], pre["text"].replace("2006–2025", "2006–2026"))

    def item(text, spans=()):
        return {"type": "list-item", "text": text, "spans": list(spans), "direction": "ltr"}

    def bold(text, phrase):
        i = text.index(phrase)
        return {"start": i, "end": i + len(phrase), "type": "strong"}

    # Where the data comes from: add the live list.
    src = sl[6]["primary"]["content"]
    t = ("USDA's live list of SNAP stores, saved November 5, 2026. It is the list behind "
         "USDA's online store locator. It shows every store authorized that day, with no dates.")
    src.insert(1, setf("source[+1]", "", item(t, [bold(t, "USDA's live list of SNAP stores")])))

    # What one dot means: the last step, and the never-shown count.
    dot = sl[8]["primary"]["content"]
    t = ("The last step is different. It shows the stores on USDA's live list on November 5, "
         "2026, not a December 31.")
    dot.insert(2, setf("dot[+2]", "", item(t, [bold(t, "The last step is different.")])))
    old = dot[-1]["text"]
    assert "45,704 stores (7.0%)" in old
    new = old.replace("45,704", f"{never:,}").replace("(7.0%)", f"({pct}%)")
    assert len(new) == len(old)
    dot[-1]["text"] = setf("dot[-1]", old, new)

    # How the file was cleaned: stores shown, and the live-only stores.
    cl = sl[10]["primary"]["content"]
    old = cl[2]["text"]
    new = old.replace("611,164", f"{n_hist_shown:,}")
    assert len(new) == len(old) and new != old
    cl[2]["text"] = setf("clean[2]", old, new)
    t = (f"The November 5, 2026 step adds {n_live:,} stores that are on the live list but not "
         "in the historical file. They are new to SNAP since the end of 2025 or missing from that file for other reasons. It leaves out "
         "Restaurant Meals Program sites and farmers' market entries the historical file has "
         "never carried.")
    cl.append(setf("clean[+]", "", item(t, [bold(t, f"{n_live:,} stores")])))

    # Update note at the top.
    note = (f"The map now ends on a new step: USDA's live list of SNAP stores on November 5, "
            f"2026. We also corrected the number of stores that never appear on the map because "
            f"they opened and closed between two December 31sts. It is {never:,} ({pct}%), not "
            f"45,704 (7.0%). The larger figure also counted {before:,} stores that left SNAP "
            f"before the map's first step, December 31, 2006.")
    blurb = {"slice_type": "highlited_page_blurb", "slice_label": None,
             "variation": "default", "version": "initial", "items": [],
             "primary": {"title": "Updated, November 11, 2026",
                         "content": [{"type": "paragraph", "text": note,
                                      "spans": [], "direction": "ltr"}]}}
    gap = {"slice_type": "spacer", "slice_label": None, "variation": "default",
           "version": "initial", "items": [], "primary": {"spacer_value": "20px"}}

    def clean_image(im):
        return {k: im[k] for k in ("id", "alt", "copyright", "dimensions") if k in im}

    for s in sl:
        s.pop("id", None)
        s.setdefault("slice_label", None)
    for f in ("featured_image", "meta_image"):
        d[f] = clean_image(d[f])
    a = d.get("author_details") or {}
    if a.get("id"):
        d["author_details"] = {"link_type": "Document", "id": a["id"]}
    d = {k: v for k, v in d.items() if v is not None}
    d["slices"] = [blurb, gap] + sl

    for p, o, n in changes:
        if isinstance(n, dict):
            print(f"  + {p}: {n['text']}")
        elif p == "schema":
            print(f"  ~ schema replaced ({len(n)} chars)")
        else:
            print(f"  ~ {p}:\n      {str(o)[:300]!r}\n   -> {str(n)[:300]!r}")
    print(f"\nnote: {note}\n{len(d['slices'])} slices (was {len(doc['data']['slices'])})")
    body = {"uid": UID, "title": d["page_title"], "data": d}
    out = ROOT / "reports" / "map-page-update.json"
    out.write_text(json.dumps(body, indent=1, ensure_ascii=False))
    print(f"wrote {out}")
    if not publish:
        print("dry run: nothing sent")
        return
    tp.load_dotenv()
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
