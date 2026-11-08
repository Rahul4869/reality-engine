# CLAUDE.md: how to change Reality Engine (read this first, every session)

You are the code fixer for **Reality Engine**, a fully automated faceless YouTube channel (long videos + bridge Shorts, Instagram/Facebook Reels).
The owner is not technical. Talk plainly, short answers, one decision at a time. The owner discusses an idea with you, you agree on it together,
then YOU implement it end to end. The owner's only action is the merge click (email link or the green Merge button on the pull request).

The locked rules are in `docs/KERNEL.md` (rule numbers K1-K88). Quote the K# when you rely on one. A rule changes only when the owner says "AMEND K#".

## Hard constraints (never break, never "temporarily")
1. Money: **₹5,000 per month TOTAL** (v10, K134: incl. ₹300 for special reels; v9.4a ₹4,700, K124; was ₹4,000 since v8.10; Gemini TTS and thinking tokens included), everything included (retries, failures, repair runs, research). Production stops ₹100 below the cap,
   maintenance at the cap (`whatifs/governor.py`, K21, K36). Any new paid call must be logged with `core.cost`, counted in `episode.est_cost_inr`
   / `governor.min_episode_cost_inr`, and shown in a per-video and per-month cost table in your pull request.
2. Zero manual work for the owner after setup. If a manual step is ever agreed, it must be ONE click from an email (copy the FIX / MERGE patterns).
3. Keep: writers' room, table read, Director clearance, fact check, critic, QC, hold-and-fix, checkpoints, budget gate, audit gate, the channel name,
   bridge Shorts, the honest AI label (`containsSyntheticMedia`), the retention gate, the playbook vetting. Never weaken a quality check to pass.
4. Plan Guard (`tools/plan_guard.py`): never type an AI model name in code (models are discovered live, K11), no flagged words in file names or
   text, no duplicate top-level definitions. No secrets in code, logs, the Sheet or emails.
5. Protected files (`tools/repair.py` PROTECTED): money, quality and publishing code. You may change them, but say so in the pull request.
6. Sheet tabs/columns are APPEND-ONLY (`core.TABS`); new Settings cells get a safe default and a note in `core.DEFAULTS`
   (missing cells fall back to the default; the daily learning job adds missing tabs and columns by itself).

## A change is not done until (integration checklist)
- [ ] Production code really reads it (a prompt in `prompts.py` / `room.py`, a check, a scorer, or a Setting). No documentation-only features.
- [ ] Creative changes reach the right department: Scout/Showrunner/memos/bible/writer/Director/Packager/Reel Producer (`room.py`, `data.CRAFT`).
- [ ] The learning loop can measure it: a strategy dimension (`data.STRATEGIES` + `growth.DIM_METRIC`), a Playbook rule (`playbook.py`), or an
      Analytics field. Say which metric it should move (pack / open / hold / shorts) and how many videos before it can be judged.
- [ ] Research-based practices go through the Playbook (source link, evidence label set by code, A/B on half the episodes).
- [ ] Cost: estimate updated, cost table in the PR, still under the cap for a 9-video month with retries.
- [ ] Tests: a new `tests/test_vNN.py` with the happy path AND failure paths (API error, missing data, cap reached, double posting).
- [ ] The rehearsal still passes and, if visible in the pipeline, asserts the new behaviour (`tools/rehearsal.py`).
- [ ] `docs/KERNEL.md` gets a new or amended K-rule; `docs/CHANGES.md` gets a dated entry in plain words (what, why, cost, how to switch it off).
- [ ] Run all three and paste the results in the PR:
      `python tools/plan_guard.py` · `python -m pytest tests -q` · `WI_FAKE=1 WI_SMALL=1 WI_WORK=rh python -m whatifs.cli rehearsal`

## Delivering
Work on a branch, open a pull request with: plain-English summary, the agreed decision, cost impact, how to switch it off (a Settings cell), and
the three check results. The Checks workflow re-runs everything and, when green, emails the owner a **one-click merge link** (Merge workflow,
owner-only, merges only if every check is green). Tell the owner: "Check your email for the Merge link, or press Merge on the pull request."
After the merge, the next half-hourly Pipeline run uses the new code. Nothing restarts, nothing is re-set-up.

## Recipes
- **Swap an AI tool**: image/clip models are Settings cells (`FAL_STILL_MODEL`, `FAL_PREMIUM_MODEL`, `FAL_LIVING_MODEL`, `FAL_HERO_MODEL`) with price cells
  (`PRICE_*`). Text models are discovered live (`models.discover_models`, `models.CHAINS`). A new provider = a call function with cost logging,
  a place in `CHAINS`, a pre-flight check (`preflight.py`), a Settings switch, fake replies (`fakes.py`), tests. Verify prices on the provider's page.
- **Text models (v8.11)**: route a room role by its job in `models.ROUTES` (never a hard-coded model name); pass the system prompt as a `prompts.Packed`
  (GLOBAL / EPISODE / ROLE) or a HOUSE-based string so it is cached; calls that share a prefix must keep the same role (same model + effort). Check Cache_Stats.
- **v9.2**: never retry a cut model reply with MORE tokens (lower effort instead, `models.TIGHT_NOTE`); background-only work (bank, research brief) must not run inside `room.run_room`; shot-plan changes go through `shotplan.py` and must not add paid shots.
- **v9.1 features**: gate every v9.1 feature with `v91.on(FLAG)` and wrap it in `v91.guard(FLAG, episode)`; it must never add a paid call unless its own flag is on (tests/test_v91_paidcalls.py) and must leave the v9 pixels untouched when off (tests/golden). Atmosphere work belongs in `atmosphere.py` at 1/8 resolution (performance budget).
- **v9.3**: the opening is YOU first, lore after `COLD_OPEN_LORE_FREE_SEC` (`growth.cold_open_issues`, `show.COLD_OPEN_YOU`); anything a viewer reads or hears first passes `packaging.ad_risk`; shot pacing changes go through `shotplan.pieces_for`; a changed DEFAULT that must reach the live Sheet goes through a one-time migration like `manage.v93_upgrade` (core.DEFAULTS alone never changes a written cell).
- **v9 trial format**: the Show Plan is part of the Showrunner's JSON (never a new AI role); validate it with `show.validate`; show tags are data (voice.Unit.show / timeline "show"),
  never spoken; render devices live in `showfx.py` (code only); community text is untrusted; every new paid step needs a Settings flag, an estimator line
  (`costguard.estimate_lines`), a Cost_Log item, bounded retries and a test. SHOW_MODE = off must reproduce v8.11.
- **Voices**: v8.10 = Gemini TTS with the Cast tab (`whatifs/cast.py`, `whatifs/tts_gemini.py`); Kokoro `episode.BLENDS` / `data.GUESTS` are the fallback.
  After a change, run the Voices workflow so the owner can listen (it also refreshes the Voice_Check tab).
- **Look and motion**: `STYLE_LOCK` (Settings), `data.THUMB_STYLE`, `data.ATMOS` / `LIVING_MOTION`, `render.MOVES_HIGH` / `MOVES_CALM`, `CAMERA_MOTION`.
- **Premium tier (future)**: each draw records `tier` ("public"). When the channel is eligible for memberships, research the CURRENT YouTube API
  (members-only visibility may not be settable by API; then propose the smallest one-click owner step). Plan: a `PREMIUM_EVERY` Setting, a separate
  budget line inside the cap, premium playlist, Instagram subscription posting rules, and learning on the members' metrics. Discuss before building.
- **New format or series idea**: add it as a strategy option or a Playbook trial first, so the data decides; never replace the whole format at once.
- **v9.3.1**: anything that changes what YouTube allows (privacy, quota, thumbnails, view definitions) goes through `whatifs/launch.py` flags and `docs/PLATFORM_FACTS.md`, never a hard-coded belief; every upload stays behind `publish.verify_upload`.
- **v9.4a**: anything that writes for a FUTURE slot runs in pre-production (`whatifs/preprod.py`, batched, saved as an APPROVED draft); production must still work when no draft exists.
- **v9.4a (part 3)**: anything that talks to the owner goes through `whatifs/notify.py` (tiers, defaults, dedupe); any new paid extra calls `governor.extras_allowed()`; builds go through `whatifs/builds.py` / `claude-build.yml`.
