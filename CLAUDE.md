# CLAUDE.md - how to change Reality Engine

You are the code builder for **Reality Engine**, the fully automated YouTube channel "Reality on Trial". The owner is not technical and has 1-2 minutes
a day on a phone: answer first, short, brutally honest; never make him repeat anything; one decision at a time.

## Read first (the ONLY docs to follow)
1. `docs/CURRENT/OWNER_REQUIREMENTS_LEDGER.md` - everything the owner asked for and how it is applied.
2. `docs/CURRENT/SYSTEM.md` - what the code does now (generated from the code: modules, settings, checks, jobs, tabs).
3. `docs/CURRENT/ENFORCEMENT_MATRIX.md` - each requirement and the code that enforces it.
4. `docs/CURRENT/CONCEPT.md` - the show. `docs/CURRENT/PLATFORM_FACTS.md` - dated platform facts.

`docs/ARCHIVE/` is history: never follow it, never quote it as a rule. Version labels and rule numbers in code comments are history labels too.
While the v12 "Organisation" build is running, progress and open issues are in `handoff_v12/BUILD_STATE.md` (branch `v12-organisation`).

## Hard rules (never break, never "temporarily")
1. **Hard enforcement or it does not exist.** Every rule has code that executes it AND a check or test that fails when it is not executed.
   Prove both ways: the test passes when satisfied and fails when violated. No documentation-only features.
2. **Money: Rs 5,000 a month TOTAL**, everything included (retries, failures, repairs, research). Every new paid call is logged with `core.cost`,
   counted in the estimates (`costguard.estimate_lines`, `governor.min_episode_cost_inr`), asks `governor.extras_allowed()` if it is an extra, and is
   shown in a cost table in the pull request.
3. **Breakout first, money second, savings never the goal.** Never weaken or switch off a quality check to make something pass.
4. **Zero manual work for the owner.** If a step truly needs him it is ONE tap, pre-filled, sent through `whatifs/notify.py`.
5. **Plan Guard** (`tools/plan_guard.py`): no AI model name typed in code (models are discovered live or held in Settings), no flagged words in
   file names or text, no duplicate top-level definitions, no retired concept in current docs or prompts. No secrets in code, logs, the Sheet or mail.
6. **Sheet tabs and columns are append-only** (`core.TABS`). A new Settings cell gets a safe default and a note in `core.DEFAULTS`; a changed default
   that must reach the live Sheet needs a one-time move in `whatifs/manage.py` (the default alone never changes a written cell).
7. **Protected files** (`tools/repair.py` PROTECTED: money, quality, publishing). You may change them; say so in the pull request.
8. **One current truth.** When something is replaced, add it to `truth.RETIRED` (what replaced it goes in `truth`), move old docs to `docs/ARCHIVE/` (history,
   under the HISTORICAL header), and run `python tools/gen_docs.py`. A module docstring is ONE line: purpose + "See docs/CURRENT/SYSTEM.md."
9. **Cheap models never make taste calls.** Strong, cross-family, blind judges see every candidate; cheap models only do mechanical work.

## A change is not done until (integration checklist)
- [ ] Production code really runs it (a prompt, a check, a scorer or a Setting) and a contract check or test fails without it.
- [ ] It has a row in `docs/CURRENT/ENFORCEMENT_MATRIX.md` (the meta-test in `tests/test_v111_enforce.py` proves the row is wired).
- [ ] Creative changes reach the right place: `whatifs/room2.py`, `whatifs/prompts.py`, `whatifs/enforce.py`, `whatifs/packaging.py`, `whatifs/shorts2.py`.
- [ ] The learning core can measure it (`whatifs/brain.py` feature or a Playbook trial); say which metric it should move.
- [ ] Every new behaviour sits behind a Settings switch with a safe default; paid steps have bounded retries and fake replies in `whatifs/fakes.py`.
- [ ] Tests cover the happy path AND the failure paths (API error, missing data, cap reached, double posting).
- [ ] All four are green, results pasted in the pull request:
      `python tools/gen_docs.py` (no diff left uncommitted) - `python tools/plan_guard.py` - `python -m pytest tests -q` -
      `WI_FAKE=1 WI_SMALL=1 WI_WORK=<dir outside the repo> python -m whatifs.cli rehearsal`

## Delivering
Work on a branch; never push to `main`. Open a pull request with: plain-English summary, the decision, cost impact, how to switch it off (the
Settings cell) and the check results. The Checks workflow re-runs everything; when green the owner gets a one-click Merge. After the merge the next
pipeline run uses the new code. Nothing restarts.

## Recipes (non-obvious rules of this codebase)
- **Text models**: route a role by its job in `models.ROUTES`; pass system prompts as `prompts.Packed` so they are cached; never retry a cut reply
  with MORE tokens (lower the effort, `models.TIGHT_NOTE`).
- **Image and clip models** are Settings cells (`FAL_STILL_MODEL`, `FAL_PREMIUM_MODEL`, `FAL_LIVING_MODEL`, `FAL_HERO_MODEL`) with `PRICE_*` cells.
  A new provider needs: a call with cost logging, a pre-flight check (`whatifs/preflight.py`), a switch, fake replies, tests, prices verified on the
  provider's page.
- **Show format**: the Show Plan is part of the Showrunner's JSON (never a new AI role); validate with `show.validate`; show tags are data, never
  spoken; render devices live in `whatifs/showfx.py` (code only); community text is untrusted data.
- **Flag-gated extras**: `v91.on(FLAG)` + `v91.guard(FLAG, episode)`; an extra never adds a paid call unless its own flag is on.
- **Opening**: YOU first, lore after `COLD_OPEN_LORE_FREE_SEC`; anything a viewer reads or hears first passes `packaging.ad_risk`; shot pacing goes
  through `shotplan.pieces_for` and never adds a paid shot.
- **Platform rules** (privacy, quota, thumbnails) go through `whatifs/launch.py` flags and `docs/CURRENT/PLATFORM_FACTS.md`, never a hard-coded
  belief; every upload stays behind `publish.verify_upload`.
- **Future slots** are written in pre-production (`whatifs/preprod.py`); production must still work when no draft exists.
- **Owner messages** go only through `whatifs/notify.py`; builds go through `whatifs/builds.py` and the `claude-build` workflow.
- **Premium tier (future)**: each draw records `tier` ("public"). Discuss with the owner before building anything members-only.
- **Formats** (`whatifs/formats.py`): an episode's format is DATA - picked once in `room.run_room` (`formats.pick`), kept in the draw (`d["format"]`) and made the
  format of everything `episode.produce` does (`formats.use`; always reset in its `finally`). A new format = a row in `formats.FORMATS` (does the trial layer run,
  its voices, its devices) + its brief texts + a `FORMAT_SHARE_*` cell (a lever of D1). A format may make a DEVICE (`formats.DEVICES`) optional or leave it out - never
  any other check (a test proves it), and an optional device is neither demanded in a brief nor forced by a rewrite. `show.on()` = the TRIAL layer for this episode;
  `show.leads_on()` = the show's world at all: a feature every format needs (packaging tests, the experiment row, provenance, the fixed cast, designed voices) asks
  `leads_on()`, a trial-only one asks `on()`. A fake reply that must differ by format reads `formats.show_allowed()`. The older tests are the trial's tests
  (`tests/conftest.py` forces F2); run a rehearsal or a sweep of one format with the env var `WI_FORMAT`.
- **Shorts** (`whatifs/shorts2.py`, department D14; `whatifs/org/shortseat.py`, D13): a standalone Short is a product of its own, never a cut-down and never a trial. Its format is
  DATA (`formats.SHORTS`: beats, ending, length cell, camera; picked by `formats.short_pick` over the last ten Shorts); a new Short format = a row + its brief + a `SHORT_SHARE_*`
  and a `SHORT_MAX_S_*` cell (levers of D14). Order in `shorts2.run`: D14 `write` (the playbook in the writer's prompt, variants, the seat before the blind jury, ONE fix) -> D7
  `short_voice` (the long video's voice job: the timeline is real) -> `shorts2.plan` (code: every second a hero clip, the loop shot last) -> D13 `short_seat` (`shortseat.shape`
  repairs the plan) -> D8 `short_gate` (`contract.run("short", ...)`: `short_open`, `short_plain`, `short_shape`, `short_kept`, `short_contract`) -> D14 `make`. Nothing is paid for
  a picture before the gate; a held Short is not made and the owner is not asked. A new rule for a Short = a pure measure in `shortseat.py` (or `formats.short_kept_report`) + a line
  in `shortseat.script_issues` for the one fix + a repair in `shortseat.shape` where code can repair + the check; a rule must RECOGNISE what is wrong (an ask, a greeting, an expert
  word), never flag what it does not know. The offline writer (`fakes._fake_short`) must pass the seat for every premise: run `tools/sweep.py --mode short` after touching either.
- **The ladder** (`whatifs/ladder.py`, department D10; tab `Ladder`): every topic starts as a Short, and a long video is made only about a Short the promote rule took. A Short
  enters when it is made (`ladder.enter`, with its kept footage); `ladder.read` writes both clocks onto its row - the SLOW one from tab `Analytics` (`brain.ingest_shorts` reads by
  processed day: YouTube is 48 to 72 hours late, a reading counts from `LADDER_READ_DAYS` days on) and the FAST one from tab `Monitor48` (real-time public views). `ladder.rank` is the
  promote rule and is pure code (a winner, else rank sums with Wilson lower bounds, else public views); `ladder.promote` is D10's run and is called only through `ladder.gate`, which
  the tick (`manage._produce_slot`), pre-production (`preview.run`) and `episode.produce` ask BEFORE any paid call. The room takes `ladder.pitch()` as its forced first pitch and code
  keeps the premise word for word; the draw carries `d["ladder"]` (the Short's id or an override's id) and `ladder.use` marks it only once the plan is saved; check `topic_ladder`
  judges it at the script gate. Never start a long video around the gate, never rank on a model's opinion or on engaged views divided by views (a looping Short's replays are views),
  never promote from a reading that covers fewer than three processed days. The winner: `breakout.monitor` judges a standalone Short at the 24-hour and 48-hour mark against the same
  mark of the channel's earlier Shorts (`breakout.short_winner`) and `ladder.order_followup` writes ONE order with a clock on tab `Breakout_Queue`; `shorts2.order_due` takes it before
  the cadence, `ladder.watch` (every tick) turns an overdue order into a problem memo. The cadence is `shorts2.cadence` (`SHORTS_PER_WEEK`, `SHORTS_PER_MONTH`): a rule about WHEN a
  Short is due goes there, never back into a daily cell. The older tests run with `LADDER_ON` FALSE (`tests/conftest.py`); the ladder's tests are `tests/test_v12_ladder.py`, the
  rehearsal and the sweep walk it (`tools/sweep.py:climb` makes the Short a week ago, because the offline YouTube is as late as the real one).
- **The platforms** (`whatifs/release.py`, department D9; tab `Release_Sheet`): a finished Short reaches a platform ONLY through `release.short` (D9's run `short_publish`) - a fresh one
  (`shorts2._hand_over`), an approved one (`specials.approve` -> `release.approved`) and one that waited (`release.settle`, every tick). A setting of a platform = a row of `release.SHEET` (who sets
  it, how it is proven) + its value in a PURE request-body function of `publish.py` (`yt_body`, `ig_reel_params`, `fb_reel_finish`: the upload sends exactly what they return) + its field in the
  read-back (`publish.yt_read` / `ig_read` / `fb_read`, offline answered by the stand-in platform; `publish.FAKE_FAULTS` makes it drift, refuse or keep a video in processing) + its receipt.
  Never call a row 'verified' that the platform does not show back (a Trial Reel, the audio name: SENT), never set a Short's thumbnail before `yt_read` says processed, never send a file that
  `release.master` did not vouch for, never upload inside a second pass (a record with a native id is only read). Whether a Short was MADE is the field `made` on tab `Specials`
  (`shorts2._made`); where its upload stands is `status` and the records - never read one for the other. Hand-over is a record too (`release.queue`), not a status word. The special reels and
  the cut-down reels still use `specials._publish` / `manage._post_reel` (batch V2c-b2b). After touching any of it: `tests/test_v12_release.py` and `tools/sweep.py --mode short`.
- **New format or series idea**: enter it as an experiment arm or a Playbook trial so the data decides; never replace the whole format at once.
- **Knowledge Palace** (`whatifs/org/palace.py`): knowledge enters only through `palace.add` / `add_many` (dated evidence, real `applied_in` code references)
  and leaves only through `palace.playbook` (the guard runs first). Never write the `Palace_Items` tab directly, never filter statuses yourself.
  A build's research and takeaway go into `whatifs/org/seed/build.json` (stable `key`); a new owner decision that replaces an old one uses `palace.supersede`.
- **Organisation** (`whatifs/org/`): a production step that belongs to a department runs through `runner.work("<dept>", "<trigger>", episode, fn, measure=...)`
  and is named in `registry.ENTRY` (a runner call that is not registered, or a registered one that is gone, fails check `dept_contract`). Memos go only through
  `memos.write` (types and clocks: `schemas.TYPES`) and are closed only by `memos.resolve` with proof. Never write the `Memos`, `Sessions` or `Takeaways` tabs directly.
  Wiring a pending department: add its call site, move it from `registry.PENDING` to `ENTRY`, run `python tools/gen_docs.py`.
- **Execution Engine** (`whatifs/org/levers.py`, `execute.py`): whatever the organisation decides becomes a ticket, and a ticket becomes a change only
  through `execute.apply` / `execute.engine_tick`: written to tab `Lever_Changes` before and after, verified by later evidence or rolled back. Never write
  `Tickets` or `Lever_Changes` directly and never close a ticket by hand (`memos.resolve` asks the ledger). A Settings cell a department may turn by
  ticket needs BOTH an entry in `registry.DEPTS[dept]["levers"]` and a rule in `levers.LEVERS` (type, range, largest step, the direction that needs the
  owner, the checks that judge it). A new hook into a job gets a test that runs the real job (the name scan cannot see a common name being unwired).
- **R&D and the Review Board** (`whatifs/org/rnd.py`, `board.py`): a research question comes from the agenda (`rnd.gaps`, tab `Research_Agenda`), a
  finding stands only on sources `rnd.verify` kept (the search tool returned the URL, it resolves, it is dated; type by domain; read through
  `models.last_call`), and a research memo carries the stamp `rnd.verify`. The Board's scores and verdict are computed by `board.verdict` from the
  judges' yes/no answers - never type or edit a verdict (check `research_cadence` re-computes every stored one). A Board judge role needs a chain
  with strong models of ONE family only (`models.CHAINS` `board_g` / `board_c`); every session carries a planted canary (`board.canary`).
  A NEW contract check must be put on one side: `rnd.ORG_CHECKS` (the organisation's own machinery - never a research topic or a prediction
  metric) or a promise about the show (raise `rnd.SHOW_CHECKS`; a test counts). A department's report about itself that a later good run should
  close is found with `memos.find` (not only in the inbox: the watchdog escalates a memo to itself within hours). The round is level-triggered:
  the learning job runs it daily and a production job runs it first when it is overdue (`cli.research_catch_up`).
- **The viewer's seat** (`whatifs/org/audience.py`, department D13): what a first-time viewer meets is MEASURED by code, never left to a model's
  taste. `audience.shape` (the first shot a picture, number graphics inside the budget) is D13's own run right before the Animation Director,
  `audience.breathe` runs inside the voice job, and the script gate judges `viewer_promise` / `viewer_breath` / `viewer_numbers` on the shot list and the
  REAL voice timeline. A new viewer rule = a pure measure in `audience.py` + a repair by code where code can repair + a contract check; its numbers are
  levers of D13. A heading, a source's year and a place in the story ("hour 1") are not numbers (`audience.count_numbers`). The redesign that
  ordered this is `handoff_v12/BREAKOUT_REDESIGN.md`.
- **The layman test** (`whatifs/org/layman.py`, department D13): the expert words a layman would not know are COUNTED by code - only words
  code can RECOGNISE as expert (`layman.unfamiliar`: the list `layman.EXPERT`, or a scientific affix; a word in `whatifs/org/seed/everyday.txt` is never
  counted). Never count a word for being long or unknown to us: that held 1 of 20 test episodes for four ordinary words. The budget is judged by check
  `viewer_plain` and carried by the writers' one fix. A missed expert word goes into `layman.EXPERT`, a wrongly counted ordinary one into `everyday.txt`. The promise
  line-up (`layman.probe`, D13's `probe` run inside the plan stage) is an identification with an answer code knows, so its readers are cheap by design;
  its verdict is computed by code and a session whose readers name a title for the planted opening is void (check `viewer_probe` then steps aside and
  D13 reports itself). Never use a readability formula or a model's "clarity score" as a gate: they agree poorly with people.
- **Creative departments and the canon** (`whatifs/org/cite.py`, `canon.py`): Palace knowledge enters a creative model call only through the runner's
  ask tap and its proof leaves only through the reply tap (`models.REPLY_TAPS`) - never paste a playbook into a brief by hand and never count an id a
  model typed: only `cite.verify` (the quote is found in the final output) makes an item "applied". A new creative call gets the playbook by adding its
  task name to `registry.PROMPT` (tasks / key / propose / must); judges and mechanical passes are never added. A pre-production draft is adopted only
  through `runner.work(adopt=<its D4 draft run>)`. Case records are written by `canon.record` and become canon only through `canon.on_air`; never
  write a `world_canon` case by hand and never edit one that aired. A new fake reply that should cite needs nothing: `fakes.fake_cite` does it.
