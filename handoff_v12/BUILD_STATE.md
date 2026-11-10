# BUILD_STATE - Reality Engine v12 "Organisation"
Updated: 10 Nov 2026 (end of B0b). Branch: `v12-organisation` (never main). Resume: read this file + `git log -5`.

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
**B4 - Execution Engine** (01 section 6; 03 "B4"). Full seven-step MANDATORY BATCH LOOP. Effort: High.
What B3 leaves ready for B4 (use it, do not rebuild it):
- The EXECUTE step of every department run already reads the department's open tickets and calls `runner.EXECUTOR(ticket, brief)`; register the engine
  with `runner.set_executor(fn)`. Until then a ticket is escalated at once with the reason. The engine closes a ticket with
  `memos.resolve(id, dept, "lever_verified" | "rolled_back", ref)` (both kinds are already in `schemas.TYPES["ticket"]["resolved_by"]`).
- A ticket is already a validated memo type: body `lever_class` A-E, `target`, `value`, `acceptance_test`, `rollback`, `decision_ref`; exactly one addressee;
  clocks P0 6 h / P1 48 h / P2 7 days. An owner memo closes by `ticket_executed` ONLY when that ticket is resolved as `lever_verified` (enforced in `memos.resolve`).
- `registry.DEPTS[dept]["levers"]` says which department owns which Settings cell and `registry.may_change(dept, key)` answers it; no lever has two owners
  (tested). Build `org/levers.py` (ranges, steps, cost impact, needs-owner-above) on top; `may_change` is not yet called by any write path.
- Proof for lever class A / D ("the next run had the item in its playbook and cited it"): tab `Sessions` holds `playbook_id` and the ACT receipt (`injected`,
  `applied`); tab `Palace_Playbooks` holds the item ids of every playbook id.
- Tabs still to append in B4: `Tickets`, `Lever_Changes`. Checks that belong to B4: `decisions_executed`, `lever_verified`.
- D12 is pending with batch B4 in `registry.PENDING`: wiring its run (build requests, class E dry-run) means a call site + moving it to `registry.ENTRY`
  (the ratchet test only lets the pending list shrink).
- Paid organisation calls: start the run with `budget="org"`; the monthly thinking cap per department is then enforced by the runner (P0 continues).
- First thing in B4: add the new org modules to `tools/repair.py` PROTECTED (B3's modules are on it).
What B0b adds for B4:
- `truth.unread_settings()` lists the cells no code reads. `org/levers.py` must refuse to register or turn such a cell (a guard test already fails when a
  department's `levers` names one). The moment B4 calls `registry.may_change` and `runner.set_executor`, Plan Guard goes RED until their two entries
  are deleted from `truth.UNWIRED_FUNCTIONS` and `UNWIRED_FUNCTIONS_MAX` is lowered to 8 - that is the rule working, not a fault.
- New checks change the totals several tests and the rehearsal assert (22 script + 19 final today): search the tests for the old numbers.
- Acceptance of B4 includes standing rules 1 and 2: the sweep (40 ids + 10 with ORG_ON = FALSE + 9 rehearsals took about 2 hours on this laptop with
  3 jobs; start it in the background on a frozen copy of the commit as soon as the build step is done) and the final commit green on GitHub.

## DONE
### B4 - Execution Engine (10 Nov 2026) - IN PROGRESS (steps recorded as they finish; resume at the first step that is missing below)

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
6. (B2 -> B6 / B8) A few low-priority limits do not fit an 1,800-token playbook: D1 3, D4 4, D12 1, Council 5 (lowest priority first out; the health
   check reports it as a note). Fix belongs to the Council / Librarian: merge overlapping limits, or raise the cap for those departments.
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
| B4 | next | | | Execution Engine |
