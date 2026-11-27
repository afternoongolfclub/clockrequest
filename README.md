# Club Clocks by Afternoon Golf Club

The order site for Club Clocks (formerly the Clock Request Desk).

Static order page for custom branded golf-club clocks, printed on a Bambu Lab P1S.

Visitors choose a layout, set the lettering, upload a crest and pick Bambu Lab
filament colors. The preview is drawn from the real print geometry — the
silhouette, accents and dial numerals are traced from the production meshes,
and the arc text sits on the measured radii (61.14 mm at the crown, 57.97 mm
below), shrinking to fit the way the plate builder does. It stops at a 3.1 mm
cap height, the point where relief stops printing cleanly at a 0.4 nozzle.

The lettering face is Caladea Bold, subset and embedded, so the preview uses
the same type as the print.

## Deploying

Live at https://clubclocks.netlify.app

No build step. Netlify serves the repo root; `netlify.toml` sets that.
Pushes to `main` deploy automatically.

## Access code

Every request passes through `netlify/edge-functions/gate.ts`, which asks for a
code before serving anything. Netlify's built-in password protection is a paid
feature; this does the same job on the free tier.

The code lives in the `ACCESS_CODE` environment variable, never in this repo.
Change it under Project configuration > Environment variables, then redeploy.
Visitors are remembered for 30 days by an HttpOnly cookie holding a hash of the
code, not the code. Clearing `ACCESS_CODE` leaves the site open rather than
locking everyone out.

## Submissions

The order form posts to Netlify Forms under the name `clock-request`, with the
crest sent as a file field. Submissions appear under **Forms** in the Netlify
dashboard. The hidden fields carry the configurator state, and `spec` is a
readable summary suitable for pasting into a quote.

## Files

- `index.html` — the whole app: markup, styles, geometry and script
- `thanks.html` — post-submit page
- `netlify.toml` — publish directory and headers


## Shop admin (/admin)

https://clubclocks.netlify.app/admin/ — dashboard, orders (status, quote, payments, notes,
build brief, photos of the finished clock), purchases (filament, parts, packaging, tools; receipt
photos or PDFs; CSV export), and costing. Photos are shrunk to 2000 px JPEG in the browser before upload
(4.5 MB cap per file). Sign-in is the `ADMIN_CODE` environment variable (separate from the
customers' `ACCESS_CODE`; the admin area stays locked while it is unset). Data lives in the private
`afternoongolfclub/clock-pipeline` repo: `requests/<id>/admin.json` per order,
`requests/<id>/photos/`, `books/purchases.json`, `books/receipts/` and `config/costing.json`, read and written by `netlify/functions/admin-api.mjs` with
`CLOCK_PIPELINE_TOKEN`.
