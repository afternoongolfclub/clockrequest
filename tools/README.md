# Build chain

`index.html` at the repo root is self-contained and can be edited directly.
These files exist so the relationship to the claude.ai artifact edition stays
reproducible rather than being folklore.

| File | What it is |
|---|---|
| `app_template.html` | The artifact edition's source: the same page, but with `claude.use()` capabilities, the admin Requests inbox and the Costing tab. Font and lettering geometry are inlined. |
| `make_netlify.py` | Derives the public `index.html` from `app_template.html`: strips the capabilities and the admin tabs, and wraps crest, filament and order in a Netlify form. |

The preview's assets sit in the repo root next to `index.html`:
`post_geom.json` (view, overlay matrix, lettering positions per size),
`shade_*.png` / `mask_*.png` (the render and its filament mask, recoloured
live), and the assembly animation (`assembly.html?size=516|363`,
`manifest_*.json`, `meshes_*.b64.txt`).

## Regenerating

```
python3 tools/make_netlify.py        # rewrites ./index.html
```

It asserts on its own output — no `claude.use`, no `window.claude`, no admin
tab remnants, one form — so a failed transform stops rather than shipping a
broken page.

## Where the geometry came from

The preview is not a drawing of a clock; it is the clock. Paths were traced
from `HCC_Club_Champion.3mf` (housing part_1 and accents part_6) and
`Clock_Dials_x4_A1.3mf` (numerals part_2). Arc text runs on the measured radii
— crown 61.14 mm, lower 57.97 mm — and shrinks to fit the way the plate
builder does, stopping at a 3.1 mm cap height where relief stops printing
cleanly at a 0.4 nozzle. Dial text is held clear of the chapter ring at
r 32.5 mm. Those numbers are measurements, not guesses; changing them
desynchronises the preview from what the printer produces.
