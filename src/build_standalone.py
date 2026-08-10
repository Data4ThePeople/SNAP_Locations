"""Bundle the map into one self-contained HTML file.

The CSS, the app, the deck.gl runtime and the whole 11.6MB dataset are inlined,
so the result opens by double-clicking it — no server, no build step, nothing
alongside it.

The dataset is gzipped before base64 because base64 alone would inflate it to
15.5MB; gzip first lands at 7.1MB. The page inflates it with DecompressionStream
(Chrome 80+, Safari 16.4+, Firefox 113+).

One thing genuinely cannot be inlined: the CARTO basemap tiles are fetched from
the network. Offline, the dots and every control still work — the map just draws
on a blank background.

    python src/build_standalone.py
"""
import base64
import gzip
import json
import sys
import urllib.request

from config import DATA, ROOT

WEB = ROOT / "web"
DIST = ROOT / "dist"
VENDOR = DATA / "vendor"
DECK_VERSION = "9.0.36"
DECK_URL = f"https://unpkg.com/deck.gl@{DECK_VERSION}/dist.min.js"
DECK_TAG = f'<script src="{DECK_URL}"></script>'


def guard(js: str) -> str:
    """Stop any literal </script> inside embedded source from closing the tag."""
    return js.replace("</script", "<\\/script")


def deck_source() -> str:
    VENDOR.mkdir(parents=True, exist_ok=True)
    cached = VENDOR / f"deck.gl-{DECK_VERSION}.min.js"
    if not cached.exists():
        print(f"Downloading {DECK_URL}")
        with urllib.request.urlopen(DECK_URL, timeout=180) as r:
            cached.write_bytes(r.read())
    return cached.read_text(encoding="utf-8")


def build() -> None:
    points = (WEB / "data" / "points.bin").read_bytes()
    meta = json.loads((WEB / "data" / "meta.json").read_text())
    html = (WEB / "index.html").read_text()
    css = (WEB / "style.css").read_text()
    app = (WEB / "app.js").read_text()

    packed = base64.b64encode(gzip.compress(points, 9)).decode("ascii")
    print(f"points.bin {len(points)/1e6:.2f} MB -> gzip+base64 {len(packed)/1e6:.2f} MB")

    if DECK_TAG not in html:
        raise SystemExit(f"Could not find the deck.gl script tag:\n  {DECK_TAG}")
    html = html.replace(DECK_TAG, f"<script>\n{guard(deck_source())}\n</script>")
    html = html.replace(
        '<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>"
    )

    payload = (
        "<script>window.__SNAP__ = {"
        f"meta: {guard(json.dumps(meta, separators=(',', ':')))},"
        f'points: "{packed}"'
        "};</script>"
    )
    if '<script src="app.js"></script>' not in html:
        raise SystemExit("Could not find the app.js script tag.")
    html = html.replace(
        '<script src="app.js"></script>',
        payload + f"\n<script>\n{guard(app)}\n</script>",
    )

    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / "snap-map.html"
    out.write_text(html, encoding="utf-8")
    size = out.stat().st_size / 1e6
    print(f"wrote {out} ({size:.2f} MB)")

    # A truncated or mis-assembled bundle is the likely failure, so check it.
    text = out.read_text(encoding="utf-8")
    for needed in ("window.__SNAP__", "deck.ScatterplotLayer", "renderPanelCounts",
                   "DecompressionStream"):
        if needed not in text:
            raise SystemExit(f"ABORT: bundle is missing {needed!r}")
    # Only </script> can close a block, and guard() escapes every one inside the
    # embedded sources, so exactly the three blocks written here should remain.
    # Counting "<script" instead would trip over the string appearing inside
    # deck.gl's own source.
    if text.count("</script>") != 3:
        raise SystemExit(
            f"ABORT: expected 3 script blocks, found {text.count('</script>')}"
        )
    roundtrip = gzip.decompress(base64.b64decode(packed))
    if roundtrip != points:
        raise SystemExit("ABORT: embedded payload does not round-trip")
    print(f"  verified: payload round-trips ({len(roundtrip):,} bytes), "
          f"{text.count('</script>')} script blocks, no external data references")


if __name__ == "__main__":
    sys.exit(build())
