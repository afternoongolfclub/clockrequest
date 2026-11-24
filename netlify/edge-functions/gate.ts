/**
 * Access code gate.
 *
 * Netlify's own password protection is a paid feature, so this does the same
 * job at the edge: every request needs a cookie carrying the hash of the code
 * in the ACCESS_CODE environment variable, or it gets a code-entry page.
 *
 * The raw code is never stored in the cookie or in this repository. Change it
 * by editing ACCESS_CODE in the project's environment variables and redeploying.
 * With no ACCESS_CODE set the site stays open, so a misconfiguration cannot
 * lock everyone out.
 */

const COOKIE = 'clockgate';
const SALT = '::clockrequest';
const THIRTY_DAYS = 60 * 60 * 24 * 30;

async function sha256(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function gatePage(failed: boolean): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>Clock Request Desk</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>
:root{--bg:#F1F2F4;--surface:#FFFFFF;--sunk:#F7F8F9;--ink:#191C20;--muted:#6B737C;
  --rule:#DBDFE4;--brass:#7A7040;--bad:#9A3029;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141619;--surface:#1C1F24;
  --sunk:#181B1F;--ink:#E9EBEE;--muted:#8B939C;--rule:#2C3138;--brass:#BCAF6E;--bad:#E08B81;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141619;--surface:#1C1F24;--sunk:#181B1F;--ink:#E9EBEE;
  --muted:#8B939C;--rule:#2C3138;--brass:#BCAF6E;--bad:#E08B81;color-scheme:dark}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:'Inter',system-ui,sans-serif;
  display:grid;place-items:center;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:14px;padding:34px 30px;
  width:min(420px,100%);box-shadow:0 1px 2px rgba(17,20,24,.06),0 8px 24px rgba(17,20,24,.06)}
.eyebrow{display:flex;align-items:center;gap:9px;color:var(--brass);font-size:11px;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;margin:0 0 12px}
.pip{width:7px;height:7px;border-radius:50%;background:var(--brass)}
h1{font-family:'Source Serif 4',Georgia,serif;font-weight:600;font-size:26px;margin:0 0 10px;line-height:1.15}
p{color:var(--muted);font-size:14.5px;line-height:1.55;margin:0 0 20px}
label{display:block;font-size:12px;font-weight:600;color:var(--ink);margin:0 0 6px}
input{width:100%;box-sizing:border-box;font:inherit;font-size:15px;color:var(--ink);background:var(--sunk);
  border:1px solid var(--rule);border-radius:9px;padding:11px 12px;letter-spacing:.04em}
input:focus{outline:2px solid var(--brass);outline-offset:-1px;border-color:var(--brass)}
button{margin-top:14px;width:100%;appearance:none;border:1px solid var(--brass);background:var(--brass);
  color:#fff;font:inherit;font-size:15px;font-weight:600;padding:11px 18px;border-radius:9px;cursor:pointer}
button:hover{filter:brightness(1.06)}
button:focus-visible{outline:2px solid var(--brass);outline-offset:2px}
.err{color:var(--bad);font-size:13px;margin:12px 0 0}
</style>
</head>
<body>
  <form class="card" method="POST" action="/__gate">
    <p class="eyebrow"><span class="pip"></span> Clock Request Desk</p>
    <h1>Enter your access code</h1>
    <p>This page is for clubs working with the shop. Use the code you were sent.</p>
    <label for="code">Access code</label>
    <input id="code" name="code" type="password" autocomplete="one-time-code"
           autocapitalize="off" autocorrect="off" spellcheck="false" autofocus required>
    <button type="submit">Continue</button>
    ${failed ? '<p class="err">That code was not recognised. Check it and try again.</p>' : ''}
  </form>
</body>
</html>`;
}

const HTML = { 'content-type': 'text/html; charset=utf-8', 'x-robots-tag': 'noindex' };

export default async (request: Request): Promise<Response | undefined> => {
  const code = Netlify.env.get('ACCESS_CODE');
  if (!code) return;                                  // not configured: stay open

  const expected = await sha256(code + SALT);
  const url = new URL(request.url);

  if (url.pathname === '/__gate') {
    if (request.method !== 'POST') {
      return new Response(gatePage(false), { status: 401, headers: HTML });
    }
    const form = await request.formData();
    const given = String(form.get('code') ?? '').trim();
    if (given && (await sha256(given + SALT)) === expected) {
      return new Response(null, {
        status: 303,
        headers: {
          Location: '/',
          'Set-Cookie':
            `${COOKIE}=${expected}; Path=/; Max-Age=${THIRTY_DAYS}; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    return new Response(gatePage(true), { status: 401, headers: HTML });
  }

  const cookies = (request.headers.get('cookie') ?? '').split(/;\s*/);
  if (cookies.includes(`${COOKIE}=${expected}`)) return;   // through to the site

  return new Response(gatePage(false), { status: 401, headers: HTML });
};

export const config = { path: '/*' };
