// relay/test_worker.mjs — run with: node --test relay/test_worker.mjs   (Node 18+; uses global WebCrypto)
import test from "node:test";
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import worker, { hmacHex, encrypt, decrypt, pinHash, pinVerify, signSession, verifySession } from "./worker.js";
import { webcrypto } from "node:crypto";
if (!globalThis.crypto) globalThis.crypto = webcrypto;          // Node 18 only; Cloudflare and Node 20+ have it (never put this in worker.js)

const KEY = Buffer.from(new Uint8Array(32).map((_, i) => i * 7 + 3)).toString("base64");
function kv() {
  const m = new Map();
  return { m, async get(k, o) { const v = m.get(k); if (v === undefined) return null; return o && o.type === "arrayBuffer" ? v : v; },
           async put(k, v) { m.set(k, v); }, async delete(k) { m.delete(k); } };
}
function env(extra = {}) {
  return { WA_VERIFY_TOKEN: "vt-123", WA_APP_SECRET: "app-secret", WA_RELAY_KEY: KEY, OWNER_WA: "919800000000",
           GH_DISPATCH_TOKEN: "ghp_test", GH_REPO: "owner/reality-engine", APP_PATH: "p".repeat(24), SESSION_KEY: "s".repeat(32), RE_KV: kv(), ...extra };
}
let sent = [];
globalThis.fetch = async (url, init) => { sent.push({ url, body: JSON.parse(init.body) }); return new Response(null, { status: 204 }); };
const root = e => "https://w.example/app/" + e.APP_PATH;
const req = (url, init = {}) => new Request(url, init);
const post = (url, body, headers = {}) => req(url, { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify(body) });

test("verify handshake", async () => {
  const e = env();
  let r = await worker.fetch(req("https://w.example/webhook?hub.mode=subscribe&hub.verify_token=vt-123&hub.challenge=42"), e);
  assert.equal(r.status, 200); assert.equal(await r.text(), "42");
  r = await worker.fetch(req("https://w.example/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=42"), e);
  assert.equal(r.status, 403);
});

test("webhook: bad signature 401, owner forwarded encrypted, stranger dropped", async () => {
  const e = env(); sent = [];
  const body = JSON.stringify({ entry: [{ changes: [{ value: { messages: [
    { id: "wamid.1", from: "919800000000", timestamp: "1", type: "text", text: { body: "hello secret idea" } },
    { id: "wamid.2", from: "111", timestamp: "1", type: "text", text: { body: "spam" } } ] } }] }] });
  let r = await worker.fetch(req("https://w.example/webhook", { method: "POST", headers: { "x-hub-signature-256": "sha256=00" }, body }), e);
  assert.equal(r.status, 401); assert.equal(sent.length, 0);
  const sig = "sha256=" + await hmacHex("app-secret", body);
  r = await worker.fetch(req("https://w.example/webhook", { method: "POST", headers: { "x-hub-signature-256": sig }, body }), e);
  assert.equal(r.status, 200); assert.equal(sent.length, 1);
  assert.equal(sent[0].body.event_type, "wa_inbound");
  assert.ok(!JSON.stringify(sent[0].body).includes("hello secret idea"), "plain text must not leave the Worker");
  const p = await decrypt(KEY, sent[0].body.client_payload);
  assert.equal(p.messages.length, 1); assert.equal(p.messages[0].text, "hello secret idea");
  writeFileSync(new URL("./_interop_payload.json", import.meta.url), JSON.stringify({ key: KEY, payload: sent[0].body.client_payload }));
});

test("first visit asks for PIN setup; enrol; then plain sign-in prompt", async () => {
  const e = env();
  let r = await worker.fetch(req(root(e) + "/api/snapshot"), e);
  assert.equal(r.status, 401); assert.equal((await r.json()).setup, true);
  r = await worker.fetch(post(root(e) + "/api/login", { pin: "123456" }), e);
  assert.equal(r.status, 200);
  const cookie = r.headers.get("set-cookie"); assert.match(cookie, /re_s=.*HttpOnly; Secure; SameSite=Strict/);
  assert.match(e.RE_KV.m.get("pin_hash"), /^pbkdf2\$30000\$/);
  r = await worker.fetch(req(root(e) + "/api/snapshot"), e);
  assert.equal(r.status, 401); assert.equal((await r.json()).setup, undefined);
  const c = cookie.split(";")[0];
  r = await worker.fetch(req(root(e) + "/api/snapshot", { headers: { cookie: c } }), e);
  assert.equal(r.status, 404);                                   // no snapshot published yet
  await e.RE_KV.put("snapshot", JSON.stringify({ generated_at: "x", acks: [] }));
  r = await worker.fetch(req(root(e) + "/api/snapshot", { headers: { cookie: c } }), e);
  assert.equal(r.status, 200); assert.deepEqual((await r.json()).acks, []);
});

test("wrong PIN five times locks for 15 minutes", async () => {
  const e = env(); await e.RE_KV.put("pin_hash", await pinHash("111111"));
  for (let i = 0; i < 5; i++) {
    const r = await worker.fetch(post(root(e) + "/api/login", { pin: "222222" }, { "cf-connecting-ip": "1.2.3.4" }), e);
    assert.equal(r.status, 401);
  }
  const r = await worker.fetch(post(root(e) + "/api/login", { pin: "111111" }, { "cf-connecting-ip": "1.2.3.4" }), e);
  assert.equal(r.status, 429);
});

test("action: verb regex, session required, encrypted dispatch", async () => {
  const e = env(); sent = [];
  let r = await worker.fetch(post(root(e) + "/api/action", { verb: "PICK|EP202611140|B" }), e);
  assert.equal(r.status, 401);
  const c = "re_s=" + await signSession(e.SESSION_KEY, 1);
  r = await worker.fetch(post(root(e) + "/api/action", { verb: "rm -rf /" }, { cookie: c }), e);
  assert.equal(r.status, 400); assert.equal(sent.length, 0);
  r = await worker.fetch(post(root(e) + "/api/action", { verb: "PICK|EP202611140|B" }, { cookie: c }), e);
  assert.equal(r.status, 200); assert.equal(sent.length, 1); assert.equal(sent[0].body.event_type, "dash_action");
  const p = await decrypt(KEY, sent[0].body.client_payload);
  assert.equal(p.verb, "PICK|EP202611140|B"); assert.equal(p.src, "dash"); assert.ok(p.id);
});

test("thumb route and wrong path", async () => {
  const e = env(); const c = "re_s=" + await signSession(e.SESSION_KEY, 1);
  await e.RE_KV.put("thumb:EP202611140:A", new Uint8Array([255, 216, 255]).buffer);
  let r = await worker.fetch(req(root(e) + "/api/thumb/EP202611140/A", { headers: { cookie: c } }), e);
  assert.equal(r.status, 200); assert.equal(r.headers.get("content-type"), "image/jpeg");
  r = await worker.fetch(req("https://w.example/app/wrongpath/api/snapshot", { headers: { cookie: c } }), e);
  assert.equal(r.status, 404);
});

test("old 100k hashes still verify; sessions expire; crypto round trip", async () => {
  assert.ok(await pinVerify("654321", await pinHash("654321", 100000)));
  assert.ok(!(await pinVerify("000000", await pinHash("654321"))));
  assert.ok(await verifySession("k".repeat(32), await signSession("k".repeat(32), 1)));
  assert.ok(!(await verifySession("k".repeat(32), await signSession("k".repeat(32), -1))));
  assert.deepEqual(await decrypt(KEY, await encrypt(KEY, { a: 1 })), { a: 1 });
});

test("PIN hash CPU time (informative)", async () => {
  const t0 = performance.now(); await pinHash("123456"); const ms = performance.now() - t0;
  console.log(`pinHash at 30,000 iterations took ${ms.toFixed(1)} ms in this Node sandbox`);
  const t1 = performance.now(); await pinHash("123456", 100000); console.log(`at 100,000: ${(performance.now() - t1).toFixed(1)} ms`);
});

test("public carousel image route: only 32-hex keys, jpeg, 404 when gone", async () => {
  const e = env(); const k = "a".repeat(32);
  await e.RE_KV.put("pub:" + k, new Uint8Array([255, 216, 255]).buffer);
  let r = await worker.fetch(req("https://w.example/pub/" + k + ".jpg"), e);
  assert.equal(r.status, 200); assert.equal(r.headers.get("content-type"), "image/jpeg");
  r = await worker.fetch(req("https://w.example/pub/" + "b".repeat(32) + ".jpg"), e); assert.equal(r.status, 404);
  r = await worker.fetch(req("https://w.example/pub/../snapshot"), e); assert.equal(r.status, 404);
  r = await worker.fetch(req("https://w.example/pub/" + k + ".jpg", { method: "POST" }), e); assert.equal(r.status, 404);
});

