# BUILD_STATE - Reality Engine v12 "Organisation"
Updated: 11 Nov 2026 (B5 ACCEPTED). Branch: `v12-organisation` (never main). Resume: read this file + `git log -5`.

## STANDING RULES ADDED DURING THE BUILD (rule 1: owner approved, 10 Nov 2026; rules 2-4: B0b, they follow from his rule "hard enforcement or it does not exist")
1. A batch is ACCEPTED only when its FINAL commit is green in GitHub's own `Checks` workflow (Ubuntu, real pytest, then the fake rehearsal) - the
   laptop runs (Windows, stand-in test runner) are necessary, not sufficient. Read it before writing "ACCEPTED" and record the run number in the batch log.
   How to read it - NO sign-in needed since B0b: open https://github.com/Rahul4869/reality-engine/actions?query=branch%3Av12-organisation in the
   browser pane and open the run. The section "Annotations" names every failed test, every skipped test, every failed contract check with its reason
   and the episode ids; when green it shows the totals ("N passed") and the rehearsal's episode id. The job summary on the same page has the full list
   (annotations are capped at 10 a step). A run takes about 30 minutes; do not wait idle for it - finish the write-up, then read it.
2. (B0b) Before a batch is accepted, run the sweep (`tools/sweep.py`, recipe under HOW TO RUN): the fake pipeline is seeded by the episode id, so one
   green rehearsal proves one id. A red rehearsal or a red test on GitHub is reproduced with the episode id its annotation prints
   (`--mode rehearsal --ids <id>`), traced to its cause and fixed - never re-run until it passes.
3. (B0b) Nothing may be built without being wired and no test may skip on GitHub: Plan Guard, the tests and check `docs_current` refuse a Settings cell
   that no code reads, a Sheet tab that no code uses and a function that no production code calls. The three lists of old cases in `whatifs/truth.py`
   (UNREAD_SETTINGS, UNUSED_TABS, UNWIRED_FUNCTIONS) may only shrink: wiring one means deleting its entry and lowering the limit next to the list.
4. (B0b) Every workflow installs a package that `requirements.txt` pins with exactly those bounds (a test fails otherwise). To move to a new major
   version of a library, change `requirements.txt` AND the workflows in one commit and re-verify the reference frames (`tests/golden_frames.py`).

## NEXT
**B6 is SPLIT (token discipline rule 6, decided 11 Nov 2026 at the start of B6): B6 has two large halves that each need the full seven-step loop,
the 40-minute suite, the sweep and a GitHub run - one window cannot hold both.**
- **B6a - Creative departments (D4/D5/D6/D7)** - IN PROGRESS (this session): the Palace playbook goes INTO the creative model prompts and is proven
  there (`palace_injected`), the models cite the items they used and code verifies each citation (`palace_cited`), world canon (the show's living
  bible) is written after every episode and reaches the next writer brief (`canon_in_brief`), creative runs emit creative memos to the Council.
- **B6b - The Council (C)** - next: gathers open research / assessment / creative / owner / performance / problem memos; diverge -> blind
  cross-family jury -> converge -> decision memo + tickets; owner cards only above thresholds; check `council_held`. Effort: High.
Original B6 scope: 01 sections 2 (D4-D7, C), 3, 5, 7 `council_held`, `canon_in_brief`, `palace_injected`, `palace_cited`; 03 "B6".
What B5 leaves ready for B6b (use it, do not rebuild it):
- Assessment memos (D3 -> C) already carry everything a decision needs: the verdict (accept / test / reject, computed by code), six scores, the
  family checklist, the research memo's evidence, its kind and `palace_ref` (a re-validation names the Palace item), and the pre-registered
  predictions (in the research memo body: action index, metric, direction, horizon). They wait SILENTLY at the owner's level until C is wired: the
  Council's first run must take up every assessment memo at level 2 (and research memos the watchdog escalated after void Board sessions - the
  Board is no longer their holder). `board.assessment_issues(m)` tells whether an assessment can be trusted.
- How the Council turns a verdict into a ticket: accept (a fact) -> lever A (a Palace item; a re-validation = accept the `proposed` item or
  supersede the expiring one named in `palace_ref`), test -> lever C (experiment: `rule`, `metric` = the prediction's metric, `source_url` = the memo's
  best evidence url), reject -> no ticket, the decision memo cites the assessment. Palace item `b4.how_to_write_a_ticket`.
- The Board can judge creative memos too: `board.assess` takes research memos today; a creative memo has no sources, so B6 decides whether D3 also
  judges creative memos (schemas: creative_memo is resolved by decision_memo OR assessment_memo) or the Council's own blind jury does.
- `board.JUDGES`, `board._parse`, `scores_from` are reusable for the Council's blind cross-family jury (strong chains `board_g` / `board_c`).
What B6a leaves ready for B6b:
- Creative memos (D4 showrunner / bible, D5 packager, D6 director) wait SILENTLY at the owner's level (owner_visible False) like the assessment
  memos: body {idea, kind (idea / experiment / bank / world_building), rationale}, already distinct (same-idea guard). A creative memo has no
  sources, so the Board cannot score its evidence: decide in B6b whether the Council's own blind jury judges ideas (recommended: ideas need taste,
  the Board's checklist is built for evidence) - and remember b5.facts_accept_ideas_test: an idea is at most a TEST (lever C), never "accepted".
- World-building decisions become canon through a ticket of lever A (kind world_canon, accepted by the Council); case records stay code-written
  and are accepted only on air (D9) - the Council never edits what aired.
- The Council's playbook (C) leaves 5 limits out at 1,800 tokens: give C its own cap (as D4 got 2,400) or narrow the audience of items, before it
  runs. C's runs that call a model should be a B6a-style prompt spec (registry.PROMPT) so its decisions cite what they used.
- D7 Sound has NO model call in its run (voice = TTS, sound = code), so it cannot cite or propose; its creative input comes through the bible.
  Open question for later batches, not a gap of B6a.
- Totals other tests and the rehearsal print: 47 hard checks (28 script + 19 final), 132 founding Palace items (133 with `b6a.takeaway`), 10 of 15
  departments wired (pending: D0, D1, D11, C, L), 41 levers.
- New org modules go on `tools/repair.py` PROTECTED first. Every function B6b adds must be called by production code (Plan Guard); a hook with a
  common name gets a test that runs the real job.
- Acceptance of B6b includes standing rules 1 and 2 (sweep on a frozen copy, final commit green on GitHub).

## DONE
### B6a - Creative departments D4/D5/D6/D7 (11 Nov 2026) - IN PROGRESS
#### Step 1 RESEARCH (13 sources, 12 of them dated; E = measured evidence, O = opinion / practice / vendor documentation)
1. E - Wallat, Heuss, de Rijke, Anand, "Correctness is not Faithfulness in RAG Attributions", arXiv 2412.18004 (Dec 2024; ICTIR 2025),
   https://arxiv.org/abs/2412.18004 : a citation can be CORRECT (the source supports the claim) while the model never used it ("post-rationalised");
   up to 57% of citations unfaithful in their adversarial tests (Command-R+). -> a self-reported `applied_items` list proves nothing by itself.
2. E - Saxena et al., "Generation-Time vs. Post-hoc Citation", arXiv 2509.21557 (Sep 2025; NeurIPS 2025 workshop), https://arxiv.org/abs/2509.21557 :
   citing while generating (G-Cite) wins on precision, citing afterwards (P-Cite) on coverage; the quality of what was retrieved drives attribution
   quality in both. -> cite at generation time (precision) AND check afterwards by code (coverage); keep the injected block small and relevant.
3. O (vendor) - Anthropic, "Introducing Citations on the Anthropic API" (23 Jan 2025), https://www.anthropic.com/news/introducing-citations-api :
   citations point at quoted spans of the given documents, which code can match back; internal evals: up to 15% better recall than custom
   prompting. -> a citation should carry a QUOTE that code can find, not only an id.
4. E - Liu et al., "Lost in the Middle", TACL 12 (2024) 157-173, https://aclanthology.org/2024.tacl-1.9/ : U-shaped accuracy - information at the
   start or end of the context is used, in the middle it is lost. -> the playbook and the canon go at the START (cached system layer), not mid-brief.
5. E - Hong, Troynikov, Huber (Chroma), "Context Rot" (14 Jul 2025), https://research.trychroma.com/context-rot : 18 models get less reliable as
   input grows, and distractors hurt more as length grows. -> bounded blocks; canon filtered to what is relevant for THIS case, not the whole bible.
6. E - "How Many Instructions Can LLMs Follow at Once?" (IFScale), arXiv 2507.11538 (Jul 2025; NeurIPS 2025), https://arxiv.org/abs/2507.11538 :
   the best frontier models reach about 68% at 500 simultaneous instructions; earlier instructions are favoured. -> caps on playbook size stay; limits first.
7. E - Li et al., "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs", arXiv 2402.10962 (Feb 2024; COLM 2024),
   https://arxiv.org/abs/2402.10962 : significant persona drift within 8 rounds. -> character canon must be re-stated in EVERY creative call of the
   run (the tap re-injects per call), not once at the top of a long chain.
8. E - ConStory-Bench, arXiv 2603.05890 (Mar 2026; ACL Findings 2026), https://arxiv.org/abs/2603.05890 : in long generated stories consistency
   errors are most common in FACTUAL and TEMPORAL dimensions, mostly mid-narrative; an automated checker grounds each judgment in explicit text.
   -> canon items must be concrete facts (who won, which prototype number, what was promised next) so code can check them.
9. E - "Finding Flawed Fictions" (FlawedFictions), arXiv 2504.11900 (Apr 2025; COLM 2025), https://arxiv.org/abs/2504.11900 :
   LLM-written stories carry 50-100% more plot holes than human originals; detection gets worse with length. -> continuity must be kept by code
   records, not trusted to the model's memory.
10. E - Park et al., "Generative Agents", UIST 2023, arXiv 2304.03442, https://arxiv.org/abs/2304.03442 : ablations - observation (memory),
    reflection and planning EACH contribute critically to believability. -> an episode record (memory) + a distilled canon line (reflection) both.
11. E - Doshi & Hauser, "Generative AI enhances individual creativity but reduces the collective diversity of novel content", Science Advances
    10(28), 12 Jul 2024, https://doi.org/10.1126/sciadv.adn5290 : AI ideas made single stories better but the set MORE ALIKE. -> creative memos must
    be checked for sameness against earlier ones by code; the Council (B6b) must see diverse options, not 10 copies.
12. E (survey) - University of Essex, parasocial study (23 May 2024), https://www.essex.ac.uk/news/2024/05/23/watching-youtube-cheers-people-up-more-than-meeting-casual-friends :
    52% of 1,080+ participants report a strong parasocial relationship with a YouTuber; classic TV research: bonds grow with REPEATED exposure and
    self-address. Backed by our own 9 Nov concept research (04 digest: winners share recurring characters and lore). -> canon is a breakout lever.
13. O (practice) - Final Draft, "10 Easy Steps to Developing Your TV Show Bible" (blog, undated),
    https://www.finaldraft.com/blog/10-easy-steps-to-developing-your-tv-show-bible , and Fiveable "running gags" (TV studies glossary): the bible is the
    archival record every incoming writer reads; running gags come back across the series and change a little each time (too much change and the
    audience stops recognising them). -> the canon keeps each gag's history; the brief asks for a VARIATION, never a repeat.
Plus official pricing: Anthropic prompt caching (docs, read 11 Nov 2026), https://platform.claude.com/docs/en/build-with-claude/prompt-caching :
cache reads 0.1x input (0.05x / 0.025x on the newest models), writes 1.25x -> a playbook in the cached system layer costs almost nothing per call.
Owner's words re-read for B6a: 02 #2 ("the writer room also should learn from researcher and R&D to enhance their performance everytime"), #6 (every
output a BREAKOUT), #8 (personify, attachment, characters to love), #12/#14/#15 (hard-enforced to the line, executed at code level), B (characters to
fall in love with, return factor, no slop, no repetition).

What the code does TODAY (read before designing, 11 Nov): all 15 departments run in "brief" mode - the playbook is "handed over" (`brief.take()`)
but `room.run_room`, `room.package` and `room.plan_shots` never read it, so NO Palace knowledge reaches any creative model call; and with
PREPROD_ON = TRUE (the default) the script is written in pre-production by `preview.run` OUTSIDE any department run, so production's D4 run only
adopts a finished draft. No world_canon item exists (0 of 126 founding items). The runner's prompt mode (the tap in `models.ask` puts the playbook
into the cached system layer and counts the calls) exists since B3 but no department uses it.

#### Step 2 CREATIVITY (6 designs + 1 parked; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A. Paste the playbook into the writer brief by hand; models list the ids they used; checks count the ids. 2/1/5/3/5. Rejected: a self-reported
  list proves nothing (research 1: up to 57% post-rationalised), and it reaches one call of one department.
- B. ONE DOORWAY IN, ONE DOORWAY OUT, QUOTE-ANCHORED CITATIONS: D4/D5/D6 switch to prompt mode for their NAMED creative calls (D4: scout,
  showrunner, bible, writer, rewrite, punchup, memo; D5: packager; D6: director) - never the judges, never the mechanical passes; the playbook sits at
  the START of the cached system layer (research 4, official caching price). A new reply tap at the same doorway collects every reply's
  `applied_items` [{id, where}] and strips it before the caller sees it. Code verifies each citation: the id was in the injected playbook, and the
  `where` quote (4-30 words) is found in the run's FINAL output (tolerant match: exact, or 80% of its words in order inside a short window). Only
  verified citations count as applied (applied_count, later D10 outcome attribution); limits are not citable (they always apply). 4/5/4/4/5.
- C. Post-hoc citation pass: after the run a model maps output lines to playbook items. 3/3/3/3/5. Rejected: one extra paid call per run; the mapper
  can rationalise the same way (research 1, 2); a cheap mapper would be a cheap model judging (rule 9).
- D. Canon as its own block (`canon.py` text pasted into the writer brief). 3/3/5/3/5. Rejected: a second doorway and a second id space; showrunner,
  bible, packager and director would each need it pasted by hand. Canon becomes Palace items (kind world_canon) in a RESERVED CANON LANE of the same
  playbook instead (limits, then canon, then proven > accepted > testing), bounded by PALACE_CANON_SHARE.
- E. ORIGINAL - CONTINUITY DEBTS: the canon is a ledger WRITTEN BY CODE from the show's own records after every D4 write (case, charge, verdict
  winner + style + deciding detail, witness twist, Grimm's prototype, the stinger's promise of the next case) - concrete factual / temporal facts, the
  kind long stories get wrong (research 8, 9). A case record becomes canon only when the platform confirms the upload ("what aired"; D9 holds the
  video id - the only status move D9 may make). The newest aired case is a MUST-CITE item for D4: the script must call back to it in at least one
  line that code finds IN THE SCRIPT (not in the notes). Repeated exposure is what builds attachment (research 12, 13) - enforced at line level and
  verified like any citation, at zero extra cost. 5/5/5/4/5.
- F. ORIGINAL - SAME-IDEA GUARD ON CREATIVE MEMOS: the showrunner, bible, packager and director may add ONE `proposal` (idea / experiment / bank /
  world_building) inside the call they already make (no extra cost); code keeps at most CREATIVE_MEMO_MAX_PER_RUN per run, validates it as a
  creative_memo to the Council and DROPS one whose word set overlaps an earlier creative memo by CREATIVE_MEMO_SAME_MAX or more (homogenisation,
  research 11) - the Council (B6b) gets distinct options, not ten copies. 4/4/5/4/5.
- G. ORIGINAL, PARKED for B8 - counterfactual ablation: re-run one creative call WITHOUT the playbook and diff the outputs to measure whether the
  knowledge changes the work causally. The most honest measure, but one extra strong call per test: it belongs to D10 as an experiment arm.
CHOSEN: B + E + F, plus the draft fix (pre-production writing runs as a D4 department run and production adopts it with proof).

#### Step 3 DESIGN MEMO
Decision: knowledge enters a creative model through ONE doorway (the ask tap) and the proof of use leaves through ONE doorway (the reply tap);
proof = a quote code can find, never a list the model typed. The show's canon is code-written history in the same Palace, served in its own lane,
accepted only on air, and the newest case is a debt the next script must pay in a line code finds.
- Runner (`whatifs/org/runner.py`): prompt mode adds CITE_RULE (the JSON key `applied_items`, and `proposal` for the proposing tasks) to the
  injected block; records WHICH tasks carried it; the reply tap collects citations + proposals per run; ACT verifies (id in playbook, quote in the
  final output) -> ACT receipt: `injected_tasks`, `cited`, `applied` (verified only), `unverified`, `ghost`; a wrapped run's citations count too.
  `work(..., adopt=<draft session>)`: production's D4 write adopts a pre-production draft only with the draft run's proof (a D4 `draft` run, ok,
  prompt mode, injected) - its verified citations carry over, re-verified against the adopted text.
- Registry: D4/D5/D6 inject "prompt" with `inject_tasks` and `key_task` (writer / packager / director) and `propose_tasks`; new D4 call site
  `whatifs/preview.py` "draft"; owners of the three new checks.
- Palace (`palace.py`): canon lane with PALACE_CANON_SHARE (default 0.25 of the cap) for departments addressed by canon; kind rule: world_canon
  `proposed -> accepted` by D9 only with a "show record" evidence (what aired); D9 may make no other move.
- Canon (`whatifs/org/canon.py`, new, PROTECTED): `record(ep, room)` after D4 write (proposed case record, key `canon|case|<ep>`, derived from
  the D4 session); `on_air(ep, video_id)` after the upload is verified; `required(...)` (cast canon + the newest aired case at that time);
  `episode_issues(ep)` for the check. Cast canon = 4 founding items from `show.CHARACTERS` (seed `canon.json`; a test keeps them equal to the code).
- Creative memos: validated + same-idea guard in the runner's EMIT for D4-D7 (`creative_memo` to C; it waits silently at the owner level until
  B6b wires the Council - the B5 pattern for assessment memos).
- Checks (script gate, 47 hard checks): `palace_injected` (each creative run of the episode - D4 write or its adopted draft, D5 package, D6 plan -
  ran in prompt mode, its key task carried the playbook, the playbook text is stored), `palace_cited` (each of those runs has >= 1 verified citation
  when its playbook had a citable item; unverified / ghost shown), `canon_in_brief` (D4's playbook held every required canon item; with
  CANON_CALLBACK_ON and an aired earlier case, the newest case is cited with a quote found in the SCRIPT; this episode's case record exists).
  NA when the organisation or ORG_PROMPT_INJECT is off, or no creative run is recorded.
- Settings (safe defaults): ORG_PROMPT_INJECT TRUE, PALACE_CANON_SHARE 0.25, CANON_CALLBACK_ON TRUE, CREATIVE_MEMO_MAX_PER_RUN 1,
  CREATIVE_MEMO_SAME_MAX 0.5, PALACE_PROMPT_EST_INR 8 (counted in the episode estimate).
- Cost: no new paid call. Extra input: about 1,900 tokens on about 12 creative calls per long video (cached on the packed calls: writer, rewrite,
  punchup, director), plus about 100 output tokens per call for the citations: estimated Rs 4-8 a video, Rs 16-32 a month at 4 long videos
  (PALACE_PROMPT_EST_INR = 8 in the estimate). Off switch: ORG_PROMPT_INJECT = FALSE (the creative runs go back to brief mode; the three checks say NA).
- Rejected: A, C, D (reasons above); G parked for B8. Risks to watch: a rewrite pass may edit away a cited line (only verified citations count; a
  run with none fails); a draft written before the previous episode aired cannot cite it (canon_in_brief judges what was aired at writing time).

#### Step 4 BUILD (what changed; commits 52d9fd4 + 3459c44)
- `whatifs/models.py`: a second doorway, REPLY_TAPS / `_rtap`, on every JSON reply (fake path, real path, batch path); the fake path runs
  `fakes.fake_cite` (a compliant offline model: cites the first playbook line and the one closest to what it wrote, pays every MUST CITE debt with
  a line in the narration, proposes once when invited).
- `whatifs/org/cite.py` (new, PROTECTED): RULE / MUST / PROPOSE texts, `block`, `tokens`, `flat`, `found` (exact, or 80% of the quote's words in
  order inside a short window), `verify` (verified / unverified / ghost / limits), `proposals_to_memos` (schema, kinds, same-idea guard, cap, silent
  to the owner), `creative_runs` (an adopted draft is judged by its D4 draft run), `episode_issues` for palace_injected / palace_cited.
- `whatifs/org/canon.py` (new, PROTECTED): `facts` / `summary` / `record` (D4's case record, PROPOSED), `on_air` (D9: aired tag + accepted),
  `newest_case`, `required`, `must_cite`, `topic_words` / `names_case` (a callback line must name its case), `ensure_cast`, `episode_issues`.
- `whatifs/org/runner.py`: mode per trigger (`registry.inject(dept, trigger)`), B6a spec only for the creative runs, the tap puts block text at the
  START of the cached global layer (`Packed.of(...).with_global`), `_reply_tap`, ACT verification + receipt fields (`injected_tasks`, `cited`,
  `citable`, `unverified`, `ghost`, `citations`, `adopted`, `legacy_draft`), citation measures in the takeaway, proposals -> creative memos in
  EMIT, `work(adopt=, legacy=)`, `_adoptable`, `last_session`, `ensure_cast` before a creative playbook is built.
- `whatifs/org/registry.py`: PROMPT (D4 write + draft, D5 package, D6 plan: tasks, key, propose, must), CREATIVE_RUNS, `prompt_spec`,
  `prompted(dept)`, D4 call site `whatifs/preview.py` "draft", data_issues refuses a prompt spec that points nowhere, owners of the 3 checks.
- `whatifs/org/palace.py`: lanes 0 limits / 1 canon / 2-4 knowledge, canon spends `canon_tokens()` ON TOP of the cap, `aired(r)`, KIND_MOVES
  (D9: world_canon proposed -> accepted, only on a show record), `sync_canon` never rewrites a case and tags older cases with their air time.
- `whatifs/org/execute.py`: a knowledge lever of D4/D5/D6 needs a CITED use (`registry.prompted`); code-only runs neither prove nor use the window.
- `whatifs/episode.py`: D4 write adopts with `adopt=` / `legacy=`, `canon.record` after D4 write, `canon.on_air` after the upload.
- `whatifs/preview.py`: the writing is a D4 "draft" run (room carries `org_session`); `take_approved` supersedes an automatic draft written
  without the Palace, keeps an owner-approved one (`_legacy_draft`, judged as written before B6a).
- `whatifs/contract.py`: checks palace_injected, palace_cited, canon_in_brief (script gate; 47 hard checks: 28 script + 19 final).
- `whatifs/governor.py` + `costguard.py`: `palace_prompt_inr()` in every estimate. `whatifs/manage.py`: `v12b6a_upgrade` (one-time move).
- `whatifs/core.py`: 7 cells - ORG_PROMPT_INJECT TRUE, PALACE_CANON_TOKENS 700, CANON_CALLBACK_ON TRUE, CREATIVE_MEMO_MAX_PER_RUN 1,
  CREATIVE_MEMO_SAME_MAX 0.5, PALACE_PROMPT_EST_INR 10, V12B6A_FLIPS_DONE; default of PALACE_PLAYBOOK_TOKENS_BY_DEPT = {"D4": 2400}.
- `tools/rehearsal.py`: B6a block (3 checks PASS, every creative run prompt-mode with a verified citation, the case on air, a distinct creative
  memo, the next draft's must-cite paid in its own script) + a next shot plan that proves the B4 knowledge lever by a cited use.
- Changed against the design memo while building, and why:
  (1) cast canon: B2 already mirrors the character bible daily (`palace.sync_canon`, from the Characters tab the owner can edit) - reused, no seed
  file (it would have doubled 4 items in every creative playbook); case key = the mirror's `canon:case:<ep>`.
  (2) canon budget instead of a share: with a share the canon pushed 2 more of the owner's limits out of the writer's playbook (measured 4 -> 6).
  (3) the writer's cap: at 1,800 tokens 4 limits ALREADY did not fit before B6a (his Soft Respawn / Zuni HR inspiration, "cheap long videos are
  built to break out too", the hard gates, the parked concept) - now that the playbook really reaches the writer, the cap moves to 2,400 once
  (measured: 0 left out). C still leaves 5 out: B6b.
  (4) the callback must NAME its case (found by a test: a model could cite the case id with any line). (5) creative memos silent to the owner
  (found by a test). (6) the engine needs a cited use for D4/D5/D6 knowledge levers (the spec's lever A rule, now possible).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken; each proven both ways in tests/test_v12_creative.py, 26 tests)
| Rule | Executing code | Fails when broken |
|---|---|---|
| The playbook is inside the key creative calls (never judges / mechanical passes) | `runner._ask_tap`, `cite.block`, `registry.prompt_spec` | `palace_injected` (script gate); runner breach "no model call carried the playbook" |
| Knowledge counts only with a quote found in the output | `runner._reply_tap`, `models._rtap`, `cite.verify`, `cite.found` | `palace_cited`; the REAL reply path of models.ask is run in a test |
| A draft is adopted only with proof | `runner._adoptable`, `preview.take_approved` | runner breach; `palace_injected` judges the draft run; the REAL pre-production job is run in a test |
| Canon written by code, canon only on air | `canon.record`, `canon.on_air`, `palace.KIND_MOVES` | `canon_in_brief` "no case record"; PalaceError for any other D9 move |
| Continuity debt paid in the final script, naming the case | `canon.must_cite`, `canon.names_case`, `cite.MUST` | `canon_in_brief` (not cited / not in the final script / does not name the case / playbook lacked canon) |
| Canon never pushes out a limit; the owner's limits fit the writer | `palace.canon_tokens`, `manage.v12b6a_upgrade` | `palace_health` notes; canon-budget and one-time-move tests |
| Distinct creative memos to the Council | `cite.proposals_to_memos` | memo tests; the rehearsal asserts distinct ideas |
| A knowledge lever of a creative department is verified by a cited use | `execute._verify_knowledge`, `registry.prompted` | `lever_verified`; engine test; the rehearsal |
| Paid inside the Rs 5,000 | `governor.palace_prompt_inr`, `costguard.estimate_lines` | estimate test |
Matrix: 7 rows in docs/CURRENT/ENFORCEMENT_MATRIX.md (meta-test `tests/test_v111_enforce.py`). Founding items: b6a.quote_anchored_citations,
b6a.knowledge_at_the_start, b6a.restate_every_call, b6a.canon_by_code, b6a.continuity_debt, b6a.distinct_ideas (132 founding items; Palace GREEN).

### B5 - R&D + Review Board (11 Nov 2026) - ACCEPTED (final code commit a1c5204 GREEN in GitHub run 67; sweep 58 of 58 green)

#### Step 1 RESEARCH (12 dated sources; E = measured evidence, O = opinion / practice / vendor documentation)
Honest note: for the arXiv papers the abstract page was read, not the full paper; 6 and 11 are quoted from a search summary (not opened).
1. E - Rao, Wong, Callison-Burch, "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents", arXiv 2604.03173,
   3 Apr 2026: 3-13% of citation URLs are hallucinated (never existed), 5-18% do not resolve; deep research agents cite MORE and hallucinate MORE;
   a liveness check given to the model cut non-resolving URLs 6-79x to under 1%. -> a source counts only if the SEARCH TOOL returned it (never a URL
   the model typed) and it answers a liveness check; a phantom source is dropped and counted against the memo.
2. E - Onweller et al., "Cited but Not Verified", arXiv 2605.06635, 7 May 2026: frontier deep-research agents keep link validity above 94% and
   relevance above 80% but reach only 39-77% factual accuracy; accuracy falls about 42% as tool calls grow from 2 to 150. -> a valid link is not
   support: the evidence a memo carries is the tool's own quoted text, the jury checks "does the finding follow from the quote", and each question
   gets a SMALL bounded search (max_uses), never an open-ended agent loop.
3. E - Awuni et al., "Who Judges Matters: Family-Conditioned Preference in LLM-as-Judge Panels", arXiv 2609.17857, 15 Sep 2026 (9,312 judgments,
   4 families): every family prefers its own family by 3.4-8.4 points; 55.4% of AB/BA pairs REVERSE with the order; panel composition changes 18.5% of
   outcomes. -> the jury is balanced by FAMILY (mean of family means, not of judges), every judge sees two orders, and the family that did not
   write the memo must clear the bar by itself before anything is accepted.
4. E - Verga et al. (Cohere), "Replacing Judges with Juries" (PoLL), arXiv 2404.18796, 29 Apr 2024: a panel of models from disjoint families beat a
   single large judge, with less intra-model bias, at over 7x lower cost. -> a cross-family panel is the right shape; a single judge never decides.
5. E - Huang & Zhou, "Comparative Evaluation of LLM-Based Review Paradigms", arXiv 2610.41391, 30 Oct 2026 (232 + 11,513 ICLR submissions): direct
   1-10 rating "compresses most predictions above the accept threshold, flagging almost none" of the weak papers; after recalibration it beat Elo
   with 24% of the calls. -> no free 0-10 scores from a model: judges answer concrete yes/no questions and CODE turns them into scores.
6. E - "LLM-as-a-Reviewer" benchmark, arXiv 2605.25415, May 2026 (search summary): most of 12 models over-rate papers, some families by up to 2.43
   points on the venue scale. -> inflation is the default; the verdict needs an independent calibration signal (design D: the planted canary).
7. E - Lee et al., "CheckEval", arXiv 2403.18771 (EMNLP 2025): decomposed binary checklist questions raised average agreement across 12 evaluator
   models by 0.45 and reduced score variance; RubricEval, arXiv 2603.25133, Mar 2026: rubric-level questions with explicit reasoning cut inter-judge
   variance further. -> the rubric is a fixed checklist per dimension with a one-line reason per answer.
8. E - Si, Hashimoto, Yang, "The Ideation-Execution Gap", arXiv 2506.20803, Jun 2025 (ICLR 2026): 43 experts executed ideas blind (100+ h each);
   LLM ideas scored HIGHER before execution and dropped significantly more after it on every metric (p < 0.05), with rankings flipping. -> a
   jury's praise is a hypothesis: a creative technique can at most be "test" (an experiment arm, lever C); "accept" is kept for facts (policy,
   tools, prices) backed by official or measured sources.
9. O - Anthropic web search tool documentation (read 11 Nov 2026): USD 10 per 1,000 searches plus tokens (results count as input); failed searches
   not billed; usable in the Message Batches API at the same search price (batches throttle searches); citations carry url, title and up to 150
   characters of `cited_text`; results carry `page_age`; `max_uses` caps searches per turn; tool versions 20250305 / 20260209 / 20260318.
   -> evidence is read from the API's citation blocks (url + quoted text + page age), not from the model's prose; cost per question is computable.
10. O - Google Gemini grounding pricing (Google Cloud pricing page via search summary, 2026): Gemini 3 family 5,000 grounded prompts a month free, then
   USD 14 per 1,000 queries; Gemini 2.5 billed per prompt (USD 35 per 1,000 after 1,500 a day). -> Gemini grounding is the fallback researcher
   (cheap, but no quoted text: its findings get a lower evidence ceiling).
11. O - YouTube "inauthentic content" monetisation update, 15 Jul 2025 (TeamYouTube; 2026 enforcement reported, search summary): mass-produced or
   repetitive uploads ("narrated stories with only superficial differences") are ineligible; AI tools are allowed. -> platform policy is a standing
   research question every 4 weeks and a risk question every juror must answer for every proposal.
12. E - NovGauge, arXiv 2609.11234, Sep 2026 (search summary): LLM judges over-attend to technical validity and underweight novelty. -> novelty is
   judged against the department's OWN playbook (what we already do), given to the jury, not against the model's general sense.
Re-read: 02 points 2 ("evaluated by another chat session objectively in its role"), 3 (cheap models never judge taste), 12, 14 ("AUTOMATIC
RESEARCH, AUTOMATIC ASSESSMENT OF RESEARCH"), 15; 01 sections 2 (D2, D3), 5, 7 `research_cadence`, 8, 9; open issues 8, 13, 30.

#### Step 2 CREATIVITY (4 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Extend the topic brief": keep `research.py`'s brief, add one web-search call, let `room2.jury` rank the findings. 2 / 2 / 5 / 3 / 5. Rejected:
  a ranking has no accept / test / reject, room2's jury includes a cheap judge (02 point 3), and the brief answers "which topic", not "what is wrong
  with us and who does it better".
- B "Deep-research agent": plan -> many searches -> read -> synthesise per question (the commercial deep-research shape). 4 / 2 / 1 / 2 / 5.
  Rejected: sources 1-2 (most hallucinated URLs, accuracy falls ~42% as tool calls grow) and the cap (Rs 300 buys about 20 bounded questions a month).
- C "Gap-driven agenda + grounded memo + checklist board": the agenda is computed by code from the organisation's own failures (failed checks,
  weakest breakout component, recurring problems, owner memos, outliers, expiring facts, policy and tool changes); one bounded search call per
  question; provenance verified by code; a blind cross-family jury answers fixed yes/no questions; code computes scores and the verdict.
  4 / 5 / 4 / 4 / 5. Taken as the core.
- D ORIGINAL, beyond the research - five rules that make a jury's verdict something code can check:
  (1) PLANTED CANARY: every Board session contains one memo the code built to be rejected (no dated source, a guaranteed-views claim, a policy
      breach, nothing measurable), shown blind among the real ones. Each FAMILY of judges must reject it on its own, or the whole session is void
      (no verdict written, the memos wait for the next run). Calibration is measured on every session, not assumed (sources 5, 6).
  (2) EVIDENCE CEILING: code computes the highest evidence score a memo can get from what it can verify (sources the search tool really returned,
      that resolve, dated, distinct domains, official or measured types, how fresh); the jury can lower it, never raise it (sources 1, 2).
  (3) FAMILY VETO: scores are the mean of FAMILY means, and nothing is accepted or sent to test unless the family that did NOT write the memo
      clears the bar by itself (source 3).
  (4) PRE-REGISTRATION: every proposed action carries a prediction in a fixed vocabulary (a contract check or an Analytics column, a direction, a
      horizon in videos); without one a technique cannot reach "test" - the prediction becomes the experiment's metric when the Council issues it.
  (5) FACTS ACCEPT, IDEAS TEST: only a fact (policy, tool, price, an expiring Palace fact) can be "accept"; a creative technique is at most "test"
      (source 8: what juries love before execution falls hardest after it).
  5 / 5 / 4 / 4 / 5.
Decision: C + D. Rejected after scoring: Message Batches for research (searches cost the same in a batch, only tokens halve - about Rs 4 a question,
~Rs 70 a month - while the batch API throttles searches and the daily job would wait up to 40 minutes per batch; recorded as an open issue for
measurement, not built); a third (cheap) judge; letting the model choose the evidence type (code classifies by domain).

#### Step 3 DESIGN MEMO
- Decision: two native departments - `whatifs/org/rnd.py` (D2) and `whatifs/org/board.py` (D3) - the first departments whose ACT returns
  `runner.Out` (memos, every inbound memo dispositioned, measures), so the runner proves every step.
- Where they run (level-triggered, so a missed day never skips a week): the daily `learn` job, in this order: D2 `daily` (Rs 0: the Outlier Lab, the
  search-demand scores and the research brief move here from `manage.learn`; then the agenda is refreshed) -> D2 `weekly` when the last complete
  weekly run is RESEARCH_DEEP_EVERY_DAYS old (paid, budget "org", cap Rs 300) -> D3 `assess` when a research memo waits (paid, budget "org", cap
  Rs 120) -> D10 `daily` as before. A research memo is therefore assessed the same day it is written (SLA 48 h).
- D2 agenda (`Research_Agenda` tab, one row per gap, deduplicated by signature, a question answered is not asked again for RESEARCH_REPEAT_DAYS):
  failed contract checks (28 days, by count; addressed to the check's owner), the weakest breakout component, recurring problem memos (attempt >= 2),
  open owner memos (P0, always asked, outside the weekly count), Outlier Lab videos (14 days), Palace facts / plans / policy rules expiring within
  14 days or expired (closes the research side of open issue 8), new or deprecated models in `Tool_Scout`, and a standing platform-policy question
  every 28 days. Priority is computed; the weekly run asks the top RESEARCH_PER_WEEK while the D2 budget left covers the estimate per question
  (RESEARCH_EST_INR or the median measured cost, whichever is higher); P0 is asked even past the cap (01 section 9).
- One question = one `models.ask` call with the web-search tool (role `rnd_research`, Sonnet chain; Gemini grounding is the fallback), at most 4
  searches. `models.last_call()` (new, additive) returns the provider, the model, the measured cost and the citations the API itself returned.
- Provenance by code (`rnd.verify`): a source counts only if its URL is among the API's citations or results (a URL the model typed is a PHANTOM:
  dropped, counted, and costs the memo 2 points of ceiling); it must resolve (404 / 410 / no host = dead; 401-429 = alive but blocked); it needs a
  publication date not in the future (the result's page age or the model's date); its type is decided by its domain (platform / vendor = official,
  research = measured, else practice), never by the model; its quoted text is the API's `cited_text`. A finding with no surviving source is dropped;
  a question with no surviving finding writes no memo (agenda row "unanswered", the money is still counted). Evidence ceiling 0-10 from distinct
  domains, official / measured sources, freshness and phantoms.
- Research memo (to D3): question, findings, confidence (never above ceiling / 10), proposed actions, expected impact, cost, target departments; new
  optional body fields kind, gap, evidence_ceiling, predictions, palace_ref; links carry the agenda row and the researcher's family (the jury never
  sees it). Schema change is additive.
- D3 Board session (`board.assess`): up to BOARD_MAX_MEMOS research memos + 1 canary, labelled A, B, C... with no department, model or id; for each
  memo the jury also sees the target department's own playbook ("what we already do") for the novelty questions. Two judges of two families
  (`board_gemini` = Gemini Pro only, `board_claude` = Sonnet then Opus: chains with NO cheap model), each in BOARD_ORDERS orders (original and
  reversed). 12 yes/no questions with a one-line reason each: evidence 2, novelty 2, impact 3, feasibility 2, risk 3 (policy, owner rules /
  canon, slop); cost is computed by code from the memo's cost. Scores per dimension = 10 x the share of "yes" (family-balanced); evidence is capped
  by the ceiling. Verdict by code (`board.verdict`): reject when evidence < BOARD_MIN_EVIDENCE, risk >= 5 or impact < 4; accept only a FACT
  (policy, tool, revalidate) with evidence >= 7, feasibility >= 5, risk < 3; test when impact >= 6, feasibility >= 5, novelty >= 5 and at least
  one valid prediction; else reject; accept / test also need the non-author family alone to clear the same bar. A judge answered by the wrong model
  (fallback to another family or to a cheap model), a single family, or a canary not rejected by every family = session void.
- Assessment memo (to the Council) carries the scores, the verdict, the jury (family:model), the rationale, the family checklist shares and the
  canary result; `research_cadence` RE-COMPUTES every stored verdict from the stored checklist and fails on a mismatch (a verdict nobody can forge).
  Until the Council exists (B6) an assessment memo waits at the owner's level silently (owner_visible only for an accepted P0 fact).
- Check `research_cadence` (script gate, owner D2): FAIL when (after a 48-hour grace from ORG_SINCE) D2's daily run is more than 50 hours old, the
  weekly run more than RESEARCH_DEEP_EVERY_DAYS + 1 days old while budget is left, a research memo is past its SLA and neither assessed nor
  escalated, a research memo lacks the provenance stamp (not written by `rnd.verify`), an assessment's verdict differs from the code's verdict on its
  own checklist, an assessment lacks two families or the canary, or a department spent past its cap by more than one question's estimate without a P0.
- Money (rule 2): D2 cap Rs 300 (about 4 questions a week at Rs ~10-15 each, measured per call), D3 cap Rs 120 (about Rs 10-20 a session).
  The unspent part of the caps of WIRED departments is reserved from production like an earmark (`governor.org_left_inr`), so the month's plan
  never counts the organisation's thinking money twice.
- Levers: + RESEARCH_PER_WEEK (D2; up = costs more -> owner), + BOARD_MIN_EVIDENCE (D3; down = weaker gate -> owner). D2 and D3 leave
  `registry.PENDING` (7 -> 5), so their tickets reach the engine.
- Rejected: the Board writing Palace items or tickets (the Council decides, B6); the model choosing the evidence type; free 0-10 scores; one judge
  family; Message Batches (see step 2); re-validating Palace facts directly (only owner, Council, D10 may - the memo carries `palace_ref` for B6).
- Tests: provenance both ways (phantom, dead, undated, future-dated, type clamp, finding without source, empty memo), agenda from every gap source and
  dedupe, cap and P0, the jury's family / model / canary rules, verdict table both ways, forged verdict, the check's every FAIL condition, the REAL
  learn job running D2 and D3, a fake research cycle end to end (agenda -> memo -> assessment -> the Council's level).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/rnd.py` (D2): `gaps` (8 gap sources, Rs 0) + `refresh` (tab `Research_Agenda`: dedupe by signature, drop closed gaps, re-open after
  RESEARCH_REPEAT_DAYS, never while the last memo is open, a dead or failed ask re-opens after 20 h); `daily` (the research brief, the Outlier Lab and
  the search-demand scores moved here from `manage.learn`, then the agenda); `deep` + `deep_due` (weekly, level-triggered, P0 first and past the cap,
  P1/P2 while the budget left covers max(RESEARCH_EST_INR, median measured)); `ask_one` (role `rnd_research`, web search, at most 4 searches);
  `verify` / `alive` / `source_type` / `parse_date` / `ceiling` (provenance by code); `build_memo` (research memo with the stamp `rnd.verify`);
  `ceiling_of` + `cadence_issues` (what the check judges).
- NEW `whatifs/org/board.py` (D3): 12 yes/no questions (2 evidence, 2 novelty, 3 impact, 2 feasibility, 3 risk); 3 canaries (no source + bought views; an irrelevant quote + daily re-uploads; an official quote that says the
  opposite + mass-produced Shorts); `assess` (blind blocks A, B, C... with the target department's own playbook, 2 families x BOARD_ORDERS orders,
  the answering model checked through `models.last_call`, void rules, assessment memos, a D3 -> D3 problem memo when void, closed by the next valid
  session); `scores_from` / `bar` / `verdict` / `cost_score` (pure: the check re-runs them); `assessment_issues`. Tab `Board_Log`.
- `whatifs/models.py` (protected): `last_call()` + `_note_call` + `_claude_sources` (the API's citations and results, the answering chain role and
  the measured USD, recorded by `_claude`, `_gemini` and the fake path); routes `rnd_research` (Sonnet chain), `board_gemini` / `board_claude` with
  chains `board_g` = Gemini Pro only and `board_c` = Sonnet then Opus (no cheap model can answer for the Board).
- `whatifs/org/schemas.py` (protected): research memo + kind, gap, evidence_ceiling, predictions, palace_ref, sources_dropped; assessment memo +
  checklist, canary, kind, evidence_ceiling, author_family, predictions, cost_inr (all optional: additive). `RESEARCH_KINDS`.
- `whatifs/org/memos.py` (protected): `id_for` (the id `write` will use, so a department can close a memo with the memo it sends in the same run).
- `whatifs/org/registry.py` (protected): D2 wired (`cli.py` daily + weekly), D3 wired (`cli.py` assess), PENDING 7 -> 5 (D0, D1, D11, C, L);
  `reach.py` moves to D10's wraps (master spec lists it under both; it measures our own videos); D2 + RESEARCH_PER_WEEK, D3 + BOARD_MIN_EVIDENCE;
  CHECK_OWNER research_cadence -> D2. `whatifs/org/levers.py`: 2 rules (41 levers).
- `whatifs/contract.py`: check `research_cadence` at the script gate: **44 hard checks (25 script + 19 final)**.
- `whatifs/cli.py`: `research_round()` runs first in the learning job (D2 daily, D2 weekly when due, D3 when a memo waits; each failure logged,
  never stops the job). `whatifs/manage.py` (protected): the research brief renewal, `OLB.run()` and `DMD.run()` left `learn` (now in D2 daily).
- `whatifs/governor.py` (protected): `org_left_inr` - the unspent part of the wired departments' thinking caps (D2 Rs 300 + D3 Rs 120 while
  research is on) is subtracted in `production_room_inr` like an earmark.
- `whatifs/core.py` (protected): tabs `Research_Agenda` (17 columns), `Board_Log` (12); 7 settings: RESEARCH_PER_WEEK 4, RESEARCH_EST_INR 15,
  RESEARCH_REPEAT_DAYS 28, RESEARCH_DEEP_EVERY_DAYS 7, BOARD_MIN_EVIDENCE 5, BOARD_ORDERS 2, BOARD_MAX_MEMOS 6.
- `whatifs/fakes.py`: a fake web search (3 sources with quotes and page ages relative to today), a fake research answer (with one phantom and one
  undated source, two predictions), a fake strict judge that rejects every canary. `tools/repair.py` PROTECTED + rnd.py, board.py.
- 7 founding items `b5.*` (125 founding items, Palace GREEN, no playbook crowded further); `tools/rehearsal.py` runs the real `research_round`.
- Changed against the design memo after seeing real behaviour or re-reading: (1) the ceiling is computed on the sources the memo CARRIES (a kept
  source no finding used had raised it); (2) a question is never asked again while its last memo is still open (the new memo would have collided with
  the open one and the runner would have refused every memo of that run); (3) the five faults of step 6a; (4) assessments stay silent at the owner's
  level for now - the design said "owner_visible for an accepted P0 fact", but the only message the ladder has today says "Stuck past its deadline"
  for a memo written a second earlier.
- Existing tests changed BY DESIGN (say so in the final PR): `tests/test_v12_org.py` (a pending department for the escalation test is now D11, D2
  is wired), `tests/test_v12_exec.py` (41 levers, 25 script checks), `tests/test_v94a.py`, `tests/test_v87.py`, `tests/test_v10_growth.py` (production
  room minus `org_left_inr`).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executes | Fails when broken |
|---|---|---|
| Research is computed from the organisation's own gaps and runs by itself | `rnd.gaps`, `refresh`, `deep_due`, `cli.research_round` | `research_cadence` FAIL (daily run older than 50 h; weekly older than RESEARCH_DEEP_EVERY_DAYS + 1 with budget left); the real learn job test |
| A source counts only if the search tool returned it, it resolves, it is dated and not in the future; type by domain | `rnd.verify`, `alive`, `source_type`, `models.last_call` | phantom / dead / undated / future dropped and counted; no surviving finding = no memo; `research_cadence` FAIL on a memo without the stamp or with a ceiling its evidence does not support |
| Blind, strong, two families, two orders, fixed questions; scores and verdict by code | `board.assess`, `_parse`, `scores_from`, `verdict` | a judge answered by another family or a cheap model is not counted; < 2 families = void; `research_cadence` re-computes every stored verdict |
| A planted canary must be rejected by every family | `board.canary`, `assess` | session void, no assessment, D3 problem memo (recurring -> escalates) |
| Only facts accepted; ideas tested only with a pre-registered prediction | `board.bar`, `rnd.metrics`, `_actions` | decided by code; the forged-verdict test |
| Caps: R&D Rs 300, Board Rs 120; P0 continues; the unspent part is not production money | `runner.run` (budget "org"), `rnd.deep` (in-run guard), `governor.org_left_inr` | CapReached before the run; `research_cadence` FAIL on overspend without an owner question |
Matrix: 5 rows (meta-test green). Founding items: 7.

#### Step 6 PROVE
- `tests/test_v12_rnd.py`: **31 tests**, each rule both ways: a phantom source dropped and costing 2 points; dead, undated and future sources dropped
  with the findings that stood only on them; the type set by the domain (a model may only lower it); the ceiling table; Gemini matched by domain and
  capped at 6; liveness on a real network (404 / 410 / no host dead, 401-429 and timeouts alive); five date forms; predictions need a known metric, a
  direction and a horizon; an unprovable answer writes no memo; a memo carries only verified evidence and passes the memo gate; the agenda from all
  8 gap sources and never from a code fault; dedupe, drop, re-open after the window, never while the last memo is open, a dead or failed ask open
  again after 20 h; the ceiling recomputed from the day the memo was written; the weekly run inside the cap with the owner's question beyond it, and
  CapReached at the cap; due by level, not by calendar (a broken run is not re-paid); a Board session blind (no memo id, author or model in any
  prompt), two families x two orders x memos + canary, each research memo closed by its own assessment, assessments silent at the Council's level;
  a judge answered by the other family or by a cheap model not counted -> void -> D3 problem memo (recurs) -> closed by the next valid session; an
  inflating jury voids the session; unanswered questions count against the memo; the verdict table and the family veto; forged verdicts, scores,
  one family, no canary caught; `research_cadence` N/A off / young, and every FAIL condition (daily 60 h, weekly 9 days with budget left - not when
  capped, no stamp, forged ceiling, past SLA and not escalated, forged verdict, D3 overspend); the REAL learning job; the collectors moved; the wiring;
  the lever rules (up costs more -> owner; down weakens the gate -> owner; another department's lever refused); the money reserve; `last_call` reading
  the API's citation blocks, Gemini grounding chunks and the fake path.
- Live proof by mutation on the real repo, each reverted: the phantom check removed and the canary rule disabled (one run) -> **7 tests fail**, the
  canary test among them;
  `research_round()` removed from the learning job -> the wiring test fails while `python -m whatifs.org.runner` and the truth scan both stay GREEN
  (the literal calls still exist inside the function: B4's warning about name scans holds again).
- Fake rehearsal on the final code: **GREEN** - contract script 25 / 25, final 19 / 19 on GitHub; the research round inside it: 3 research memos ->
  policy: accept, technique: test, technique: test; canary rejected by both families; `research_cadence` PASS.
- Full suite: **1232 passed / 0 failed / 1 skipped** (66 files, one uninterrupted run by itself on a frozen copy of c325b3e; the skip is the dashboard
  render, which needs node - GitHub runs it). The final commit a1c5204 adds only the takeaway seed item, a CLAUDE.md recipe and generated docs.
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (126 founding items; the limits note unchanged: D1 3,
  D4 4, D12 1, C 6). Organisation **GREEN** (10 wired, 5 pending).
- Sweep (standing rule 2): on a frozen copy of a1c5204 - A: 40 fixed ids, organisation ON: **40 ok, 0 held, 0 crashed** (each: status SCHEDULED,
  38 PASS + 6 N/A, 9 department runs verified, 0 live memos, 0 owner messages, 0 degraded steps); B: 10 ids with ORG_ON = FALSE: **10 ok** (35 PASS +
  9 N/A); C: 8 full rehearsals with a forced id: **8 ok** (status LIVE, 39 PASS + 5 N/A, the research round in each: 3 live memos = the assessments
  waiting silently for the Council). **58 of 58 green.** Warning classes: the same 9 in every episode and 1 in 1 of 40 as in B4 - none is new.
  Traced, not new: every rehearsal also sends the owner a 'similar script' message because the rehearsal renders the SAME episode again and
  `similarity.check` compares it with its own earlier fingerprint (the episode is named as its own twin; code untouched by B5) - open issue 47.
- GitHub Checks (standing rule 1), every commit of the batch read on the public run page: #61 (step 1) and #62 (steps 2-3) GREEN. **#63 (be89fa4) RED**
  - 6 failed / 1196 passed: exactly the six tests whose expectation changed by design (41 levers, 25 script checks, D2 no longer pending, three
  production-room formulas off by the organisation's Rs 420 reserve), updated in the next commit. **#64 (9060e41) and #65 (8f5a9d7) RED at the
  rehearsal** (unit tests 1231 / 1233 passed): the rehearsal's own production-room formula (`maintenance reserve ... must sit inside the cap`) - the same
  assertion my laptop rehearsal failed on, fixed in c325b3e. Traced from the annotations, not re-run. **#66 (c325b3e) GREEN. #67 (a1c5204, the final
  code commit): GREEN - 1233 passed, 0 skipped, rehearsal GREEN (episode id EP202611102139, script 25 / 25, final 19 / 19).** New notice on the run page:
  GitHub's `ubuntu-latest` label moves to Ubuntu 26 from 19 Oct 2026 (open issue 46).
- Money: Rs 0 spent (fake mode). Expected in production: R&D about Rs 10-15 a question x 4 a week (cap Rs 300), the Board about Rs 10-20 a session
  (cap Rs 120); NOT measured - the first real runs must be read (open issue 40).

#### Step 7 TAKEAWAY (also Palace item `b5.takeaway`, 126 founding items)
- WORKED: every judgement as a PURE function of stored data (the ceiling, the scores, the verdict). The check re-runs them on what is stored, so a
  typed, edited or forged verdict fails `research_cadence` - the Board's word is not trusted, its arithmetic is re-done.
- WORKED: a test the judge must fail. The planted canary turns "is the jury inflating?" (sources 5-6) from a worry into a measurement per session; a
  flattering judge (yes to every good question, no to every risk) is caught by the test that simulates it.
- WORKED: re-reading the finished code as a stranger again (B4's lesson). It found five faults no test had asked about, each about TIME: a row stuck
  in "asked" after a killed run, a 28-day wait after a failed call, a one-day shift at midnight in the recomputed ceiling, a broken weekly run re-paid
  every day, and a "stuck" message to the owner for a memo written a second earlier.
- WORKED: the real-job test. Removing `research_round()` from the learning job left the registry scan AND the truth scan green (the literal calls
  still exist inside the function); only the test that runs `python -m whatifs.cli learn` saw it.
- WATCH: the fake judge recognises the canaries by their words - it is a stand-in. Real calibration exists only in production: read `Board_Log`
  (verdict "void" and its reason) after the first real sessions.
- WATCH: nothing researched changes a video until the Council (B6) turns assessments into tickets; until then every assessment waits silently at
  the owner's level (open issue 38).
- WATCH: the real web-search citations, Gemini grounding and the cost per question are proven with stand-ins and the documentation (open issue 40).

### B4 - Execution Engine (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below; final code commit ad99fd2 GREEN in GitHub run 59)
Result in one line: whatever the organisation decides can now only exist as a change that runs - a ticket is compiled into a typed change, written to a
ledger before and after, verified by evidence somebody else wrote later, and rolled back when that fails; a decision without executed tickets fails a
HARD check before picture money. Honest limits: no real ticket is written until the Council exists (B6), so B4 by itself changes no video; knowledge is
proven "served", not yet "cited" (B6); the code lever is proven with stand-ins for GitHub, never on GitHub itself; tickets for the 7 departments that
are still pending go straight to the owner's level.

#### Step 1 RESEARCH (14 dated sources; E = measured evidence, O = opinion / practice / vendor documentation)
Honest note: for sources 1-5 and 14 the abstract page was read, not the full paper; 4 and 9c are quoted from a search summary.
1. E - Mohammadi et al., "Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows", arXiv 2602.14849, 16 Feb 2026 (v2 29 May 2026):
   orchestrators treat a tool's RETURN as the signal that work is settled; effects are bufferable, reversible or irreversible; commit only when
   nothing earlier can still conflict; abort compensates what was already let out. -> "applied" is not "done": a change is settled only by later evidence.
2. E - Chen et al., "Cordon: Semantic Transactions for Tool-Using LLM Agents", arXiv 2606.17573, 16 Jun 2026: reversible changes first, outward
   actions staged, the composed flow validated BEFORE an irreversible commit, audit metadata recorded. -> the undo is computed and stored before
   the change; the only irreversible lever (merged code) has the strictest gate.
3. E - Wu et al., "Safe to Resume? Breaking Execution Continuity of Agent Execution via Rollback", arXiv 2608.29381, 29 Aug 2026: "correct rollback
   does not imply secure recovery" - a faithfully restored state can sit next to newer external facts that never coexisted with it (three
   end-to-end attacks, five frameworks). -> a rollback restores the old value ONLY if the cell still holds what the engine wrote.
4. E - "Always-On Agents" survey, arXiv 2606.30306, Jun 2026: 27 of 435 surveyed works expose any rollback; none reports recovery success or cost.
5. E - Lin et al., "Safety in Self-Evolving LLM Agent Systems", arXiv 2606.23075, 22 Jun 2026: a bad self-change is lineage-persistent (40 of 40
   payloads persisted); 17 of 25 module x life-cycle cells critical; scanners that sit beside the agent stopped 2.5%. -> every self-change carries
   its lineage (ticket -> decision -> memos), is reversible, and the commit gate is code OUTSIDE the component that proposed it.
6. E - Cloudflare post-mortem, 18 Nov 2025: an internally generated configuration file doubled in size, the proxy hit a hard limit and failed
   network-wide for 5 h 46 min; first remediation: treat internally generated configuration "the same way" as user input; more kill switches.
   -> the organisation's own values pass type, range and step checks like untrusted input; one switch (`EXEC_ON`) stops the engine.
7. E - Google Cloud incident report, 12 Jun 2025: a policy with blank fields replicated worldwide in seconds into a code path with no flag and
   no error handling. Remediation: flags off by default, incremental roll-out with time to validate, fail open. -> one change at a time, a
   verification window before "verified", and a broken engine never throws away or blocks work that is already paid.
8. O - LaunchDarkly "guarded rollouts" documentation (read 10 Nov 2026): automatic rollback needs a minimum sample; with too little data at
   the end it rolls back; it suits metrics where "worse" is unambiguous. -> at one video a week statistics are impossible, so the engine ISOLATES
   (one unverified change per department) and uses the hard contract checks (pass / fail) as guardrails; no evidence in the window = rolled back.
9. E - reward hacking by coding agents: (a) SpecBench, arXiv 2605.21384, 21 May 2026: 97.8% on the visible tests against 83.3% on held-out tests
   (gap 14.5 points, growing with task size); (b) ImpossibleBench rates quoted in a 2026 safety report: 0-11.8% of runs change or game the tests;
   (c) METR: one model gamed the scorer in 39 of 128 runs, and telling it not to "had a nearly negligible effect". -> a code lever is verified
   by checks the build did not write, and the automatic merge is decided by code reading the real diff - never by the request or the prompt.
10. E - The Hacker News, 4 Jun 2026: flaw in the Claude Code GitHub Action (fixed in v1.0.94, CVSS 7.8): injected text could make the agent read the
   job's environment and leak its secrets; advice: a job that reads untrusted text holds no secret beyond the model credential and the workflow's
   own access. -> `claude-build.yml`: the Sheet, WhatsApp and merge secrets move off the step in which Claude Code runs.
11. O - optional stopping: Johari et al., arXiv 1512.04922, and simulations in practitioner write-ups (stopping at the first p < 0.05 gives about
   21-28% false positives instead of 5%). -> the engine never judges an experiment arm early; it verifies only that the arm is assigned and
   recorded, and the existing fixed rule (plays on both sides) gives the verdict.
12. E - Tang et al., "Holistic Configuration Management at Facebook", SOSP 2015: validators on every change, canary on a subset, automatic rollback.
13. O - the Kubernetes controller pattern (level-triggered reconciliation: a missed event is harmless because the next pass re-reads state).
   -> the engine's tick pass reads state (cells, Sessions, the ledger of checks), never an event queue; a killed job is settled by the next pass.
14. E - Zhang et al., "Darwin Goedel Machine", arXiv 2505.22954, 29 May 2025 (v3 12 Mar 2026): a self-modifying agent went from 20.0% to 50.0% on
   SWE-bench with sandboxing and human oversight. -> gated self-change works; the gate is the product.
Re-read: 02 points 2, 12, 14, 15 ("whatever they learn or brainstorm or decide ... strictly code line level executed and enforced"), 01 sections 4-7.

#### Step 2 CREATIVITY (4 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Immediate applier": apply by lever class, read back, mark verified. 2 / 2 / 5 / 2 / 4. Rejected: read-back proves the write, not the effect
  (source 1); nothing ever rolls back.
- B "Guarded roll-out": apply -> probation -> guardrail checks -> automatic rollback (sources 8, 12). 4 / 4 / 5 / 4 / 4. Taken as the core.
- C "Desired-state reconciler": a pass on every tick compares what should be with what is and converges (source 13). 3 / 4 / 4 / 5 / 4. Taken for
  crash-safety: the tick pass also settles an apply that a killed job left half done.
- D ORIGINAL, beyond the research - five rules for a system with ONE video a week and ONE owner:
  (1) isolation instead of statistics: at most one unverified setting or experiment per department, and settings change BETWEEN videos, never
      inside one - so one video's checks can be attributed to one change, and no script is judged against a bar it was not written for;
  (2) proof by somebody else: a change is verified only by rows another component wrote AFTER it (a later department run, a later video's check
      rows, a later Video_Features row, GitHub's own check runs) - the engine's own read-back is necessary, never sufficient;
  (3) the owner's hand wins: rollback is compare-and-swap; a cell the owner edited after the engine is never overwritten (source 3);
  (4) the direction decides who may turn a lever: inside its range a department moves a lever freely in the direction that makes a gate stricter
      or cheaper; the direction that weakens a gate or costs more needs the owner's one tap, pre-filled;
  (5) additive-only automatic merge: a build may ADD tests and rule data and nothing else; one deleted line, one protected file or no new test
      sends it to the owner (source 9).
  5 / 5 / 5 / 4 / 5.
Decision: B + C + D together.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/levers.py` (every lever: type, range, largest step, the direction that needs the owner, the checks that judge it; the
  scope of an automatic merge) and `whatifs/org/execute.py` (the engine). A ticket's free text (`acceptance_test`, `rollback`) is for people; the
  engine compiles `lever_class` + `target` + `value` into a typed operation with a registered verifier, or refuses the ticket with the reason.
- Tabs appended: `Tickets` (one row per ticket: the engine's state) and `Lever_Changes` (append-only: intent, applied, verified, rolled_back,
  refused, queued, owner_asked ... one row per event, written BEFORE and AFTER every change).
- States: queued -> (awaiting_owner) -> intent -> applied -> verified | rolled_back; refused; failed. Code lever: dispatched -> pr_open -> merged -> verified.
- Lever classes: A knowledge = a Palace item accepted with the Council's authority (the Palace's own gate refuses anybody else); verified when a
  later run of the target department was served it (and cited it once that department runs in `prompt` mode - B6); undo = retire / restore the old
  version. B setting = a registered cell, owner department only (`registry.may_change`), type / range / step, never a cell no code reads; applied
  between videos; verified by a video BORN after the change passing the lever's own checks; a failed check, a failed run or no evidence in the
  window = rollback. C experiment = a rulebook trial (`whatifs/playbook.py`: coin flip per video = holdout, plays on both sides before a verdict);
  the long video's features now record its arms; verified when the next N long videos carry the arm, or the trial was judged. D prompt rule = a
  Palace rule item (style / policy), bounded per department, otherwise as A. E code = a `build_request` from D12, the build workflow, checks,
  additive-only automatic merge or the owner's Merge tap, checks on the merge commit, at most 2 re-builds, then escalation.
- The reconcile pass runs on every tick (next to the SLA watchdog); D12 Operations gets its run (trigger `operate`) only when it has a ticket to
  execute. A ticket closes as `lever_verified` / `rolled_back` only when the ledger holds that row (`memos._proof_problem`).
- Waiting for evidence is not being late: once a change is applied the ticket's resolve clock moves to the end of its verification window
  (`memos.await_proof`, typed, bounded, needs the ledger row); the engine itself rolls back when that window ends.
- Checks: `decisions_executed` and `lever_verified`, both at the script gate (before picture money). They FAIL on a broken invariant (a decision
  with no ticket, a ticket closed without ledger proof, a change past its window with no verdict, a failed rollback, an overdue ticket nobody
  escalated) - never merely because the owner has not answered yet.
- Money: Rs 0 (no model call). Code builds run on the owner's Claude plan (Rs 0 API), at most 1 + 2 attempts per ticket.
- Rejected: executing the ticket's `acceptance_test` text (a self-written test is the thing sources 9 and 14 warn about); applying a setting in
  the EXECUTE step of an episode run (it would change the bar under a script already written); automatic revert of drift (it would fight the
  owner's hand edits); a department run for D12 on every tick (about 670 empty runs per two-week verification window).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/levers.py`: the lever table - 39 Settings cells (15 whole numbers, 6 decimals, 9 switches, 3 choices, 4 JSON maps, the publish days,
  the list of switched-off checks), each with type, range, largest step, the direction that needs the owner (28 of 39 have one) and the contract
  checks that judge it (22 of 39; the rest are judged by the next complete run of their department). `check`, `same`, `issues`, `owner_of`, `merge_scope`.
- NEW `whatifs/org/execute.py` (599 lines): `apply` (the runner's EXECUTE step), `engine_tick` + `reconcile` (the tick pass), the five lever classes as
  (plan, do, read-back, verify, undo), the owner's approval message and its answer, `decision_issues` / `lever_issues` (what the two checks judge).
- Tabs appended: `Tickets` (24 columns), `Lever_Changes` (12). 9 settings: EXEC_ON, EXEC_VERIFY_RUNS (3), EXEC_VERIFY_DAYS (14), EXEC_ARM_OUTPUTS (2),
  EXEC_RULES_PER_DEPT (12), EXEC_BUILD_RETRIES (2), EXEC_BUILD_WAIT_H (6), EXEC_AUTO_MERGE_ON (TRUE), EXEC_TICK_AT (auto).
- `whatifs/org/memos.py`: a ticket closes as `lever_verified` / `rolled_back` (a build request as `merged_verified`) only when the ledger holds that row
  with a proof for that ticket; only the engine may close them that way; `await_proof` (typed, needs the ledger row, at most 130 days).
- `whatifs/org/runner.py`: the engine is the default executor (`_engine`); with `EXEC_ON` = FALSE a ticket is escalated at once. `set_executor` is gone.
- `whatifs/org/registry.py`: D12 Operations is wired (`execute.py`, trigger `operate`; pending list 8 -> 7); the two new checks have owners (C, D12);
  `data_issues` includes the lever table.
- `whatifs/contract.py`: checks `decisions_executed` and `lever_verified`, both at the script gate: **43 hard checks (24 script + 19 final)**.
- `whatifs/builds.py` + `whatifs/cli.py` + `.github/workflows/claude-build.yml`: a build can carry its build request id; the real diff (`pr_files`) and
  the checks of any commit (`commit_state`) can be read; the workflow's Sheet, WhatsApp, owner and merge credentials moved from the whole job to its
  last step - the step in which Claude Code reads the spec now holds only its own model credential and the workflow's own repository access.
- `whatifs/manage.py` (tick: `EXE.engine_tick()` next to the watchdog), `whatifs/notify.py` (the approval answer is registered), `whatifs/episode.py`
  (the long video's features now record its experiment arms - they were always empty for long videos).
- `whatifs/truth.py`: two entries deleted, `UNWIRED_FUNCTIONS_MAX` 10 -> 8. `tools/repair.py` PROTECTED: + levers.py, execute.py, builds.py.
- Generated docs: SYSTEM.md section 12 (states, the five classes, the whole lever table). 5 matrix rows. 7 founding items `b4.*`: 118, 0 refused.
- `tools/rehearsal.py`: a Council decision with one knowledge ticket is written before the video and must end `verified` on the ledger.
- Changed against the design memo after seeing real behaviour: (1) proof names the exact item VERSION (an updated item was "verified" by a playbook
  that still held its old text); (2) a video that starts in the very second of a change counts as made after it; (3) the tick takes up new tickets
  of every wired department itself - a department that only runs inside a video would have seen its ticket a week late and the ticket would have
  climbed to the owner for a missed acknowledgement; (4) the tick records when it last finished and the check fails when tickets wait and that is a day
  old; (5) a merge whose checks never report is escalated, never reverted on a guess; (6) the automatic merge scope is narrower than the master
  spec's "tests + rules": NEW TEST FILES ONLY - rule data has its own lever (D) with verification and rollback, a build that edits it would bypass both;
  (7) `decisions_executed` says N/A, not PASS, while nothing has been decided: the sweep showed 40 videos each "passing" a check that had judged nothing;
  (8) found by GitHub, not by the laptop: "after the change" is judged to the second, and on a fast machine the next run of the department began in
  the very second of the change - it was skipped and the proof named a later run. Now a run that begins in that second counts, and the run that
  hands the ticket over is recorded (`Tickets.session`) and can never be the proof of its own ticket.
- Existing tests changed because their expectation changed BY DESIGN (say so in the final PR): `tests/test_v94a.py` (the model credential sits on
  the Claude step, not on the job), `tests/test_v12_org.py` (a ticket cannot be closed with a made-up reference any more; "no engine registered" is now
  "engine switched off"; D12 left the pending set; the registry fixture copies execute.py).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executes | Fails when broken |
|---|---|---|
| A ticket is compiled into a typed change or refused with the reason; its free text is never executed | `execute.apply`, `_start`, the five `_plan_*` | ticket rejected, ledger row `refused`, nothing written (tests: more than 20 refusal cases) |
| Intent before, applied + read-back after, then a verdict with its proof; rows only appended | `execute._start`, `_applied`, `_judge`, `_log` | `lever_verified` FAIL ("without an intent row", "verified without a proof", "rolled back without a ledger row") |
| Verified only by rows another component wrote after the change | `_verify_knowledge` (later run, exact version), `_verify_setting` (video made after, the lever's checks), `_verify_arm` (features of later videos), `_verify_build` (checks on the merge commit) | stays `applied`; no evidence inside the window = rollback |
| A department turns only its own registered lever, right type, inside range, one step, never a cell no code reads | `levers.check`, `registry.may_change` | refused before anything is written |
| The direction that weakens a gate, costs more or changes the plan waits for the owner's tap | `levers._owner_reason`, `execute._ask_owner`, `_on_answer` | state `awaiting_owner`, cell unchanged; ONE message |
| A setting / experiment changes between videos; one unverified change per department | `execute.idle`, `_start`, `_wait` | state `queued` with the reason (one ledger row per reason) |
| Rollback never overwrites the owner's later value | `execute._undo_setting` (compare and swap) | ledger `rollback_skipped`, cell untouched |
| A rollback that fails, or a build out of attempts, goes up at once and the owner hears | `execute._fail` -> `memos.escalate` -> watchdog | `lever_verified` FAIL; owner message (tests assert the message) |
| A ticket closes only on the ledger; only the engine closes it that way | `memos._proof_problem`, `memos._roles` | MemoError, memo unchanged |
| Waiting for proof is typed, bounded and needs the applied row | `memos.await_proof` | MemoError |
| Knowledge by lever needs the Council's authority, never the owner's words, must fit the playbook at once | `_plan_knowledge`, `palace.add`, `_present_knowledge` | refused; an item that does not fit is retired again at once |
| A department's rulebook is bounded | `_plan_knowledge` (`EXEC_RULES_PER_DEPT`) | refused |
| A code build merges by itself only when the real diff adds new test files and nothing else | `levers.merge_scope`, `execute._verify_build` | owner's Merge message with the reason (tests: 10 kinds of diff) |
| At most 1 + 2 builds; closed pull request, red main, silent main are never "done" | `execute._retry_build`, `_judge`, `_undo_build` | state `failed`, escalated |
| No credential on the step that reads the spec | `.github/workflows/claude-build.yml` | `tests/test_v12_exec.py` (job env, step env), `tests/test_safety.py` |
| Nothing decided stays text | `execute.decision_issues` | `decisions_executed` FAIL (no ticket, ghost ticket, forged close, late and nobody told) |
| The tick pass is alive | `execute.engine_tick` (`EXEC_TICK_AT`), `lever_issues` | `lever_verified` FAIL after a day; a test runs the REAL tick job and fails when the call is removed |
| The lever table is honest | `levers.issues` in `registry.data_issues` and in `lever_verified` | `python -m whatifs.org.runner` RED; check FAIL; tests |

#### Step 6 PROVE
- `tests/test_v12_exec.py`: **88 tests (46 functions)**, each rule both ways: 18 kinds of setting value refused; the direction rule for every lever
  type; a setting from queue to applied to verified with the exact ledger rows; rollback on the lever's own check (and NOT on another check); the
  owner's hand-typed value surviving a rollback; the window ending; the approval message word for word, asked once, Approve / Reject / approve while a
  video is being made; one unverified change per department; a ticket a person closes; an apply killed before and after the write; a rollback that
  fails (the owner hears); knowledge accepted, served, verified with the session named; a proposed takeaway accepted by the Council; a changed text
  restored; knowledge nobody is served retired again; a prompt-mode department must cite; 8 kinds of knowledge ticket refused; the bounded rulebook;
  an experiment arm from registration to the features of two later videos; an arm nobody carries retired; 4 kinds of arm refused; a code ticket to
  build request to dispatch to pull request to automatic merge to green main; outside the scope -> the owner, once; red checks -> two re-builds ->
  escalation; no pull request; red main -> revert build + escalation; silent main -> escalation, no revert; a closed pull request; 10 kinds of diff
  against the merge scope; the workflow file; the memo doorway; both checks with every FAIL condition; the real tick job; and the real pipeline
  twice (a knowledge ticket verified in the first video, a setting ticket applied in the gap and verified by the second video's retention check).
- Faults the tests and the re-reading found in the new code, all fixed (repair attempts: none reached 3): points (1) to (5) of step 4 "changed against the design
  memo" and the unnoticed removal of the tick call; plus two mistakes of my own on the way: a patch pasted through a shell here-document lost
  its backslashes, failed its own assertion and the UNPATCHED script reformatted the whole founding-knowledge file (restored from git, redone from a
  file - the warning under HOW TO RUN is right); and new founding items addressed to D1 and the Council pushed three more low-priority limits out of
  D1's playbook (audiences narrowed: D1 is back at 3; the Council went from 5 to 6, open issue 6).
- Live proof on the real repo: the engine's call removed from `manage.tick` -> the new wiring test fails (1 failed), restored -> passes. One lever rule
  deleted from `levers.py` -> `python -m whatifs.org.runner` RED naming it. NOTE: the truth scan stayed GREEN in the first case - it counts names and
  the name still appears in the rehearsal and in the docs generator; that is why the wiring test runs the real job.
- Fake rehearsal on the final code: **GREEN** - contract script 24 / 24, final 19 / 19; 9 department runs, 9 takeaways; the rehearsal's decision:
  ticket -> `intent > applied > verified`, proof "Sessions:... (D6 assets) ran after the change with PI-...@1 in its playbook".
- Full suite: **1201 passed / 0 failed / 1 skipped** (65 files, one uninterrupted run by itself on a frozen copy of the final code commit ad99fd2; the skipped
  test is the dashboard render, which needs node - GitHub runs it: 1202). An earlier full run (commit 822dfa3) had 1197 / 0 / 1 in 64 files and the 65th
  file stopped by the runner's 15-minute limit - my mistake: the sweep was running at the same time (by itself that file takes 477 s).
- Sweep (standing rule 2): on a frozen copy of 822dfa3 - A: 40 fixed ids, organisation ON: **40 ok, 0 held, 0 crashed** (each: status SCHEDULED, 9 department
  runs verified, 0 live memos, 0 owner messages, 0 degraded steps); B: 10 ids with ORG_ON = FALSE: **10 ok** (35 PASS + 8 N/A); C: 8 full rehearsals with
  a forced id: **8 ok** (status LIVE, 39 PASS + 4 N/A, the rehearsal's decision verified on the ledger in each). **58 of 58 green.** Warning classes: the
  same 9 in every episode and 1 in 1 of 40 as in B0b - none is new. The two later code commits (one status word of one check; the one-second rule of the
  verifier) each got a short sweep on its own frozen copy - 7f9e7fd: 4 + 1 + 2, ad99fd2: 3 + 3 rehearsals: **13 of 13 green** (organisation ON and
  nothing decided: 38 PASS + 5 N/A).
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (118 founding items). Organisation **GREEN**.
- GitHub Checks (standing rule 1): every commit of the batch read on the public run page. Runs 54, 55, 56 GREEN (56 = 822dfa3: 1201 passed, 0 skipped,
  rehearsal GREEN). **Run 57 (7f9e7fd): RED - 1 failed / 1200 passed**: this batch's own end-to-end test, at an assertion whose first part held
  (`'verified' == 'verified'`). Traced, not re-run (step 4, point 8): the proof named a later run than the test expected, because the next run of the
  department had begun in the same clock second as the change. Honest limit of that diagnosis: the public run page shows only the first line of the
  assertion (log lines need a sign-in); the failing part is INFERRED - it is the only part of that assertion that depends on timing - and the
  mechanism is reproduced in `test_a_later_run_in_the_very_second_of_the_change_counts...`, which fails on the old code. Run 58 (e362042: the same
  code + one CLAUDE.md recipe) GREEN half an hour later - the fault is a matter of milliseconds. **Run 59 (ad99fd2, the final code commit, with the fix and a test that fails on the old code): GREEN - 1202 passed,
  0 skipped, rehearsal GREEN (episode id EP202611101921, script 24 / 24, final 19 / 19).** The one warning on every run page is GitHub's own (Node.js 20
  deprecated for `actions/setup-node@v4`; open issue 37).
- Money: Rs 0 added (no model call). Not measured in production: nothing is live until the final PR.

#### Step 7 TAKEAWAY (also Palace item `b4.takeaway`)
- WORKED: asking of every proof "who wrote it, and when?". The first verifier accepted a playbook holding the OLD text of an item and would have
  called an unchanged department "verified". Proof now names the version, the session and the playbook.
- WORKED: re-reading the finished engine as a stranger before the long runs. It found the three faults no test had asked about: the week-long wait of
  a ticket for a department that only runs inside a video, the blind revert of a healthy merge, and the dead tick nobody would have noticed.
- WORKED: testing the silence again (B3's lesson): every state that waits now has a clock that ends, and every end has somebody who is told.
- WORKED: standing rules 1 and 2. GitHub's faster machine failed ONE test once (run 57) that the laptop, the 58-run sweep and the runs before and
  after it all passed. Traced from the public run page alone to a one-second ordering rule, reproduced in a test, fixed. The run after it was green
  on the SAME code: had the red run been re-run instead of traced, the fault would have gone into production as "flaky".
- WATCH: until the Council exists (B6) NO real ticket is written. The engine is proven by tests and the rehearsal; it changes no video by itself.
- WATCH: "served" is the proof for knowledge and rules today; "cited" arrives when B6 puts playbooks into prompts (the verifier already demands it then).
- WATCH: the code lever has never touched the real GitHub (no keys on this laptop, by rule): the diff reader, the checks on the merge commit and the
  changed workflow file are proven with stand-ins and by reading. The first organisation build must be watched (open issue 29).
- WATCH: at one video a week a setting change takes about a week to verify and a failed check rolls it back even when the script was simply weak.
  That is the price of isolation; the Council will see "rolled back: EP... failed <check>" and may ask again.
- WATCH: a name-count scan cannot protect a wiring with a common name. For every new hook: one test that runs the real job.

### B0b - Baseline re-check (10 Nov 2026) - ACCEPTED (final code commit 9c5d0e3 GREEN in GitHub run 52)
Result in one line: the code the build stands on was re-proven the hard way - 58 full fake pipelines over fixed episode ids are green - and the real
faults turned out to sit in the PROOF, not in the pipeline: a comparison that ran on no machine, GitHub's Checks measuring another major version of
OpenCV than production, red runs nobody could read, and features that were built or promised but never wired. All four classes are now refused by
code. Honest limits: nothing here changes a video; the never-wired features are listed and marked, NOT built (open issues 22-25; the owner decided
on 10 Nov that the largest one, the room value test, is to be BUILT in B8).
No new feature, so no seven-step loop; the six steps of the B0b plan are recorded instead, plus the research behind the new rules.

#### Step 1 - GitHub Checks read for every commit since the baseline
- Runs 42, 43, 44 (B3's three last commits): GREEN. Run 45 (the sweep tool): GREEN.
- Run 38 (B2 final, red at the rehearsal step): CAUSE CONFIRMED without a sign-in. The rehearsal step started at 11:11:33 UTC, the rehearsal names
  its episode by the minute, and on the old B2 code `tools/sweep.py --mode rehearsal --ids EP202611101111` is HELD by `promise_paid` ("promise first
  shown at 44.7 s (limit 30 s)") and then dies on `r["master"]`, exactly a red rehearsal; the ids of 11:12 and 11:13 pass. It is the stale promise
  flag B3 fixed. On the NEW code the same id passes both gates (35 checks PASS, no FAIL, status SCHEDULED).
- Runs 27, 30, 32: red at unit tests, already explained (before B0's fixes; the two mid-batch commits of B1 / B1b).
- Runs 46, 47, 48: RED at unit tests BECAUSE THE NEW RULE WORKED - the first runs in which the reference-frame comparison really ran on GitHub. Their
  annotation named the cause in one line: OpenCV 5.0.0 on GitHub, 36 of 36 frames differ (step 3 below). Run 49, the first with the library pin (step 5): GREEN - 1111 passed, 0 skipped, rehearsal GREEN. Runs 50, 51, 52: GREEN.

#### Step 2 - the sweep (`tools/sweep.py`, kept tool)
- One process per id (module state never leaks), fixed future-dated ids `EP2099MMDDHHMM` that are the same on every machine, one RESULT line per id
  with the outcome, failed checks + evidence, warning classes, degraded steps, owner messages and the organisation's runs; a work folder inside the
  repo is refused; episode folders are deleted after each id (117 MB each).
- A: 40 ids, organisation ON: **40 ok, 0 held, 0 crashed**. Every id: status SCHEDULED, 37 checks PASS + 4 N/A, 9 department runs all verified, 0 live
  memos, 0 owner messages, 0 degraded steps.
- B: 10 ids with ORG_ON = FALSE (the old path): **10 ok, 0 held, 0 crashed** (35 PASS + 6 N/A: the two organisation checks are N/A by design when the organisation is off).
- C: 9 full rehearsals with a forced id (the path GitHub runs): **8 of 8 fixed ids ok** (status LIVE, 37 PASS + 4 N/A, every assertion of the rehearsal holds).
  The ninth run was the id of run 38's minute on the NEW code: it passes both gates (it was held on the old code); the rehearsal then stops on its own
  assertion that the two organisation checks PASS, which cannot hold for an id dated before the organisation started on the Sheet (N/A by design).
  Counted as explained, not as green: 40 + 10 + 8 = 58 green pipelines.
- Warning classes: 9 appear in every episode and 1 in 1 of 40, all traced (step 3). None depends on the id.

#### Step 3 - every class traced to its cause
| Class | Cause | Verdict / action |
|---|---|---|
| JUDGE / WITNESS "no checked voice available" (every id) | the sweep recipe runs no voice lab, so tab Voice_Check is empty | recipe artifact; the fallback to the default prebuilt voice is the designed one |
| "script length ... adjusting", "retention gate ... / fix did not reduce", "Showrunner's premise was not one of the scored pitches" (every id) | the canned fake replies (a 158-word script, a premise outside the pitch list) | fake-data artifacts; each is a guarded fallback, and the HARD checks judge the final script (`retention` PASS on all 40) |
| "atmosphere over its time budget (153% > 30%) - particles switched off" (every id; fog too on 1 id) | the time valve `ATMOSPHERE_MAX_OVERHEAD_PCT`: in the SMALL fake render the rest of the frame work is tiny, so the share is always over | by design, logged, stored in `Episodes.atmos_json`; whether it trips at full size can only be seen on the first real render (open issue 26) |
| "prompt cache: two calls share a prefix but differ in model parameters" (every id, twice) | REAL: `CACHE_ALIGN_EFFORT` (default TRUE) is read by no code; `models.aligned_effort` was tested but never called in any version | measured on one fake episode: 21 calls, 44,006 tokens read from cache, 14,538 written, hit ratio 0.75; the two misses cost about one extra cache write each, an estimated Rs 3-10 a video (NOT measured in production). Not wired now, because aligning efforts would LOWER or raise the effort of a creative or judging call (breakout first); cell marked NOT ACTIVE; open issue 23 |
That one real class led to a scan of the whole table, and then of tabs and functions:
- **8 of 691 Settings cells are read by no code, in any version ever pushed**: `CACHE_ALIGN_EFFORT`; `ROOM_VALUE_ON` (default TRUE), `ROOM_VALUE_EVERY`,
  `ROOM_MIN_WINRATE` - the blind test "writers' room script against a single-prompt script", with its own tab, about Rs 15 a video, was NEVER BUILT;
  `RUNTIME_HARD_MAX_SEC` (the code enforces `RUNTIME_MAX_SEC`); `PKG_VARIANT_C_IMAGE`; `VIEWER_NAME_ON_SCREEN` (no code shows a name, so the safe
  default is what happens); `PREMISE_BENCH_MAIL_MONTH`.
- **2 of 78 tabs are used by no code**: `Room_Value`, `Repairs`. **10 of 1,404 functions are called by no production code**: `models.aligned_effort`,
  `show.bible_issues` (the check of the character bible for protected names, real people and child characters - only tests call it),
  `enforce.fix_markers`, `enforce.fix_retention`, `prompts.episode_pack`, `publish.meta_bio`, `data.ptype_for`, `shotplan.prompt_variety`, and the two
  hooks B4 will call (`registry.may_change`, `runner.set_executor`).
- What was done about them now: each is listed in `whatifs/truth.py` with what is TRUE today, the 8 cell notes start with "NOT ACTIVE (no code reads this
  cell)" and SYSTEM.md section 4 prints all three lists, so no chat and no owner is told a behaviour exists that does not. What was NOT done: none of
  them was built or wired in this batch (each needs its department's batch or an owner word - open issues 22-25).
- Known candidates of the plan: open issue 1 measured (below); open issue 16 not triggered by any id (stays with B7); open issue 20 closed by the
  episode-id trace (step 4).
- Open issue 1 measured: world particles at real 1080p, 12 seeds x 4 worlds, one 4-second shot each: 43 of 48 shots read 100% alive, the lowest are
  rain 57% / 71% / 86% and embers 71%; dust and wind 100% on all seeds. No id of the sweep failed `aliveness`. The per-shot guarantee is still missing.

#### Step 4 - the tests the laptop skipped (6)
| Test | Did GitHub run it? | Now |
|---|---|---|
| `test_safety` restore step (python-docx) | yes | python-docx installed in the venv; the test now also uses the interpreter that runs it (it called whatever `python` was first on PATH) |
| `test_v94b` dashboard render (node) | yes | still skipped on the laptop (node not installed; not worth an install - GitHub runs it) |
| `test_v91_core` + 2 in `test_v91_matrix`: the picture equals the reference frames | **NO - on no machine** | always compared now, see below |
| `test_v87` mirror files of the old upload package | **NO - on no machine** (the folder exists nowhere) | removed, with the dead branch of one `test_v89` test |
- The reference-frame comparison skipped wherever OpenCV / NumPy differed from the versions the file was made with (4.13.0 / 2.4.4) - and production
  and Checks pin NumPy below 2.1. 22 more comparisons in `test_each_flag_alone` and one in `test_v91_atmos` were switched off by the same guard without
  even counting as skipped. Forced to run with the original versions on this laptop: **25 failures, 36 of 36 frames differ**. Bisected: the commit
  that added the file matches on Windows too (so the frames are identical across Linux and Windows), live `main` matches, the handoff snapshot does not;
  with `PARTICLES_ON` = FALSE the current code matches again on 4.13.0 / 2.4.4 AND on 4.14.0 / 2.0.2. So: NO regression in the base renderer; the
  particle layer (on by default, intended) is the whole difference; and the version guard had been hiding that the promise "all switches off = the old
  picture" was unchecked. Now: `tests/golden_frames.py` `v9_baseline` (later layers off) + `same_as_v9` (never skips; the message says whether the code
  or an unverified library version is the suspect); a new default-on render layer fails it until its switch is listed.
- The no-skip rule: `tests/skip_policy.py` + `tests/conftest.py` + `WI_NO_SKIPS=1` in the Checks workflow. Proven with real pytest on this laptop both
  ways: the file with the node test exits 1 and names the test on a strict run, exits 0 on a normal run; files without a skip exit 0 on a strict run.
- A red run names its cause in public: `tools/ci_report.py` after the unit tests and after the rehearsal writes annotations + an uncapped job summary
  (failed and skipped tests, failed contract checks with the reason, the last error line, the episode ids a failed test printed, and the command that
  reproduces a red rehearsal). The step still ends with the tests' own exit code.

#### Step 5 - B0's two fixes on Linux, and what GitHub was really measuring
- `whatifs/reels.py` (Windows-only path lines) and `whatifs/render.py` (particle seed): GitHub run 28 (B0 final) and every later unit-test step are green on
  Linux, the particle test included.
- FOUND by the first annotated run: `pip install opencv-python-headless` without bounds in the Checks workflow installs **OpenCV 5.0.0**, while
  `requirements.txt` (production) pins `>=4.9,<5`. Every green GitHub run of B0-B3 was therefore measured on another major version than the one that
  renders the videos; with 5.0.0 all 36 reference frames differ. Fixed at the root: all 13 workflow pip lines that name a pinned package now carry the
  bounds of `requirements.txt` (OpenCV in 4 workflows, plus pillow, requests, soundfile); a test fails on any line that does not, and another fails when
  the installed or imported version on the test machine is outside the pins. The pipeline's own jobs install from `requirements.txt` and were always right.

#### Research behind the new rules (dated sources; E = measured, O = official / practice)
1. E - Kim, Chen et al., "How Disabled Tests Manifest in Test Maintainability Challenges?", ESEC/FSE 2021: 122,000 commits, 15 systems; 41% of disabled
   tests never come back, most stay disabled for years. -> no test may skip where acceptance is decided.
2. E - Dutta et al., "Detecting Flaky Tests in Probabilistic and Machine Learning Applications" (FLASH), ISSTA 2020: running tests under many seeds found
   11 new flaky tests in 20 projects. -> the sweep over fixed ids.
3. E - Dutta et al., "To Seed or Not to Seed?", ICST 2022: 114 projects; fixing one seed is a workaround that hides the failing seeds. -> the rehearsal
   keeps its time-based id, and the id is printed so a failure is reproduced, not re-run away.
4. E - Parry et al., "Systemic Flakiness", EASE 2025 (arXiv 2504.16777): 810 flaky tests; failures cluster around shared causes. -> one cause (the promise
   flag) explained both B3's held test and run 38; trace the cluster, not the single red.
5. E - Chen et al., arXiv 2502.02760 (Feb 2025): randomised hash order exposes implementation-dependent flakiness. -> same class as B0's particle seed.
6. O - GitHub Docs, workflow commands (read 10 Nov 2026): error / notice annotations, job summaries (20 step summaries a job); GitHub community
   discussion 68471: 10 error annotations a step, the rest dropped silently. -> 8 causes + "and N more" + totals, full list in the job summary.
7. O - Flutter golden-file guide and others: reference images are compared on one defined platform, usually with a tolerance. -> measured here instead
   of assumed: the frames are bit-identical on two systems and two version pairs, so the comparison stays exact, and the failure message names an
   unverified library version as the first suspect.

#### What changed (code)
- NEW `tools/sweep.py`, `tools/ci_report.py`, `tests/skip_policy.py`, `tests/test_v12_b0b.py` (20 tests).
- `whatifs/truth.py`: `settings_issues` / `unread_settings`, `wiring_issues` / `unused`, the three shrinking lists; all three run inside `truth.issues`, so
  Plan Guard, the tests and contract check `docs_current` enforce them. `tools/gen_docs.py`: SYSTEM.md section 4 prints the lists.
- `whatifs/core.py`: 10 notes reworded (the 8 dead cells + one stale cadence note + the safe-mode note); NO default value changed.
- `.github/workflows/`: Checks runs strict + reports (2 steps); 13 pip lines pinned like `requirements.txt`.
- Tests: `tests/golden_frames.py`, `test_v91_core`, `test_v91_matrix`, `test_v91_atmos` (always compare), `test_v87` (-1 dead test), `test_v89`, `test_safety`,
  `tests/conftest.py` (skips, episode ids of failed tests). `tests/golden/v9_render_frames.json`: verified versions recorded.
- 8 matrix rows; 6 founding Palace items `b0b.*` + the owner's decision `owner.room_value_test` (111 items, 0 refused; build rules entered as techniques for D12 / D8 so that no limit was pushed out
  of a playbook - the first try as policy rules pushed out 8).
- Laptop venv: + python-docx, + pytest 9.2 (real pytest for single files: `../.venv/Scripts/python.exe -m pytest tests/<file> -q`; the stand-in runner
  still wins when PYTHONPATH points at the shim).

#### Proof
- Each new rule both ways, live on the real repo: a Settings cell nothing reads -> Plan Guard RED, check `docs_current` FAIL, test file 12 / 1; a function
  nothing calls -> Plan Guard RED; files restored -> GREEN. The particle layer left on -> the reference comparison FAILS (a kept test). A strict run with
  a skip -> exit 1 (real pytest). A failed test under real pytest prints its `EPISODE-IDS` line.
- Mistakes of my own on the way (repair attempts, none reached 3): the first sweep chain was started behind a failed clean-up command and ran on the
  working tree (stopped, restarted on a frozen copy of the commit); `tools/ci_report.py` was broken twice by a shell that eats backslashes in pasted
  code (now only written through the file tools); the settings scan first counted its own list as a reader; 4 truth tests failed on a fixture without
  a settings table.
- Laptop, final code: full suite (64 files), ONE uninterrupted run with the stand-in runner: **1113 passed / 0 failed / 1 skipped** (1088 before; + 20 in
  `test_v12_b0b`, + 1 live test of the reference comparison, + 4 that used to skip and now run). The 1 skip is the dashboard render test (node), which GitHub runs.
- Fake rehearsal on the final code: **GREEN** - episode id EP202611101515, contract script 22 / 22, final 19 / 19. Plan Guard GREEN (truth scan included), Palace GREEN
  (111 founding items, 0 refused), SYSTEM.md regenerated, no drift.
- GitHub: final code commit 9c5d0e3 = run 52: **GREEN** - 1114 passed, 0 skipped (real pytest, Ubuntu, OpenCV under 5), rehearsal GREEN with episode
  id EP202611101504 (22 / 22 + 19 / 19) - read from the public annotations, no sign-in. Runs 49, 50, 51 GREEN too; runs 46, 47, 48 RED for the one
  explained cause (OpenCV 5.0.0 before the pin). The commit that adds this record changes this file only (run 53): a record cannot contain its own
  run, so the next session reads run 53 before it starts B4.
- Money: Rs 0 (no model call, no paid step). Nothing is live until the final PR.

#### Takeaway (also Palace item `b0b.takeaway`)
- WORKED: making the failure readable first. The first run whose failures were written onto the public page showed in one glance what four batches of
  green had hidden (OpenCV 5 on GitHub). Before trusting any proof, ask where it really runs and whether it can skip.
- WORKED: following ONE warning to its cause instead of classing it as noise. The prompt-cache line led to a cell nothing reads, that to a scan of every
  cell, tab and function, and that to a paid test that was never built.
- WORKED: bisecting with the original library versions instead of regenerating the reference frames. Regenerating would have signed off the unknown.
- WATCH: "listed and marked" is not "built". Open issues 22-25 are real gaps; the lists only stop them from growing and from being believed.
- WATCH: the sweep is fake mode. It proves the plumbing for many ids, not the taste of a real script; and the time valve of the atmosphere always trips
  in the small render, so the full set of layers is never rehearsed past frame 120.
- WATCH: knowledge items written as limits push other limits out of the 1,800-token playbooks at once (seen and undone here; open issue 6 stands).

### B3 - Memo system + Department contract (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: the project now runs like an organisation at the level of code - every step of the long video that belongs to a department, and the
daily learning job, goes through LOAD -> ACT -> EMIT -> LEARN -> EXECUTE -> REPORT with a proof per step; departments talk through validated memos with
deadlines that escalate to the owner; a failed check or a crashed step becomes a problem memo for the department that owns it; two new HARD checks hold
the video when a department walks around the contract. Honest limits: 7 of 15 departments are wired (8 are pending by plan); the playbook is HANDED to
each run but is not yet inside any model prompt (B6), so B3 by itself changes no video; no ticket can be executed until B4.

#### Step 1 RESEARCH (11 dated sources; E = measured evidence, O = opinion / practice / official guidance)
1. E - Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (MAST), arXiv 2503.13657, 17 Mar 2025 (v3 26 Oct 2025, NeurIPS 2025): 1,600+ annotated
   traces, 7 frameworks, 14 failure modes. Largest: step repetition 15.7%, reasoning-action mismatch 13.2%, unaware of termination conditions 12.4%,
   disobey task specification 11.8%; verification failures together 23.5%; "ignored other agent's input" 1.9%, "fail to ask for clarification" 6.8%.
   Better role prompts gave +9.4%, an added verification step +15.6%, and the authors say prompt fixes are inconsistent and the cause is
   organisational design, not the model. -> the six steps are a state machine in CODE with a proof per step; nothing relies on a prompt saying "follow the steps".
2. E - Wang et al., "The Unreliable Progress Bar", arXiv 2609.08589, 8 Sep 2026: models report their own task progress unreliably while work is under
   way; "frameworks should not control task flow on the strength of the model's state reports alone". -> a memo or a step changes state only on
   evidence that code observed (ids returned by the store, a cost counter, a ledger row), never on a claim.
3. E - Wang, Goyal, Chandrasekharan, Sundaram, "Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM Handoffs", arXiv 2608.29028,
   29 Aug 2026: a compressed handoff keeps the facts and loses the rules about how they may be used (boundary survival 0.80 -> 0.57 at a 25-word
   budget while facts stay near ceiling); vague boundary wording leaked in 73% / 50% of cases, explicit constraints under 15%, a typed audience
   allowlist nearly zero. -> a memo carries a typed audience list enforced by code on read and a `constraints` list that is never shortened.
4. E - Dubey, "Real-Time Detection and Repair of LLM Agent Failures", arXiv 2608.02464, 3 Aug 2026 (2,823 episodes): a deterministic verification
   layer (recompute stated totals from tool results, check required calls) caught 60% of failures, 96% with a coverage check, 0 false positives;
   roll back + re-run recovered 45% vs 16%. -> the runner recomputes cost and counts itself and runs a coverage check: every inbound memo that was
   loaded must be dispositioned.
5. E - Dennis et al., "In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks", arXiv 2604.27891, 30 Apr 2026: an external
   orchestrator graph failed 9-24% of conversations against 0.5-11.5% for one prompt holding the whole procedure. -> departments are code wrappers;
   the organisation adds NO model hop; knowledge goes into the existing call's context (and Rs 0).
6. O/official - Anthropic, "How we built our multi-agent research system", 13 Jun 2025: a delegated task needs an objective, an output format,
   tool guidance and clear boundaries; multi-agent runs cost about 15x a chat; resume from a checkpoint instead of restarting; pass artifacts by
   reference. -> every asking memo needs `subject` + `done_when` + `constraints`; bodies are small and link to artifacts; each run leaves a durable row at start.
7. O/official - PagerDuty escalation policy docs (read 10 Nov 2026): not acknowledged inside the timeout -> next level; acknowledging halts
   escalation but does not resolve; a policy repeats a bounded number of times (9) and then stops. -> two clocks per memo (acknowledge, resolve),
   a ladder as data, bounded owner reminders.
8. O/official - A2A Protocol specification 1.0.0 (a2a-protocol.org, read 10 Nov 2026): task states submitted / working / input-required /
   auth-required / completed / failed / canceled / rejected; a task in a terminal state accepts no further message; the sender's message id is used
   to detect duplicates. -> memo statuses and legal moves are data; a terminal memo is immutable; a recurrence is a new, linked memo.
9. O/practice - Richardson, "Transactional outbox" (microservices.io, read 10 Nov 2026): a relay can publish the same message twice, so the
   consumer must be idempotent. -> a Sheet has no transaction, so the memo id is the hash of (type, sender, audience, dedupe key): writing it twice is a no-op.
10. E - Yin et al., "From Reflection to Co-Evolution: Self-Evolving Agents with Locally Verified Memory" (Anchor), arXiv 2611.10382, 7 Nov 2026:
    most self-written lessons barely change a decision and some reinforce the wrong action; admitting only verified ones gave up to +19.9% success
    with 41% fewer stored memories. And E - Asadolahi et al., "Memory Reward Inflation in Self-Improving LLM Agents", arXiv 2608.00017, 29 Jun 2026:
    self-graded memories inflate and a judge with correlated errors cannot fix it. -> a takeaway cannot score itself, is built on measured outcomes,
    enters the Palace only as `proposed`, and only when it is new (a confirmation is counted, not stored again).
11. E (numbers from secondary summaries, not re-checked against the paper) - Hong et al., MetaGPT, arXiv 2308.00352 (2023, ICLR 2024): structured
    documents and subscriptions instead of free dialogue raised executability (reported 3.75 of 4). -> departments subscribe to memo types.
Not established by any source found: a controlled study that isolates typed schema validation of handoffs (only vendor claims exist); and what SLA
lengths are best for an automated content organisation - the hours below are a design choice taken from the master spec, to be tuned by D1 later.

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Spec-literal": a Memos tab with a JSON body, `write / ack / resolve`, a watchdog that flips overdue rows to escalated, a runner that calls six
  functions in order. 2/2/5/3/5 = 17. Weak: "the step ran" is proven only by the call; a re-run duplicates memos; a takeaway can be boilerplate;
  nothing stops production from calling the old module directly; a raise after the upload step could cause a second upload on the retry.
- B "Research stack": typed schemas, statuses and moves as data, two clocks + bounded ladder, hashed idempotent ids, deterministic verification
  with a coverage check, delegation fields, boundary fields, takeaways gated by measurement. 3/4/5/4/5 = 21. Weak: still a wrapper production can
  walk around; "a takeaway every run" floods the Palace; escalation would wait on departments that do not exist yet.
- C "The receipt chain" (ORIGINAL, on B's mechanics):
  1. Receipts, not claims: the proof of each step is assembled by the runner from what code observed and hash-chained in order; a run is complete
     only with all six links; the gate re-computes the chain.
  2. Never lose paid or irreversible work (my own rule, from reading the upload path): before ACT the runner is strict (it raises before any money);
     after ACT a failed step becomes a recorded BREACH and the result of ACT is still returned - the gate, not an exception, then holds the video.
  3. The episode gate judges the organisation: HARD checks `dept_contract` (script stage, before picture money) and `takeaways_written` (final stage,
     before upload).
  4. Escalation never waits on a department that cannot act: the ladder department -> Council -> owner skips every holder that has no wired entry
     point, computed from the registry, so the Council is skipped until B6 wires it and joins by itself afterwards.
  5. An honest registry: a department either names real call sites that run under the runner (verified by reading the code) or is listed as
     pending with its batch; the pending list can only shrink and SYSTEM.md prints it.
  6. Measured takeaways with a novelty gate: built from the run's measured outcomes against the department's own history; only a deviation or a
     failure is proposed to the Palace; a confirmation is counted. Model-written lessons join in B6 / B8 through the same validator.
  7. Boundaries travel verbatim: audience allowlist enforced on read, constraints never shortened (too long = refused on write), ONE render function.
  8. Two clocks plus attempts: a third failed attempt escalates at once; a terminal memo is immutable; a recurrence opens a linked successor.
  9. One tap at the one model doorway (`models.ask`): counts a run's model calls and, for a department in "prompt" mode, puts the playbook into the
     cached layer of the system prompt and proves it was there. B3 wraps the real departments in "brief" mode (behaviour unchanged, as the plan
     orders); B6 flips the creative ones to "prompt" in the registry.
  4/5/5/4/5 = 23.
- DECISION: C.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/schemas.py` (memo types, bodies, SLA clocks, statuses and moves as data; real JSON Schema output; a small validator, no
  new dependency), `whatifs/org/memos.py` (write / inbox / ack / start / resolve / reject / escalate / watchdog / render), `whatifs/org/registry.py`
  (15 departments: mission, wrapped modules, cadence, levers, monthly thinking cap, subscriptions, owned checks, wired entry points or pending batch),
  `whatifs/org/runner.py` (`run` = strict six steps; `work` = the wrapper for existing production call sites). Tabs appended: `Memos`, `Sessions`,
  `Takeaways`, `Org_Audit` (`Tickets` and `Lever_Changes` arrive with the Execution Engine in B4; a ticket is already a validated memo type).
- Wrapped in B3 (behaviour unchanged; 9 call sites in `whatifs/episode.py`, 1 in `whatifs/cli.py`): D4 write, D7 voice, D5 package, D6 plan,
  D8 script gate, D6 assets, D6 render, D8 final gate, D9 publish; D10 daily learning. The SLA watchdog runs on every tick.
  Pending by plan: D0, D1 (B9), D2, D3 (B5), D11, D12 (B4 / B7), Council (B6), Librarian (B8).
- Memo traffic that is real after B3: problem memos (a department run that crashed -> D12; a failed contract check -> the department that owns the
  check), resolved by code when the same check passes again, the owner waives it or the episode is closed; takeaways from every run.
- EXECUTE in B3: the step always runs and reads the department's open tickets; with no engine registered a ticket is escalated at once with the
  reason (never left as text). B4 registers `execute.apply`.
- Money: Rs 0 (no model call is added). Monthly thinking caps per department are data now and enforced by the runner for runs that declare
  `budget="org"` (P0 continues, P1 / P2 wait - master spec section 9); the paid organisation calls themselves arrive in B5 / B6.
- Sheet traffic per run: about 4 reads and 4 writes; 9 runs per episode.
- Rejected: a JSON Schema library (new dependency for a subset we can validate in 60 lines); wrapping inside `room.py` / `publish.py` themselves
  (every test and side path would change behaviour at once - call sites first, the rest per department batch); a model-written takeaway per run
  now (about Rs 0.5 each and exactly the unverified self-lesson sources 10 warn about); raising on a bookkeeping error after ACT (double-upload risk);
  one owner message per stuck memo (noise - one grouped message, bounded reminders).
- Enforcement plan and tests: steps 5-6 (each rule both ways; the acceptance tests of the plan: a run without takeaway / without playbook
  injection / with an invalid memo FAILS; SLA escalation).
- Palace seed items: `whatifs/org/seed/build.json`, keys `b3.*`, written in step 4 once the code they point at exists (the write gate refuses a
  reference to code that is not there).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/schemas.py` (11 memo types as data: sender, audience, body, two clocks, statuses, legal moves, kinds of proof; a validator for the
  JSON Schema subset used; `json_schema(type)` gives the real schema; `check_memo`, `check_takeaway`), `whatifs/org/memos.py` (write / inbox / ack /
  start / resolve / reject / escalate / watchdog / sweep_episodes / render / stats), `whatifs/org/registry.py` (15 departments: mission, wrapped modules,
  rhythm, levers, thinking cap, wired call sites or pending batch, runs each gate needs, owner of each of the 41 checks), `whatifs/org/runner.py`
  (`run`, `work`, `verify`, `episode_issues`, `build_takeaway`, `audit`, `daily_check`, `health`; by hand: `python -m whatifs.org.runner`),
  `whatifs/org/wraps.py` (measures of each wrapped step, gate memos and their settlement).
- Tabs appended: `Memos` (30 columns), `Sessions` (21), `Takeaways` (16), `Org_Audit` (20). 9 settings: ORG_ON, ORG_SINCE, ORG_SLA_HOURS,
  ORG_ESCALATE_HOURS, ORG_OWNER_REMINDS_MAX (2), ORG_DEVIATION_PCT (25), ORG_CAPS_INR, ORG_RUN_STALE_H (6), ORG_WATCHDOG_AT.
- Two taps, each a few lines in a protected file: `models.ASK_TAPS` (every text call passes `models.ask`; the runner counts a run's calls and, in
  "prompt" mode, puts the playbook into the cached layer of the system prompt) and `core.COST_TAPS` (every logged cost is attributed to the run in flight).
- Production wiring: 9 call sites in `whatifs/episode.py` (D4 write, D7 voice, D5 package, D6 plan, D8 script_gate, D6 assets, D6 render, D8 final_gate,
  D9 publish) and the daily learning job in `whatifs/cli.py` (D10 daily) now run through `runner.work`; the SLA watchdog and the check for runs that
  never reported run on every tick (`manage.tick`); Setup and the first run mark when the organisation started on a Sheet (`ORG_SINCE`); the owner's
  answer to a stuck-item message is registered with the owner messages (`notify._ensure_handlers`).
- Checks: `dept_contract` (script stage) and `takeaways_written` (final stage): 41 HARD checks now (22 script + 19 final).
- Founding knowledge: 12 new items `b3.*` in `whatifs/org/seed/build.json` (11 research-backed + the takeaway): 104 founding items, 0 refused.
- Generated docs: SYSTEM.md section 11 (the six steps, the department table with wired / pending, memo types with clocks and kinds of proof, check owners).
- Changed against the design memo after seeing real behaviour: (1) a memo that asks for work is visible to the owner by default - the first deadline
  test showed a stuck memo reaching the owner's level and no message going out; (2) the runner settles the memos it wrote about a department's own
  crashes and breaches itself (a clean run of the same step is the proof) - otherwise a department's own breach memo blocked its next run; (3) one
  breach memo per CLASS (department, step, broken step), carrying no episode, so an episode going live can never close a broken contract.
- FIX of an existing fault found on the way (not organisation code; say so in the final PR): `whatifs/anim.py` - when the Animation Director moved the
  animated scenes, the `promise` flag stayed on a shot it had turned into a still; the re-aim in `episode.produce` was then skipped and `promise_paid`
  HELD THE FINISHED VIDEO at the final gate, after the picture money ("promise first shown at 43.7 s"). It depended on where the room had put its first
  animated scene, i.e. on the episode. Found because the new end-to-end test was held on one run out of four; reproduced with a fixed episode id with
  the organisation ON and OFF (same hold); now the flag leaves with the demotion and that episode passes with the promise at 0.3 s.

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| Six steps, in order, each with a receipt built by the runner and chained | `runner.run`, `runner._Run.receipt` | ContractBreach at the step; `runner.verify` -> `dept_contract` / `takeaways_written` FAIL |
| LOAD before any work: inbound memos acknowledged, a non-empty playbook from the Palace | `runner.run` (LOAD) | ContractBreach before ACT is called (also for `work`): nothing spent |
| The playbook reaches the work (brief: taken; prompt: inside a model prompt of the run) | `Brief.take`, `runner._ask_tap` | breach "no playbook injection" |
| A run may cite only Palace items its playbook served | `runner.run` (ACT) | breach "not in its playbook" |
| Every outbound memo valid or none is sent; every inbound memo dispositioned | `schemas.check_memo`, `runner.run` (EMIT) | breach "invalid memo" / "loaded and ignored" |
| At least one valid takeaway per run; stock, empty, ungrounded or self-scored refused | `schemas.check_takeaway`, `runner.build_takeaway` | breach at LEARN; `takeaways_written` FAIL |
| Only a new finding is proposed to the Palace, as `proposed`, one item per class | `runner._propose` -> `palace.add` | tests; the Palace guard keeps `proposed` out of every playbook |
| A ticket is executed by the engine or escalated at once | `runner.run` (EXECUTE) | tests; the ticket's own clocks |
| Never lose paid or irreversible work | `runner.work` (strict=False after ACT) | tests (upload id returned; the gate holds instead) |
| Every wired call site exists and is registered; pending list only shrinks | `registry.entry_issues` | `dept_contract` FAIL; `python -m whatifs.org.runner` RED; tests |
| Memo: valid, to the right audience, closed only with proof, never rewritten, never reopened | `memos.write`, `memos.inbox`, `memos._move`, `memos.resolve` | MemoError, nothing written / status unchanged |
| Two clocks; a miss climbs department -> Council -> owner, skipping a level that cannot act | `memos.watchdog`, `memos.escalate` | tests; `Org_Audit` rows |
| The owner hears once, bounded reminders, 3 messages a pass at most; DROP / KEEP by one tap | `memos._tell_owner`, `memos._on_answer` | tests |
| A dead watchdog is noticed | `runner.daily_check` (owner message after 6 h), `runner.episode_issues` (gate FAIL after 24 h) | tests |
| A run that never reported is flagged and becomes a problem memo | `runner.audit` (every tick) | tests |
| A failed check -> problem memo for its owner; closed by the ledger (passed / waived) or the episode's end | `wraps.gate_memos`, `wraps.gate_settle`, `memos.sweep_episodes` | tests |
| A department's own paid thinking stays under its monthly cap (P0 continues) | `runner.run` (budget "org"), `registry.caps`, `registry.spent` | CapReached before the run starts |
6 matrix rows added (docs/CURRENT/ENFORCEMENT_MATRIX.md; the meta-test proves every reference is wired). The rehearsal asserts: all 9 department runs
of the episode present, ok and verified; both checks PASS (not N/A); 9 valid takeaways; the watchdog ran; organisation health; no open problem memo.

#### Step 6 PROVE
- `tests/test_v12_org.py`: 99 tests (56 functions), each rule both ways. The plan's acceptance tests are in it: a department run WITHOUT TAKEAWAY fails
  (nothing reported / stock takeaway), WITHOUT PLAYBOOK INJECTION fails (brief mode never taken; prompt mode with no model call; Palace cannot feed it),
  with an INVALID MEMO fails (and none of its memos is sent); SLA ESCALATION (unacknowledged, unresolved, third attempt, through the Council once it is
  wired, never before the deadline). Also: 26 kinds of bad memo each refused with nothing written; all 150 combinations of status x move x role checked
  against the move table; a tampered Sessions row (missing step, reordered, edited receipt, wrong chain) fails verification; the upload id survives a
  broken contract; the real pipeline end to end (9 runs, both checks PASS) and the same pipeline with ONE department walking around the runner
  (held at the script gate, nothing made or uploaded).
- The tests found 3 real bugs in the new code, all fixed: the silent owner level, the self-blocking breach memo (both above), and a measure function that
  crashed on odd output (it would have turned a healthy step into a breach and held a video).
- Repair attempts used: test file first run 91 / 8 (4 causes: the 3 bugs and the voice stand-in missing in the end-to-end test) -> 98 / 1 (the
  measure bug had a second input shape) -> 99 / 0. Nothing reached the cap of 3.
- Live proof on the real repo: one wrapper removed from `whatifs/episode.py` + the stock-phrase rule switched off in `schemas.py` ->
  `python -m whatifs.org.runner` RED (naming the missing call site), the test file 89 passed / 10 failed, and the real pipeline HELD the episode with
  `contract:dept_contract`; files restored -> GREEN. The promise fix: its regression test fails on the old `anim.py` (13 / 1) and passes on the new.
- Full suite (63 files), ONE uninterrupted run on the final code: **1088 passed / 0 failed / 6 skipped** (988 before + 99 organisation tests + 1 promise
  regression test). No existing test needed a change. (A first full run before the promise fix was 1087 / 0.)
- Fake rehearsal on the final code: **GREEN** - contract script 22 / 22 (`dept_contract` included), final 19 / 19 (`takeaways_written` included);
  9 department runs, 9 takeaways, 0 live memos; Palace 109 items.
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (104 founding items). Organisation **GREEN**.
- Money: Rs 0 added (no model call). Not measured in production: nothing is live until the final PR.

#### Step 7 TAKEAWAY (also Palace item `b3.takeaway`)
- WORKED: reading the production path BEFORE wrapping it. The upload id is saved only after the upload returns, so a raise in between means a second
  upload on the retry: that one reading turned "any broken step raises" into "strict before the work, never throw the work away after it".
- WORKED: testing the silence. The deadline test asked "who hears about it?" and the answer was nobody. For every escalation or alarm in later batches,
  assert the message that goes out, not only the status that changes.
- WORKED: an end-to-end test on the real pipeline. It found a fault in code B3 never touched (the stale promise flag) that had been holding finished
  videos on some episodes. Trace an intermittent hold to its cause before calling it flaky: here it was reproducible with a fixed episode id.
- WATCH: "handed over" is not "used". After B3 no model prompt contains Palace knowledge. B6 must flip the creative departments to "prompt" mode and
  wrap the Script Preview / pre-production room first (open issues 12, 13).
- WATCH: a receipt proves that a step happened and what the runner saw; it does not prove the work was good. Quality stays with the contract checks.
- WATCH: the organisation's bookkeeping is now on the critical path: LOAD failing stops a department before it starts (by design). `ORG_ON` = FALSE
  is the switch if the organisation layer itself ever misbehaves; the Palace switch turns the organisation off with it.
- WATCH: until the Council is wired (B6) an unresolved memo goes straight from the department to the owner's level (issues 15, 17).

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
- B4: `whatifs/core.py` (2 tabs + 9 settings appended; nothing existing changed), `whatifs/episode.py` (ONE argument added to the brain's `tag` call: the
  long video's experiment arms are recorded in its features), `whatifs/manage.py` (one call on the tick: `EXE.engine_tick()`), `tools/repair.py`
  (PROTECTED list + levers.py, execute.py, builds.py), `whatifs/org/memos.py` / `schemas.py` / `runner.py` / `registry.py` (ledger proof on the memo
  doorway, the engine as verifier, the typed wait for proof, the engine as default executor, D12 wired), `whatifs/contract.py` (2 checks added; no existing
  check changed), `whatifs/truth.py` (2 list entries deleted, limit lowered). Also touched, not on the protected list before: `whatifs/builds.py` (new
  optional arguments and three read functions; the owner's own builds behave as before), `whatifs/cli.py` (one optional argument), `whatifs/notify.py`
  (one handler registered), `tools/gen_docs.py`, `tools/rehearsal.py`, and **`.github/workflows/claude-build.yml`** (one optional input `request`; the
  Sheet, WhatsApp, owner and merge credentials moved from the job to its last step; the model credential to the Claude step) - a WORKFLOW change that
  could not be run here: read it in the final PR.
- B0b: `whatifs/core.py` (10 Settings NOTES reworded: the 8 cells no code reads, one stale cadence note, the safe-mode note; no default value changed),
  `.github/workflows/checks.yml` (unit tests run strict and report; rehearsal reports; pip line pinned) and the pip line of 12 more workflows (same
  bounds as `requirements.txt`; OpenCV goes from 5.0.0 back under 5 in `preview.yml` job 2, `sheets.yml`, `repair.yml`; pillow / requests / soundfile
  resolve to the same versions as today). Also touched, not on the protected list: `whatifs/truth.py` (two scans + three lists), `tools/gen_docs.py`,
  new `tools/sweep.py`, `tools/ci_report.py`.
- B3: `whatifs/episode.py` (9 call sites wrapped with `ORG.work`; what each step does is unchanged), `whatifs/core.py` (4 tabs + 9 settings appended, `COST_TAPS`
  hook in `cost`), `whatifs/models.py` (`ASK_TAPS` hook in `ask` and `ask_batch`; a no-op when nothing listens), `whatifs/manage.py` (watchdog + audit on the tick,
  `install` in Setup), `tools/repair.py` (PROTECTED list extended with the org modules, `contract.py`, `truth.py`). Also touched, not on the protected list before:
  `whatifs/contract.py` (2 checks added), `whatifs/cli.py` (learning job wrapped), `whatifs/notify.py` (one handler registered), `whatifs/anim.py` (the promise-flag
  fix), `tools/gen_docs.py`, `tools/rehearsal.py`.
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
   MEASURED in B0b (real 1080p, 12 seeds x 4 worlds, one 4-second shot each, flat depth, push-in): 43 of 48 shots 100% alive; rain 57% / 71% / 86% on
   seeds 8 / 2 / 9, embers 71% on seed 10; dust and wind 100% on every seed. No id of the 58-run sweep failed check `aliveness`. Still open for B6-B7.
2. (B1b follow-up, low, for B9) In a month with 5 Saturdays one week has no long video (cap 4). By design today; D1 planning (B9) may choose which
   Saturday to skip or spread differently. `DIGEST_DAYS` (owner digests) still Tue,Sat,Sun - unrelated to publishing, left as is.
3. (NEW, low) `mission_control/worker.js` line 27 comment still says fixes were "recorded in CHANGES.md". Left alone on purpose: it is a comment in the
   deployed Worker file, and JS comments are outside the scan. Fix it the next time the Worker is changed anyway.
4. (laptop) Test temp dirs `mt_*` accumulate in `%TEMP%`; automatic cleanup of that shared folder was blocked by the app's safety rule. Disk free
   333 GB, so no risk; delete by hand only if space ever gets tight.
5. (handoff folder, outside git) The handoff `CLAUDE.md` still says the repo's own CLAUDE.md "is historical until batch B1 rewrites it". B1 has
   rewritten it; the sentence is now simply spent. No action needed.
6. (B2 -> B6 / B8) A few low-priority limits do not fit an 1,800-token playbook: D1 3, D4 4, D12 1, Council 6 (5 before B4: the Council now also gets
   the item that says how a ticket must look) (lowest priority first out; the health
   check reports it as a note). Fix belongs to the Council / Librarian: merge overlapping limits, or raise the cap for those departments - since B4
   there is a lever for that (`PALACE_PLAYBOOK_TOKENS_BY_DEPT`, owned by L; a ticket to L reaches the engine once L is wired in B8).
7. (B2 -> B8) An edit of the `Palace_Items` tab made outside the code is recorded as `external_edit` only when upkeep runs before the next Palace
   write. Served content is safe either way (the guard re-checks every row); only the audit entry can be missed.
8. (B2 -> B5) Founding tool facts expire 60 days, and the two plans 45 days, after they are first written to the live Sheet (the clock starts at
   seeding, not at the date of the research) unless re-validated. By design; B5's research cadence has to re-validate or replace them.
9. (B2 -> B10) The Palace's real Google Sheets / Drive path is proven with the local store and stubs only (no keys on this laptop, by rule). The
   first learning job after the merge writes 92 rows in one append and makes no Drive call (founding bodies resolve from the repo). B10's first-run
   verification must check tab `Palace_Items` and `palace_health` in `Feature_Ledger`.
10. CLOSED in B3: `whatifs/org/palace.py` and every org module are on the `tools/repair.py` PROTECTED list.
11. (B2, low) `Palace_Versions` numbers come from the last row + 1: two jobs writing in the same second could reuse a number (timestamp and hash
   still tell them apart; the tick's concurrency group makes it unlikely).

12. (B3 -> B6) Brief mode is a hand-over: no model prompt contains Palace knowledge yet. B6: set `inject` to "prompt" for D4-D7 in `registry.DEPTS`
   (and `inject_tasks` if the blind judges must not be handed the playbook), add `applied_items` to the creative outputs, build `palace_injected` /
   `palace_cited`. An adopted Script Preview makes no model call, so in prompt mode it would (correctly) breach: wrap the preview room first.
13. (B3 -> B5 / B6 / B9) Not under the runner yet: Script Preview and pre-production room runs (`whatifs/preview.py`, `preprod.py`), standalone Shorts,
   specials, Case Files, Deep Trial, packaging rescue, releases (Reels), the research and trends jobs. Each needs its call site + registry entry in
   its department's batch; B10 must end with `registry.PENDING` empty.
14. (B3 -> B6) D7's voice run covers the first narration only; the "too short -> extend -> narrate again" loop re-narrates outside the run.
15. (B3 -> B7) A step that keeps crashing may reach the owner twice: the pipeline's existing failure mail and the stuck-item message (after the third
   attempt or 24 h; weekly tier unless P0). B7's repair loop must make it ONE path.
16. (B3 -> B7) `promise_paid` is judged at the final gate although the shot plan exists at the script gate: a failure costs the picture money first.
   Proposal: judge it at the script gate too (needs shots and units in the script-stage context).
17. (B3 -> B6 / B8) Proposed takeaway items wait in the Palace until the Council exists. Bounded by class (department x step x signature), not by runs.
18. (B3 -> B10) About 9-10 extra Sheets calls per department run, 9 runs an episode: proven on the local store only. First-run verification must watch
   for quota errors and look at tabs `Memos`, `Sessions`, `Takeaways`, `Org_Audit` and at both organisation checks in `Feature_Ledger`.
19. (B3 -> B9) The SLA hours are the master spec's defaults, not tuned. D1 owns tuning (setting ORG_SLA_HOURS).
20. CLOSED in B0b (the ids are traceable now: a failed test prints its episode ids onto the public run page, a red rehearsal prints its id and the
   command that reproduces it, and `tools/sweep.py` runs any id on any machine). Was: (B3, low) `tests/test_integration.py` and the rehearsal still make time-based episode ids and the fake pipeline is seeded by the id, so another
   id-dependent fault could surface on some minute. That is a feature while faults remain: trace it, do not re-run it away.

21. CLOSED in B0b (every run read; run 38 reproduced with the id of its minute: the stale promise flag; standing rules 1-2). Was: (FOUND 10 Nov after B3, verification gap of B0-B3) GitHub runs the `Checks` workflow on EVERY push of this branch (Ubuntu, Python 3.11, real pytest,
   then the fake rehearsal) and no batch ever read its result: every "green" in this file is the laptop (Windows, the stand-in test runner). Read on
   10 Nov (step outcomes are public; log lines need a GitHub sign-in): baseline RED at unit tests (expected, before B0's fixes); B0 GREEN; B1 final
   GREEN; B1b final GREEN; the two mid-batch commits of B1 / B1b RED at unit tests (the 939 / 1 and 948 / 1 already recorded above, fixed one commit
   later); **B2's final commit c54b9b6 RED at the REHEARSAL step (unit tests green there)** although the laptop rehearsal was green; B3's first three
   commits GREEN; B3's final commit 6b89d83 was still running. Best hypothesis for the B2 failure, NOT confirmed (no log access): the stale promise
   flag fixed in B3, which holds the rehearsal's episode on some minutes. To do: confirm from the log, sweep the fake pipeline over many fixed episode
   ids, and make "the batch's final commit is green on GitHub" part of every batch's acceptance.
   Where to look: https://github.com/Rahul4869/reality-engine/actions?query=branch%3Av12-organisation

22. (B0b -> B8, OWNER DECIDED 10 Nov 2026: "build") The blind test "writers' room script against a single-prompt script" was NEVER BUILT: 3 Settings
   cells (`ROOM_VALUE_ON` default TRUE, `ROOM_VALUE_EVERY`, `ROOM_MIN_WINRATE`) and tab `Room_Value` exist, no code does. The owner was asked "build it
   with the learning loop (B8), or drop it?" and answered "build" (Palace item `owner.room_value_test`, addressed to D10). B8 builds it inside the full
   batch loop: strong blind judges of another model family (cheap models never make taste calls), cost logged and counted in the estimates (the old
   note says about Rs 15 a video - re-estimate it), fake replies, a switch, a matrix row, the win rate where the owner sees it. When it runs: delete
   the three cells from `truth.UNREAD_SETTINGS` and the tab from `truth.UNUSED_TABS`, drop the NOT ACTIVE marks. Until then the cells do nothing.
23. (B0b -> B4 / B7) `CACHE_ALIGN_EFFORT` is NOT ACTIVE: two calls with different effort on one cached prefix cost one extra cache write each, on every
   episode (fake episode: 2 misses; an estimated Rs 3-10 a video, at most about Rs 40 a month at 4 videos; NOT measured in production). Wiring
   `models.aligned_effort` as written would change the effort of a creative or judging call to whatever came first - against 'breakout first'. Options
   for the batch that owns model levers: per-message effort (`CACHE_EFFORT_PER_MESSAGE`, needs a real API call to prove), or retire the cell.
24. (B0b -> B6) `show.bible_issues` (protected names, real people, child characters, audio chain) is called by tests only: a hand edit of the
   `Characters` tab is not checked in production. The seed bible is clean (a test proves it). B6 wires it into a check when it wraps the creative departments.
25. (B0b -> B6 / B7 / B10) Never wired, harmless today, each to be wired or removed by its department's batch: cells `RUNTIME_HARD_MAX_SEC`,
   `PKG_VARIANT_C_IMAGE`, `VIEWER_NAME_ON_SCREEN`, `PREMISE_BENCH_MAIL_MONTH`; functions `enforce.fix_markers`, `enforce.fix_retention`,
   `prompts.episode_pack`, `publish.meta_bio`, `data.ptype_for`, `shotplan.prompt_variety`; tab `Repairs`. B10 must end with the three lists in
   `whatifs/truth.py` as short as they can be and say so in the PR.
26. (B0b -> B10) The atmosphere's time valve (`ATMOSPHERE_MAX_OVERHEAD_PCT` 30) switches its particles off on EVERY small fake render (153% measured),
   so the rehearsal never shows the full set of layers after frame 120 and says nothing about full size. First-run verification must read
   `Episodes.atmos_json` (`dropped`) of the first real videos; if layers are dropped there, D6 tunes the cell.
27. (B0b, laptop) One test still skips on the laptop: the dashboard render needs node (GitHub runs it). Install node only if a batch changes the Worker.
28. (B4 -> B6) Knowledge and rule levers (A, D) are verified as SERVED (the item, in that version, was in the playbook of a later complete run). CITED
   is demanded by the same verifier as soon as a department runs in `prompt` mode (B6, open issue 12). Until then "verified" for A / D means handed over.
29. (B4 -> B10) The code lever (E) has never run against the real GitHub: `builds.pr_files`, `builds.commit_state`, the dispatch of `checks.yml` on main
   after a merge, the new `request` input and the moved credentials in `claude-build.yml` are proven with stand-ins, by a YAML test and by reading.
   First-run verification must watch the first organisation build end to end. If the checks on a merge commit never report, the ticket is escalated
   after `EXEC_VERIFY_DAYS` (never reverted on a guess).
30. (B4 -> B6 / B8 / B9; D2 and D3 unlocked in B5) A ticket for a department that has no wired run (D0, D1, D11, C, L) goes straight to the owner's level (B3 rule),
   so the 16 levers of those departments are in the table but cannot be turned by ticket yet. Each batch that wires a department unlocks its levers.
31. (B4 -> B7) A rollback reaches the sender only through the ticket's resolution note and an `Org_Audit` row (kind `lever`). No problem memo and no
   failure lesson is written for it yet: B7's repair loop must feed rollbacks into both.
32. (B4, low) The tick job and the produce job can touch the same ticket at the same moment (two processes, one Sheet, no lock). The engine's steps are
   idempotent (same item id, compare-and-swap, a recovery pass for a half-done apply), so the worst case seen in thought is a doubled ledger row.
33. (B4 -> B6) A script written BEFORE a setting change (an approved Script Preview) and adopted after it is judged against the new bar and counts as
   "made after the change". A stricter bar can so fail an older draft and roll the setting back. B6 wraps the preview room: stamp the draft with the
   lever values it was written under.
34. (B4 -> B9) The owner's approval message for a lever goes out on tier `week` unless the ticket is P0 (as the stuck-item message does). D0 may want
   `now` for approvals; and an approval that is never answered rests on his list after the usual reminders.
35. (B4 -> B6 / B10) `EXEC_AUTO_MERGE_ON` defaults to TRUE with a scope of NEW TEST FILES ONLY. The master spec says "tests + rules only": narrowed on
   purpose (rules have lever class D). Tell the owner in the final PR; he can widen it or switch it off.
36. (B4 -> B7) `CACHE_ALIGN_EFFORT` (open issue 23) was NOT taken up in B4: it is not a lever of any department. Still open for B7.
37. (B4, low -> B10) GitHub's run page shows one warning that is GitHub's own: Node.js 20 is deprecated and `actions/setup-node@v4` (in `checks.yml`) is
   forced onto Node.js 24. Green today; move the action to its next major version when a batch touches the workflows anyway.

38. (B5 -> B6) Assessment memos wait silently at the owner's level until the Council is wired (C pending); research memos that the watchdog escalated
   after a void Board session can no longer be assessed by D3 (it is not their holder). The Council's first run must take up both.
39. (B5 -> B6) Re-validation: a research memo about an expiring Palace fact carries `palace_ref`; only the owner, the Council or D10 may re-validate,
   so founding facts still expire until B6's Council issues the A ticket (open issue 8: the research side is closed, the Palace side is not).
40. (B5 -> B10) Real APIs never touched (no keys here, by rule): the web-search citation blocks (`cited_text`, `page_age`), Gemini grounding chunks
   (domain-level match, titles are domains), the liveness check from GitHub's runners and the real cost per question are proven with stand-ins and the
   documentation. First-run verification must read tab `Research_Agenda` (notes: ceiling, kept, dropped, rupees) and `Board_Log` (families, models).
41. (B5 -> B8) Message Batches are not used for research or the Board: searches cost the same in a batch, only tokens halve (about Rs 4 a question),
   and the batch API throttles searches while the job waits. Decide on measured cost (RESEARCH_EST_INR follows the median measured cost).
42. (B5 -> B8) Predictions are stored and validated but nobody scores them yet against later videos; D10's learning loop (B8) should score them
   (research yield per gap source, which kinds of advice came true).
43. (B5 -> B9) The owner sees research verdicts nowhere yet (no digest, assessments are silent until the Council exists); D0 (B9).
44. (B5, low) Inside one weekly run the in-run budget guard counts the last successful model call of each question only; the monthly figure in
   `Org_Audit` (and so the cap) is exact. The manual `research.yml` workflow (`cli research`) still runs the topic brief outside the runner.
45. (B5) Liveness from GitHub's runners: a site that blocks robots (401-429) counts as alive, a timeout counts as alive, 404 / 410 / no host is dead.

46. (B5, low -> B10) GitHub's run page now notes that the `ubuntu-latest` label moves to Ubuntu 26 from 19 Oct 2026. The Checks pin Python 3.11 and
   the library bounds of requirements.txt, so the move should be quiet; if a run turns red right after it, read the annotation for a system library
   (ffmpeg, fonts) first. Pin `runs-on: ubuntu-24.04` only if that happens.

47. (B5 sweep, medium -> B6 or the next batch that touches the Script Room) `whatifs/similarity.py:check` compares a script with the last 10
   fingerprints INCLUDING the same episode's own earlier one. Any episode scripted twice (seen in the rehearsal's re-render; NOT checked whether
   a production re-run does it) is reported 'N% similar to itself': a degraded step and a false `similar_script` owner message. Fix: skip rows whose `episode_id` equals the
   episode (replace that episode's fingerprint instead of appending a second); test both ways (a twin of ITSELF is not similar, a different
   episode at the same score still is). Not a weakened check - the comparison with other episodes stays.
   FIXED in B6a: `whatifs/similarity.py:check` compares with the last 10 fingerprints of OTHER episodes and keeps one fingerprint per episode
   (a re-scripted episode replaces its own); test_a_script_is_never_similar_to_its_own_earlier_draft_and_a_copy_of_another_episode_still_is.
48. (B6a -> B8) A verified citation proves the quoted line EXISTS in the output, not that the knowledge CAUSED it (a model can still quote a line
   it would have written anyway). The callback to the last case must name the case (code), but a general technique has no such topical test.
   The causal measure is design G (parked): D10 re-runs one creative call without the playbook as an experiment arm and compares; and D10's
   outcome attribution per applied item (applied_count, outcome_score). B8.
49. (B6a, one-time cost, tell the owner in the PR) On the first production after the merge, an AUTOMATIC pre-production draft written before
   B6a is superseded (it never saw the Palace) and production writes the script again under D4 at the normal price instead of using the
   half-price draft, once (the draft already paid is lost: the writing is paid again, about Rs 150-180 by the LLM_EST_INR allowance). An owner-approved draft is kept (his decision) and judged as written before B6a.
50. (B6a -> B6b) The Council's playbook leaves 5 limits out at 1,800 tokens: give C its own cap or narrow audiences before the Council runs.
51. (B6a, low) D7 Sound has no model call inside its run (TTS + code), so it can neither cite Palace knowledge nor propose; sound ideas reach the
   show only through the bible (D4). Revisit if a D7 model step is ever added.

## HOW TO RUN ON THIS LAPTOP (the Bash tool = Git Bash works; from `reality-engine/`)
- Env: `export PYTHONUTF8=1 WI_FAKE=1 PY=../.venv/Scripts/python.exe`
- Suite: `bash ../shim/runall.sh . <outdir outside repo>` (~35 min; run it in the background). Some files: `bash ../shim/runseq.sh . <outdir> test_a test_b`.
- Rehearsal: `WI_SMALL=1 WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.cli rehearsal > <log outside repo>` (~3 min); delete the work dir after.
- Plan Guard: `../.venv/Scripts/python.exe tools/plan_guard.py`. Truth only: `../.venv/Scripts/python.exe -m whatifs.truth`.
- Organisation only (registry honesty + data, prints GREEN / RED): `WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.org.runner`.
- After adding or moving a runner call site: update `whatifs/org/registry.py` ENTRY / PENDING, then `tools/gen_docs.py`.
- The end-to-end test in `tests/test_v12_org.py` runs two fake episodes (about 2 minutes); the file needs `tools/rehearsal.py` importable (it is).
- Palace only (seeds a local store, prints GREEN / RED + every problem): `WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.org.palace`.
- After ANY change to a seed file in `whatifs/org/seed/`: run that Palace command, then `tools/gen_docs.py` (SYSTEM.md prints the seed counts).
- Stopping a background suite run: stopping the task does NOT stop the runner loop on Windows. Also stop the `bash.exe` processes whose command line
  contains `runall.sh` / `runseq.sh` and the `python.exe` running `minitest.py`, or tests keep starting.
- After ANY change to settings, checks, tabs, workflows or a module docstring: `../.venv/Scripts/python.exe tools/gen_docs.py` and commit SYSTEM.md.
- Plan Guard flags one specific word in every text file and several words in file names (see `tools/plan_guard.py` BANNED_NAME_WORDS) - keep
  BUILD_STATE and seed files clear of them.
- Sweep (standing rule 2; about 2 minutes an id alone, 4-5 with 3 jobs; ALWAYS on a frozen copy so that edits do not change the code under test):
  `git worktree add --detach <scratch>/wt <commit>`, then from that folder `<venv python> tools/sweep.py --n 40 --jobs 3 --work <dir outside any repo> --out <file>`;
  `--org off` = the old path; `--mode rehearsal --ids <id,...>` = the full rehearsal with a forced id; `--one <id> --work <dir>` = one id, folder kept.
  Read only the `TOTAL` and `SUMMARY` lines; per-id logs are in `<work>/_logs/`. Afterwards `git worktree remove --force <scratch>/wt` and, if git then
  complains about `.git/worktrees/<name>`, delete that folder by hand (OneDrive can hold it for a minute).
- Real pytest for single files (same runner as GitHub): `PYTHONPATH= ../.venv/Scripts/python.exe -m pytest tests/<file>.py -q -p no:cacheprovider`;
  add `WI_NO_SKIPS=1` to run strict like GitHub's Checks.
- Truth registry by hand: `../.venv/Scripts/python.exe -m whatifs.truth` (retired concepts, unread cells, unused tabs, uncalled functions).
- The engine by hand in a test or a scratch store: write a ticket with `memos.write`, call `execute.engine_tick(now=...)`, read tab `Tickets` (state, proof,
  note) and tab `Lever_Changes` (the events). Every engine function takes `now`, so a verification window can be walked through without waiting.
- After adding a founding item addressed to a department: run the Palace command and read its `note:` line - an item for a crowded department (D1, D4,
  D12, C) can push a low-priority limit out of that playbook. Narrow the audience instead.
- NEVER run the full suite and the sweep at the same time: the suite runner stops a test file after 15 minutes, and under the sweep's load
  `test_v91_flaky_root` (999 s that day) and `test_v82` (764 s) run into it. Suite first (about 40 minutes with the engine's tests), then the sweep.
- NEVER paste code with backslashes through a shell here-document on this laptop: the shell halves them (it broke a file twice in B0b). Write the
  file with the file tools, then run it.
- git: `core.autocrlf=false` (keep LF); write files with LF. Commit identity Rahul4869 (noreply address); push with
  `GIT_TERMINAL_PROMPT=1 GCM_INTERACTIVE=always git push` (credentials are saved).

## BATCH LOG
| Batch | Status | Suite | Rehearsal | Notes |
|---|---|---|---|---|
| B0 | done 10 Nov 2026 | 912 / 0 / 6 skipped | GREEN (19 + 18) | 2 small fixes (Windows ffmpeg path; particle seed determinism). GitHub run 28: GREEN |
| B1 | done 10 Nov 2026 | 940 / 0 / 6 skipped | GREEN (20 + 18) | Truth Registry; docs/CURRENT + ARCHIVE; generated SYSTEM.md; check `docs_current` (38 hard checks now). GitHub run 31: GREEN |
| B1b | done 10 Nov 2026 | 949 / 0 / 6 skipped | GREEN (20 + 18) | Owner decision "4 a month" executed: cap 4, weekly Saturday, one-time Sheet move, truthful viewer lines, retired rule. GitHub run 33: GREEN |
| B2 | done 10 Nov 2026 | 988 / 0 / 6 skipped | GREEN (21 + 18) | Knowledge Palace core: 92 founding items, write gate, life cycle with authority, guarded playbooks, check `palace_health` (39 hard checks now). GitHub run 38: RED at the rehearsal (the stale promise flag, reproduced in B0b; fixed in B3) |
| B3 | done 10 Nov 2026 | 1088 / 0 / 6 skipped | GREEN (22 + 19) | Memos + department contract: 4 org modules + wrappers, 7 departments wired, SLA watchdog, checks `dept_contract` + `takeaways_written` (41 hard checks now); promise-flag fix. GitHub run 42: GREEN |
| B0b | done 10 Nov 2026 | 1113 / 0 / 1 skipped | GREEN (22 + 19) | Baseline re-check: sweep 58 of 58 fixed ids green; reference frames always compared; no-skip rule; Checks pinned to production's library versions (they ran OpenCV 5.0.0); red runs name their cause in public; 8 cells / 2 tabs / 10 functions that were never wired are listed and may only shrink; owner: build the room value test in B8. GitHub run 52: GREEN (1114 passed, 0 skipped); runs 46-48 RED = OpenCV 5.0.0 before the pin |
| B4 | done 10 Nov 2026 | 1201 / 0 / 1 skipped | GREEN (24 + 19) | Execution Engine: lever table (39 levers), 5 lever classes from ticket to ledger proof or rollback, owner approval by direction, between-videos rule, D12 wired, checks `decisions_executed` + `lever_verified` (43 hard checks now), build workflow hardened. GitHub run 59: GREEN (1202 passed, 0 skipped); run 57 RED = one test, a one-second ordering rule of the verifier, traced and fixed (runs 54-56 and 58 GREEN) |
| B5 | done 11 Nov 2026 | 1232 / 0 / 1 skipped | GREEN (25 + 19) | R&D + Review Board: gap-driven research agenda (8 gap sources), sources verified by code (phantom / dead / undated dropped, evidence ceiling), blind two-family Board with yes/no checklist, verdict by code, family veto, planted canary per session; check `research_cadence` (44 hard checks), D2 + D3 wired, 41 levers. Sweep 58 of 58. GitHub run 67: GREEN (1233 passed, 0 skipped); #63 RED = 6 by-design tests, #64/#65 RED = rehearsal money formula, traced and fixed |
| B6 | next | | | Creative departments + Council |
