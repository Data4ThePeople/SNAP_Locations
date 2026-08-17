# SNAP Retailer Map

Interactive map of SNAP-authorized retailers, 2006–2025.

```bash
python src/export_map.py          # builds web/data/points.bin + meta.json
python src/verify_map.py          # decodes the binary and checks it against the DB
python web/serve.py               # then open http://127.0.0.1:8765

python src/build_standalone.py    # -> dist/snap-map.html, one shareable file
```

## Single-file build

`build_standalone.py` inlines the CSS, the app, the deck.gl runtime and the
whole dataset into **dist/snap-map.html (8.4 MB)**. Double-click it — no server,
nothing alongside it. The data is gzipped before base64 (7.1 MB rather than the
15.5 MB base64 alone would cost) and inflated in-page with `DecompressionStream`,
which needs Chrome 80+, Safari 16.4+ or Firefox 113+.

The one thing that cannot be inlined is the **basemap**: CARTO tiles come from
the network. Offline, every dot and control still works — the map just draws on
a blank background.

`serve.py` is a plain file server that sends `no-store`; use it rather than
`python -m http.server`, which lets the browser cache app.js so edits appear
not to take effect. There is no build step and no backend. `index.html`
loads a single pinned dependency (deck.gl UMD) from unpkg; the basemap is CARTO
raster tiles, which need no API key.

## How it works

The whole dataset is **one row per store with a 20-bit year mask**, where bit *i*
means "authorized on Dec 31 of 2006+*i*". 611,164 stores × 19 bytes = 11.61 MB,
fetched once. The year slider is a bit test and every filter is a linear pass over
typed arrays, so nothing round-trips to a server.

`points.bin` is five concatenated typed arrays. Section order guarantees alignment
for any N — `10N` is always even, `12N` always divisible by 4:

| Offset | Array | Type | Contents |
|---|---|---|---|
| `0` | position | Float32 ×2 | lon, lat |
| `8N` | format_id | Uint8 | index into `meta.formats` |
| `9N` | ownership_id | Uint8 | 0 chain / 1 independent / 2 unknown |
| `10N` | brand_id | Uint16 | index into `meta.brands`, +1; 0 = unbranded |
| `12N` | year_mask | Uint32 | bit *i* = active Dec 31 of 2006+*i* |

## Color

This is an all-pairs chart form — any two dots can land next to each other — so the
validated categorical palette carries **at most three hues**. That is why **format
is a filter, not a color dimension**: with 18 formats, coloring them all would
produce pairs no colorblind reader (and often no full-color reader) could separate.

- **Ownership** — chain / independent / gray for unknown.
- **Format** — highlight up to 3; everything else falls back to a non-identity gray.
- **None** — a single hue, best when a brand filter is already doing the selecting.

Both palettes were validated against the actual basemap background colors
(`#0e0e0e` dark, `#fafaf8` light) for CVD separation, normal-vision separation,
lightness band, chroma floor, and contrast. Dark is the default because all three
hues clear 3:1 there (4.97–5.67); on the light basemap the aqua sits at 2.69 and
relies on the legend.

## Data note

`web/data/` is generated and **gitignored** — regenerate it with `export_map.py`
rather than committing it. Deploying to GitHub Pages requires committing it
deliberately (11.61 MB); note that Pages on a private repo needs a paid plan.

A store appears in a year only if it was authorized on **Dec 31** of that year.
45,704 stores (7.0%) opened and closed between Dec 31sts and never appear at all.
Stores without usable coordinates are excluded; 9 stores active at the end of 2025 fall into that gap.
