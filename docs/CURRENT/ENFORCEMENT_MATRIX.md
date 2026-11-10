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
