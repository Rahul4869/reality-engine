# SYSTEM - what Reality Engine does now

GENERATED from the code by `python tools/gen_docs.py`. Never edit by hand: change the code, run the generator, commit both.
`tests/test_docs_current.py` fails when this file differs from what the code says, or when any current doc names a retired concept.

## 1. Facts (read from the code)
- Channel: "Reality on Trial" (brand Reality Engine). Concept: `docs/CURRENT/CONCEPT.md`. Owner requirements: `docs/CURRENT/OWNER_REQUIREMENTS_LEDGER.md`.
- Money: hard cap Rs 5,000 a month, everything included (`BUDGET_CEILING_INR`); extras pause at 90% of the cap; breakout fund carries over at most Rs 1,000. One month can be overridden in `MONTH_CAP_OVERRIDES`.
- Quality: 60 HARD contract checks (35 at the script stage and 19 on the final video of an episode, 5 at the short gate of a standalone Short and 1 at its release gate, after the uploads). A FAIL holds the episode and asks the owner (Rewrite / Approve anyway); a held Short is simply not made; a release row a platform did not keep is a problem memo to Publishing (the Short is public by then). No upload below Breakout Score 80.
- Writers' room: mode `v2` (3 drafts, blind cross-family jury, one checklist revision, joke tournament). Room v1 is an optional fallback.
- Animated scenes: 4 per long video on `fal-ai/kling-video/o3/standard/image-to-video`; stills on `fal-ai/flux/schnell`; look `toybox_noir`; voice engine `gemini`.
- Cadence: at most 4 long videos a month, on Sat (US Eastern); 3 standalone Shorts a week, 12 a month at most - every topic starts as a Short and the promote rule picks the long video's topic (`whatifs/ladder.py`); spin-offs: the Case Files countdown and the monthly Deep Trial.
- Size: 124 code modules, 766 settings, 84 Sheet tabs, 24 GitHub workflows.

## 2. How it runs
- Code: the Python package `whatifs/` runs on GitHub Actions (`python -m whatifs.cli <command>`). State lives in one Google Sheet (tabs and columns are
  append-only), media in Google Drive. A Cloudflare Worker (`mission_control/worker.js`) relays WhatsApp, serves the phone dashboard and is the watchdog clock.
- Providers: fal (clips and stills), Gemini (text, images, designed voices), Claude (showrunner, writer, jury member, chores), ffmpeg + OpenCV (render).
  Model names are never typed in code: they are discovered live (`whatifs/models.py`) or held in Settings cells.
- One long episode: tick (`whatifs/manage.py`) -> writers' room (`whatifs/room2.py`, early through `whatifs/preprod.py`) -> script-stage contract ->
  voice -> shot plan -> paid pictures and clips -> render (`whatifs/render.py`) -> final-stage contract -> held for the owner or scheduled ->
  release with Shorts and Reels -> 48-hour breakout monitor (`whatifs/breakout.py`) -> learning (`whatifs/brain.py`). Every paid step is checkpointed.
- Money: every paid call is logged (`core.cost`), estimated before it runs and stopped by the governor (`whatifs/governor.py`).
- Organisation: each step of the long-video pipeline that belongs to a department runs under the department contract (`whatifs/org/runner.py`, section 11).
- Fake mode: `WI_FAKE=1` replaces every provider (`whatifs/fakes.py`); the rehearsal (`tools/rehearsal.py`) runs the whole pipeline at zero cost.

## 3. The v12 Organisation build (status)
- Truth hygiene: one current truth (this file, the registry of retired concepts, check `docs_current`): **built**
- Knowledge Palace core (`whatifs/org/palace.py`: guarded items, life cycle, versions, bounded playbooks, founding knowledge, check `palace_health`; section 10): **built**
- Memos and the department contract (`whatifs/org/schemas.py`, `memos.py`, `registry.py`, `runner.py`; the long-video pipeline and the daily learning job run under it; checks `dept_contract`, `takeaways_written`; section 11): **built**
- Playbooks inside the creative departments' model prompts, cited back with quotes code verifies, the show's canon written by code and paid back in every script, creative memos (`whatifs/org/cite.py`, `canon.py`; checks `palace_injected`, `palace_cited`, `canon_in_brief`): **built (B6a)**
- Execution Engine (`whatifs/org/levers.py`, `execute.py`: a ticket becomes a typed change that is written down before and after, verified by later evidence or rolled back; checks `decisions_executed`, `lever_verified`; section 12): **built**
- R&D and the Review Board (`whatifs/org/rnd.py`, `board.py`; check `research_cadence`): **built (B5)**
- The Council, QA repair loop, learning loop with the Librarian's merges and outcome scores, Owner Office: **not built yet**

## 4. Truth rules (enforced by `whatifs/truth.py`)
- Follow only `docs/CURRENT/` and `CLAUDE.md`. `docs/ARCHIVE/` is history: never follow it.
- Version labels and rule numbers inside code comments are history labels, not instructions.
- Retired concepts (15 rules). Naming one in a current doc, a module docstring or a prompt fails Plan Guard, the tests and check `docs_current`:
  - `brand_what_ifs`: the brand is Reality Engine and the show is Reality on Trial.
  - `old_month_cap`: the cap is Rs 5,000 a month all-in (November 2026 only: Rs 5,226).
  - `kling_v3_path`: the hero clip model id is fal-ai/kling-video/o3/standard/image-to-video (Kling 3.0 Standard).
  - `kling_25_hero`: the hero clip model is Kling 3.0 Standard; older Kling models exist only as fallback rungs of MODEL_LADDERS.
  - `table_read_room`: the writers' room is v2 (diverse drafts + blind cross-family jury + one checklist revision); the table read belongs to the optional room v1.
  - `life_layer_active`: the breathing warp is OFF (measured ineffective); the world particle layer replaced it.
  - `technique_library_core`: Technique_Library is the outlier-video library; the learning core uses Technique_Evidence.
  - `case_file_you`: the concept is Reality on Trial; CASE FILE: YOU is parked and may return only as an R&D proposal that wins in the Council.
  - `master_build_plans`: the plan is the v12 Organisation build (handoff_v12/BUILD_STATE.md).
  - `history_pointer`: the only docs to follow are in docs/CURRENT (start at docs/CURRENT/SYSTEM.md).
  - `kernel_rule_number`: the numbered kernel rules are history; current rules are the checks listed in docs/CURRENT/ENFORCEMENT_MATRIX.md.
  - `old_version_tag`: current docs describe what the code does now, without the history of versions 7 to 10.
  - `old_long_cadence`: the plan is 4 long videos a month, one a week (STANDARD_MAX_LONG_PER_MONTH, PUBLISH_DAYS); lines for viewers say 'every week'.
  - `no_kling_statement`: every long video has animated Kling scenes (ANIM_SHOTS) plus the ffmpeg/OpenCV render.
  - `daily_shorts_cadence`: the Shorts cadence is set in weeks: SHORTS_PER_WEEK (3) and SHORTS_PER_MONTH (12); every topic starts as a Short (whatifs/ladder.py).
- Every Settings cell must be read by code. 8 cells are read by NO code (their notes start with 'NOT ACTIVE'); changing one changes nothing. The list may only shrink (limit 8); a new unread cell fails Plan Guard, the tests and check `docs_current`:
  - `CACHE_ALIGN_EFFORT`: each call keeps the effort its task is routed with; two efforts on one cached prefix cost one extra cache write, logged on every run.
  - `ROOM_VALUE_ON`: the blind test of the writers' room against a single prompt was never built; tab Room_Value stays empty. Owner, 10 Nov 2026: build it (with the learning loop).
  - `ROOM_VALUE_EVERY`: belongs to the room value test, which was never built.
  - `ROOM_MIN_WINRATE`: belongs to the room value test, which was never built.
  - `RUNTIME_HARD_MAX_SEC`: the ceiling the code enforces is RUNTIME_MAX_SEC (sampler and governor).
  - `PKG_VARIANT_C_IMAGE`: the third packaging pair never gets an image of its own.
  - `VIEWER_NAME_ON_SCREEN`: no code puts a viewer's name on screen, so FALSE is what happens; TRUE would change nothing.
  - `PREMISE_BENCH_MAIL_MONTH`: no code writes or reads this bookkeeping cell.
- Every Sheet tab must be used by code and every function of `whatifs/` must be called by production code. 2 tabs and 8 functions are not (built but never wired); both lists may only shrink and a new one fails the same three guards:
  - `Repairs`: no code writes or reads it: the repair robot counts its repairs from the pull requests on GitHub.
  - `Room_Value`: the room value test was never built (see UNREAD_SETTINGS).
  - `whatifs/models.py:aligned_effort`: never called (see UNREAD_SETTINGS, CACHE_ALIGN_EFFORT).
  - `whatifs/show.py:bible_issues`: only tests call it: a hand edit of the Characters tab is not checked for protected names, real people or child characters.
  - `whatifs/enforce.py:fix_markers`: never called.
  - `whatifs/enforce.py:fix_retention`: never called: the writers' room runs its own retention fix.
  - `whatifs/prompts.py:episode_pack`: never called.
  - `whatifs/publish.py:meta_bio`: never called (a stub).
  - `whatifs/data.py:ptype_for`: never called.
  - `whatifs/shotplan.py:prompt_variety`: a measure that only a test uses.

## 5. Contract checks (`whatifs/contract.py` FEATURES)
| check | stage | what it guarantees |
|---|---|---|
| retention | script | re-hook at least every REHOOK_MAX_GAP_SEC, promise shown early, every opened question answered |
| brain_playbook | script | the channel's own proven/retired evidence reached the writer |
| no_retired | script | no technique the learning core retired |
| docs_current | script | one current truth: no retired concept in current docs, docstrings or prompts |
| palace_health | script | Knowledge Palace fit to feed departments: evidenced items tied to real code, nothing retired or expired served, playbooks inside their caps |
| dept_contract | script | every department that worked on the script ran under the department contract: memos and playbook loaded, work done, memos sent, takeaway written, tickets executed, run reported |
| decisions_executed | script | nothing the organisation decided stays text: every decision has tickets, every ticket is executed with proof, refused with a reason or escalated |
| lever_verified | script | every change made by ticket is written down before and after, verified by later evidence or rolled back; none sits past its window |
| research_cadence | script | R&D researched on schedule with sources proven by code, and the Review Board judged every research memo in time, blind, across two model families, with a rejected canary and the verdict computed by code |
| viewer_promise | script | the video opens on a made picture and the thumbnail's promise is on screen within PROMISE_BY_SEC seconds (the viewer's seat) |
| viewer_breath | script | the voice breathes: a real pause at least every BREATH_EVERY_S seconds (the viewer's seat) |
| viewer_numbers | script | few numbers: a budget for the numbers a viewer hears and for full-screen number graphics, none in the opening (the viewer's seat) |
| viewer_plain | script | everyday words: a budget for the expert words a layman would not know - in the narration, in the first 30 s, in one sentence (the layman test) |
| viewer_probe | script | the promise line-up: from the first 30 s alone two first-time readers pick this video's title, and give none to a planted opening (the layman test) |
| format_kept | script | the script is what its format says: a format that is not a trial does not sound like one, a trial has its Show Plan (formats as data) |
| topic_ladder | script | every topic starts as a Short: this long video is about the topic of a Short the promote rule took, or was made under an override on record (the ladder) |
| palace_injected | script | the Knowledge Palace playbook was inside the model prompt of every creative run's key call (the writer, the packager, the director), and the exact text is stored |
| palace_cited | script | every creative run cited Palace knowledge it really applied: each counted citation has a quote that code found in the final output |
| canon_in_brief | script | the writer was given the show's canon (cast and the newest aired case), called back to that case in a line of the final script, and wrote this episode's case record |
| idea_evidence | script | the premise is backed by an outlier at IDEA_MIN_MULTIPLE x |
| joke_density | script | a [PUNCH] line at least every JOKE_EVERY_SEC_LONG seconds |
| send_and_awe | script | a [SEND] moment and an [AWE] peak (not in the last 20%) |
| hook_lab | script | 15-candidate Hook Lab, best opening applied |
| owners_cut | script | independent judge scores the script above the bar |
| cold_open | script | no greeting: the video opens inside the story |
| emotion_beat | script | one earned emotion beat |
| audience_asks | script | comment/predict/share asks placed by the rules |
| verdict_style | script | verdict style rotates (no same-outcome repetition) |
| originality | script | not a near-copy of an earlier script |
| end_tease | script | the video ends on the next case |
| research | script | the writers' room used the research brief |
| time_ladder | script | the case is examined on the time ladder (ticking clock) |
| exhibits | script | science claims entered as Exhibits with real sources |
| grimm_prototype | script | Grimm's failed Prototype demonstration (mad-scientist beat) |
| verdict_line | script | Nana's verdict opens with 'Here's what's true' |
| designed_voices | final | every character speaks in its designed voice |
| music_bed | final | music/ambience bed under the story |
| animation | final | minimum seconds of animated character scenes |
| real_motion | final | animated scenes really move (no template push-ins) |
| no_frozen_frames | final | no still picture held too long |
| slop_guard | final | anti-'AI slop' score under the hold line |
| thumbnails | final | thumbnail passes the phone check + runner-up |
| titles | final | several scored titles |
| chapters | final | YouTube chapters (at least 3) |
| shorts | final | Shorts cut, checked and ready |
| short_covers | final | every Short has a designed cover |
| self_review | final | 6-point creative self-review at or above the bar |
| promise_paid | final | the thumbnail's promise is on screen early |
| impact_map | final | Impact Map: hook in 3 s, timed punchlines, sound spacing, variety vs last 10, flash safety |
| visual_change | final | a new picture state every <= VISUAL_CHANGE_MAX_S, no overload |
| living_characters | final | reaction cutaways show the approved character, blinking, breathing and talking |
| breakout_bar | final | Breakout Score >= BREAKOUT_HARD_BAR (no upload below it) |
| aliveness | final | no stretch of the video looks like a still photo |
| takeaways_written | final | every department run of this episode finished its six steps and wrote a valid takeaway |
| short_open | short | a Short opens on the moving promise picture, its hook has at most SHORT_HOOK_WORDS_MAX words and ends inside SHORT_HOOK_BY_S seconds of the real voice, the promise text is on screen in the first second (the viewer's seat for a Short) |
| short_plain | short | a Short a layman follows on one listen: one number at most, no expert word (the viewer's seat for a Short) |
| short_shape | short | a Short has its format's length, hands its last line back to the first, asks for nothing, is an animated clip in every second and loops into its first frame, captions above the buttons (the viewer's seat for a Short) |
| short_kept | short | a Short is what its Short format says and is not like the last ten Shorts (Short formats as data) |
| short_contract | short | every department that worked on a Short (the Shorts Studio, Sound, Audience) ran under the department contract before the short gate |
| release_sheet | release | every setting of a Short's release sheet that code sets was kept by YouTube, Instagram and Facebook as each platform itself answers (or was repaired once), and each got the one master file (the release sheet) |

## 6. Settings that matter (defaults from `core.DEFAULTS`; the live Sheet wins)
**Money**

| setting | default | meaning |
|---|---|---|
| BUDGET_CEILING_INR | 5000 | hard monthly spending cap, everything included: pictures, clips, Claude writing incl. thinking, Gemini incl. TTS, retries and repairs (₹5,000 incl. ₹300 for special reels, owner 2026-11-08; a single month can be overridden in MONTH_CAP_OVERRIDES) |
| BUDGET_FLOOR_INR | 5000 | monthly budget floor; paired with the ceiling for a hard cap (₹5,000 all-in incl. ₹300 for special reels, owner 2026-11-08) |
| MONTH_CAP_OVERRIDES | (blank) | one-month caps 'YYYY-MM=INR,...' set by the owner (the v11 upgrade writes 2026-11=5226: Rs 1,226 already spent + Rs 4,000 approved on 9 Nov for the rest of November; December is back to Rs 5,000) |
| BUDGET_GUARD_PCT | 90 | at this % of the cap, extras pause (spin-offs, tool tests, follow-up Shorts); long episodes and the Shorts of the cadence keep their money; one alert per month |
| BREAKOUT_FUND_CAP_INR | 1000 | the most that carries over |
| BUDGET_MODE | standard | standard / runway (owner's tap: email link 'MODE RUNWAY' / dashboard) / growth (set by itself when revenue exists, GROWTH_AUTO_ON) |
| STANDARD_MAX_LONG_PER_MONTH | 4 | Standard makes at most this many long videos a month (owner, 10 Nov 2026: 4 - each one built to break out; the Shorts and the spin-offs carry the volume) |

**Schedule and formats**

| setting | default | meaning |
|---|---|---|
| PUBLISH_DAYS | Sat | US Eastern day(s) of the long-video slots. Owner plan (10 Nov 2026): ONE long video a week, 4 a month; the month's count is capped by STANDARD_MAX_LONG_PER_MONTH and the money governor |
| SHORTS_TRACK_ON | TRUE | standalone Shorts - every topic starts as a Short (v12 V2c-b: SHORTS_PER_WEEK and SHORTS_PER_MONTH set how many) |
| SHORTS_PER_WEEK | 3 | v12 V2c-b (a lever of the Shorts Studio, D14): standalone Shorts in any 7 days (3 = inside the band of 2 to 4 a week in which a Short does best per post). They are spaced 24 x floor(7 / this) hours apart; a follow-up of a winner comes on top |
| SHORTS_PER_MONTH | 12 | v12 V2c-b (a lever of the Shorts Studio, D14): standalone Shorts in a calendar month at most (a follow-up of a winner comes on top) |
| LADDER_ON | TRUE | v12 V2c-b (the ladder, D10): TRUE = every topic starts as a Short; a long video is made only about a topic the promote rule took from the Shorts of the last LADDER_WINDOW_DAYS days, or with your recorded override (check topic_ladder) [FALSE = long videos take their topics from the premise bench as before; Shorts are still measured] |
| LADDER_WINDOW_DAYS | 30 | v12 V2c-b (a lever of Growth and Learning, D10): a Short can be promoted to a long video for this many days after it went public; then its topic is passed over and its kept footage is deleted |
| SHORTS_BREAKOUT_X | 3 | v12 V2c-b: a Short whose public views at the 24-hour or the 48-hour mark reach this many times the median of the channel's earlier Shorts at the same mark is a WINNER: one follow-up Short is ordered with a clock (FOLLOWUP_WITHIN_H) |
| FOLLOWUP_WITHIN_H | 48 | v12 V2c-b (a lever of the Shorts Studio, D14): a winner's follow-up Short must be made within this many hours of the order; later the Shorts Studio gets a problem memo that climbs to the owner |
| CASEFILES_ON | TRUE | one Case Files countdown a month once enough episodes are archived |
| DEEP_TRIAL_ON | TRUE | one long slot a month becomes a ~20-minute Deep Trial (three acts + a Jury Room segment) |
| PREPROD_ON | TRUE | the writers' room for the next slot runs early (when nobody waits) through Message Batches at half price; production takes the result as written [FALSE = the room runs inside production] |
| PAUSED | FALSE | TRUE stops everything |

**Writers' room and show**

| setting | default | meaning |
|---|---|---|
| ROOM_MODE | v2 | v2 = diverse drafts + blind cross-family jury + one checklist revision (no role memos); v1 = the previous room |
| ROOM_V2_DRAFTS | 3 | drafts per episode, each with a different cold-open archetype |
| SHOW_MODE | auto | auto = the Showrunner also returns a Show Plan (no extra AI call), validated and logged in Show_Log; off = the Showrunner prompt without a Show Plan |
| CONSTITUTION | (blank) | the Creative Constitution (blank = the built-in one in data.CONSTITUTION). Type your own text here to replace it; every department reads it |
| BRAIN_ON | TRUE | the learning core: features per video, Technique_Evidence from YouTube's engaged views, Thompson sampling with a holdout, forecasts scored against the median |
| BRAIN_HOLDOUT | 0.2 | share of Shorts that keep the default hook (the control the sampler must beat) |

**Pictures, motion, voice**

| setting | default | meaning |
|---|---|---|
| ART_STYLE | toybox_noir | the look of animated scenes, masters and the intro: toybox_noir (owner-approved 9 Nov 2026), photoreal (matches the first locked portraits) or illustrated. STYLE words only; faces and costumes always come from Characters.visual |
| FAL_HERO_MODEL | fal-ai/kling-video/o3/standard/image-to-video | animated scenes (Kling 3.0 Standard on fal, $0.084/s audio off = $0.42 per 5 s; the Steward falls back along MODEL_LADDERS) |
| FAL_STILL_MODEL | fal-ai/flux/schnell | cheap stills |
| ANIM_SHOTS | 4 | animated scenes per long video (~20 s) |
| PARTICLES_ON | TRUE | world particle layer on every still (dust in court/case, embers in the lab, rain in the office, wind outdoors) - independent motion that reads as alive |
| LIVING_CHARACTERS_ON | TRUE | reaction cutaways show the LOCKED expression still with blinks, breathing and word-synced mouth movement |
| LIFE_LAYER_ON | FALSE | breathing warp of the near part of a still. OFF: measured on 9 Nov it reads like a camera zoom (the still detector cannot tell it apart, and neither can a viewer); the world particle layer replaces it |
| TTS_ENGINE | gemini | gemini = Gemini TTS (two speakers per request, expression tags, word timings derived by code) with automatic fallback to Kokoro on failure; kokoro = the Kokoro blended voices [kokoro] |

**Quality gates**

| setting | default | meaning |
|---|---|---|
| CONTRACT_ON | TRUE | every promised feature is a mandatory check; a failure HOLDS the video (never uploaded) with an owner card |
| CONTRACT_OFF | (blank) | comma-separated feature ids switched off (owner decision only; shown in the ledger as not checked) |
| BREAKOUT_HARD_BAR | 80 | HARD - no upload below this Breakout Score (held with the weakest part named; owner can approve anyway) |
| REHOOK_MAX_GAP_SEC | 75 | longest stretch of script allowed without a re-hook (a question, a turn, a reveal) |
| JOKE_EVERY_SEC_LONG | 15 | at least one [PUNCH] line per this many seconds of narration (long) |
| VISUAL_CHANGE_MAX_S | 4 | V2 - longest a picture state may hold in a long video (graphics / clips 2x) |
| PROMISE_BY_SEC | 5 | v12 V1: 5 (was 30) - the promise is the FIRST picture of the video. v11: the thumbnail/title promise must be on screen by this second of a long video |
| IDEA_MIN_MULTIPLE | 5 | outlier multiple required |

**Owner**

| setting | default | meaning |
|---|---|---|
| WA_ON | TRUE | WhatsApp messages and chat (only once WA_TOKEN / WA_PHONE_ID / OWNER_WA secrets exist); email always goes too |
| BUILDS_ON | TRUE | owner-ordered changes and repairs are built by Claude Code in GitHub Actions on the owner's Claude plan (secret CC_OAUTH_TOKEN); FALSE = nothing is built automatically |
| DASH_ON | TRUE | the pipeline writes the dashboard snapshot to Cloudflare KV after each tick (only once CF_ACCOUNT_ID / CF_KV_NAMESPACE_ID / CF_KV_TOKEN exist) |

**Knowledge Palace**

| setting | default | meaning |
|---|---|---|
| PALACE_ON | TRUE | TRUE = the Knowledge Palace is kept up (founding knowledge, expiry, size caps, mirrors of the learning core and the show records) and check palace_health runs on every episode [FALSE = the Palace is left untouched and the check does not apply] |
| PALACE_PLAYBOOK_TOKENS | 1800 | hard cap, in estimated tokens, of the knowledge block one department receives from the Palace before it acts (200-6000) |
| PALACE_PLAYBOOK_TOKENS_BY_DEPT | {"D4": 2400} | optional JSON {department id: cap} that overrides PALACE_PLAYBOOK_TOKENS for single departments, e.g. {"D4": 2400} |
| PALACE_LIMITS_SHARE | 0.4 | share of every department playbook reserved for limits (the owner's words, policy rules, failure lessons); limits are always served first (0.1-0.9) |
| PALACE_CANON_TOKENS | 700 | v12 B6a: estimated tokens a playbook may spend on the show's canon (the cast, then the newest aired cases), ON TOP of the department's cap, so canon never pushes out a limit or knowledge (100-2000) |
| PALACE_REVIEW_DAYS | (blank) | optional JSON {kind: days} that overrides how long an item stays valid before it must be re-validated (defaults: REVIEW_DAYS in whatifs/org/palace.py; 0 = never) |
| PALACE_KIND_CAPS | (blank) | optional JSON {kind: most served items}; over the cap the lowest-value item of that kind is expired by code (defaults: KIND_CAPS in whatifs/org/palace.py) |

**Creative departments**

| setting | default | meaning |
|---|---|---|
| ORG_PROMPT_INJECT | TRUE | v12 B6a: TRUE = the creative runs (D4 write and draft, D5 package, D6 plan) put their Palace playbook INTO the model prompts of their creative calls, the models cite what they applied with a quote and code verifies it (checks palace_injected, palace_cited, canon_in_brief) [FALSE = the playbook is handed over with the brief only; the three checks say NA] |
| CANON_CALLBACK_ON | TRUE | v12 B6a: TRUE = the newest aired case is a continuity debt: the script must call back to it in one spoken line, cited with that exact line (check canon_in_brief) |
| CREATIVE_MEMO_MAX_PER_RUN | 1 | v12 B6a: proposals (new ideas, experiments, joke or hook banks, world-building) a creative run may send to the Council as creative memos (0-3) |
| CREATIVE_MEMO_SAME_MAX | 0.5 | v12 B6a: a proposal whose words overlap an earlier creative memo this much (0-1) is dropped as the same idea - the Council sees distinct options |
| PALACE_PROMPT_EST_INR | 15 | v12 B6a: allowance per long video for the Palace playbook inside the creative prompts and the citations: about 2,000 input tokens at the end of each creative call (not cached, so the cached brief is never re-written; about Rs 10) plus about 120 output tokens of citations a call (about Rs 4); counted in the episode estimate while ORG_PROMPT_INJECT is on. Reconcile with Cost_Log after 2-3 videos |

**Organisation**

| setting | default | meaning |
|---|---|---|
| ORG_ON | TRUE | TRUE = every wired department runs under the department contract (load its memos and Palace playbook, act, emit memos, write a takeaway, execute tickets, report) and checks dept_contract and takeaways_written run on every episode [FALSE = the plain calls without the organisation; the organisation also needs PALACE_ON] |
| ORG_SLA_HOURS | (blank) | optional JSON {memo type: [acknowledge hours, resolve hours]} that overrides a memo type's two clocks (defaults: TYPES in whatifs/org/schemas.py) |
| ORG_ESCALATE_HOURS | (blank) | optional JSON {"1": [P0, P1, P2 hours a memo may sit with the Council], "2": [P0, P1, P2 hours between reminders to the owner]} (defaults: ESCALATE_H in whatifs/org/memos.py) |
| ORG_OWNER_REMINDS_MAX | 2 | how many times the owner is reminded of the same stuck item after the first message (0-9); after that it rests on his list |
| ORG_DEVIATION_PCT | 25 | a measure that moves this many percent against the median of a department's earlier runs turns the run's takeaway into a new finding for the Palace (5-200) |
| ORG_CAPS_INR | (blank) | optional JSON {department: rupees a month} for the organisation's own paid thinking (defaults in whatifs/org/registry.py: D2 300, D3 120, C 150, L 40, takeaways 60) |
| ORG_RUN_STALE_H | 6 | a department run still marked running after this many hours is flagged as abandoned and becomes a problem memo (1-48) |

## 7. Jobs (`.github/workflows/`)
| file | name | schedule (cron, UTC) | other triggers | cli commands |
|---|---|---|---|---|
| bakeoff.yml | Model bake-off | - | workflow_dispatch | bakeoff |
| brief.yml | Monthly Brief | 15 6 1 * * | workflow_dispatch | brief |
| checks.yml | Checks | - | workflow_dispatch, push, pull_request | prready, rehearsal |
| claude-build.yml | Claude build | - | workflow_dispatch, issues | build_ready |
| dash.yml | Dashboard action | - | repository_dispatch | dash_action |
| fix.yml | Fix held video | - | issues | fixheld |
| google_signin.yml | Google Sign-in (one time) | - | workflow_dispatch | - |
| keepalive.yml | Keep Alive | 0 3 1,15 * * | workflow_dispatch | - |
| learn.yml | Learning Loop | 41 9 * * * | workflow_dispatch | learn |
| merge.yml | Merge change | - | issues | - |
| pipeline.yml | Pipeline | 7,37 * * * * | workflow_dispatch, repository_dispatch | produce, tick |
| preprod.yml | Pre-production | 17 * * * * | workflow_dispatch | preprod |
| preview.yml | Script Preview | - | workflow_dispatch, issues | preview, previewdecide |
| repair.yml | Repair Bot | - | workflow_run | - |
| research.yml | Research Brief | - | workflow_dispatch | research |
| restore.yml | Restore code | - | workflow_dispatch, push | - |
| setup.yml | Setup | - | workflow_dispatch | setup, voices |
| sheets.yml | sheets | - | workflow_dispatch | sheets |
| special.yml | Special reel | 40 14 * * * | workflow_dispatch | pilot, special |
| trends.yml | Trend Scout | 23 5 * * 1 | workflow_dispatch | trends |
| upload_check.yml | Upload check | - | workflow_dispatch | upload_check |
| voices.yml | Voice Lab | - | workflow_dispatch | voices |
| wa_setup.yml | WhatsApp setup | - | workflow_dispatch | wa_templates |
| whatsapp.yml | WhatsApp | - | repository_dispatch | wa_inbound |

## 8. Sheet tabs (`core.TABS`; append-only)
| tab | columns | first columns | note |
|---|---|---|---|
| Settings | 3 | key, value, note |  |
| Setup_Status | 4 | step, status, detail, updated |  |
| Models | 4 | role, provider, model, chosen_at |  |
| Premises | 10 | premise_id, grid, anchor, rule, lens, premise ... |  |
| Banned | 2 | phrase, reason |  |
| Strategies | 9 | dimension, name, definition, status, plays, score_sum ... |  |
| Episodes | 34 | episode_id, slot_et, premise, ptype, presentation_format, title ... |  |
| Cost_Log | 16 | ts, episode_id, item, provider, units, inr ... |  |
| Run_Log | 5 | ts, job, episode_id, level, message |  |
| Revenue_Log | 4 | month, source, inr_received, note |  |
| Trend_Brief | 5 | week, kind, item, detail, source |  |
| Lessons | 4 | ts, lesson, evidence, applies_to |  |
| Playbook | 13 | rule_id, department, rule, metric, source, evidence ... | the older research rulebook (whatifs/playbook.py); NOT a Palace playbook |
| Strategy_Log | 7 | ts, dimension, action, name, replaces, mean_at_change ... |  |
| Analytics | 25 | episode_id, yt_id, pulled, views, avg_view_pct, avg_view_sec ... |  |
| Repairs | 5 | ts, file, error, result, pr |  |
| Research_Brief | 9 | brief_id, brief_date, kind, ref, item, detail ... |  |
| Hook_Candidates | 14 | episode_id, rank, line, words, type, clarity ... |  |
| Cut_Map | 11 | episode_id, cut_id, start, end, duration, kind ... |  |
| Reaction_Map | 7 | episode_id, t, kind, word, line, style ... |  |
| Table_Read | 8 | episode_id, arm, mode, kind, from_role, to_role ... |  |
| Cast | 14 | id, role, display_name, voice, gender, pitch ... |  |
| Voice_Check | 7 | ts, voice, source, listed, synth_ok, multi_speaker_ok ... |  |
| Premise_Scores | 16 | ts, episode_id, round, premise, headline, source ... |  |
| Craft_Notebook | 5 | added, note, applies_to, priority, active |  |
| Technique_Library | 15 | ts, video_id, title, channel, views, hook_device ... | the outlier-video library (techniques seen in other channels' outliers); NOT the learning core |
| Owners_Cut | 11 | ts, episode_id, round, inside_scene, weirdness_hook, emotional_peaks ... |  |
| Script_Previews | 11 | draft_id, created, status, premise, title, hook ... |  |
| Dash_Acks | 5 | ts, id, verb, ok, note |  |
| Localizations | 5 | ts, episode_id, yt_id, langs, ok |  |
| Slop_Scores | 10 | ts, episode_id, slop, still, motion, template_sim ... |  |
| Data_Rules | 8 | ts, key, kind, text, videos, effect ... |  |
| Expiry_Calendar | 4 | item, expires, renew, reminded |  |
| Backups | 3 | ts, name, file |  |
| Pilots | 8 | ts, id, bench_id, premise, hook, yt_id ... |  |
| Outlier_Lab | 4 | ts, video_id, title, status |  |
| Bakeoff | 3 | ts, models, card |  |
| Script_Fingerprints | 3 | ts, episode_id, sig |  |
| Owner_Briefs | 10 | ts, id, target, premise, brief_json, scores_json ... |  |
| Room_Value | 8 | ts, episode_id, winner, margin, room_score, solo_score ... |  |
| Impact_Maps | 4 | ts, episode_id, signature, summary |  |
| Tool_Scout | 8 | ts, endpoint_id, name, category, unit_price, unit ... |  |
| Reach | 6 | key, date, video_id, impressions, ctr, updated |  |
| Breakout_Scores | 8 | ts, episode_id, format, score, grade, weakest ... |  |
| Monitor48 | 7 | yt_id, video_key, kind, published, v24, v48 ... |  |
| Breakout_Queue | 7 | ts, video_key, status, plan, left, due ... |  |
| Jury_Log | 7 | ts, episode_id, stage, judge, order, ranking ... |  |
| Video_Features | 13 | ts, video_key, yt_id, format, hook, title ... |  |
| Technique_Evidence | 19 | technique_id, format, family, level, alpha, beta ... | the learning core's evidence table (whatifs/brain.py) |
| Brain_Log | 6 | ts, event, technique_id, from, to, evidence |  |
| Forecasts | 11 | ts, video_key, format, metric, lo, mid ... |  |
| Feature_Ledger | 7 | ts, episode_id, stage, feature, status, evidence ... |  |
| Model_Changes | 5 | ts, role, from, to, why |  |
| Viewer_Questions | 6 | ts, video_id, comment_id, author, text, used |  |
| Carousels | 6 | ts, episode_id, files, caption, status, ig_id |  |
| Specials | 19 | ts, id, kind, title, format, ask ... |  |
| WA_Outbox | 5 | ts, wamid, action_id, kind, status |  |
| WA_Chat | 4 | ts, msg_id, who, text |  |
| Owner_Actions | 16 | id, created, tier, kind, episode_id, text ... |  |
| Premise_Bench | 17 | bench_id, added, status, premise, headline, family ... |  |
| Demand_Signals | 9 | ts, video_id, title, channel, views, channel_median ... |  |
| Packaging_Tests | 15 | episode_id, yt_id, variant, title, thumb_text, thumb_file ... |  |
| Comment_Queue | 10 | ts, episode_id, comment_id, author, kind, text ... |  |
| Season | 8 | ts, episode_id, case, verdict, meter_final, jury_tally ... |  |
| Experiments | 26 | episode_id, created, premise_source, packaging_variant, intensity, hook_shape ... |  |
| Character_Sheets | 8 | ts, character, expression, hash, prompt, file ... |  |
| Show_Log | 11 | ts, episode_id, format, intensity, witness_twist, verdict_winner ... |  |
| Retention_Map | 10 | ts, episode_id, beat, start, end, shot_types ... |  |
| Role_ROI | 9 | ts, episode_id, role, calls, notes, accepted ... |  |
| Characters | 21 | id, name, speaker, role, philosophy, rhythm ... |  |
| Cache_Stats | 17 | updated, episode_id, job, run_id, calls, cached_calls ... |  |
| Palace_Items | 28 | id, kind, title, body_ref, summary, departments ... | the Knowledge Palace index (whatifs/org/palace.py) |
| Palace_Versions | 10 | version, ts, actor, action, item_id, item_version ... | one row per Palace change: running version + hash of the whole Palace |
| Palace_Playbooks | 11 | playbook_id, ts, dept, stage, topic, palace_hash ... | each distinct department playbook the Palace built (id = hash of its text) |
| Memos | 30 | id, type, from_dept, to_depts, holder, level ... | one row per memo between departments (whatifs/org/memos.py) |
| Sessions | 21 | id, key, dept, trigger, episode_id, attempt ... | one row per department run with its six chained receipts (whatifs/org/runner.py) |
| Takeaways | 16 | id, ts, session_id, dept, trigger, episode_id ... | what every department run learned; new findings are also proposed to the Palace |
| Org_Audit | 20 | ts, kind, run_id, dept, trigger, episode_id ... | one row per department run, escalation and watchdog pass that did something |
| Tickets | 24 | id, created, updated, from_dept, dept, lever_class ... |  |
| Lever_Changes | 12 | ts, change_id, ticket_id, lever_class, dept, target ... |  |
| Research_Agenda | 17 | id, ts, updated, source, ref, signature ... |  |
| Board_Log | 12 | ts, session_id, memo_ref, label, canary, judge ... |  |
| Release_Sheet | 13 | ts, id, platform, kind, native_id, state ... |  |
| Ladder | 27 | id, topic, premise, title, format, hook ... |  |

## 9. Modules
| module | purpose |
|---|---|
| whatifs/__init__.py | Reality Engine: the automated pipeline behind the YouTube channel Reality on Trial. |
| whatifs/anim.py | Animation director: places the animated (Kling) scenes of a long video at the retention cliffs and writes their motion prompts. |
| whatifs/art.py | Thumbnails and reel covers: premium key art, cinematic grade, bold type, phone-size readability check, brand mark. |
| whatifs/atmosphere.py | Atmosphere pack: code-only, deterministic per-shot overlays applied under the show overlay at zero API cost. |
| whatifs/bakeoff.py | One-time, hand-started clip-model bake-off: the same scenes animated by the current hero model and each candidate, capped by BAKEOFF_CAP_INR. |
| whatifs/brain.py | Channel Brain, the learning core: video features, engaged-view outcomes, Technique_Evidence (Beta-binomial), Thompson sampling with a holdout, forecasts and the weekly 'what we learned'. |
| whatifs/breakout.py | Breakout Protocol checks and tools: promise-paid, the aliveness (still-photo) detector, the Breakout Score and the 48-hour breakout monitor. |
| whatifs/builds.py | Owner builds and repairs through Claude Code in GitHub Actions (claude-build workflow) and the Merge / Reject / auto-merge rules. |
| whatifs/caretaker.py | Keeps the channel safe and the owner informed without noise (policy rescue and related watch duties). |
| whatifs/carousel.py | Instagram 'Case Files' carousel per long episode: six slides from the episode's own stills and show plan. |
| whatifs/cast.py | The Cast tab: recurring experts and rotating guests, no-repeat guest rotation, and the cast brief for the writer. |
| whatifs/charts.py | Charts as PNG images for WhatsApp and the digests (real numbers only; no data = no chart). |
| whatifs/checkpoint.py | Saves and restores an episode's expensive state (plan, assets) in the owner's Drive so a retry never pays twice. |
| whatifs/cli.py | Entry point for every GitHub workflow: python -m whatifs.cli <command>. |
| whatifs/community.py | The jury outside the video: the in-character jury comment, the keyword-parsed jury tally and viewer finds fed to the next episode. |
| whatifs/contract.py | Feature Contract: every promised feature is a named HARD check at a stage, judged from real evidence; a FAIL holds the episode and sends the owner a decision message. |
| whatifs/core.py | Settings, storage (Google Sheet or local rehearsal store), logging, cost log and Google sign-in. |
| whatifs/costguard.py | Cost controls that never touch pictures: the per-stage estimator, the spend monitor and the overrun ladder. |
| whatifs/craft.py | The owner's creative voice in the pipeline: the Creative Constitution, the Craft_Notebook tab and the outlier-video technique library. |
| whatifs/cta.py | The three audience asks (like, subscribe, share), written as witty in-show moments and placed by rules. |
| whatifs/cutmap.py | Reviewable cut map (edit-decision proposal) measured from the rendered video; nothing is ever cut automatically. |
| whatifs/dash.py | The phone dashboard's data snapshot and its taps (never contains secrets, scripts or unreleased premises). |
| whatifs/data.py | Seed data loaded into the Sheet at setup: topic grids, banned list, strategy pools, director lessons. |
| whatifs/deeptrial.py | The monthly Deep Trial: one long slot a month becomes a ~20-minute episode. |
| whatifs/demand.py | Search-demand score for bench premises from the YouTube search API (no scraping). |
| whatifs/digests.py | The daily and weekly WhatsApp briefs, built only from the owner view. |
| whatifs/enforce.py | Hard enforcement of the researched breakout rules: writer instruction, one automatic fix, then the Feature Contract check. |
| whatifs/engage.py | Engagement engine and emotion beats: typed, in-character audience prompts and one earned emotion beat in the writer brief. |
| whatifs/episode.py | One full episode in resumable stages: plan (writing, voice, shots), assets (paid pictures and clips) and the final render with its checks and packaging. |
| whatifs/facts_watch.py | Platform Facts watcher: weekly fingerprint of the official change-log pages; a change sends the owner one message (no AI call). |
| whatifs/fakes.py | Offline stand-ins for every model call (rehearsal mode WI_FAKE=1), including a fake prompt-cache server; zero cost. |
| whatifs/fixes.py | Repairs for problems full QC finds, in a fixed order with limits: free fixes first, paid fixes only up to a rupee cap. |
| whatifs/format_engine.py | Presentation-format controls (Settings cell PRESENTATION_FORMAT) and the code check of the script's format. |
| whatifs/formats.py | Formats: the show's formats as data - which one an episode is, what it tells the writers, and which devices it requires, allows or leaves out (the three-tier contract). |
| whatifs/governor.py | The money governor: hard monthly cap with a pre-flight gate, per-episode estimates, the extras guard and the breakout fund. |
| whatifs/growth.py | The click-through and retention layer of the learning loop: routed lessons, title choice, cold-open and retention rules (no model calls). |
| whatifs/herostill.py | Hero-still reels, per-character cinematic grammar and the courtroom composition (code only). |
| whatifs/hooks.py | Opening-line candidates per episode: written, validated by code, scored by an independent judge; the best one opens the video. |
| whatifs/hours.py | Hours engine: more watch hours without new videos (localised titles and descriptions, and related helpers). |
| whatifs/immersion.py | First-person immersion: the Immersion Director maps the script to a viewer-inside-the-scene vantage, sensation and camera effects. |
| whatifs/insights.py | Flag-gated learning and community extras (retention map and others), each fail-safe and bounded. |
| whatifs/ladder.py | The ladder (Growth and Learning, D10): every topic starts as a Short - each Short's real numbers are written onto one record, the promote rule picks the long video's topic by code, a long video without a promoted Short is refused unless the owner's override is recorded, and a winner's follow-up Short is ordered with a clock. |
| whatifs/launch.py | Launch checks: the zero-cost upload check, the private-lock detector and the uploads-open rule. |
| whatifs/living.py | Living characters: locked expression art in every reaction cutaway, with blink, breathing and mouth movement. |
| whatifs/manage.py | Scheduler and upkeep: tick, release, packaging rescue, hold/resume, trend scout, learning loop, guardian, setup, self-test and the one-time setting moves. |
| whatifs/media.py | fal.ai images and clips, free NASA/Pexels footage, depth maps, motion graphics and fake assets for rehearsal. |
| whatifs/microscope.py | Retention Microscope: second-by-second retention turns shot types into boosters or killers for the writer's brief. |
| whatifs/models.py | Model discovery (names never typed in code), Claude and Gemini calls with prompt caching and routing, JSON repair, fallback and fake mode. |
| whatifs/notify.py | The one owner-messaging layer with no-spam tiers; every owner message goes through notify.send(). |
| whatifs/occasions.py | Calendar-aware special reels: the special-reel slots go first to the month's best-loved occasions. |
| whatifs/orchestra.py | Time-window rule so heavy optional jobs never run inside a release window or a production run. |
| whatifs/outlier_lab.py | Outlier Lab: daily, videos doing unusually well in the wider space are analysed and their techniques stored for the writers. |
| whatifs/overlay.py | The speaker tag: a small code-drawn chip with level bars shown while a recurring role speaks. |
| whatifs/owner_brief.py | Owner Brief: the owner proposes a topic on WhatsApp, the Showrunner refines it with him, and 'lock' makes it the forced premise. |
| whatifs/owner_view.py | The owner view: one evidence-labelled data layer for WhatsApp, the dashboard, the digests and the chat brain. |
| whatifs/packaging.py | Title and thumbnail pairs per video, the owner pick, rotation in the first 48 hours, hook shapes and the ad-risk check. |
| whatifs/pilots.py | Pilot Shorts: cheap 12-15 s Shorts that test bench premises before a long video is written. |
| whatifs/playbook.py | The research-based rulebook: weekly proposed practices, vetted by code (source, evidence label) and trialled on half the episodes. |
| whatifs/preflight.py | Free health checks before any paid step; a red critical check stops the run before money is spent. |
| whatifs/premise.py | Premise quality: the generated premise bank, scoring and the Premise_Bench that ships the best premise. |
| whatifs/preprod.py | Pre-production: the writers' room for a future slot runs early through the Message Batches API and saves an approved draft. |
| whatifs/preview.py | Script Preview: scout and writers' room only, then one email with title, hook, script, shot list and estimated cost. |
| whatifs/prompts.py | Every role's brief (the prompt templates), packed for prompt caching; filled with fill(), never str.format. |
| whatifs/publish.py | Publishing: YouTube upload (scheduled, verified), thumbnail, captions, playlist, AI label; Instagram and Facebook Reels; Drive archive; Gmail notices. |
| whatifs/qc.py | Quality checks before anything goes public; any FAIL stops the upload of that file. |
| whatifs/reach.py | Impressions and thumbnail click-through per video per day from the YouTube Reporting API. |
| whatifs/reactions.py | Reaction moments: a short voiced reaction plus original code-drawn effects that amplify the feeling. |
| whatifs/reels.py | 9:16 reels cut from the long video's own shots: cover first, new order, re-voiced lines, burned captions. |
| whatifs/release.py | The release sheet (Publishing, D9): every setting of every platform as data - who sets it, what it must be, how it is proven - one master file sent natively to YouTube Shorts, Instagram Reels and Facebook Reels, and a receipt for every row read back from the platform. |
| whatifs/render.py | The renderer: segments (parallax stills, crops, clips, graphics, particles) piped into FFmpeg, frame-accurate against the narration clock, with score and effects. |
| whatifs/replan.py | The mid-month re-planner: invests money that is truly free in breakout steps, each one a WhatsApp decision the owner can veto. |
| whatifs/research.py | Audience and topic research before topic selection, with observed evidence kept apart from interpretation. |
| whatifs/room.py | Writers' room v1 and the shared room steps: scout, showrunner, production bible, writer, critic and policy-safety gate, promise shot. |
| whatifs/room2.py | Writers' room v2 (the default): diverse drafts from one strong writer, a blind cross-family jury, one checklist revision and the joke tournament. |
| whatifs/sampler.py | The per-episode draw (runtime, counts, strategies): a bandit with exploration. |
| whatifs/scout.py | The weekly tool scout: new models, prices and deprecations from the fal catalog and Artificial Analysis. |
| whatifs/sheets.py | The one-time character sheets workflow: expression sheets and the courtroom set under a hard lifetime image cap. |
| whatifs/shorts2.py | Shorts Studio (D14): the standalone Short as a product of its own - a Short format as data, three scripts judged blind, every second an animated clip planned by code, the loop closed by code, and the viewer's seat for a Short before any picture is paid. |
| whatifs/shortslab.py | Shorts Lab: the weekly list of winning Shorts for the owner to link to the full episode. |
| whatifs/shotplan.py | Shot-plan rules: where the animated clips go, shot pacing (pieces_for) and related fixes; never adds a paid shot. |
| whatifs/show.py | Reality on Trial as code: the Show Plan contract with its validator, the character bible, the script-tag contract and the IP-similarity guard. |
| whatifs/showfx.py | The trial's signature devices drawn by code at render time (reconstruction stack, HUD, jury meter, exhibit pins, teacup, letterbox). |
| whatifs/similarity.py | Script similarity guard: a MinHash fingerprint of every final script, compared with the last 10. |
| whatifs/slop.py | Slop Guard: one 0-100 'AI slop' risk score per video from existing measurements. |
| whatifs/sound.py | Sound design: code-generated textures under the shots, per-world beds, story events and a music bed that moves. |
| whatifs/specials.py | Specials: short cast reels that are not episode cut-downs (cast intro, occasion reels). |
| whatifs/spinoff.py | The 'Case Files' countdown spin-off: a long video built from past episodes, with originality gates. |
| whatifs/steward.py | Model Steward: watches picture and clip models and prices, proposes upgrades and tells the owner in advance. |
| whatifs/tableread.py | The optional table read of writers' room v1 (off by default; room v2 does not use it) and its with/without comparison. |
| whatifs/truth.py | Truth Registry: the single statement of what is current and what is retired, and the scanner that enforces it in docs, docstrings and prompts. |
| whatifs/tts_gemini.py | Gemini TTS narration: chunked requests, designed voices, retries and timing (the model name is discovered live). |
| whatifs/v91.py | Feature switchboard: on(flag) and the fail-safe guard(feature, episode) wrapper for flag-gated features. |
| whatifs/viewers.py | 'Viewer v. Physics': weekly, viewers' what-if questions from comments are stored and handed to the scout as premise data. |
| whatifs/visual_lab.py | Visual Lab: weekly ranking of picture treatments by how viewers held during them, proposed at the same cost. |
| whatifs/voice.py | Narration voice and pacing: the TTS engine with its fallback, human-style timing, markers and the master chain. |
| whatifs/voice_lab.py | Voice samples and the voice check: samples emailed, uploaded to Drive and kept as a GitHub artifact. |
| whatifs/voiceq.py | Designed character voices (by voice ID) and voice loudness. |
| whatifs/wa.py | The WhatsApp control room: interactive buttons inside the 24-hour window, the approved template outside it, and inbound owner messages. |
| whatifs/ypp.py | The North-Star tracker: weekly YouTube Analytics progress toward the Partner Program thresholds. |
| whatifs/org/__init__.py | The Organisation: the departments and work stages every org module shares (Knowledge Palace now; memos, runner and registry build on these). |
| whatifs/org/audience.py | Audience (D13): the viewer's seat - what a first-time viewer would meet is measured by code and repaired by code before any picture is paid: the promise as the first picture, a voice that breathes, few numbers. |
| whatifs/org/board.py | Review Board (D3): every research memo judged blind by strong judges of two model families on a fixed yes/no checklist, with a planted canary in every session; scores and the verdict are computed by code. |
| whatifs/org/canon.py | World canon: the show's living bible as Palace items - the cast mirrored from the character bible, a case record written by code after every D4 write and accepted only when the upload is confirmed, the continuity debt the next script must pay, and the check canon_in_brief. |
| whatifs/org/cite.py | Creative citations: the rule the creative model calls receive, quote-anchored verification of every Palace item a model says it applied, creative memos with the same-idea guard, and the episode checks palace_injected / palace_cited. |
| whatifs/org/execute.py | Execution Engine: turns a ticket into a typed change, writes it down before and after, verifies it with evidence another component wrote later, and rolls it back when that fails. |
| whatifs/org/layman.py | Layman test (D13): the expert words a first-time viewer would not know are counted by code, and the promise line-up asks two cheap readers whether the first 30 seconds say what the video is about. |
| whatifs/org/levers.py | Lever registry: every Settings cell a department may change by ticket - type, range, largest step, the direction that needs the owner, the checks that judge it - and the scope of an automatic merge. |
| whatifs/org/memos.py | Memos: the organisation's nervous system - validated on write, read only by their audience, moved only with proof, escalated by the SLA watchdog when a clock runs out. |
| whatifs/org/palace.py | Knowledge Palace: the one repository every department reads and writes - guarded items, life cycle, versions and bounded department playbooks. |
| whatifs/org/registry.py | Department registry: what each department is for, the code it wraps, its rhythm, levers, thinking cap, owned checks and the call sites that really run under the runner. |
| whatifs/org/rnd.py | R&D (D2): a research agenda computed from the organisation's own gaps, one bounded web-search question at a time, every source proven by code, research memos to the Review Board. |
| whatifs/org/runner.py | Department runner: the six-step contract of every department run - LOAD, ACT, EMIT, LEARN, EXECUTE, REPORT - each proven by a receipt the runner itself builds and chains. |
| whatifs/org/schemas.py | Memo schemas: every memo type the organisation can send - sender, audience, body, clocks, statuses and legal moves as data - with the validator that runs on every write. |
| whatifs/org/shortseat.py | Audience (D13): the viewer's seat for a Short - the first frame, the hook, plain words, the shape and the loop are measured by code and repaired by code before any picture is paid. |
| whatifs/org/wraps.py | Department wrappers: what each wrapped production step reports about its own output (measures, lessons, problem memos) when it runs under the department runner. |
| tools/atmos_bench.py | Render performance check: times one still shot through the real render path with the atmosphere layer off and on (run: python tools/atmos_bench.py [seconds]). |
| tools/ci_report.py | CI report: turns the unit-test or rehearsal log of GitHub's Checks into annotations on the run page (readable without a sign-in), so a red run names its cause and a green run shows its totals and the rehearsal's episode id. |
| tools/gen_docs.py | Generates docs/CURRENT/SYSTEM.md from the live code (run: python tools/gen_docs.py); the test suite fails when the committed file differs. |
| tools/google_signin.py | One-time Google sign-in helper run on GitHub: prints the sign-in links, swaps the pasted address for a long-life key and emails it to the owner (never printed in the log). |
| tools/perf_atmosphere.py | Render-time comparison of one rehearsal-size episode with ATMOSPHERE_ON true vs false (usage: WI_FAKE=1 WI_SMALL=1 python tools/perf_atmosphere.py). |
| tools/plan_guard.py | Plan Guard: runs on every push; RED when code breaks a locked rule (typed model names, flagged words, duplicate definitions, retired concepts in current docs or prompts). |
| tools/rehearsal.py | Full offline rehearsal: setup -> voices -> tick -> produce -> release -> trends -> learn -> brief with fake models, images and voice; proves every stage connects at zero cost. |
| tools/repair.py | Repair bot: on a crashed job, sends the traceback and the failing file to the model, checks the fixed file with Plan Guard and the offline rehearsal, and opens a pull request. |
| tools/sweep.py | Episode-id sweep: runs the whole fake pipeline once per FIXED episode id (the fake pipeline is seeded by the id) and writes one RESULT line per id; every hold, crash or warning class it shows is a fault to trace. |

## 10. Knowledge Palace (`whatifs/org/palace.py`)
- One repository every department reads and writes. Index: tab `Palace_Items` (one row per item; enough to build a playbook in one read). Full bodies:
  founding items resolve from `whatifs/org/seed/`, runtime items live in the Drive folder palace/. Nothing is ever deleted.
- Kinds (11): takeaway, technique, strategy, plan, world_canon, style_rule, policy_rule, tool_fact, audience_insight, failure_lesson, owner_preference. Limits (served first, never dropped silently): policy_rule, owner_preference, failure_lesson and every item holding the owner's words.
- Statuses: proposed, accepted, testing, proven, retired, superseded, expired. Only proven, accepted, testing can reach a prompt (`palace.servable`, the guard that runs before any ranking).
- The write gate (`palace.check`): dated evidence is required, trust is computed from the evidence type, every `applied_in` reference must exist in the code,
  and text that names a retired concept, reads like an instruction to a model or proposes gaming the platform is refused.
- Evidence types and the trust code gives them: owner decision 1.0, own data 0.9, show record 0.9, measured 0.8, official 0.8, build record 0.7, practice 0.6, research digest 0.5, opinion 0.3, model 0.2.
- The owner's words change only by the owner. An item that is retired or superseded sends everything derived from it back for re-validation (`palace._cascade`).
- Expiry: past `review_by` an item leaves every playbook until re-validated; a limit stays served, marked review due, and is reported.
- Playbook (`palace.playbook(dept, stage, topic)`): guard, then lanes (limits, proven, accepted, testing), then relevance, filled under a hard cap of 1800 estimated tokens; limits hold a reserved share of 0.4. Same Palace state = byte-identical text; `playbook_id` is the hash of the text.
- Runs in production: `palace.daily` in the learning job, `palace.maintain` in Setup, contract check `palace_health` on every episode.
- Every wired department run loads its playbook (section 11); the creative runs (D4 write and draft, D5 package, D6 plan) put it INTO their model
  prompts and cite what they applied (v12 B6a). Not yet wired (later batches): the Council, the Librarian's merges, outcome scores.

**Founding knowledge** (166 items in `whatifs/org/seed/`; 0 invalid): breakout.json 15, build.json 91, feel.json 15, owner.json 30, platform.json 15.
By kind: audience_insight 8, failure_lesson 4, owner_preference 26, plan 2, policy_rule 12, strategy 28, takeaway 14, technique 53, tool_fact 19.

**Life cycle** (`palace.MOVES`; a move that is not listed is illegal for everyone)

| from | to | who may make the move |
|---|---|---|
| proposed | accepted | owner, council |
| proposed | retired | owner, council |
| proposed | superseded | owner, council, librarian, build |
| accepted | testing | owner, council, D10 |
| accepted | proven | D10 |
| accepted | retired | owner, council, D10 |
| accepted | expired | clock, librarian |
| accepted | superseded | owner, council, D10, librarian, build |
| testing | accepted | council, D10 |
| testing | proven | D10 |
| testing | retired | owner, council, D10 |
| testing | expired | clock, librarian |
| testing | superseded | owner, council, D10, librarian, build |
| proven | testing | D10 |
| proven | retired | owner, council, D10 |
| proven | expired | clock, librarian |
| proven | superseded | owner, council, D10, librarian, build |
| expired | accepted | owner, council, D10 |
| expired | testing | council, D10 |
| expired | proven | D10 |
| expired | retired | owner, council, D10, librarian |
| expired | superseded | owner, council, D10, librarian, build |
| retired | proposed | anyone |
| retired | testing | D10 |

**Review window and size cap by kind** (days before re-validation, 0 = never; most served items)

| kind | review days | cap |
|---|---|---|
| takeaway | 180 | 400 |
| technique | 120 | 300 |
| strategy | 180 | 80 |
| plan | 45 | 40 |
| world_canon | 0 | 600 |
| style_rule | 180 | 120 |
| policy_rule | 90 | 120 |
| tool_fact | 60 | 150 |
| audience_insight | 120 | 120 |
| failure_lesson | 365 | 200 |
| owner_preference | 0 | 150 |

**Departments** (`whatifs/org/__init__.py`; stage = the stage a playbook is built for when none is named). Stages: ideation, writing, packaging, visual, sound, qa, publishing, growth, finance, ops, planning, research.

| id | department | default stage |
|---|---|---|
| D0 | Owner Office | ops |
| D1 | Strategy & Planning | planning |
| D2 | R&D - Research | research |
| D3 | Review Board | research |
| D4 | Creative - Ideation & Writers' Room | writing |
| D5 | Packaging | packaging |
| D6 | Visual Production | visual |
| D7 | Sound | sound |
| D8 | QA & Enforcement | qa |
| D9 | Publishing & Distribution | publishing |
| D10 | Growth & Learning | growth |
| D11 | Finance | finance |
| D12 | Operations | ops |
| D13 | Audience | qa |
| D14 | Shorts Studio | writing |
| C | The Council | planning |
| L | The Librarian | ops |

## 11. The organisation: departments, the department contract, memos (`whatifs/org/`)
- Every department run goes through `runner.run` and its 6 steps, always in this order: LOAD -> ACT -> EMIT -> LEARN -> EXECUTE -> REPORT. Each step leaves a receipt that the
  runner builds from what code observed (the playbook it loaded, the ids the Sheet returned, the money and model calls it counted); the receipts are
  chained, stored in tab `Sessions`, and re-computed by the episode gates (`runner.verify`). A department cannot report its own progress.
- LOAD is strict: it raises before any work or money. After ACT nothing is thrown away: the other steps always run and are recorded, the error of ACT
  is re-raised, and a broken step is a BREACH. `runner.work` (existing production steps) records the breach and still returns the result - a paid
  or uploaded result is never lost - and the gates `dept_contract` (before picture money) and `takeaways_written` (before upload) then hold the video.
- Playbook: `brief` mode hands the department's Palace playbook over with the work order; `prompt` mode puts it into the cached layer of the system
  prompt at the one doorway for text calls (`models.ask`) and proves it was there. A run whose playbook never reached the work is a breach.
- Takeaway: every run writes at least one to tab `Takeaways`, built from what the run measured against the department's own earlier runs. A stock
  or empty one is refused (`schemas.check_takeaway`). Only a new finding (a deviation, a failed check, a failure) is proposed to the Palace, as
  `proposed`; it reaches no prompt until it is accepted. A takeaway cannot score itself.
- Memos (tab `Memos`): validated on write (`schemas.check_memo`), read only by their audience (`memos.inbox`), closed only with proof
  (`memos.resolve`), never rewritten while open, never reopened once closed. The id is the hash of type, sender, audience and dedupe key.
- Statuses: open, acknowledged, in_progress, escalated, resolved, rejected (closed: resolved, rejected). Two clocks per memo: acknowledge and resolve. Acknowledging stops only the first.
- The SLA watchdog (`memos.watchdog`, every tick): a memo whose clock ran out climbs department -> Council -> owner, skipping a level that has no
  wired run. The owner hears about a stuck item once, then at most 2 reminders, 3 messages a pass at most.
- EXECUTE: every open ticket of the running department goes to the Execution Engine (`execute.apply`, section 12). With the engine switched off
  (`EXEC_ON`) a ticket is escalated at once with the reason - it is never left as text.

**Departments** (`whatifs/org/registry.py`). Wired = real call sites run it under the runner (checked against the code); pending = the build batch that wires it.

| id | department | rhythm | runs under the runner | playbook | thinking cap (Rs / month) | levers (Settings cells) |
|---|---|---|---|---|---|---|
| D0 | Owner Office | tick | pending (B9) | brief | - | WA_ON, DASH_ON |
| D1 | Strategy & Planning | weekly | pending (B9) | brief | - | STANDARD_MAX_LONG_PER_MONTH, PUBLISH_DAYS, VIDEOS_PER_MONTH_EST, FORMAT_SHARE_F1, FORMAT_SHARE_F2, FORMAT_SHARE_F3 |
| D2 | R&D - Research | daily | daily (whatifs/cli.py), weekly (whatifs/cli.py) | brief | 300 | RESEARCH_ON, IDEA_MIN_MULTIPLE, RESEARCH_PER_WEEK |
| D3 | Review Board | weekly | assess (whatifs/cli.py) | brief | 120 | BOARD_MIN_EVIDENCE |
| D4 | Creative - Ideation & Writers' Room | episode | write (whatifs/episode.py), draft (whatifs/preview.py) | brief | - | ROOM_MODE, ROOM_V2_DRAFTS, REHOOK_MAX_GAP_SEC, JOKE_EVERY_SEC_LONG, COLD_OPEN_LORE_FREE_SEC |
| D5 | Packaging | episode | package (whatifs/episode.py) | brief | - | PROMISE_BY_SEC |
| D6 | Visual Production | episode | plan (whatifs/episode.py), assets (whatifs/episode.py), render (whatifs/episode.py) | brief | - | ANIM_SHOTS, VISUAL_CHANGE_MAX_S, PARTICLES_ON, LIVING_CHARACTERS_ON, CAMERA_MOTION |
| D7 | Sound | episode | voice (whatifs/episode.py), short_voice (whatifs/shorts2.py) | brief | - | SOUND_DESIGN_ON, TTS_ENGINE |
| D8 | QA & Enforcement | episode | script_gate (whatifs/episode.py), final_gate (whatifs/episode.py), short_gate (whatifs/shorts2.py), release_gate (whatifs/release.py) | brief | - | CONTRACT_OFF, BREAKOUT_HARD_BAR, CRITIQUE_MIN |
| D9 | Publishing & Distribution | episode | publish (whatifs/episode.py), short_publish (whatifs/release.py) | brief | - | REEL1_DELAY_MIN, REEL2_DELAY_MIN, NEXT_LINK_ON, IG_TRIAL_REELS_ON, SHORT_THUMB_ON |
| D10 | Growth & Learning | daily | daily (whatifs/cli.py), promote (whatifs/ladder.py) | brief | - | BRAIN_ON, BRAIN_HOLDOUT, LADDER_WINDOW_DAYS, LADDER_MIN_ENGAGED |
| D11 | Finance | daily | pending (B9) | brief | - | BUDGET_GUARD_PCT, BREAKOUT_FUND_CAP_INR, AUTO_FIX_PAID_INR |
| D12 | Operations | tick | operate (whatifs/org/execute.py) | brief | - | PREFLIGHT_ON |
| D13 | Audience | episode | seat (whatifs/episode.py), probe (whatifs/episode.py), short_seat (whatifs/shorts2.py) | brief | - | NUMBERS_PER_MIN_MAX, GRAPHICS_MAX_LONG, GRAPHICS_FREE_SEC, BREATH_EVERY_S, PLAIN_HARD_PER_MIN_MAX, PLAIN_OPENING_HARD_MAX, PLAIN_HARD_PER_SENTENCE_MAX, SHORT_HOOK_WORDS_MAX, SHORT_HOOK_BY_S, SHORT_NUMBERS_MAX, SHORT_EXPERT_MAX, SHORT_PROMISE_WORDS_MAX |
| D14 | Shorts Studio | episode | write (whatifs/shorts2.py), make (whatifs/shorts2.py) | brief | - | SHORT_SHARE_S1, SHORT_SHARE_S2, SHORT_SHARE_S3, SHORT_MIN_S, SHORT_MAX_S_S1, SHORT_MAX_S_S2, SHORT_MAX_S_S3, SHORTS_PER_WEEK, SHORTS_PER_MONTH, SHORTS_BREAKOUT_X, FOLLOWUP_WITHIN_H |
| C | The Council | weekly | pending (B6) | brief | 150 | ORG_SLA_HOURS |
| L | The Librarian | weekly | pending (B8) | brief | 40 | PALACE_PLAYBOOK_TOKENS, PALACE_PLAYBOOK_TOKENS_BY_DEPT, PALACE_LIMITS_SHARE, PALACE_REVIEW_DAYS, PALACE_KIND_CAPS |

Runs an episode needs before each gate: script: D4 write, D7 voice, D5 package, D6 plan, D13 probe, D13 seat; final: D4 write, D7 voice, D5 package, D6 plan, D13 probe, D13 seat, D8 script_gate, D6 assets, D6 render; short: D14 write, D7 short_voice, D13 short_seat; release: D9 short_publish.

**Memo types** (`whatifs/org/schemas.py` TYPES; clocks in hours at urgency P1)

| type | from | to | kind | acknowledge / resolve | closed by | purpose |
|---|---|---|---|---|---|---|
| owner_memo | D0 | any | ask | 1 / 24 | ticket_executed, owner_answer | the owner's words VERBATIM, the interpretation and the departments it affects |
| research_memo | D2 | D3 | ask | 24 / 48 | assessment_memo | a research question, what was found, the dated sources, proposed actions, expected impact, cost and the departments it targets |
| assessment_memo | D3 | C | ask | 168 / 168 | decision_memo | the blind cross-family jury's scores for one memo and its verdict |
| creative_memo | D4, D5, D6, D7 | C | ask | 84 / 84 | decision_memo, assessment_memo | a new idea, an experiment proposal, a joke or hook bank, a world-building proposal |
| performance_memo | D10 | any | inform | 24 / 24 | read_by_all, closed_unread | 48 h / 7 d / 28 d outcomes of a video, changes in technique evidence, breakouts |
| problem_memo | any | any | ask | 2 / 24 | repair_verified, owner_waived, episode_closed, repair_memo | what failed, where, the evidence and the attempt count |
| repair_memo | any | D8 | ask | 24 / 24 | repair_verified, repair_refused | the fix that was applied and the proof that it passed again |
| decision_memo | C | any | inform | 24 / 24 | read_by_all, closed_unread | what changes, why (the memos it cites), the lever class, the tickets and whether the owner must approve |
| ticket | C or any department | any | ask | 24 / 48 | lever_verified, rolled_back, owner_answer | ONE executable change: lever, target, value or diff, acceptance test, rollback |
| build_request | D12 | D12 | ask | 24 / 72 | merged_verified, owner_answer | a code change that no lever can make: the spec, the files, the tests to add and the acceptance |
| takeaway | any | L | record | 0 / 0 | - | one atomic learning from one department run (kept in the Takeaways tab, proposed to the Palace when it is new) |

**Who owns each contract check** (a failed check becomes a problem memo to that department): D1: breakout_bar; D2: research, research_cadence; D4: audience_asks, canon_in_brief, cold_open, emotion_beat, end_tease, exhibits, format_kept, grimm_prototype, hook_lab, idea_evidence, joke_density, no_retired, originality, owners_cut, palace_cited, palace_injected, retention, send_and_awe, time_ladder, verdict_line, verdict_style; D5: chapters, short_covers, thumbnails, titles; D6: aliveness, animation, impact_map, living_characters, no_frozen_frames, promise_paid, real_motion, slop_guard, visual_change; D7: designed_voices, music_bed; D8: dept_contract, self_review, short_contract, takeaways_written; D9: release_sheet, shorts; D10: brain_playbook, topic_ladder; D12: docs_current, lever_verified; D13: short_open, short_plain, short_shape, viewer_breath, viewer_numbers, viewer_plain, viewer_probe, viewer_promise; D14: short_kept; C: decisions_executed; L: palace_health.

## 12. The Execution Engine: from a decision to a change that runs (`whatifs/org/levers.py`, `execute.py`)
- A ticket is ONE change: lever class, target, value. The engine compiles it into a typed operation with a registered way to verify and to undo it,
  or refuses it with the reason. The ticket's free text (`acceptance_test`, `rollback`) is for people; code never executes it.
- States (tab `Tickets`, one row per ticket): queued, awaiting_owner (nothing changed yet) -> intent, applied, dispatched, pr_open, merged (a change is under way or waits for its
  proof) -> verified, rolled_back, refused, failed. Tab `Lever_Changes` is the ledger: one appended row per event - `intent` BEFORE the change, `applied` with the
  read-back after it, then `verified` with the proof or `rolled_back` with what was restored. A row is never edited.
- A change is verified only by rows another component wrote AFTER it: a later department run, the check rows of a video made after it, the features
  of later videos, GitHub's own check runs. The engine's read-back is necessary, never enough.
- The tick pass (`execute.engine_tick`, next to the SLA watchdog) reads state, not events: it takes up every new ticket of a wired department at once,
  starts a waiting ticket when its moment is free, settles an apply that a killed job left half done, verifies or rolls back, follows a build to its
  merge, and takes back a change whose ticket a person closed. It records when it last finished (`EXEC_TICK_AT`); check `lever_verified` fails when
  tickets wait and that is more than a day old.
- A setting or an experiment changes BETWEEN videos (no video with status PLANNING / VOICING / VISUALS), and a department has at most one unverified setting or
  experiment at a time - so the checks of one video can be attributed to one change.
- Rollback of a setting is compare-and-swap: the old value returns only if the cell still holds what the engine wrote. A value typed by the owner afterwards wins.
- Windows: a change with no evidence after 14 days (`EXEC_VERIFY_DAYS`) is rolled back; knowledge that 3 complete runs of its department
  were not served is retired again; an arm must be in the features of 2 later long videos. While a ticket waits for its proof its resolve clock
  is the end of that window (`memos.await_proof`, at most 130 days); the engine itself rolls back when it ends.
- A ticket closes as `lever_verified` or `rolled_back` only when the ledger holds that row for it (`memos.resolve`); only the engine may close it that way.
- The owner: a move in the direction that weakens a gate, costs more or changes his plan waits for ONE pre-filled message (Approve / Reject); nothing
  changes before his tap. A change that could neither be verified nor undone is escalated to him at once.

| class | what it changes | how it is applied | verified by | undone by |
|---|---|---|---|---|
| A knowledge | a Palace item (`palace:<key>`) | accepted with the Council's authority; must fit the department's playbook at once | a later complete run of the department was served that version (and cited it, once the department runs in `prompt` mode) | retire it / restore the earlier text |
| B setting | a registered Settings cell | `levers.check` (owner department, type, range, one step), then written between videos | a video made after the change passes the lever's checks (no checks: the next complete run of the department) | compare-and-swap back to the old value |
| C experiment | a trial in the research rulebook (`playbook:<room role>`) | vetted by `playbook.vet`, needs a free trial slot (of 3) | the features of later long videos carry the arm, or the trial was judged on its data | the trial is retired |
| D prompt rule | a Palace rule item (style_rule / policy_rule) | as A; at most 12 rules made by ticket per department | as A | as A |
| E code | the repository (ticket to D12) | a `build_request`, the build workflow, at most 2 re-builds | merged AND every check on the merge commit green | pull request closed; after a merge a revert build the owner merges |

- Automatic merge of a code build (`levers.merge_scope`, switch `EXEC_AUTO_MERGE_ON`): decided on the REAL diff - only new files `tests/test_*.py` (plus the
  regenerated SYSTEM.md), nothing deleted, at least one new test, at most 400 added lines. Anything else gets the owner's Merge / Reject message with the reason.

**The lever table** (`whatifs/org/levers.py`). Range and step are refused, never clamped. Owner = the direction that needs his tap.

| lever (Settings cell) | department | type | range | largest step | needs the owner | judged by |
|---|---|---|---|---|---|---|
| WA_ON | D0 | bool | - | - | always: it is your own channel to the pipeline | the next complete run |
| DASH_ON | D0 | bool | - | - | always: it is your own dashboard | the next complete run |
| STANDARD_MAX_LONG_PER_MONTH | D1 | int | 1 to 8 | 1 | always: it changes the plan you set | the next complete run |
| PUBLISH_DAYS | D1 | days | - | - | always: it changes the plan you set | the next complete run |
| VIDEOS_PER_MONTH_EST | D1 | int | 1 to 8 | 1 | always: it changes the plan you set | the next complete run |
| FORMAT_SHARE_F1 | D1 | int | 0 to 100 | 20 | - | the next complete run |
| FORMAT_SHARE_F2 | D1 | int | 0 to 100 | 20 | - | the next complete run |
| FORMAT_SHARE_F3 | D1 | int | 0 to 100 | 20 | - | the next complete run |
| RESEARCH_ON | D2 | bool | - | - | off: it switches off something you rely on | research |
| IDEA_MIN_MULTIPLE | D2 | float | 2 to 20 | 2 | down: it weakens a quality gate | idea_evidence |
| RESEARCH_PER_WEEK | D2 | int | 1 to 8 | 2 | up: it costs more money | research_cadence |
| BOARD_MIN_EVIDENCE | D3 | int | 3 to 9 | 1 | down: it weakens a quality gate | research_cadence |
| ROOM_MODE | D4 | enum | v2, v1 | - | value v1: v1 is the older writers' room without the blind jury | owners_cut |
| ROOM_V2_DRAFTS | D4 | int | 2 to 5 | 1 | up: it costs more money | owners_cut |
| REHOOK_MAX_GAP_SEC | D4 | int | 30 to 120 | 15 | up: it weakens a quality gate | retention |
| JOKE_EVERY_SEC_LONG | D4 | int | 8 to 60 | 10 | up: it weakens a quality gate | joke_density |
| COLD_OPEN_LORE_FREE_SEC | D4 | int | 10 to 45 | 10 | down: it weakens a quality gate | cold_open |
| PROMISE_BY_SEC | D5 | int | 5 to 60 | 10 | up: it weakens a quality gate | promise_paid, viewer_promise |
| ANIM_SHOTS | D6 | int | 2 to 8 | 1 | up: it costs more money | animation, real_motion |
| VISUAL_CHANGE_MAX_S | D6 | float | 2 to 8 | 1 | up: it weakens a quality gate | visual_change |
| PARTICLES_ON | D6 | bool | - | - | off: it weakens a quality gate | aliveness |
| LIVING_CHARACTERS_ON | D6 | bool | - | - | off: it weakens a quality gate | living_characters |
| CAMERA_MOTION | D6 | enum | dynamic, gentle | - | - | no_frozen_frames |
| SOUND_DESIGN_ON | D7 | bool | - | - | off: it weakens a quality gate | music_bed |
| TTS_ENGINE | D7 | enum | gemini, kokoro | - | - | designed_voices |
| CONTRACT_OFF | D8 | csv | - | - | always: it switches a promised check off | the next complete run |
| BREAKOUT_HARD_BAR | D8 | int | 50 to 95 | 5 | down: it weakens a quality gate | breakout_bar |
| CRITIQUE_MIN | D8 | float | 4 to 9 | 1 | down: it weakens a quality gate | self_review |
| REEL1_DELAY_MIN | D9 | int | 0 to 120 | 30 | - | the next complete run |
| REEL2_DELAY_MIN | D9 | int | 60 to 1440 | 180 | - | the next complete run |
| NEXT_LINK_ON | D9 | bool | - | - | - | the next complete run |
| IG_TRIAL_REELS_ON | D9 | bool | - | - | - | release_sheet |
| SHORT_THUMB_ON | D9 | bool | - | - | - | release_sheet |
| BRAIN_ON | D10 | bool | - | - | off: the channel stops learning from its own videos | the next complete run |
| BRAIN_HOLDOUT | D10 | float | 0.05 to 0.5 | 0.1 | - | the next complete run |
| LADDER_WINDOW_DAYS | D10 | int | 14 to 60 | 7 | - | topic_ladder |
| LADDER_MIN_ENGAGED | D10 | int | 0 to 500 | 50 | - | topic_ladder |
| BUDGET_GUARD_PCT | D11 | int | 50 to 100 | 10 | up: it costs more money | the next complete run |
| BREAKOUT_FUND_CAP_INR | D11 | int | 0 to 3000 | 500 | up: it costs more money | the next complete run |
| AUTO_FIX_PAID_INR | D11 | int | 0 to 100 | 20 | up: it costs more money | the next complete run |
| PREFLIGHT_ON | D12 | bool | - | - | off: paid steps would start without the free health checks | the next complete run |
| NUMBERS_PER_MIN_MAX | D13 | float | 1 to 8 | 1 | up: it weakens a quality gate | viewer_numbers |
| GRAPHICS_MAX_LONG | D13 | int | 0 to 8 | 1 | up: it weakens a quality gate | viewer_numbers |
| GRAPHICS_FREE_SEC | D13 | int | 0 to 180 | 30 | down: it weakens a quality gate | viewer_numbers |
| BREATH_EVERY_S | D13 | int | 15 to 60 | 10 | up: it weakens a quality gate | viewer_breath |
| PLAIN_HARD_PER_MIN_MAX | D13 | float | 1 to 5 | 1 | up: it weakens a quality gate | viewer_plain |
| PLAIN_OPENING_HARD_MAX | D13 | int | 0 to 3 | 1 | up: it weakens a quality gate | viewer_plain |
| PLAIN_HARD_PER_SENTENCE_MAX | D13 | int | 1 to 4 | 1 | up: it weakens a quality gate | viewer_plain |
| SHORT_HOOK_WORDS_MAX | D13 | int | 4 to 20 | 2 | up: it weakens a quality gate | short_open |
| SHORT_HOOK_BY_S | D13 | float | 1.5 to 6 | 1 | up: it weakens a quality gate | short_open |
| SHORT_NUMBERS_MAX | D13 | int | 0 to 4 | 1 | up: it weakens a quality gate | short_plain |
| SHORT_EXPERT_MAX | D13 | int | 0 to 3 | 1 | up: it weakens a quality gate | short_plain |
| SHORT_PROMISE_WORDS_MAX | D13 | int | 2 to 10 | 2 | up: it weakens a quality gate | short_open |
| SHORT_SHARE_S1 | D14 | int | 0 to 100 | 20 | - | the next complete run |
| SHORT_SHARE_S2 | D14 | int | 0 to 100 | 20 | - | the next complete run |
| SHORT_SHARE_S3 | D14 | int | 0 to 100 | 20 | - | the next complete run |
| SHORT_MIN_S | D14 | int | 10 to 40 | 5 | down: it weakens a quality gate | short_shape |
| SHORT_MAX_S_S1 | D14 | int | 20 to 60 | 5 | up: it weakens a quality gate | short_shape |
| SHORT_MAX_S_S2 | D14 | int | 20 to 60 | 5 | up: it weakens a quality gate | short_shape |
| SHORT_MAX_S_S3 | D14 | int | 20 to 60 | 5 | up: it weakens a quality gate | short_shape |
| SHORTS_PER_WEEK | D14 | int | 1 to 5 | 1 | up: it costs more money | the next complete run |
| SHORTS_PER_MONTH | D14 | int | 4 to 20 | 2 | up: it costs more money | the next complete run |
| SHORTS_BREAKOUT_X | D14 | float | 2 to 10 | 1 | down: it costs more money | the next complete run |
| FOLLOWUP_WITHIN_H | D14 | int | 24 to 96 | 24 | - | the next complete run |
| ORG_SLA_HOURS | C | json | 0.25 to 720 | - | always: it changes how fast the organisation must act | the next complete run |
| PALACE_PLAYBOOK_TOKENS | L | int | 200 to 6000 | 600 | - | palace_health |
| PALACE_PLAYBOOK_TOKENS_BY_DEPT | L | json | 200 to 6000 | - | - | palace_health |
| PALACE_LIMITS_SHARE | L | float | 0.1 to 0.9 | 0.2 | - | palace_health |
| PALACE_REVIEW_DAYS | L | json | 0 to 3650 | - | - | palace_health |
| PALACE_KIND_CAPS | L | json | 1 to 5000 | - | - | palace_health |
