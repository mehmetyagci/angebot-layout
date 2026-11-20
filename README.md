# sok-angebot-layout

Automatic page layout for the ŞOK weekly "Top Angebote" flyer (1587x2245 px template, 4 equal bands).
Products are pre-grouped into boxes (`data/boxes13.json`); the solver chooses row composition and box widths,
the engine places photo + text inside each box and renders HTML -> PNG with Playwright/Chromium.

## Files
- `engine.py` – per-box layout: photo fit from aspect ratio, price badge, text column, overlap for multi-variety boxes. Hooks: MAYS, HCAP, OVMAP, UPMAP, NARROW.
- `search.py` – loads boxes (env `BOXFILE`).
- `gen54.py` – solver: row compositions, hero width, per-row widths (fill + share objective, equal-width rule, exceptions).
- `gen53lib.py` – `build(page, rows, spec, name)` renders a hand/solver spec `(box_idx, x_units, w_units, r0, r1)`.
- `render.py` – HTML for a box, Chromium screenshot.
- `examples/run61.py, run62.py` – page 2 hand specs; `run60.py` – page 4 (liter rule).
- `trim/` (you provide) – trimmed product photos `<artikel>.png`, or set env `TRIM`.
- `data/` – boxes, photo metadata (`ph.json`), page template image. **Product photos are NOT included** (paths in `ph.json` point to your own photo folder; adapt).

## Run
```
pip install pillow playwright && playwright install chromium
python examples/run62.py     # writes out/L2b.png
```
Run from the repo root. Fonts: Liberation Sans (`/usr/share/fonts/truetype/liberation`).

## Layout rules (accumulated)
1 tea first, then olives; hero first element top-left. 2 spread products evenly. 3 same-gramaj boxes look identical.
4 equal widths per row (exceptions: hero, Classic Dimes, more important item). 5 same liter = same photo size; smaller volume smaller.
6 photos as large as possible but balanced. 7 rice -> pulses -> pastes, sauces last. 8 cleaning top, drinks bottom of p4.
Text never below photo; price badge top-right; photos never cropped.

## Known limits
Quality metric is photo fill only; neighbour harmony and page-level balance are tuned by hand. Flat products in narrow equal-width boxes leave empty strips.
