# Clock Request Desk

Static order page for custom branded golf-club clocks, printed on a Bambu Lab A1.

Visitors choose a layout, set the lettering, upload a crest and pick Bambu Lab
filament colours. The preview is drawn from the real print geometry — the
silhouette, accents and dial numerals are traced from the production meshes,
and the arc text sits on the measured radii (61.14 mm at the crown, 57.97 mm
below), shrinking to fit the way the plate builder does. It stops at a 3.1 mm
cap height, the point where relief stops printing cleanly at a 0.4 nozzle.

The lettering face is Caladea Bold, subset and embedded, so the preview uses
the same type as the print.

## Deploying

No build step. Netlify serves the repo root; `netlify.toml` sets that.

## Submissions

The order form posts to Netlify Forms under the name `clock-request`, with the
crest sent as a file field. Submissions appear under **Forms** in the Netlify
dashboard. The hidden fields carry the configurator state, and `spec` is a
readable summary suitable for pasting into a quote.

## Files

- `index.html` — the whole app: markup, styles, geometry and script
- `thanks.html` — post-submit page
- `netlify.toml` — publish directory and headers
