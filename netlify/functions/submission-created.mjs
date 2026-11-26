/**
 * Files every clock request into the private pipeline repo the moment it arrives.
 *
 * Netlify runs this automatically for each verified form submission (the
 * "submission-created" event). It copies the customer's crest out of Netlify's
 * temporary upload link before that link expires, and writes
 *
 *   requests/<order_id>/order.json   settings order_build.py reads (crest path filled in)
 *   requests/<order_id>/crest.png    the one-colour crest the customer approved in the preview
 *   requests/<order_id>/crest_original.<ext>  their upload, byte for byte
 *   requests/<order_id>/brief.txt    the build brief from the email
 *
 * to afternoongolfclub/clock-pipeline. A Claude chat then needs only the
 * request ID from the email: clone the repo, run order_build.py on that folder.
 *
 * Needs CLOCK_PIPELINE_TOKEN in the Netlify environment: a fine-grained GitHub
 * token with Contents read/write on afternoongolfclub/clock-pipeline only.
 * Without it the function logs and does nothing, so the form and the email
 * keep working regardless.
 */

const REPO = process.env.CLOCK_PIPELINE_REPO || 'afternoongolfclub/clock-pipeline';
const MAX_CREST = 8 * 1024 * 1024;
const EXT = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/svg+xml': 'svg', 'image/webp': 'webp' };

function safeId(s) {
  return String(s || '').replace(/[^A-Za-z0-9-]/g, '').slice(0, 40);
}

function orderFromBrief(brief) {
  const lines = String(brief || '').split('\n');
  const i = lines.findIndex((l) => l.startsWith('ORDER JSON'));
  if (i < 0) return null;
  try { return JSON.parse(lines[i + 1]); } catch { return null; }
}

function crestInfo(field) {
  if (!field) return null;
  if (typeof field === 'string') return field.startsWith('http') ? { url: field } : null;
  if (field.url) return field;
  return null;
}

async function put(token, path, bytes, message) {
  const res = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'clockrequest-netlify',
    },
    body: JSON.stringify({ message, content: Buffer.from(bytes).toString('base64') }),
  });
  if (!res.ok) throw new Error(`GitHub ${res.status} on ${path}: ${(await res.text()).slice(0, 200)}`);
}

export async function fileRequest(payload, token, fetchImpl = fetch) {
  const data = payload.data || {};
  if ((payload.form_name || data['form-name']) !== 'clock-request') return { skipped: 'other form' };
  const id = safeId(data.order_id) || safeId(payload.id) || `req-${Date.now()}`;
  const dir = `requests/${id}`;
  const order = orderFromBrief(data.build_brief) || {};
  const club = order.club_name || data.club || 'unknown club';
  const files = [];

  // crest_print: the one-colour image the customer saw in the preview (what prints).
  // crest: their original upload, kept beside it for reference.
  async function grab(field) {
    const info = crestInfo(field);
    if (!info) return null;
    const r = await fetchImpl(info.url);
    if (!r.ok) throw new Error(`crest download ${r.status}`);
    const buf = Buffer.from(await r.arrayBuffer());
    if (buf.length > MAX_CREST) throw new Error(`crest is ${buf.length} bytes`);
    const type = (info.type || r.headers.get('content-type') || '').split(';')[0].trim();
    const fromName = (info.filename || '').split('.').pop().toLowerCase();
    const ext = EXT[type] || (['png', 'jpg', 'jpeg', 'svg', 'webp'].includes(fromName) ? fromName : 'png');
    return { buf, ext };
  }
  const printed = await grab(data.crest_print);
  const original = await grab(data.crest);
  if (printed) {
    files.push([`${dir}/crest.png`, printed.buf]);
    order.crest = 'crest.png';
  }
  if (original) {
    files.push([`${dir}/crest_original.${original.ext}`, original.buf]);
    if (!printed) order.crest = `crest_original.${original.ext}`;   // older page or no canvas: trace the original
  }
  if (!printed && !original) order.crest = '';
  order.request_id = id;
  // who and what, for the shop's Requests inbox (this repo is private)
  order.customer = {
    club: data.club || '', contact: data.contact || '', email: data.email || '', phone: data.phone || '',
    quantity: data.quantity || '1', needed_by: data.needed_by || '', notes: data.notes || '',
  };
  order.filaments = {
    housing: data.filament_housing || '', accents: data.filament_accents || '',
    dial: data.filament_dial || '', numerals: data.filament_numerals || '',
  };
  order.received = payload.created_at || new Date().toISOString();
  files.push([`${dir}/order.json`, Buffer.from(JSON.stringify(order, null, 1) + '\n')]);
  if (data.build_brief) files.push([`${dir}/brief.txt`, Buffer.from(String(data.build_brief))]);

  for (const [path, bytes] of files) await put(token, path, bytes, `Request ${id}: ${club}`);
  return { filed: files.map(([p]) => p) };
}

export const handler = async (event) => {
  const token = process.env.CLOCK_PIPELINE_TOKEN;
  let payload;
  try { payload = JSON.parse(event.body).payload; } catch { return { statusCode: 400, body: 'bad payload' }; }
  if (!token) {
    console.log('CLOCK_PIPELINE_TOKEN not set; request not filed to the pipeline repo');
    return { statusCode: 200, body: 'not configured' };
  }
  try {
    const out = await fileRequest(payload, token);
    console.log(JSON.stringify(out));
    return { statusCode: 200, body: JSON.stringify(out) };
  } catch (e) {
    // Never fail the submission itself: the email still carries everything.
    console.error(`filing failed: ${e.message}`);
    return { statusCode: 200, body: 'filing failed' };
  }
};
