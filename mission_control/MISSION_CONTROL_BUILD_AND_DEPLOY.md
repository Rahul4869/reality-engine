# MISSION CONTROL — BUILD AND DEPLOY (work package M1)

Prepared 2026-11-07. Companion to `REALITY_ENGINE_v10_LAUNCH_AND_HYPERGROWTH_BRIEF.md` §10. The build chat implements Part A, proves Part B, then babysits Part C with the owner on a phone. Cost: ₹0/month (Cloudflare free plan).

Files in this pack:
- `dashboard/mission_control.html` — the page (prototype with demo data; already uses relative API paths; ships unchanged into the repo as `dashboard/mission_control.html`).
- `relay/worker.js` — reference Cloudflare Worker: WhatsApp webhook (WP5) + Mission Control routes. Tested 2026-11-07 in Node with WebCrypto: encrypt/decrypt round-trip, tamper rejection, HMAC, PIN hash/verify, session sign/verify, verify handshake, bad-signature 401, owner-only forwarding, encrypted dispatch, PIN enrol/lockout, snapshot/action/thumb routes, wrong-path 404. Deploy it as it is unless the build chat finds a defect; record any change in CHANGES.md.

**One brain, three remotes.** WhatsApp (WP5), email links (existing) and Mission Control all send the same verbs to the same router (`cli wa_inbound`). Mission Control adds a rich screen: thumbnails side by side, meters, charts, settings.

---

## Part A — what the build chat implements

### A1. New module `whatifs/dash.py`
- `build_snapshot()` → dict following the contract in the brief §10, built only from Sheet tabs and Settings:
  - `engine`: `PAUSED`, budget mode (`BUDGET_MODE`), owner mode, next scheduled episode (Episodes status SCHEDULED, earliest `slot_et`), `UPLOAD_LOCK`.
  - `docket`: open `Owner_Actions` rows (WP4) mapped to cards: kind, title, why, `default_label`, `default_at` (= `expires_at`), `window_h`, options (for picks: the Packaging_Tests A/B/C rows with `thumb_url` = `api/thumb/<episode>/<key>`), `verbs` (label → `VERB|args`), `links` (Studio deep links for the link pack and for `NATIVETEST`).
  - `progress`: subscribers, qualified watch hours (365 d), Shorts views (90 d), 14-day series (views, engaged views) and KPIs from `Analytics` (CTR, rel30, APV, Shorts stay ratio, subs per 1,000); `old_bar_deadline` = `2027-01-31` from `Platform_Facts`.
  - `learned`: last 3 promoted lessons/rules from `Strategy_Log` with confidence and loop.
  - `lab`: running experiments (strategy dimensions and Playbook trials with their posterior `p_best` and n), Retention Microscope boosters/killers (G3; empty list until it exists).
  - `money`: month spend by line from `Cost_Log`, cap, revenue (affiliate/ads/clients from `Revenue_Log`), the three modes with costs from Settings.
  - `health`: `Expiry_Calendar` rows, last run per workflow from `Run_Log`.
  - `settings`: the allow-listed quick toggles (`SLEEP_SESSIONS_ON`, `LOCALIZATIONS_ON`, `AFFILIATE_BLOCK_ON`, `NATIVE_TEST_REMINDER_ON`, `SHORTS_PER_DAY`).
  - `whatsapp`: the test-number link (`wa.me/<number>`) when WP5 is set up, else "".
  - Never include secrets, premises not yet released, scripts or critic notes (K32). Titles of **scheduled** episodes are fine (the owner must see them to pick).
- `push_snapshot()` → `PUT https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/snapshot` with `Authorization: Bearer {CF_KV_TOKEN}`; body = JSON. Then for each open pick: `PUT .../values/thumb:<episode>:<key>` with the 640-px JPEG (≤ 60 KB each; re-encode from Drive `thumb_A/B/C`). Skip thumbs already pushed (`Dash_Pushed` tab or a hash cell).
- `push_app()` → `PUT .../values/app_html` with `dashboard/mission_control.html` whenever its SHA-256 differs from Setting `DASH_APP_SHA` (so dashboard updates deploy from the repo, never from the Cloudflare editor).
- Called from: end of `cli tick` (every 30 min), end of produce/release/learn/preprod jobs, and from the verb router after every handled action (so "Queued" becomes "Done" quickly). Budget: ~70–120 KV writes/day. VERIFY Cloudflare KV free-tier write limit (expected 1,000/day) and keep a daily counter in Settings; above 800 writes, only the tick pushes.
- Settings: `DASH_ON` (TRUE), `DASH_PUSH_MIN_INTERVAL_MIN` (10), `DASH_APP_SHA` (auto), `DASH_WRITES_TODAY` (auto). Missing CF secrets → one Setup_Status ❌ row `dashboard_ready`, no crash, no retries every tick (back off 6 h).

### A2. Actions path
- `.github/workflows/whatsapp.yml` (WP5): `on: repository_dispatch: types: [wa_inbound, dash_action]`. The job decrypts `client_payload` with `WA_RELAY_KEY` (Python `cryptography` AES-GCM, pinned) and calls `python -m whatifs.cli wa_inbound`.
- The router accepts `dash_action` payloads `{id, verb, ts, src: "dash"}`; dedupes on `id` in the same `Inbound_Seen` tab as WhatsApp message ids; runs the verb; writes the `Owner_Actions` row status (DONE / error text); then calls `dash.push_snapshot()`.
- New verbs (also usable from WhatsApp): `MODE|lean|standard|growth`, `OWNERMODE|minimal|hands_on|studio`, `LOCKSHEETS|<char>`, `REDOSHEETS|<char>`, `NATIVETEST|<EP>`, `SET|<allow-listed key>|<value>`, `LINKED|<EP>`, `DISCUSS|<id>`. `SET` obeys the WP13.2 allow-list and protected-key rules; protected keys answer "needs the second confirm on WhatsApp".
- Owner replies to the page are not possible (one-way GitHub dispatch); the page shows "Queued" and reads the result from the next snapshot. A verb that fails is shown on the card in the next snapshot (`Owner_Actions.answer`).

### A3. Worker
- Commit `relay/worker.js` unchanged (or with recorded fixes). Add `relay/README.md` with the secrets table below. The owner pastes the file into the Cloudflare editor once (Part C); later Worker changes are rare and babysat the same way.

### A4. Secrets and settings
| Where | Name | What |
|---|---|---|
| Cloudflare Worker secrets | `WA_VERIFY_TOKEN`, `WA_APP_SECRET`, `OWNER_WA` | WhatsApp (WP5); can be blank until WP5 is set up |
| Cloudflare Worker secrets | `WA_RELAY_KEY` | base64 of 32 random bytes; same value in GitHub |
| Cloudflare Worker secrets | `GH_DISPATCH_TOKEN`, `GH_REPO` | fine-grained token (this repo, Contents read/write), `user/reality-engine` |
| Cloudflare Worker secrets | `APP_PATH`, `SESSION_KEY` | random 24+ and 32+ characters; Claude generates and shows them, the owner pastes them |
| Cloudflare Worker binding | `RE_KV` | KV namespace `re-kv` |
| GitHub secrets | `WA_RELAY_KEY`, `CF_ACCOUNT_ID`, `CF_KV_NAMESPACE_ID`, `CF_KV_TOKEN` | KV token: API token with permission "Workers KV Storage: Edit" on this account only; expiry 1 year → `Expiry_Calendar` |
| Nobody | the PIN | enrolled on first login in the app; stored only as a PBKDF2 hash in KV |

### A5. Security notes for the record
- The page lives at `/app/<APP_PATH>/`; without the secret path nothing answers. The PIN gates every API call; 5 misses lock the IP for 15 minutes. Session cookie: HttpOnly, Secure, SameSite=Strict, 30 days.
- Everything sent to GitHub is AES-GCM encrypted; public Actions logs show counts and status only (K32).
- To reset the PIN: delete the KV key `pin_hash` in the Cloudflare dashboard (babysat, 1 minute); the next login enrols a new one.
- If the owner's phone is lost: rotate `APP_PATH` and `SESSION_KEY` (2 minutes, babysat).

---

## Part B — tests the build chat must run (`tests/test_v94b_dash.py` + the Worker test)
- `build_snapshot()` on the fake store: contract keys present; no secrets, no unreleased premise text, no critic notes in the JSON (string scan against Settings secrets and the DRAFT tab).
- Thumb push skips already-pushed hashes; 640-px JPEG ≤ 60 KB.
- `push_app()` pushes only when the SHA changed.
- Missing CF secrets → ❌ Setup_Status row, exit 0, backoff respected.
- Daily write counter: above 800 only the tick pushes.
- `dash_action` payload: dedupe on id; unknown verb → error recorded, no crash; `SET` on a protected key → refused with the WhatsApp hint.
- Worker: run `node --test` (or the harness in this pack's history) covering: verify handshake, bad signature 401, non-owner dropped, encrypted dispatch, PIN enrol/verify/lockout, session required, snapshot/thumb/action routes, verb regex, wrong APP_PATH 404. If Node is unavailable in the sandbox, say so and run it in the Checks workflow instead.
- Rehearsal: `dash.build_snapshot()` runs inside the fake rehearsal without a paid call.

---

## Part C — one-time deployment, babysat on the owner's phone (about 20 minutes, splittable)

Use the §1.2 babysitting format from the master file. Cloudflare's dashboard works in Chrome on a phone with ⋮ → Desktop site.

**C1. Cloudflare account (5 min).** Owner signs up at dash.cloudflare.com (free plan; email + password; no card). Claude explains the exact screens from the owner's screenshots.

**C2. KV namespace (2 min).** Workers & Pages → KV → Create namespace → name `re-kv` → Create. Claude reads the namespace ID from the page (it is an ID, not a secret).

**C3. Worker (4 min).** Workers & Pages → Create → Start with Hello World → name `re-relay` → Deploy → Edit code → select all → paste `relay/worker.js` (Claude provides it as a copy-ready block; it is not a secret) → Deploy. Then Settings → Bindings → Add → KV namespace → variable name `RE_KV` → select `re-kv` → Save.

**C4. Worker secrets (4 min).** Settings → Variables and Secrets → Add, type **Secret**, one at a time: `APP_PATH` and `SESSION_KEY` (Claude generates both and shows them in chat — they are not account credentials; the owner copies them in), `WA_RELAY_KEY` (Claude generates: 32 random bytes, base64), `GH_REPO`, `GH_DISPATCH_TOKEN` (owner generates on GitHub: Settings → Developer settings → Fine-grained tokens → this repo only → Contents: Read and write → 1 year; owner pastes it straight into Cloudflare, never into chat). WhatsApp secrets come later with WP5; leave them unset until then.

**C5. GitHub secrets (3 min).** Repo → Settings → Secrets and variables → Actions → New: `WA_RELAY_KEY` (same value), `CF_ACCOUNT_ID` (from the Cloudflare dashboard URL or Overview page), `CF_KV_NAMESPACE_ID` (from C2), `CF_KV_TOKEN` (Cloudflare → My Profile → API Tokens → Create → Custom → Workers KV Storage: Edit → this account → 1 year; owner pastes it into GitHub). Add the two expiry dates to `Expiry_Calendar`.

**C6. First publish (1 min, automatic).** Run the Pipeline workflow once (or wait ≤30 min). `dash.push_app()` publishes the page and the first snapshot. Setup_Status `dashboard_ready` ✅.

**C7. Open it (2 min).** Claude sends the link `https://re-relay.<account>.workers.dev/app/<APP_PATH>/`. Owner opens it in Chrome, types a 6-digit PIN (this first login sets it), then ⋮ → **Add to Home screen**. Done. Test one harmless action: Controls → the Sleep Session toggle off and on; the snapshot after the next run shows it.

**If the owner skips C7 for days:** nothing breaks; WhatsApp and email keep working; the dashboard waits.

---

## Part D — later, optional upgrades (not in M1)
- Cloudflare Access (free for up to 50 users) in front of `/app/` for email one-time-PIN login.
- Push notifications (Web Push via the Worker) for urgent HOLD alerts, so WhatsApp is not the only urgent channel.
- A "Ask the engine" box on the Controls tab that sends `ASK|<text>` to the chat brain (WP5); the reply arrives as a card in the next snapshot. WhatsApp remains better for back-and-forth.
- Track B order intake (brief §5) as a sixth tab.

---

## Amendments 2026-11-07 (build chat, after the Step 0 sense check; these win over the text above)
1. **Snapshot gains `acks`** = list of `{verb, at (ISO), ok (bool), note}` for actions handled in the last 48 h. The page clears "Queued" only when it sees its verb here; without it every tap stayed "Queued" forever. `dash.build_snapshot()` fills it from `Owner_Actions` rows answered in the last 48 h.
2. **First PIN:** the Worker answers any signed-out API call with `401 {setup:true}` while no `pin_hash` exists. The page then asks for the PIN twice and enrols it through `api/login`. The prototype called `/api/pin/setup`, a route that does not exist, with a leading slash, so a typo became the PIN.
3. **PIN hashing at 30,000 PBKDF2 iterations** (`PIN_ITERATIONS`), measured at 6.5 ms vs 13.4 ms for 100,000 in Node. The Workers Free plan allows 10 ms CPU per request; going over returns Error 1102. Iterations are stored per hash, so they can be raised later. The secret path, the 5-try lockout and the session cookie carry the rest.
4. **Never demo data when served:** a network error or a missing snapshot used to switch the live app into demo mode, where taps went nowhere. Now it keeps the last real data, shows "No connection / No data yet", and refuses taps ("Your tap was not sent"). Demo data is only used when the file is opened directly.
5. **Worker tests:** `relay/test_worker.mjs` (8 tests: handshake, bad signature, owner-only + encrypted forward, first-PIN setup flag, enrol + cookie, lockout, verb regex + encrypted dispatch, thumb route, wrong path, old-hash compatibility). Plus a Python AES-GCM decrypt of a real Worker payload (interop with the pipeline). Run them in Checks: `node --test relay/test_worker.mjs`.
