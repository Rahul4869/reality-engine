/* relay/worker.js — Reality Engine relay (reference implementation, 2026-11-07)
 *
 * One Cloudflare Worker on the free plan does two jobs:
 *   1. WhatsApp Cloud API webhook
 *        GET  /webhook                      Meta's verify handshake (hub.verify_token must equal WA_VERIFY_TOKEN)
 *        POST /webhook                      inbound messages: HMAC checked, owner-only, encrypted, forwarded to GitHub as repository_dispatch "wa_inbound"
 *   2. Mission Control (the phone dashboard)
 *        GET  /app/<APP_PATH>/              the page (served from KV key "app_html", which the pipeline publishes)
 *        POST /app/<APP_PATH>/api/login     {pin}  first login enrols the PIN; later logins verify it; 5 misses = 15-minute lockout
 *                                            (any signed-out API call answers 401 {setup:true} while no PIN exists, so the page asks for it twice)
 *        GET  /app/<APP_PATH>/api/snapshot  the latest snapshot JSON (KV key "snapshot")
 *        GET  /app/<APP_PATH>/api/thumb/<episode>/<A|B|C>   a thumbnail preview (KV key "thumb:<episode>:<key>")
 *        POST /app/<APP_PATH>/api/action    {verb}  encrypted and forwarded to GitHub as repository_dispatch "dash_action"
 *
 * Secrets (Worker → Settings → Variables and Secrets, type Secret):
 *   WA_VERIFY_TOKEN   random string, also typed into Meta's webhook form
 *   WA_APP_SECRET     Meta app secret (App settings → Basic)
 *   WA_RELAY_KEY      base64 of 32 random bytes; the SAME value is the GitHub secret WA_RELAY_KEY
 *   OWNER_WA          the owner's number, digits only, with country code
 *   GH_DISPATCH_TOKEN fine-grained GitHub token, this repo only, Contents: read and write
 *   GH_REPO           "githubuser/reality-engine"
 *   APP_PATH          random 24+ characters; the dashboard lives at /app/<APP_PATH>/
 *   SESSION_KEY       random 32+ characters (signs the login cookie)
 * Binding: KV namespace bound as RE_KV.
 *
 * Nothing here logs message text, verbs, PINs or secrets (K32). Everything sent to GitHub is AES-GCM encrypted.
 * Fixes 2026-11-07 (build chat, recorded in CHANGES.md): (1) 401 {setup:true} before the first PIN exists; (2) PIN hashing at
 * PIN_ITERATIONS = 30,000 (PBKDF2 at 100,000 measured ~13 ms CPU elsewhere vs the free plan's 10 ms limit -> Error 1102 risk; the
 * runtime also refuses >100,000). Iterations are stored in each hash, so they can be raised later without breaking old PINs.
 * The build chat must run the tests in MISSION_CONTROL_BUILD_AND_DEPLOY.md before the owner deploys this.
 */

const te = new TextEncoder();
const td = new TextDecoder();

function toB64(buf) {
  const bytes = new Uint8Array(buf); let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}
const toB64u = buf => toB64(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
function fromB64(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/"); while (s.length % 4) s += "=";
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
}
const toHex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
function safeEq(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
const json = (obj, status = 200, extra = {}) =>
  new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra } });

/* ---------------------------------------------------------------- crypto helpers (exported for tests) */
export async function hmacHex(secret, data) {
  const key = await crypto.subtle.importKey("raw", te.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return toHex(await crypto.subtle.sign("HMAC", key, te.encode(data)));
}
export async function encrypt(keyB64, obj) {
  const key = await crypto.subtle.importKey("raw", fromB64(keyB64), { name: "AES-GCM" }, false, ["encrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, te.encode(JSON.stringify(obj)));
  return { c: toB64(ct), n: toB64(iv) };                     // Python: AESGCM(key).decrypt(nonce, ct, None)
}
export async function decrypt(keyB64, payload) {               // used only by tests (the pipeline decrypts in Python)
  const key = await crypto.subtle.importKey("raw", fromB64(keyB64), { name: "AES-GCM" }, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: fromB64(payload.n) }, key, fromB64(payload.c));
  return JSON.parse(td.decode(pt));
}
const PIN_ITERATIONS = 30000;                                   // fits the Workers Free 10 ms CPU budget; secret path + lockout carry the rest
export async function pinHash(pin, iterations = PIN_ITERATIONS) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const base = await crypto.subtle.importKey("raw", te.encode(pin), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, base, 256);
  return `pbkdf2$${iterations}$${toB64(salt)}$${toB64(bits)}`;
}
export async function pinVerify(pin, stored) {
  const [alg, iter, saltB64, hashB64] = String(stored || "").split("$");
  if (alg !== "pbkdf2") return false;
  const base = await crypto.subtle.importKey("raw", te.encode(pin), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: fromB64(saltB64), iterations: Number(iter) }, base, 256);
  return safeEq(toB64(bits), hashB64);
}
export async function signSession(secret, days = 30) {
  const payload = toB64u(te.encode(JSON.stringify({ exp: Date.now() + days * 86400e3, v: 1 })));
  const sig = await hmacHex(secret, payload);
  return payload + "." + sig;
}
export async function verifySession(secret, token) {
  const [payload, sig] = String(token || "").split(".");
  if (!payload || !sig) return false;
  if (!safeEq(await hmacHex(secret, payload), sig)) return false;
  try { return JSON.parse(td.decode(fromB64(payload))).exp > Date.now(); } catch (e) { return false; }
}

/* ---------------------------------------------------------------- GitHub dispatch (encrypted payload) */
export async function dispatch(env, eventType, payload) {
  const client_payload = await encrypt(env.WA_RELAY_KEY, payload);
  const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/dispatches`, {
    method: "POST",
    headers: { "authorization": `Bearer ${env.GH_DISPATCH_TOKEN}`, "accept": "application/vnd.github+json",
               "content-type": "application/json", "user-agent": "reality-engine-relay", "x-github-api-version": "2022-11-28" },
    body: JSON.stringify({ event_type: eventType, client_payload }) });
  return r.status === 204;
}

/* ---------------------------------------------------------------- WhatsApp webhook */
function waVerify(url, env) {
  const mode = url.searchParams.get("hub.mode"), token = url.searchParams.get("hub.verify_token"), ch = url.searchParams.get("hub.challenge");
  if (mode === "subscribe" && token && safeEq(token, env.WA_VERIFY_TOKEN || "")) return new Response(ch || "", { status: 200 });
  return new Response("Forbidden", { status: 403 });
}
export function normaliseMessage(m) {                          // only the fields the pipeline needs; never logged
  const out = { id: m.id, ts: m.timestamp, type: m.type };
  if (m.type === "text") out.text = m.text?.body || "";
  else if (m.type === "button") { out.payload = m.button?.payload || ""; out.text = m.button?.text || ""; }
  else if (m.type === "interactive") {
    const br = m.interactive?.button_reply || m.interactive?.list_reply || {};
    out.payload = br.id || ""; out.text = br.title || "";
  } else if (m.type === "image" || m.type === "video" || m.type === "document") { out.media_id = m[m.type]?.id || ""; out.text = m[m.type]?.caption || ""; }
  else if (m.type === "reaction") { out.payload = m.reaction?.emoji || ""; out.reply_to = m.reaction?.message_id || ""; }
  return out;
}
async function waInbound(req, env) {
  const raw = await req.text();
  const given = req.headers.get("x-hub-signature-256") || "";
  const expected = "sha256=" + await hmacHex(env.WA_APP_SECRET || "", raw);
  if (!safeEq(given, expected)) return new Response("Bad signature", { status: 401 });
  let body; try { body = JSON.parse(raw); } catch (e) { return new Response("", { status: 200 }); }
  const messages = [], statuses = [];
  for (const entry of body.entry || []) for (const ch of entry.changes || []) {
    const v = ch.value || {};
    for (const m of v.messages || []) if (String(m.from) === String(env.OWNER_WA)) messages.push(normaliseMessage(m));
    for (const s of v.statuses || []) if (String(s.recipient_id) === String(env.OWNER_WA)) statuses.push({ id: s.id, status: s.status, ts: s.timestamp });
  }
  if (messages.length || statuses.length) {
    try { await dispatch(env, "wa_inbound", { messages, statuses }); } catch (e) { /* Meta retries; the pipeline dedupes by message id */ }
  }
  return new Response("", { status: 200 });                     // always 200: anything else makes Meta retry and disable the webhook
}

/* ---------------------------------------------------------------- Mission Control */
const FALLBACK_HTML = `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mission Control</title>
<body style="font-family:system-ui;background:#151A2E;color:#ECEEF6;display:grid;place-items:center;height:100vh;margin:0;text-align:center;padding:24px">
<div><h1 style="font-weight:600">Mission Control is not published yet</h1><p>The pipeline publishes the page on its next run (every 30 minutes). Nothing is wrong.</p></div>`;

function cookieToken(req, name) {
  const c = req.headers.get("cookie") || "";
  for (const part of c.split(";")) { const [k, ...v] = part.trim().split("="); if (k === name) return v.join("="); }
  return "";
}
async function app(req, env, url, root) {
  const rel = url.pathname.slice(root.length);
  if (rel === "") return Response.redirect(url.origin + root + "/", 301);
  const secHeaders = { "x-frame-options": "DENY", "referrer-policy": "no-referrer", "x-content-type-options": "nosniff" };
  if (rel === "/" && req.method === "GET") {
    const html = (await env.RE_KV.get("app_html")) || FALLBACK_HTML;
    return new Response(html, { headers: { ...secHeaders, "content-type": "text/html; charset=utf-8", "cache-control": "no-store",
      "content-security-policy": "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'" } });
  }
  if (rel === "/api/login" && req.method === "POST") return login(req, env, root);
  if (!rel.startsWith("/api/")) return new Response("Not found", { status: 404 });
  if (!(await verifySession(env.SESSION_KEY, cookieToken(req, "re_s")))) {
    const enrolled = !!(await env.RE_KV.get("pin_hash"));         // fix 2026-11-07: tell the page to run the two-entry PIN setup
    return json(enrolled ? { error: "Signed out" } : { error: "Create your PIN", setup: true }, 401);
  }
  if (rel === "/api/snapshot" && req.method === "GET") {
    const snap = await env.RE_KV.get("snapshot");
    return snap ? new Response(snap, { headers: { ...secHeaders, "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } })
                : json({ error: "No snapshot yet. The pipeline writes one on its next run." }, 404);
  }
  const thumb = rel.match(/^\/api\/thumb\/(EP[0-9]{6,14}|DRAFT[0-9]{6,14})\/([ABC])$/);
  if (thumb && req.method === "GET") {
    const img = await env.RE_KV.get(`thumb:${thumb[1]}:${thumb[2]}`, { type: "arrayBuffer" });
    return img ? new Response(img, { headers: { ...secHeaders, "content-type": "image/jpeg", "cache-control": "private, max-age=300" } })
               : new Response("", { status: 404 });
  }
  if (rel === "/api/action" && req.method === "POST") {
    let body; try { body = await req.json(); } catch (e) { return json({ error: "Bad request" }, 400); }
    const verb = String(body?.verb || "");
    if (!/^[A-Z]{2,12}(\|[A-Za-z0-9_.:+\-]{0,80}){0,3}$/.test(verb)) return json({ error: "That action is not allowed." }, 400);
    const id = crypto.randomUUID();
    const ok = await dispatch(env, "dash_action", { id, verb, ts: Date.now(), src: "dash" });
    return ok ? json({ ok: true, id }) : json({ error: "GitHub did not accept the action. Try again in a minute." }, 502);
  }
  return json({ error: "Not found" }, 404);
}
async function login(req, env, root) {
  let body; try { body = await req.json(); } catch (e) { return json({ error: "Bad request" }, 400); }
  const pin = String(body?.pin || "").replace(/\D/g, "");
  if (pin.length !== 6) return json({ error: "The PIN has 6 digits." }, 400);
  const ip = req.headers.get("cf-connecting-ip") || "0";
  const failKey = "pinfail:" + ip;
  const fails = Number((await env.RE_KV.get(failKey)) || 0);
  if (fails >= 5) return json({ error: "Locked for 15 minutes after 5 wrong PINs." }, 429);
  let stored = await env.RE_KV.get("pin_hash");
  if (!stored) { stored = await pinHash(pin); await env.RE_KV.put("pin_hash", stored); }     // first login enrols the PIN (the secret path protects this moment)
  else if (!(await pinVerify(pin, stored))) {
    await env.RE_KV.put(failKey, String(fails + 1), { expirationTtl: 900 });
    return json({ error: `That PIN did not match (${4 - fails} tries left).` }, 401);
  }
  await env.RE_KV.delete(failKey);
  const token = await signSession(env.SESSION_KEY, 30);
  return json({ ok: true }, 200, { "set-cookie": `re_s=${token}; Path=${root}; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000` });
}

/* ---------------------------------------------------------------- router */
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/webhook") {
      if (req.method === "GET") return waVerify(url, env);
      if (req.method === "POST") return waInbound(req, env);
      return new Response("", { status: 405 });
    }
    const pub = url.pathname.match(/^\/pub\/([a-f0-9]{32})\.jpg$/);      // v10.1: short-lived public JPEGs for Instagram carousels (unguessable keys, 1-day TTL set by the pipeline)
    if (pub && req.method === "GET") {
      const img = await env.RE_KV.get("pub:" + pub[1], { type: "arrayBuffer" });
      return img ? new Response(img, { headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=3600", "x-content-type-options": "nosniff" } })
                 : new Response("Not found", { status: 404 });
    }
    if (env.APP_PATH) {
      const root = "/app/" + env.APP_PATH;
      if (url.pathname === root || url.pathname.startsWith(root + "/")) return app(req, env, url, root);
    }
    return new Response("Not found", { status: 404 });
  }
};
