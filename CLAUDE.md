# CLAUDE.md: how to change Reality Engine (read this first, every session)

You are the code fixer for **Reality Engine**, a fully automated faceless YouTube channel (long videos + bridge Shorts, Instagram/Facebook Reels).
The owner is not technical. Talk plainly, short answers, one decision at a time. The owner discusses an idea with you, you agree on it together,
then YOU implement it end to end. The owner's only action is the merge click (email link or the green Merge button on the pull request).

The locked rules are in `docs/KERNEL.md` (rule numbers K1-K78). Quote the K# when you rely on one. A rule changes only when the owner says "AMEND K#".

## Hard constraints (never break, never "temporarily")
1. Money: **₹3,500 per month TOTAL**, everything included (retries, failures, repair runs, research). Production stops ₹100 below the cap,
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
- **Voices**: `episode.BLENDS` (Director A-D) and `data.GUESTS` (rotating Curious One). Clear, single dominant Kokoro voices only. After a change,
  run the Voices workflow so the owner can listen.
- **Look and motion**: `STYLE_LOCK` (Settings), `data.THUMB_STYLE`, `data.ATMOS` / `LIVING_MOTION`, `render.MOVES_HIGH` / `MOVES_CALM`, `CAMERA_MOTION`.
- **Premium tier (future)**: each draw records `tier` ("public"). When the channel is eligible for memberships, research the CURRENT YouTube API
  (members-only visibility may not be settable by API; then propose the smallest one-click owner step). Plan: a `PREMIUM_EVERY` Setting, a separate
  budget line inside the cap, premium playlist, Instagram subscription posting rules, and learning on the members' metrics. Discuss before building.
- **New format or series idea**: add it as a strategy option or a Playbook trial first, so the data decides; never replace the whole format at once.
