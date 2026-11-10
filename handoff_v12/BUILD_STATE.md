# BUILD_STATE - Reality Engine v12 "Organisation"
Updated: 10 Nov 2026 (end of B2). Branch: `v12-organisation` (never main). Resume: read this file + `git log -5`.

## NEXT
**B3 - Memo system + Department contract** (01 sections 4, 5; 03 "B3"). Full seven-step MANDATORY BATCH LOOP. Effort: High.
What B2 leaves ready for B3 (use it, do not rebuild it):
- `whatifs/org/__init__.py` holds DEPARTMENTS (D0-D12, C, L with a default stage) and STAGES: `org/registry.py` builds on it.
- The runner's LOAD step calls `palace.playbook(dept, stage, topic)` (returns `playbook_id`, `text`, `items`); its LEARN step writes takeaways with
  `palace.add(item, actor=<dept id>)` (a department can only PROPOSE; the write gate already rejects an empty or unevidenced takeaway); cited ids go
  to `palace.mark_applied(ids)`. Checks `palace_injected` / `palace_cited` can compare a prompt with the stored text of `playbook_id` (tab `Palace_Playbooks`).
- Tabs still to append in B3+: `Memos`, `Tickets`, `Sessions`, `Takeaways`, `Lever_Changes`, `Org_Audit` (B2 added only the three it uses).
- First thing in B3: add `whatifs/org/palace.py` (and the new org modules) to `tools/repair.py` PROTECTED (see open issue 10).

## DONE
### B2 - Knowledge Palace core (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: the organisation has ONE repository of knowledge - 92 founding items (the owner's words, the research, the build's own lessons),
each with dated evidence and a pointer to the code that enforces it - with a write gate, a life cycle with authority, and one guarded doorway that
builds a bounded playbook per department. It runs daily, at Setup and as HARD check `palace_health` on every episode. Honest limit: no department
READS a playbook yet (that is B3 + B6), so B2 by itself changes no video.

#### Step 1 RESEARCH (10 dated sources; E = measured evidence, O = opinion / practice / official guidance)
1. E - Zhang et al., "Agentic Context Engineering" (ACE), arXiv 2510.04618, Oct 2025 (v3 Mar 2026, ICLR 2026): knowledge kept as itemised bullets
   (id + helpful/harmful counters), changed only by small delta entries merged with NON-model logic; asking a model to rewrite the whole memory
   collapses it into a vague summary. +10.6% on agent tasks, +8.6% finance, 86.9% lower adaptation latency. Limit: without a reliable outcome
   signal the memory turns noisy or harmful. -> items, never a rewritten document; deterministic merges; outcome counters come from D10 only.
2. E - Shen, Toyoda, Leung, "Revoked but Still Authoritative", arXiv 2609.08258, 8 Sep 2026: five memory systems that mark a contradicted fact
   "invalid" but keep it; 9 scenarios x 9 models: NO system enforces the revocation by default - if the retrieval layer can see the revoked record it
   is returned, ranks above its replacement and the agent acts on it. Fix that worked: a guard between agent and memory that withholds it.
   -> the status filter runs in code BEFORE ranking; a retired / superseded / expired item can never reach a prompt, label or no label.
3. E - Nakayashiki, "When Stale Constraints Go Unchecked", arXiv 2608.25553, 26 Aug 2026: 16 models; a consolidated memory whose source record was
   later withdrawn still drove the decision in 77.3 / 74.7 / 74.7% of episodes; models checked where a memory came from in about 1 episode in 5; a
   "freshness" cue did nothing; a rule that prefers memories stating a LIMIT recovered +89.3 points. -> (a) code, not the reader, invalidates items
   derived from a withdrawn source; (b) limits get a reserved lane at the top of every playbook.
4. E - Rasmussen et al., "Zep: a temporal knowledge graph architecture for agent memory", arXiv 2501.13956, Jan 2025: contradicted facts get an end
   date instead of being deleted; 94.8% vs 93.4% on Deep Memory Retrieval; up to +18.5% accuracy and -90% latency on LongMemEval, mostly because the
   context shrank from ~115,000 to ~1,600 tokens. -> keep history, serve a small current slice.
5. E - Dash et al., "From Untrusted Input to Trusted Memory" (MPBench), arXiv 2606.04329, 3 Jun 2026: one hostile memory write has long-term effect;
   4 write channels, 9 structural weaknesses; agents that write and read memory more eagerly are more exploitable; prompt-injection defences do not
   cover it. -> a write gate: evidence required, the trust level is computed by code from the evidence type, viewer / web text never enters as an
   accepted item, items are rendered to models as data.
6. O/official - Anthropic, "Effective context engineering for AI agents", 29 Sep 2025: the smallest set of high-signal tokens; hybrid loading (a
   small preloaded block + fetch the rest on demand). -> a bounded playbook is preloaded; full bodies are fetched by id only when needed.
7. O/official - Anthropic prompt-caching docs (read 10 Nov 2026): a cache hit needs a 100% identical prefix; minimum cacheable length 512-4,096
   tokens by model; cache reads cost 0.1x (0.05x on the newest Opus / Sonnet). -> the same Palace state must give a byte-identical playbook
   (deterministic order, id = hash of the text), and it only changes when knowledge changes.
8. O/practice - Consortium for Service Innovation, KCS v6 Practices Guide, technique 5.2 (article states): Work in Progress / Not Validated /
   Validated / Archived; the life cycle is non-linear; an article is validated by being REUSED successfully; archive, never delete.
   -> status life cycle with re-validation, promotion by evidence of use, nothing deleted.
9. E/official - Google Sheets API limits (developers.google.com, read 10 Nov 2026): 300 requests a minute per project, 60 per user, 2 MB payload
   advised; a cell holds 50,000 characters. -> the Sheet row is a small index that is enough to build a playbook in ONE read; long bodies live
   outside the Sheet; writes are batched.
10. E - "BM25 wins at scale" (2026 scaling study, as reported; primary id not verified): keyword ranking beats dense retrieval and agent search on
   large piles, and at small sizes exact matching is enough. -> tag + keyword scoring in code (Rs 0, deterministic, no new dependency); an embedding
   scorer can be plugged in later if the Palace outgrows it.
Not established by any source found: that a rule placed first in a long prompt is obeyed more reliably than one placed last (the "lost in the
middle" work is about retrieval). The lane order below is therefore a design choice backed by source 3, not by a placement study.

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Spec-literal store": item rows edited in place, bodies on Drive, playbook = top items by tag overlap cut at a character cap. 2/3/5/3/5 = 18.
  Weak: a retired item is only as safe as every caller's filter; nothing ties knowledge to the code that applies it; ids change with wording.
- B "Research stack" (ACE + Zep + KCS): itemised entries, deterministic delta merges, end-dating instead of deleting, promotion by reuse, keyword
  retrieval, small preloaded block. 4/4/4/4/5 = 21. Weak: still trusts labels at read time (source 2) and lets a stale limit vanish quietly.
- C "The guarded ledger" (ORIGINAL, built on B's mechanics):
  1. ONE doorway out: every playbook is built by one function whose first step is the status-and-date guard, so nothing retired, superseded,
     expired or still only proposed can reach a prompt even if maintenance never ran.
  2. Provenance cascade: when an item is superseded or retired, everything `derived_from` it is expired by code in the same call.
  3. Limits lane: owner words, policy rules and failure lessons are served first and hold a reserved share of every playbook.
  4. Asymmetric expiry (my own rule, from sources 2-3): a stale TECHNIQUE is dropped until re-validated; a stale LIMIT keeps being served, marked
     "review due" and reported - a limit must never disappear silently.
  5. Content-addressed playbooks: id = hash of the exact text, so the id is proof of what was injected and the cached prefix stays stable.
  6. Trust is computed, not typed: confidence comes from the evidence types (owner decision > own measured data > measured study / official
     > practice > research digest > opinion > model claim); nothing enters without dated evidence.
  7. Knowledge is tied to code: every `applied_in` reference (a check, a setting, a function, a file) must exist or the Palace is unhealthy.
  8. Founding knowledge is code: seed items live in the repo (`whatifs/org/seed/*.json`), load idempotently, and can never resurrect a status that
     the organisation later changed.
  9. The truth registry guards the door: an item naming a retired concept is refused on write and flagged if a concept is retired later.
  4/5/5/4/5 = 23.
- DECISION: C.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/palace.py` (+ `whatifs/org/__init__.py` with the department and stage lists, `whatifs/org/seed/*.json`). Tabs appended:
  `Palace_Items` (index: everything a playbook needs, so one Sheet read builds it), `Palace_Versions` (one row per change with a running version and
  a hash of the whole Palace), `Palace_Playbooks` (each distinct playbook once). Bodies: seed items resolve from the repo; runtime items go to the
  Drive folder `palace/` (retry, then an inline fallback so learning never stops on a Drive hiccup).
- Life cycle as DATA: proposed -> accepted -> testing -> proven / retired; superseded; expired; each move lists who may make it (owner, council,
  D10, librarian, clock, build). Owner items change only by the owner. An illegal move raises.
- Playbook: guard -> lanes (limits, proven, accepted, testing) -> relevance (department, stage, topic keywords) -> greedy fill under a hard cap
  (default 1,800 estimated tokens per department) -> id = hash.
- Size caps per kind: when a kind is over its cap the lowest-value item (never owner words or limits) is expired by code, not by a model.
- Runs in production now: daily learning job + both setup paths (`palace.daily` / `palace.maintain`), and a new HARD contract check `palace_health`
  on every episode (index valid, seed present, no dead code reference, no retired concept, caps, every department's playbook builds inside its cap
  with only servable items). NOT in this batch (by the plan): injecting playbooks into department prompts and citing them (B3 runner, B6 checks
  `palace_injected` / `palace_cited`), the Council, the Librarian's merges, D10 outcome scores.
- Rejected: an embedding index (new dependency or paid calls for a few hundred short items; source 10); storing bodies only in Sheet cells
  (cell limit, heavy reads); letting a model merge or rewrite items (source 1); deleting anything (sources 4, 8); a hand-kept Palace doc (the
  generated SYSTEM.md gets a Palace section instead).
- Enforcement plan and tests: see steps 5-6 (every transition both ways, guard, cascade, expiry both kinds, caps, cap of the playbook, seed
  validity, contract PASS / FAIL, rehearsal assertion, matrix row).
- Cost: Rs 0 (no model call). Sheet traffic: 1 read per playbook, 1-3 writes per change; seeding is one batched append.
- Palace seed items: `whatifs/org/seed/build.json` (keys `b2.*`: 10 research-backed items + the takeaway). The seed moved out of `handoff_v12/palace_seed`
  into the code tree, because production loads it.

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/__init__.py` (departments + stages) and `whatifs/org/palace.py` (930 lines): `check` / `validate` (write gate), `add` / `add_many`,
  `transition`, `supersede`, `expire`, `revalidate`, `mark_applied`, `enforce_caps`, `tidy`, `servable` (the guard), `playbook`, `playbook_issues`,
  `body`, `seed_items` / `ensure_seed`, `sync_brain`, `sync_canon`, `reconcile`, `snapshot`, `maintain`, `daily`, `health`. By hand: `python -m whatifs.org.palace`.
- NEW founding knowledge, 92 items in `whatifs/org/seed/`: owner.json 29 (his words, verbatim quote kept as evidence), breakout.json 15, feel.json 15,
  platform.json 15, build.json 18 (B1, B1b, B2). By kind: owner_preference 25, technique 27, tool_fact 13, policy_rule 10, strategy 7, audience_insight 4,
  takeaway 3, plan 2, failure_lesson 1. 0 refused by the gate. Over 120 `applied_in` references, every one resolves to a real check, setting, tab,
  function or file. Second-hand research is honest about itself: status accepted, computed trust 0.5, nothing is "proven" until D10 measures it.
- Mirrors of records that already exist (seed sources 3 and 4 of the plan): `sync_brain` (Technique_Evidence -> technique items, and a retired level
  becomes an "avoid" lesson in the limits lane; the learning core stays the authority) and `sync_canon` (character bible + every published case from
  Show_Log / Season; viewer handles never enter).
- Tabs appended: `Palace_Items` (28 columns), `Palace_Versions`, `Palace_Playbooks`. 7 settings: PALACE_ON, PALACE_PLAYBOOK_TOKENS (1800),
  PALACE_PLAYBOOK_TOKENS_BY_DEPT, PALACE_LIMITS_SHARE (0.4), PALACE_REVIEW_DAYS, PALACE_KIND_CAPS, PALACE_FOLDER_ID.
- Production hooks: `manage.learn` -> `palace.daily` (after the learning core's own update), `manage.setup` -> `palace.maintain`,
  contract check `palace_health` (39 hard checks now: 21 script + 18 final).
- `truth.code_files` and `gen_docs._modules` now walk sub-packages, so `whatifs/org/` is under the truth scan and in SYSTEM.md; SYSTEM.md has a
  generated section 10 (kinds, statuses, the whole move table, review windows, caps, departments, founding-knowledge counts).
- `publish.drive_upload` gained `parent=` (the Drive folder palace/); bodies fall back to an inline copy when Drive fails.
- Added during the build after looking at real output (not in the design memo): item `priority` 1-3 (3 = core, only owner / Council / seed may set it)
  and tighter department addressing - the first writers' playbook had opened with a minor owner idea and left out "it happens to YOU".

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| Nothing enters without dated evidence, a known kind / department / stage, a 20-400 character summary; trust computed by code | `palace.check` | write refused (PalaceError), nothing stored; `palace_health` on stored rows |
| Every `applied_in` reference exists in the code | `palace.ref_ok` | write refused; seed -> tests + `palace_health` FAIL; runtime row -> reference dropped + logged |
| No retired concept, no instruction-like text, no platform-gaming proposal in the Palace | `palace.text_issues` (uses `truth.RETIRED`) | write refused; later hit -> never served, auto-expired (owner words: `palace_health` FAIL) |
| Only listed moves, only by the listed roles, always with a reason | `palace.transition` + `MOVES` | PalaceError, status unchanged |
| The owner's words change only by the owner | `palace._owner_rule` | PalaceError |
| Nothing retired / superseded / expired / proposed reaches a prompt (also after a hand edit) | `palace.servable` inside `palace.playbook` | `playbook_issues` -> `palace_health` FAIL |
| Withdrawn knowledge sends its descendants back | `palace._cascade` | tests |
| Stale technique dropped; stale limit kept, marked, reported | `palace.expire` + guard | tests; note in `palace_health` |
| Playbook inside its hard cap, limits first, deterministic, id = hash of text | `palace.playbook` | `playbook_issues` -> `palace_health` FAIL |
| Size caps per kind by code; limits, owner words and canon never displaced | `palace.enforce_caps` | `palace_health` FAIL when a kind stays over its cap |
| Founding knowledge present; a seed never resurrects a changed status | `palace.ensure_seed` | `palace_health` FAIL (missing items / broken seed file) |
| Palace kept up every day, at Setup and before every episode's check | `palace.daily` / `maintain` | rehearsal asserts; `palace_health` |
4 matrix rows added (docs/CURRENT/ENFORCEMENT_MATRIX.md; the meta-test proves every reference is wired). Rehearsal asserts `palace_health` PASS, the
seed, mirrored canon, a recorded writers' playbook inside its cap, and a healthy Palace at the end.

#### Step 6 PROVE
- `tests/test_v12_palace.py`: 39 tests, each rule both ways. Highlights: 23 kinds of bad item each refused with nothing written; ALL 343 combinations
  of from-status x to-status x role checked against the move table; a randomised 140-item Palace in every status, for 15 departments x 3 caps: nothing
  unservable ever served, never over the cap, limits first, same text whatever the row order; a hand-edited status cell cannot bring a superseded
  item back; Drive down -> learning continues; real-Drive path proven with stubs (folder found / created / unreachable).
- The tests found 2 real bugs in my own code, both fixed: (1) the playbook checker crashed on a retired row instead of reporting it; (2) upkeep logged
  its own changes before the audit compared hashes, so an edit made outside the code went unrecorded - the audit now runs first.
- 3 test expectations were wrong on first run and corrected (repair attempt 1 of 3 each): a department's default stage, the count of mirrors created
  when a retired level turns promising, an over-clever file-order assertion.
- Live proof on the real repo: a dead code reference + a retired concept put into feel.json, and a retired brand name put into a string of
  palace.py -> the test file went 34 passed / 5 failed, Plan Guard RED (naming the line), `python -m whatifs.org.palace` RED (naming both seed faults);
  files restored -> 39/39, GREEN, GREEN.
- Fake rehearsal on the final code: **GREEN** - contract script 21/21 (`palace_health` included), final 18/18; Palace 97 items (92 founding +
  4 characters + the rehearsal's case), writers' playbook 1,745 of 1,800 estimated tokens, recorded in `Palace_Playbooks`.
- Full suite (62 files), ONE uninterrupted run on the final code: **988 passed / 0 failed / 6 skipped** (949 before + the 39 new tests; no existing
  test needed a change, although `palace_health` now runs inside every script-stage contract call of the older tests).
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift.

#### Step 7 TAKEAWAY (also Palace item `b2.takeaway`)
- WORKED: writing the founding knowledge through the SAME gate as runtime knowledge. The `applied_in` rule forced every "this is enforced" claim to
  name code that exists; the gate is exercised by 92 real items before any department uses it.
- WORKED: reading the real output before trusting the rule. The ranking was correct by its own rules and still wrong for the writer; priority and
  addressing fixed it. Do this for every selection or ranking rule in later batches (memo routing, the Council's agenda, the research agenda).
- WORKED: testing the checker against inputs it should never see - that is how the crash on a retired row surfaced.
- WATCH: a few low-priority limits do not fit an 1,800-token playbook (D1 3, D4 4, D12 1, Council 5). Reported by the health check as a note, nothing
  is silent - but the Council (B6) / Librarian (B8) must merge them or the cap for those departments must rise (setting PALACE_PLAYBOOK_TOKENS_BY_DEPT).
- WATCH: an edit made outside the code is recorded only if the next upkeep runs before the next Palace write (the hash is taken after each write).
- WATCH: tool facts expire 60 days and plans 45 days after seeding unless re-validated: B5's research cadence must re-validate them.
- WATCH: the Sheets / Drive path of the Palace is proven with the local store and stubs only (no keys on this laptop, by rule). First real proof =
  the first learning job after the merge; the B10 first-run verification must look at tab `Palace_Items` and at `palace_health` in the Feature_Ledger.
### B1b - Owner decision executed: 4 long videos a month (10 Nov 2026) - ACCEPTED
Not a plan batch: the generated SYSTEM.md from B1 exposed that the ledger said 4 long videos a month while the code allowed 8. The owner was asked
in one line and answered "4 a month". Executed at code-line level the same session (no new research: the decision is the owner's).
- BUILD: `core.DEFAULTS` STANDARD_MAX_LONG_PER_MONTH 8 -> 4, PUBLISH_DAYS Tue,Sat -> Sat (one a week; Saturday was already one of the two days and
  is the Runway day), VIDEOS_PER_MONTH_EST 9 -> 4, new cell V12_FLIPS_DONE. `manage.v12_upgrade` + `V12_FLIPS`: ONE-time move of the live Sheet,
  only for cells still at the old default (an owner-typed value is never touched); called from both setup paths. `governor.long_videos_per_week`.
  Viewer lines in `whatifs/cta.py`: 4 subscribe lines promised "twice a week" -> "every week" (true at any cadence of one a week or more, so no
  runtime substitution and nothing to leak). `caretaker.cadence_words`: the policy-rescue prompt now describes the channel from the settings
  (it said "about 2 long videos + 10-14 Shorts a week").
- Design note: a cadence placeholder filled at use time was considered for the viewer lines and rejected (leak risk into a spoken script, and tests
  compare pool lines verbatim); wording that cannot become false won.
- ENFORCE: gate `governor.can_start_episode` (already existed; now reads 4); new retired rule `old_long_cadence` in `truth.RETIRED` (14 rules) so
  "twice a week" / "8 videos a month" / "2 long videos" fail Plan Guard, the tests and contract `docs_current`; matrix row added; ledger section D updated.
- PROVE: `tests/test_v12_cadence.py` 8 tests, both ways (4th allowed / 5th blocked / cell change lifts it; Sheet move flips old defaults once and
  leaves owner values; no viewer line states a numeric cadence; prompt follows the settings). The new rule caught a 4th "Twice a week" line that a
  case-sensitive search had missed. Expectation updates forced by the decision: test_v94a (at most 8 -> 4), test_hardening (PUBLISH_DAYS),
  test_v91_matrix (V12_FLIPS added to the documented one-time moves), test_v91_insights (see below).
- Full suite (61 files): **949 passed / 0 failed / 6 skipped**. Honest detail: the uninterrupted run was 948 / 1. The 1 = test_v91_insights estimator
  bound (comment-mining share + variety rewrite < Rs 3 per video): the MONTHLY comment-mining money is unchanged (about Rs 6) but is now shared by 4
  videos instead of 9, so the per-video line rose from Rs 0.7 to Rs 1.5. Test now asserts the monthly amount (repair attempt 1 of 3) -> file 9/9.
  No second uninterrupted full run after that one-file test edit. Rehearsal **GREEN** (20 + 18). Plan Guard **GREEN**.
- EFFECT ON MONEY (not measured in production - nothing is live until the final PR): the planner now splits the month over 4-5 weekly slots instead
  of 8-9, so each long video gets a larger share of the cap and extras (Shorts, breakout follow-ups) have more free money. The cap itself is unchanged.
- TAKEAWAY: a decision is only executed when every place that SAYS the old thing is found; registering the old value as a retired concept found one
  the manual search missed. Do this for every future owner decision that replaces something.

### B1 - Truth hygiene (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: there is now ONE current truth, and code refuses anything else - in docs, CLAUDE.md, module docstrings, the build prompt and
every prompt string - on every push (Plan Guard), in the suite, in the rehearsal and on every episode (contract check `docs_current`).

#### Step 1 RESEARCH (7 dated sources; E = measured evidence, O = opinion/practice)
1. E - Gloaguen et al., "Evaluating AGENTS.md" (ETH Zurich / LogicStar), arXiv 2602.11988, 12 Feb 2026 (v3 29 Sep 2026): repository context files do
   NOT generally raise coding-agent success and raise cost > 20%; agents obey what the file says; repo overviews do not help; only non-standard
   practices are worth writing. -> CLAUDE.md must be short, rules only, and never wrong (a wrong line is obeyed).
2. E - Chroma, "Context Rot" (Hong, Troynikov, Huber), Jul 2025, 18 models: reliability falls as input grows; distractors that are topically CLOSE to
   the right answer hurt most. -> an old doc about the same system is the worst kind of distractor; keep history out of what a chat loads.
3. O/official - Anthropic Claude Code memory docs (code.claude.com/docs/en/memory, read 10 Nov 2026): CLAUDE.md is context, not enforcement; target
   under 200 lines; specific + concise is followed more reliably. -> enforcement must live in tests/checks, not in the file's wording.
4. E/practice - Grafana Loki CI "check generated documentation" step: reference docs are generated from code and CI fails when the committed file
   differs. Same idea: Fern "Stopping schema drift" (Aug 2026): derive, don't document. -> SYSTEM.md is generated, drift fails the build.
5. O/practice - Vale prose linter (vale.sh; Fern guide Oct 2026; Grafana writers' toolkit): retired terms are data (existence / substitution rules);
   only zero-false-positive rules get error severity. -> retired concepts as data rules with context exceptions, all at error level.
6. O/practice - ADR immutability (Fowler bliki; Backstage docs): never delete or rewrite an accepted record; mark it superseded and point to the
   replacement. -> ARCHIVE keeps files byte-intact under a HISTORICAL header naming what replaced them.
7. E/practice - ESLint bulk suppressions (eslint.org, Apr 2025) and Notion's ratchet file: legacy violations are baselined by count per file+rule; new
   ones fail at once; stale baselines must be pruned. -> a reviewed baseline for code strings that legitimately name old values (migrations).

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Move + grep" (literal minimum): move files, hand-write SYSTEM.md, one test with a regex list. 2/2/5/2/5 = 16. Weak: SYSTEM.md is stale the day
  after; the list lives in a test the organisation cannot extend; nothing runs outside pytest.
- B "Docs-as-code stack" (research): generated SYSTEM.md + drift test, Vale-style rules as data, ADR-style archive, ratchet baseline. 3/4/4/4/5 = 20.
  Weak: still only a build-time gate; Vale itself would be a new CI dependency (rejected: same rule model in ~100 lines of Python).
- C "Truth Registry" (ORIGINAL): ONE module (`whatifs/truth.py`) is the organisation's single statement of what is current and what is retired:
  retired concepts are data (pattern, allowed context, why, the CURRENT truth that replaced it); current facts are RENDERED from the live code into
  SYSTEM.md (a doc cannot state a number the code does not hold); the same scan runs in four places - Plan Guard (every push), the test suite, the
  rehearsal, and as contract check `docs_current` on every episode (it also reads the CONSTITUTION cell, the one prompt source that changes without a
  merge). Later batches append to the registry (Council retires a concept -> it is banned everywhere on the next run). 4/5/4/4/5 = 22.
- DECISION: C built with B's mechanics (generate-and-diff, rule data, ADR archive, ratchet baseline).

#### Step 3 DESIGN MEMO
- Decision: docs/CURRENT (SYSTEM.md generated by `tools/gen_docs.py`; CONCEPT.md, OWNER_REQUIREMENTS_LEDGER.md, ENFORCEMENT_MATRIX.md,
  PLATFORM_FACTS.md hand-kept) + docs/ARCHIVE (KERNEL, CHANGES, the two old laptop prompts, all v11.1 module docstrings) under a
  "HISTORICAL - DO NOT FOLLOW" header. CLAUDE.md rewritten (< 200 lines, rules only, points only at docs/CURRENT). Every module docstring = one-line
  purpose + pointer. claude-build.yml prompt re-pointed. `whatifs/truth.py` = registry + scanner.
- Why: sources 1-3 (a chat obeys what it reads; near-topic history is the worst distractor; wording is not enforcement), 4 (generated beats written).
- Rejected: Vale binary (new dependency); a `.claude/settings.json` Read-deny on docs/ARCHIVE (would also block the owner's own history look-ups and
  changes how his Claude Code behaves without him asking); deleting history (source 6); a new hand-kept changelog (second source of truth - git + PR
  bodies are the log until the Palace exists in B2).
- Cost: Rs 0 (no model call; the scan takes ~1.5 s once per process, then cached).
- Palace seed items: `handoff_v12/palace_seed/B1.json`.

#### Step 4 BUILD (what changed)
- NEW `whatifs/truth.py`: RETIRED (13 rules, each with the truth that replaced it), BASELINE (2 reviewed entries), `scan`, `docstring_issues`,
  `layout_issues`, `live_prompt_issues` (CONSTITUTION cell), `issues`. Run by hand: `python -m whatifs.truth`.
- NEW `tools/gen_docs.py` -> `docs/CURRENT/SYSTEM.md` (369 lines: facts, how it runs, v12 status, truth rules, 38 checks, 39 key settings, 24 jobs,
  71 tabs, 103 modules). NEW `docs/CURRENT/CONCEPT.md`. Ledger + matrix moved to docs/CURRENT and corrected. PLATFORM_FACTS moved (content unchanged).
- docs/ARCHIVE: KERNEL.md, CHANGES.md, OWNER_LAPTOP_CHANGES.md, PROMPT_LAPTOP_CHANGE.md (header added, text unedited), MODULE_DOCSTRINGS_v11_1.md
  (every old docstring, nothing lost).
- CLAUDE.md rewritten: 64 lines (was 67 lines of v8-v10 history incl. the old caps and "table read" as a keep-rule).
- 101 module docstrings -> one line each. `.github/workflows/claude-build.yml` prompt now reads CLAUDE.md + docs/CURRENT/SYSTEM.md and runs gen_docs.
- Stale statements the scan found INSIDE live code and that are now fixed (settings notes in `whatifs/core.py`, text only, no default changed):
  PUBLISH_DAYS (cited the old cap), BUDGET_FLOOR_INR / BUDGET_CEILING_INR (old-cap history), BRAIN_ON (named the outlier library as the learning-core
  table), CONSTITUTION + MODEL_ROUTES (pointed at the old changelog), PREPROD_ON, SHOW_MODE, FAL_HERO_MODEL, TTS_ENGINE (old version labels).
  Mission Control guide: 2 rule numbers, 1 old changelog pointer, 1 dead test path fixed.

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| No retired concept in current docs, CLAUDE.md, build prompt, docstrings, prompt strings | `truth.scan` | Plan Guard RED; contract `docs_current` FAIL (episode HELD); tests |
| No retired concept in the owner's CONSTITUTION cell (changes without a merge) | `truth.live_prompt_issues` | contract `docs_current` FAIL |
| SYSTEM.md equals the code | `gen_docs.render` / `gen_docs.drift` | `test_system_md_*` (hand edit AND code change without regenerating) |
| docs/ = CURRENT + ARCHIVE only; ARCHIVE files marked; CLAUDE.md <= 200 lines; every named path exists | `truth.layout_issues` | Plan Guard RED; contract; tests |
| Docstring = one line + pointer, no history | `truth.docstring_issues` | Plan Guard RED; contract; tests |
| Old values in code only where reviewed (ratchet) | `truth.BASELINE` | one more hit fails; one fewer fails until pruned |
Matrix row added (`contract:docs_current`, `fn:whatifs.truth.issues`, `fn:tools.plan_guard.main`, `fn:tools.gen_docs.render`); the meta-test covers it.
Rehearsal asserts `docs_current` ran and passed.

#### Step 6 PROVE
- `tests/test_docs_current.py`: 28 tests, every rule proven BOTH ways (13 retired rules each fire on the retired sentence and stay quiet on the true
  one; 6 surfaces - 2 current docs, CLAUDE.md, build prompt, 2 prompt strings - each fail when a retired term is inserted and pass when removed;
  layout, docstrings, baseline ratchet, SYSTEM.md drift x2, contract PASS/FAIL incl. a dirty CONSTITUTION cell, Plan Guard GREEN/RED by subprocess).
- Live proof on the real repo: appended "The monthly cap is Rs 4,700 and the room is the table read." to docs/CURRENT/CONCEPT.md -> the suite file went
  21 passed / 7 failed and Plan Guard went RED naming both rules; file restored -> 28/28 and GREEN.
- Full suite (60 files): **940 passed / 0 failed / 6 skipped**. Honest detail: the one uninterrupted full run was 939 / 1 failed. The 1 =
  `test_v11_stage_e::test_scout_uses_the_current_endpoints_only`, which had been passing only because the OLD docstring of scout.py contained the
  endpoint text (the code builds the URL from a base constant). Test rewritten to judge the code itself (repair attempt 1 of 3) -> file re-run 8/8.
  A second uninterrupted full run after that one-file test edit was not repeated (35 min).
- This full run also closes B0's caveat: every B0-era test passed in one uninterrupted run (incl. test_v11_feel after the particle-seed fix).
- Fake rehearsal: **GREEN** (contract script 20/20 - `docs_current` included - and final 18/18). Plan Guard: **GREEN**.

#### Step 7 TAKEAWAY
- WORKED: generating the doc from the code and then scanning the generated doc found stale statements inside LIVE settings notes that no grep of the
  docs folder could find. Scan what the code says about itself, not just the documents.
- WORKED: the one-line-docstring change exposed a test that was passing on docstring text instead of code. Tests that grep source files can be
  satisfied by comments; prefer asserting on imported values.
- WATCH: rules are line-based with an "unless" context - keep current docs one fact per line or a true sentence can be flagged (or a false one missed).
- WATCH: inline code comments still carry version labels and rule numbers (thousands; declared "history labels" in CLAUDE.md and SYSTEM.md section 4).
  If a future chat is ever seen acting on one, extend `truth.scan` to comments.

### B0 - Bootstrap & verify (10 Nov 2026) - ACCEPTED
- Laptop (Windows 11): installed Git 2.56, Python 3.12.10, ffmpeg/ffprobe 9.0.2 via winget. venv at `REALITY_ENGINE_HANDOFF/.venv` with the
  requirements.txt pins (numpy 2.0.2, opencv-headless 4.14, pillow 12.3, requests, pyyaml) + tzdata, soundfile, cryptography (Checks installs these too).
  Not installed: kokoro, transformers (no test needed them).
- Repo cloned, branch `v12-organisation` from main, commit "v11.1 baseline (from handoff)" pushed.
- Files only on main (kept, untouched): `.keepalive`, `PRIVACY.md`, `README.md`. 35 files only in the snapshot (v10.2-v11.1 work) are now on the branch.
- Plan Guard GREEN; full suite (59 files) 912 passed / 0 failed / 6 skipped; fake rehearsal GREEN (script 19/19, final 18/18).
- How 912/0 was reached: first run 897 / 15 (9 = Windows ffmpeg path in `whatifs/reels.py`, fixed with 2 nt-only lines; 5 = `cryptography` missing in
  the venv; 2 = no DejaVu font on Windows, fonts copied to the path the code looks for). Second run 911 / 1: `test_v11_feel` particle test,
  intermittent - a REAL v11.1 bug (`render.Particles` seeded from Python's per-process `hash()`), fixed with an md5 seed. Confirmed by B1's full run.
- Code changes in B0 (both protected-area; say so in the final PR): `whatifs/reels.py` (Windows-only path escaping), `whatifs/render.py`
  (deterministic particle seed).

## PROTECTED-AREA FILES TOUCHED SO FAR (list them in the final PR)
- B2: `whatifs/core.py` (3 tabs + 7 settings appended; nothing existing changed), `whatifs/manage.py` (2 calls: `palace.daily` in the learning job,
  `palace.maintain` in Setup), `whatifs/publish.py` (`drive_upload` gained an optional `parent`; behaviour without it is unchanged). Also touched,
  not on the protected list: `whatifs/contract.py` (check `palace_health` added), `whatifs/truth.py` + `tools/gen_docs.py` (walk sub-packages),
  `tools/rehearsal.py` (Palace assertions).
- B0: `whatifs/reels.py`, `whatifs/render.py`.
- B1b: `whatifs/core.py` (3 defaults changed: STANDARD_MAX_LONG_PER_MONTH, PUBLISH_DAYS, VIDEOS_PER_MONTH_EST; 1 new cell), `whatifs/manage.py`
  (`v12_upgrade` added + 2 calls), `whatifs/governor.py` (`long_videos_per_week` added; no existing rule changed).
- B1: `tools/plan_guard.py` (truth hook added), `whatifs/contract.py` (check `docs_current` added; no existing check changed), `whatifs/core.py`
  (10 settings NOTES reworded, no default value changed), `tools/repair.py` / `whatifs/governor.py` / `whatifs/publish.py` / `whatifs/episode.py` /
  `whatifs/manage.py` and the other protected modules: docstring line only.

## OPEN ISSUES
1. (D6/D8, for B6-B7) Rain particles ("office" world) can read as a still for some seeds (aliveness 0.0 seen). Now deterministic, and seed 7 passes,
   but the particle layer has no guarantee per seed. Proper fix: after rendering, measure aliveness and re-seed/boost when below the bar (needs an
   enforcement check + failing test).
2. (B1b follow-up, low, for B9) In a month with 5 Saturdays one week has no long video (cap 4). By design today; D1 planning (B9) may choose which
   Saturday to skip or spread differently. `DIGEST_DAYS` (owner digests) still Tue,Sat,Sun - unrelated to publishing, left as is.
3. (NEW, low) `mission_control/worker.js` line 27 comment still says fixes were "recorded in CHANGES.md". Left alone on purpose: it is a comment in the
   deployed Worker file, and JS comments are outside the scan. Fix it the next time the Worker is changed anyway.
4. (laptop) Test temp dirs `mt_*` accumulate in `%TEMP%`; automatic cleanup of that shared folder was blocked by the app's safety rule. Disk free
   333 GB, so no risk; delete by hand only if space ever gets tight.
5. (handoff folder, outside git) The handoff `CLAUDE.md` still says the repo's own CLAUDE.md "is historical until batch B1 rewrites it". B1 has
   rewritten it; the sentence is now simply spent. No action needed.
6. (B2 -> B6 / B8) A few low-priority limits do not fit an 1,800-token playbook: D1 3, D4 4, D12 1, Council 5 (lowest priority first out; the health
   check reports it as a note). Fix belongs to the Council / Librarian: merge overlapping limits, or raise the cap for those departments.
7. (B2 -> B8) An edit of the `Palace_Items` tab made outside the code is recorded as `external_edit` only when upkeep runs before the next Palace
   write. Served content is safe either way (the guard re-checks every row); only the audit entry can be missed.
8. (B2 -> B5) Founding tool facts expire 60 days, and the two plans 45 days, after they are first written to the live Sheet (the clock starts at
   seeding, not at the date of the research) unless re-validated. By design; B5's research cadence has to re-validate or replace them.
9. (B2 -> B10) The Palace's real Google Sheets / Drive path is proven with the local store and stubs only (no keys on this laptop, by rule). The
   first learning job after the merge writes 92 rows in one append and makes no Drive call (founding bodies resolve from the repo). B10's first-run
   verification must check tab `Palace_Items` and `palace_health` in `Feature_Ledger`.
10. (B2 -> B3, small) `whatifs/org/palace.py` is not yet on the `tools/repair.py` PROTECTED list. In practice an automatic repair of it is never
   auto-merged (the file contains network and file-removal calls, which the repair job treats as risky), but the list should say so explicitly.
11. (B2, low) `Palace_Versions` numbers come from the last row + 1: two jobs writing in the same second could reuse a number (timestamp and hash
   still tell them apart; the tick's concurrency group makes it unlikely).

## HOW TO RUN ON THIS LAPTOP (the Bash tool = Git Bash works; from `reality-engine/`)
- Env: `export PYTHONUTF8=1 WI_FAKE=1 PY=../.venv/Scripts/python.exe`
- Suite: `bash ../shim/runall.sh . <outdir outside repo>` (~35 min; run it in the background). Some files: `bash ../shim/runseq.sh . <outdir> test_a test_b`.
- Rehearsal: `WI_SMALL=1 WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.cli rehearsal > <log outside repo>` (~3 min); delete the work dir after.
- Plan Guard: `../.venv/Scripts/python.exe tools/plan_guard.py`. Truth only: `../.venv/Scripts/python.exe -m whatifs.truth`.
- Palace only (seeds a local store, prints GREEN / RED + every problem): `WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.org.palace`.
- After ANY change to a seed file in `whatifs/org/seed/`: run that Palace command, then `tools/gen_docs.py` (SYSTEM.md prints the seed counts).
- Stopping a background suite run: stopping the task does NOT stop the runner loop on Windows. Also stop the `bash.exe` processes whose command line
  contains `runall.sh` / `runseq.sh` and the `python.exe` running `minitest.py`, or tests keep starting.
- After ANY change to settings, checks, tabs, workflows or a module docstring: `../.venv/Scripts/python.exe tools/gen_docs.py` and commit SYSTEM.md.
- Plan Guard flags one specific word in every text file and several words in file names (see `tools/plan_guard.py` BANNED_NAME_WORDS) - keep
  BUILD_STATE and seed files clear of them.
- git: `core.autocrlf=false` (keep LF); write files with LF. Commit identity Rahul4869 (noreply address); push with
  `GIT_TERMINAL_PROMPT=1 GCM_INTERACTIVE=always git push` (credentials are saved).

## BATCH LOG
| Batch | Status | Suite | Rehearsal | Notes |
|---|---|---|---|---|
| B0 | done 10 Nov 2026 | 912 / 0 / 6 skipped | GREEN (19 + 18) | 2 small fixes (Windows ffmpeg path; particle seed determinism) |
| B1 | done 10 Nov 2026 | 940 / 0 / 6 skipped | GREEN (20 + 18) | Truth Registry; docs/CURRENT + ARCHIVE; generated SYSTEM.md; check `docs_current` (38 hard checks now) |
| B1b | done 10 Nov 2026 | 949 / 0 / 6 skipped | GREEN (20 + 18) | Owner decision "4 a month" executed: cap 4, weekly Saturday, one-time Sheet move, truthful viewer lines, retired rule |
| B2 | done 10 Nov 2026 | 988 / 0 / 6 skipped | GREEN (21 + 18) | Knowledge Palace core: 92 founding items, write gate, life cycle with authority, guarded playbooks, check `palace_health` (39 hard checks now) |
| B3 | next | | | Memo system + Department contract |
