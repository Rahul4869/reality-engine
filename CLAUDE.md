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
- **New format or series idea**: enter it as an experiment arm or a Playbook trial so the data decides; never replace the whole format at once.
- **Knowledge Palace** (`whatifs/org/palace.py`): knowledge enters only through `palace.add` / `add_many` (dated evidence, real `applied_in` code references)
  and leaves only through `palace.playbook` (the guard runs first). Never write the `Palace_Items` tab directly, never filter statuses yourself.
  A build's research and takeaway go into `whatifs/org/seed/build.json` (stable `key`); a new owner decision that replaces an old one uses `palace.supersede`.
