# Enforcement matrix (owner rule, 10 Nov 2026: every point HARD-enforced, nothing for namesake)
Every row names the code that enforces it. contract references = a Feature Contract check (FAIL -> episode HELD + owner card); `fn:module.function` = code
that does it on every run. tests/test_v111_enforce.py fails the build if any reference below is missing.
This file lives in docs/CURRENT (the only docs to follow); the list of retired concepts is `whatifs/truth.py` RETIRED.

| Requirement (owner / research) | Enforced by | Kind |
|---|---|---|
| Hook lab ran and scored the cold open | `contract:hook_lab` | hard gate |
| Owner's Cut bar (best script at the quality bar) | `contract:owners_cut` | hard gate |
| Cold open, emotion beat, asks, verdict rotation, originality, end tease | `contract:cold_open` `contract:emotion_beat` `contract:audience_asks` `contract:verdict_style` `contract:originality` `contract:end_tease` | hard gates |
| Sourced exhibits, time ladder, Grimm's Prototype, "Here's what's true" | `contract:exhibits` `contract:time_ladder` `contract:grimm_prototype` `contract:verdict_line` | hard gates |
| Channel's own evidence reaches the writer | `contract:brain_playbook` `fn:whatifs.enforce.brain_block` | hard gate + brief |
| Retired techniques never used | `contract:no_retired` | hard gate |
| Idea-first: premise backed by a 5x outlier | `contract:idea_evidence` | hard gate (once outlier data exists) |
| A laugh at least every 15 s (Shorts 6 s) | `contract:joke_density` `fn:whatifs.enforce.fix_markers` `fn:whatifs.shorts2._valid` | auto-fix + hard gate |
| Pause-then-punch (300-700 ms before every punchline) | `fn:whatifs.voice._peel` `contract:impact_map` | built into timing + measured |
| A send ("that's so you") moment and an awe peak | `contract:send_and_awe` | hard gate |
| Hook: question / "you" stake in 3 s | `contract:impact_map` | hard gate |
| Re-hook cadence, loops close | `contract:retention` | hard gate |
| Picture changes every <= 4 s, no overload | `contract:visual_change` `fn:whatifs.shotplan.pieces_for` | built into render + hard gate |
| Promise on screen by 0:30 | `contract:promise_paid` | hard gate |
| No frame looks like a still photo | `contract:aliveness` `fn:whatifs.render.Particles` | built into render + hard gate |
| Sound worlds, story sounds, no repeated effect | `fn:whatifs.sound.worlds` `fn:whatifs.sound.story_events` `contract:impact_map` | built in + measured |
| No near-copy of the last 10 episodes | `contract:impact_map` | hard gate |
| Flash safety | `contract:impact_map` | hard gate |
| Breakout Score >= 80 before upload | `contract:breakout_bar` | hard gate |
| Designed voices, music bed, real motion, no frozen frames, slop score | `contract:designed_voices` `contract:music_bed` `contract:real_motion` `contract:no_frozen_frames` `contract:slop_guard` | hard gates |
| Thumbnails, titles, chapters, Shorts + covers | `contract:thumbnails` `contract:titles` `contract:chapters` `contract:shorts` `contract:short_covers` | hard gates |
| 6-point self-review at the bar | `contract:self_review` | hard gate |
| Policy safety (critic) | `fn:whatifs.room.critic` | hard (script rewritten / held) |
| Blind cross-family jury picks the best draft and jokes | `fn:whatifs.room2.write` `fn:whatifs.room2.jokes` | every episode |
| 48-hour breakout monitor -> 2 follow-ups + sequel | `fn:whatifs.breakout.monitor` `fn:whatifs.shorts2.run` | every tick |
| Money: caps, guard, breakout fund, long slots protected | `fn:whatifs.governor.extras_allowed` `fn:whatifs.governor.breakout_fund_left_inr` | every spend |
| 4 animated scenes at the retention cliffs, real motion | `contract:animation` `contract:real_motion` | hard gates |
| Research done before writing | `contract:research` | hard gate |
| Blink + breathing + mouth movement on character shots; approved character art in every reaction | `contract:living_characters` `fn:whatifs.living.render` | built into render + hard gate |
| One mandatory fix for every open retention / marker problem | `fn:whatifs.enforce.fix_all` | every episode |
| One current truth: no retired concept in current docs, CLAUDE.md, module docstrings or prompts; SYSTEM.md equals the code | `contract:docs_current` `fn:whatifs.truth.issues` `fn:tools.plan_guard.main` `fn:tools.gen_docs.render` | hard gate + every push |
| Knowledge Palace: one repository every department reads and writes; nothing enters without dated evidence; trust computed by code; every code reference real; the owner's words change only by the owner (owner, 10 Nov) | `contract:palace_health` `fn:whatifs.org.palace.check` `fn:whatifs.org.palace.transition` `fn:whatifs.org.palace.ensure_seed` | hard gate + refused on write |
| Nothing retired, superseded, expired or merely proposed can reach a prompt; withdrawn knowledge sends what was derived from it back for re-validation; a stale limit stays served and is reported | `fn:whatifs.org.palace.servable` `fn:whatifs.org.palace.supersede` `fn:whatifs.org.palace.expire` `fn:whatifs.org.palace.tidy` `contract:palace_health` | built into the one doorway + hard gate |
| Every department's playbook is bounded (hard cap), limits first, deterministic and named by the hash of its text; size caps per kind enforced by code | `fn:whatifs.org.palace.playbook` `fn:whatifs.org.palace.playbook_issues` `fn:whatifs.org.palace.enforce_caps` `contract:palace_health` | built in + hard gate |
| The Palace is kept up and mirrors the learning core and the show records every day | `fn:whatifs.org.palace.daily` `fn:whatifs.org.palace.maintain` `fn:whatifs.org.palace.sync_brain` `fn:whatifs.org.palace.sync_canon` | daily job + Setup + every episode |
| Launch cadence: 4 long videos a month, one a week; nothing said to viewers or to a model states another cadence (owner, 10 Nov) | `fn:whatifs.governor.can_start_episode` `fn:whatifs.manage.v12_upgrade` `fn:whatifs.governor.long_videos_per_week` `fn:whatifs.caretaker.cadence_words` `contract:docs_current` | hard gate + one-time Sheet move |
| The project works like an organisation: every wired department run goes through LOAD, ACT, EMIT, LEARN, EXECUTE, REPORT in order; each step is proven by a receipt the runner builds itself; a skipped or broken step fails the run and the episode gate (owner, 10 Nov) | `contract:dept_contract` `fn:whatifs.org.runner.run` `fn:whatifs.org.runner.verify` `fn:whatifs.org.runner.episode_issues` | raised at the step + hard gate before picture money |
| Learning both ways: every department reads its Palace playbook before it acts and writes a valid takeaway after; an empty, stock, ungrounded or self-scored takeaway is refused; only a new finding is proposed to the Palace (owner, 10 Nov) | `contract:takeaways_written` `fn:whatifs.org.schemas.check_takeaway` `fn:whatifs.org.runner.build_takeaway` `fn:whatifs.org.runner.work` | refused on write + hard gate before upload |
| Memos between departments: validated on write, read only by their audience, closed only with proof, never rewritten while open, never reopened once closed | `fn:whatifs.org.schemas.check_memo` `fn:whatifs.org.memos.write` `fn:whatifs.org.memos.inbox` `fn:whatifs.org.memos.resolve` `fn:whatifs.org.memos.render` | refused on write / on the move |
| Do-or-die urgency: every memo has an acknowledge clock and a resolve clock; a miss climbs department -> Council -> owner and never waits on a department that cannot act; the owner hears once, with bounded reminders; a dead watchdog fails the gate and alarms the owner | `fn:whatifs.org.memos.watchdog` `fn:whatifs.org.memos.escalate` `fn:whatifs.org.runner.daily_check` `contract:dept_contract` | every tick + daily + hard gate |
| A failed promise or a crashed department becomes a problem memo for the department that owns it, closed only by a verified re-pass, the owner's waiver or the end of the episode; a run that never reported is flagged | `fn:whatifs.org.wraps.gate_memos` `fn:whatifs.org.wraps.gate_settle` `fn:whatifs.org.memos.sweep_episodes` `fn:whatifs.org.runner.audit` | every gate run + every tick |
| The registry is honest: a department is wired (real call sites under the runner) or pending, never both; a ticket is executed by the engine or escalated at once, never left as text; each department's own thinking has a monthly cap | `fn:whatifs.org.registry.entry_issues` `fn:whatifs.org.registry.data_issues` `fn:whatifs.org.registry.caps` `contract:dept_contract` | hard gate + refused before the run starts |
| No test may skip on GitHub's Checks: a skipped test fails the run and is named. Reason (10 Nov, baseline re-check): the comparison with the reference frames of the base renderer skipped on every machine while the particle layer had changed every frame | `fn:tests.skip_policy.verdict` `fn:tests.conftest._no_skip_verdict` | Checks RED on any skip |
| With every render layer that has its own switch turned off, the picture equals the stored reference frames of the base renderer, compared on every run and on every library version; a new default-on render layer fails the comparison until its switch is listed | `fn:tests.golden_frames.same_as_v9` `fn:tests.golden_frames.v9_baseline` | test that never skips |
| A red Checks run names its cause on the public run page (failed tests, skipped tests, failed contract checks with their reason); a green one shows the totals and the rehearsal's episode id, which reproduces that run on any machine | `fn:tools.ci_report.unit` `fn:tools.ci_report.rehearsal` `fn:tools.ci_report.command` | workflow step after the tests |
| The fake pipeline is swept over FIXED episode ids (it is seeded by the id): every hold, crash and warning class is traced to its cause before a batch is accepted | `fn:tools.sweep.fixed_ids` `fn:tools.sweep.one` `fn:tools.sweep.summary` | tool, part of batch acceptance |
| Every Settings cell is read by code: a cell nothing reads is a promise nothing keeps. The cells that were never read are listed, marked NOT ACTIVE in their notes and in SYSTEM.md, and the list may only shrink (owner rule: hard enforcement or it does not exist) | `fn:whatifs.truth.settings_issues` `fn:whatifs.truth.unread_settings` `contract:docs_current` | Plan Guard RED + hard gate |
| The tests measure the library versions that make the videos: every workflow installs a pinned package with the bounds of requirements.txt, and the installed and imported versions on the test machine are inside them. Reason (10 Nov, baseline re-check): GitHub's Checks had been running another major version of OpenCV than production | `fn:tests.test_v12_b0b._unpinned` `fn:tests.test_v12_b0b.test_this_machine_runs_the_library_versions_production_pins` | tests on every push |
| A failed test leaves the episode ids it used on the public run page: the fake pipeline is seeded by the id, so the id reproduces the failure on any machine | `fn:tests.conftest.pytest_runtest_logreport` `fn:tools.ci_report.unit` `fn:tools.sweep.one` | test run + workflow step |
| Built but never wired does not exist: every Sheet tab is used by code and every function of the pipeline is called by production code. The ones that never were are listed with what is true today, and the lists may only shrink | `fn:whatifs.truth.wiring_issues` `fn:whatifs.truth.unused` `contract:docs_current` | Plan Guard RED + hard gate |
