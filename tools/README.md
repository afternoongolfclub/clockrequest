# Build chain

`index.html` at the repo root is self-contained and can be edited directly.
These files exist so the relationship to the claude.ai artifact edition stays
reproducible rather than being folklore.

| File | What it is |
|---|---|
| `app_template.html` | The artifact edition's source: the same page, but with `claude.use()` capabilities, the admin Requests inbox and the Costing tab. `__GEOM__` and `__FONT__` are placeholders. |
| `geom.json` | SVG path data for the live preview — body silhouette, accents and dial numerals, traced from the production meshes at 0.05 mm and simplified. |
| `cal.b64` | Caladea Bold, subset to Latin-1 plus punctuation, woff2, base64. The lettering face the clocks actually print in. |
| `make_netlify.py` | Derives the public `index.html` from `app_template.html`: strips the capabilities and the admin tabs, swaps the layout radios for buttons, and wraps the order fields in a Netlify form. |

## Regenerating

```
python3 make_netlify.py        # writes ../netlify-site/index.html
```

It asserts on its own output — no `claude.use`, no `window.claude`, no admin
tab remnants — so a failed transform stops rather than shipping a broken page.

## Where the geometry came from

The preview is not a drawing of a clock; it is the clock. Paths were traced
from `HCC_Club_Champion.3mf` (housing part_1 and accents part_6) and
`Clock_Dials_x4_A1.3mf` (numerals part_2). Arc text runs on the measured radii
— crown 61.14 mm, lower 57.97 mm — and shrinks to fit the way the plate
builder does, stopping at a 3.1 mm cap height where relief stops printing
cleanly at a 0.4 nozzle. Dial text is held clear of the chapter ring at
r 32.5 mm. Those numbers are measurements, not guesses; changing them
desynchronises the preview from what the printer produces.
