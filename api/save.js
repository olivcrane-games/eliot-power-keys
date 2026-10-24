// Cloud save for Eliot's Power Keys.
// The browser encrypts the save with a key derived from the game password before sending it,
// so this function only ever stores scrambled text. The file name is a hash of the password too.
import { put, list } from '@vercel/blob';

const ok = (k) => /^[a-f0-9]{64}$/.test(k);

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'GET' && String(req.url || '').includes('ping')) {
    try { await list({ limit: 1 }); return res.status(200).json({ ok: true, store: 'reachable' }); }
    catch (e) { return res.status(500).json({ error: String(e && e.message || e) }); }
  }
  const key = String(req.headers['x-save-key'] || '');
  if (!ok(key)) return res.status(400).json({ error: 'bad key' });
  const pathname = 'saves/' + key + '.txt';
  try {
    if (req.method === 'GET') {
      const { blobs } = await list({ prefix: pathname, limit: 1 });
      if (!blobs.length) return res.status(404).json({ error: 'none' });
      const r = await fetch(blobs[0].url + '?v=' + Date.now(), { cache: 'no-store' });
      return res.status(200).send(await r.text());
    }
    if (req.method === 'PUT' || req.method === 'POST') {
      let body = req.body;
      if (typeof body !== 'string') body = body ? JSON.stringify(body) : '';
      if (!body || body.length > 400000) return res.status(413).json({ error: 'too big' });
      await put(pathname, body, { access: 'public', addRandomSuffix: false, contentType: 'text/plain', cacheControlMaxAge: 60 });
      return res.status(200).json({ ok: true });
    }
    return res.status(405).json({ error: 'method' });
  } catch (e) {
    return res.status(500).json({ error: String(e && e.message || e) });
  }
}
