/**
 * Shop admin API for Club Clocks. Everything lives in the private repo
 * afternoongolfclub/clock-pipeline, next to the requests the order form files:
 *
 *   requests/<id>/order.json     what the club asked for (written by submission-created)
 *   requests/<id>/admin.json     the shop's side: status, quote, payments, notes, promised date
 *   config/costing.json          filament, parts and margin settings
 *   books/purchases.json         what the shop has bought: filament, parts, packaging, tools
 *
 * Routes (all behind the admin password, checked again here as well as at the edge):
 *   GET  /api/admin/orders              every order with its admin record
 *   GET  /api/admin/orders/<id>         one order, plus its build brief
 *   PUT  /api/admin/orders/<id>         save the admin record
 *   GET  /api/admin/file/<id>/<name>    a crest file
 *   GET  /api/admin/costing             costing settings
 *   PUT  /api/admin/costing             save costing settings
 *   GET  /api/admin/purchases           every purchase
 *   POST /api/admin/purchases           add a purchase
 *   PUT  /api/admin/purchases/<pid>     change a purchase
 *   DELETE /api/admin/purchases/<pid>   remove a purchase
 */

const REPO = process.env.CLOCK_PIPELINE_REPO || 'afternoongolfclub/clock-pipeline';
const BRANCH = 'main';
const STATUSES = ['new', 'quoted', 'approved', 'printing', 'ready', 'delivered', 'cancelled'];
const ID = /^[A-Za-z0-9-]{1,40}$/;
const FILE = /^crest(_original)?\.(png|jpe?g|svg|webp)$/;
const MIME = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', svg: 'image/svg+xml', webp: 'image/webp' };

const PURCHASES = 'books/purchases.json';
const CATS = ['filament', 'parts', 'packaging', 'tools', 'maintenance', 'shipping', 'other'];
const PID = /^p[a-z0-9]{6,24}$/;

const NOSTORE = { 'cache-control': 'no-store', 'x-robots-tag': 'noindex' };
const json = (data, status = 200) => Response.json(data, { status, headers: NOSTORE });

async function sha256(v) {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(v));
  return Array.from(new Uint8Array(b)).map((x) => x.toString(16).padStart(2, '0')).join('');
}

async function signedIn(req) {
  const code = process.env.ADMIN_CODE;
  if (!code) return false;
  const want = `ccadmin=${await sha256(code + '::clubclocks-admin')}`;
  return (req.headers.get('cookie') || '').split(/;\s*/).includes(want);
}

function gh(path, init = {}) {
  const token = process.env.CLOCK_PIPELINE_TOKEN;
  return fetch(`https://api.github.com/repos/${REPO}/${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'clubclocks-admin',
      ...(init.headers || {}),
    },
  });
}

async function blob(sha) {
  const r = await gh(`git/blobs/${sha}`);
  if (!r.ok) throw new Error(`GitHub ${r.status} reading a file`);
  return Buffer.from((await r.json()).content, 'base64');
}

async function tree() {
  const r = await gh(`git/trees/${BRANCH}?recursive=1`);
  if (!r.ok) throw new Error(`GitHub ${r.status} listing the repo`);
  return (await r.json()).tree || [];
}

async function readJSON(path) {
  const r = await gh(`contents/${path}?ref=${BRANCH}`);
  if (r.status === 404) return { data: null, sha: null };
  if (!r.ok) throw new Error(`GitHub ${r.status} reading ${path}`);
  const j = await r.json();
  return { data: JSON.parse(Buffer.from(j.content, 'base64').toString('utf8')), sha: j.sha };
}

async function writeJSON(path, data, message) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const { sha } = await readJSON(path);
    const r = await gh(`contents/${path}`, {
      method: 'PUT',
      body: JSON.stringify({
        message, branch: BRANCH, ...(sha ? { sha } : {}),
        content: Buffer.from(JSON.stringify(data, null, 1) + '\n').toString('base64'),
      }),
    });
    if (r.ok) return;
    if (r.status !== 409 && r.status !== 422) throw new Error(`GitHub ${r.status} saving ${path}`);
  }
  throw new Error(`Could not save ${path}: it changed while saving. Try again.`);
}

// read, change and write back; retried if the file changed underneath (phone and laptop at once)
async function updateJSON(path, change, message) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const { data, sha } = await readJSON(path);
    const next = change(data);
    const r = await gh(`contents/${path}`, {
      method: 'PUT',
      body: JSON.stringify({
        message, branch: BRANCH, ...(sha ? { sha } : {}),
        content: Buffer.from(JSON.stringify(next, null, 1) + '\n').toString('base64'),
      }),
    });
    if (r.ok) return next;
    if (r.status !== 409 && r.status !== 422) throw new Error(`GitHub ${r.status} saving ${path}`);
  }
  throw new Error(`Could not save ${path}: it changed while saving. Try again.`);
}

const num = (v) => (Number.isFinite(+v) ? Math.round(+v * 100) / 100 : 0);
const str = (v, n = 2000) => String(v ?? '').slice(0, n);

function cleanAdmin(b, prev) {
  const status = STATUSES.includes(b.status) ? b.status : (prev?.status || 'new');
  const history = Array.isArray(prev?.history) ? prev.history.slice(-50) : [];
  if (!prev || prev.status !== status) history.push({ at: new Date().toISOString(), status });
  return {
    status,
    price: num(b.price),
    promised: str(b.promised, 10),
    payments: (Array.isArray(b.payments) ? b.payments : []).slice(0, 50).map((p) => ({
      date: str(p.date, 10), amount: num(p.amount), method: str(p.method, 20), note: str(p.note, 200),
    })).filter((p) => p.amount),
    notes: str(b.notes, 5000),
    history,
    updatedAt: new Date().toISOString(),
  };
}

function cleanPurchase(b, id) {
  const date = /^\d{4}-\d{2}-\d{2}$/.test(b.date || '') ? b.date : new Date().toISOString().slice(0, 10);
  return {
    id, date,
    vendor: str(b.vendor, 100).trim(),
    item: str(b.item, 200).trim(),
    category: CATS.includes(b.category) ? b.category : 'other',
    amount: num(b.amount),
    qty: Math.max(0, num(b.qty)),
    kg: Math.max(0, Math.round((+b.kg || 0) * 1000) / 1000),
    order: ID.test(b.order || '') ? b.order : '',
    note: str(b.note, 500).trim(),
    updatedAt: new Date().toISOString(),
  };
}
const purchaseList = (d) => (d && Array.isArray(d.purchases) ? d.purchases : []);

async function listOrders() {
  const t = await tree();
  const byId = {};
  for (const e of t) {
    const m = /^requests\/([^/]+)\/([^/]+)$/.exec(e.path);
    if (!m || e.type !== 'blob') continue;
    (byId[m[1]] ||= { id: m[1], files: [], sha: {} }).files.push(m[2]);
    byId[m[1]].sha[m[2]] = e.sha;
  }
  const rows = await Promise.all(Object.values(byId).map(async (o) => {
    if (!o.sha['order.json']) return null;
    const [order, admin] = await Promise.all([
      blob(o.sha['order.json']).then((b) => JSON.parse(b.toString('utf8'))).catch(() => null),
      o.sha['admin.json'] ? blob(o.sha['admin.json']).then((b) => JSON.parse(b.toString('utf8'))).catch(() => null) : null,
    ]);
    if (order && !order.customer && o.sha['brief.txt']) {
      // filed before order.json carried contact details: read them from the brief's ORDER section
      const text = (await blob(o.sha['brief.txt']).catch(() => Buffer.from(''))).toString('utf8').replace(/\r\n/g, '\n');
      const sec = (text.split('ORDER\n')[1] || '').split('\n\n')[0];
      const keys = { Club: 'club', Contact: 'contact', Email: 'email', Phone: 'phone', Quantity: 'quantity', 'Needed by': 'needed_by', Notes: 'notes' };
      const cu = {};
      for (const line of sec.split('\n')) {
        const m = /^- ([A-Za-z ]+): (.*)$/.exec(line);
        if (m && keys[m[1]]) cu[keys[m[1]]] = m[2].trim();
      }
      if (Object.keys(cu).length) order.customer = cu;
    }
    return order && { id: o.id, files: o.files.filter((f) => FILE.test(f)), order, admin };
  }));
  return rows.filter(Boolean).sort((a, b) => String(b.order.received || b.id).localeCompare(String(a.order.received || a.id)));
}

export default async (req) => {
  if (!(await signedIn(req))) return json({ error: 'Not signed in' }, 401);
  if (!process.env.CLOCK_PIPELINE_TOKEN) return json({ error: 'CLOCK_PIPELINE_TOKEN is not set' }, 503);
  const parts = new URL(req.url).pathname.replace(/^\/api\/admin\/?/, '').split('/').filter(Boolean);
  try {
    if (parts[0] === 'orders' && parts.length === 1 && req.method === 'GET') {
      return json({ orders: await listOrders() });
    }
    if (parts[0] === 'orders' && parts.length === 2 && ID.test(parts[1])) {
      const id = parts[1];
      if (req.method === 'GET') {
        const [{ data: order }, { data: admin }] = await Promise.all([
          readJSON(`requests/${id}/order.json`), readJSON(`requests/${id}/admin.json`),
        ]);
        if (!order) return json({ error: 'No such order' }, 404);
        const br = await gh(`contents/requests/${id}/brief.txt?ref=${BRANCH}`, { headers: { Accept: 'application/vnd.github.raw' } });
        return json({ id, order, admin, brief: br.ok ? await br.text() : '' });
      }
      if (req.method === 'PUT') {
        const { data: order } = await readJSON(`requests/${id}/order.json`);
        if (!order) return json({ error: 'No such order' }, 404);
        const { data: prev } = await readJSON(`requests/${id}/admin.json`);
        const admin = cleanAdmin(await req.json(), prev);
        await writeJSON(`requests/${id}/admin.json`, admin, `Admin ${id}: ${admin.status}`);
        return json({ ok: true, admin });
      }
    }
    if (parts[0] === 'file' && parts.length === 3 && ID.test(parts[1]) && FILE.test(parts[2]) && req.method === 'GET') {
      const r = await gh(`contents/requests/${parts[1]}/${parts[2]}?ref=${BRANCH}`, { headers: { Accept: 'application/vnd.github.raw' } });
      if (!r.ok) return json({ error: 'No such file' }, 404);
      const ext = parts[2].split('.').pop().toLowerCase();
      return new Response(await r.arrayBuffer(), {
        headers: { 'content-type': MIME[ext] || 'application/octet-stream', 'cache-control': 'private, max-age=3600',
                   'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'", 'x-content-type-options': 'nosniff' },
      });
    }
    if (parts[0] === 'costing' && parts.length === 1) {
      if (req.method === 'GET') return json({ costing: (await readJSON('config/costing.json')).data });
      if (req.method === 'PUT') {
        const body = await req.json();
        const raw = JSON.stringify(body.costing || {});
        if (raw.length > 20000) return json({ error: 'Costing settings too large' }, 413);
        const costing = JSON.parse(raw);
        await writeJSON('config/costing.json', costing, 'Costing settings');
        return json({ ok: true });
      }
    }
    if (parts[0] === 'purchases') {
      if (parts.length === 1 && req.method === 'GET') {
        return json({ purchases: purchaseList((await readJSON(PURCHASES)).data) });
      }
      if (parts.length === 1 && req.method === 'POST') {
        const b = await req.json();
        const p = cleanPurchase(b, 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
        if (!p.item && !p.vendor) return json({ error: 'Say what was bought' }, 400);
        const out = await updateJSON(PURCHASES, (d) => {
          const list = purchaseList(d);
          if (list.length >= 5000) throw Object.assign(new Error('The purchase book is full'), { status: 409 });
          return { purchases: [...list, p] };
        }, `Purchase: ${p.item || p.vendor} ${p.amount}`);
        return json({ ok: true, purchase: p, purchases: out.purchases }, 201);
      }
      if (parts.length === 2 && PID.test(parts[1]) && (req.method === 'PUT' || req.method === 'DELETE')) {
        const pid = parts[1];
        const b = req.method === 'PUT' ? await req.json() : null;
        const out = await updateJSON(PURCHASES, (d) => {
          const list = purchaseList(d);
          if (!list.some((x) => x.id === pid)) throw Object.assign(new Error('No such purchase'), { status: 404 });
          return { purchases: list.flatMap((x) => (x.id !== pid ? [x] : b ? [cleanPurchase(b, pid)] : [])) };
        }, `${b ? 'Purchase changed' : 'Purchase removed'}: ${pid}`);
        return json({ ok: true, purchases: out.purchases });
      }
    }
    return json({ error: 'Not found' }, 404);
  } catch (e) {
    console.error(e);
    return json({ error: e.message || 'Something went wrong' }, e.status || 502);
  }
};

export const config = { path: ['/api/admin/*'] };
