VERDICT: FINDINGS (1)
CLOSED F1: 20f00be, the new test fails on the break and passes on the code (its break F1 CAUGHT on a32d2be, V2b's final code: "BREAKS V2b: 320 caught, 0 MISSED, 0 void of 320 listed"; the test alone "1 passed in 93.64s"; in ONE process with every test file after `tests/test_v12_inside.py` - `tests/test_v12_motion.py` among them - "1052 passed in 3106.31s"; no line of `whatifs/` changed for it - closed by V2b's fifth Opus builder, for the finisher to check). THE FINDING WAS: the seconds PAID that check `moving_share` judges have no test of their own - in `whatifs/episode.py`, function `_finish`, the line `"moving_paid_s": sum(cs_.values())` can be changed to count only the clips the render showed (the plan's 12.1 forbids exactly that: "lowering `paid_s` to what was shown") and every test stays green; proof: on a frozen copy of 5827d97 with that ONE line replaced, `python -m pytest tests/test_v12_motion.py -q -p no:cacheprovider` printed "59 passed in 263.85s (0:04:23)"; the sweep cannot see it either (every id would still print 100%).
FIX: NO production code changes - the code is right today; a guard is missing (law L8: a rule without a test that fails when it is broken).
(1) In `tests/test_v12_motion.py`, the tuple `OWN_IDS` gets a sixth id, appended, so that every index in use keeps its meaning:
`OWN_IDS = ("EP209906070900", "EP209906140900", "SH209906070900", "SH209906210900", "SH209906280900", "EP209907050900")`
(2) At the END of the same file, after `test_with_the_ladder_switched_off_a_short_sounds_and_is_gated_as_before`, type this test exactly (it was run by the
auditor in its own scratch copy, never in the repo: on the unchanged code alone "1 passed in 85.72s", in the whole file "60 passed in 354.87s"; with the
break of (3) "1 failed" - the video is then held by `visual_change` only and `moving_share` passes at 100%):
```python
# ------------------------------------------------------------------ 11. AUDIT F1 OF V2d-b: what was PAID is the clip files bought, never only what reached the screen
def test_a_paid_clip_that_never_reaches_the_screen_stays_in_what_was_paid_and_holds_the_video(ladder, setting, monkeypatch):
    """The seconds PAID that check moving_share is given are the seconds of every clip file this video bought (episode._finish: `moving_paid_s`), whether
    or not the renderer could show the clip. Here every still brought to life fails to draw in a whole production (the renderer shows its fallback
    picture in its place): the video is HELD by moving_share, and the check's words carry every second the cost log says was paid."""
    import re
    from tests import test_v12_opening_e2e as E2E
    E2E._start(monkeypatch, setting); C = OWN_IDS[5]; LAD.override("owner", "make it anyway")                      # under an override: its own scenes and living stills, no footage
    kept = {}; real_place, real_seg = MOT.place, RN.clip_segment
    def place(*a, **k): kept["shots"] = real_place(*a, **k); return kept["shots"]
    def seg(clip_path, path, nframes, *a, **k):
        m = re.match(r"clip(\d+)", os.path.basename(str(clip_path)))
        if m and kept["shots"][int(m.group(1))].get("type") == "living": raise RuntimeError("this clip cannot be drawn (planted by the test)")
        return real_seg(clip_path, path, nframes, *a, **k)
    monkeypatch.setattr(MOT, "place", place); monkeypatch.setattr(RN, "clip_segment", seg)
    r = EP.produce(E2E._slot(10), episode_id=C); led = _led(C); core.flush_costs()
    paid = {k: sum(float(x["units"]) for x in core.store().rows("Cost_Log") if x["episode_id"] == C and x["item"] == k) for k in ("hero_clip", "living_clip")}
    assert paid["hero_clip"] >= 5 and paid["living_clip"] >= 5, paid                                               # the video bought scenes AND living clips
    assert r.get("held") and "contract:moving_share" in (r.get("problems") or []), r
    m = re.search(r"of ([\d.]+) s of clip this video paid for only ([\d.]+)% are on screen and moving", led["moving_share"][1])
    assert led["moving_share"][0] == "FAIL" and m, led["moving_share"]
    total = paid["hero_clip"] + paid["living_clip"]
    assert float(m.group(1)) == pytest.approx(total, abs=0.5) and float(m.group(2)) == pytest.approx(100.0 * paid["hero_clip"] / total, abs=1.5), (paid, led["moving_share"])      # every paid second is in the sum; only the scenes are seen
    shutil.rmtree(os.path.join(core.WORK, C), ignore_errors=True)
```
THE ARITHMETIC IT PINS: paid = the cost log's `hero_clip` seconds + `living_clip` seconds of the episode (what `_finish` sums from the clip files:
`cs_ = {i: RN.probe_dur(files["clips"][i]) for i in own_}`, `own_` = every line whose shot is `kling` or `living`, is not the Short's footage and has a
clip file); seen = the scenes only (their living clips never drew), so the check must say "of <paid> s of clip this video paid for only
<100 * hero / paid>% are on screen and moving" and hold the video.
(3) THE DELIBERATE BREAK, one more entry of the break list of the batch that closes this finding (`proving/breaks/V2b.json`), typed exactly:
`{"id": "F1", "file": "whatifs/episode.py", "find": "\"moving_paid_s\": sum(cs_.values()),", "replace": "\"moving_paid_s\": sum((cs_.get(m_[\"i\"]) or 0) for m_ in sm_ if m_.get(\"clip\") and m_.get(\"type\") in MOT.MOVING and not m_.get(\"short\")),", "tests": ["tests/test_v12_motion.py::test_a_paid_clip_that_never_reaches_the_screen_stays_in_what_was_paid_and_holds_the_video"], "would_fail": "what was paid is every clip file bought, never only the clips that reached the screen"}`
It must come back CAUGHT. Before the test exists it is MISSED (the auditor's run above).
(4) DONE WHEN: the new test passes on the unchanged production code, alone and once in ONE process with every test file after it (the plan's 5.7; the id
`EP209907050900` is used by no other test file - the file's own test proves it); the break is CAUGHT; the suite's total is one test higher (about 90
seconds more); the builder names the test in its record and rewrites the finding's line above to
`CLOSED F1: <commit>, the new test fails on the break and passes on the code`. The finisher checks that no line of `whatifs/` changed for it.

WHAT A VIEWER OR THE MONEY LOSES BY F1 TODAY: nothing - the code counts every paid second. What is missing is the guard: a later edit of that one line
would let a video whose paid clips never reached the screen pass at "100% seen" (money nobody sees, and no check, test or sweep id would say so).

NOTES (not findings; they block nothing; a designer or a Fable session decides each)
NOTE 1: THE VERDICT'S LOG ARCHIVE IS RESTORED (open issue 183 of `BUILD_STATE.md`; the designer carries this into the record: the issue narrows to its
cause). What was done, nothing else in `proving/`: `attrib -R` on the 11 empty folders under `proving/logs/V2d-b_5827d97_1/`, then
`robocopy <the shared notes copy> proving\logs\V2d-b_5827d97_1 /E` - "Files : 154 copied, 0 failed" (154 files, 960,466 bytes; the record's "1.3 MB" is
the size on disk). The app refused nothing. THE CAUSE IS NOT FIXED: `proving/verdict.py` still removes an archive with
`shutil.rmtree(dst, ignore_errors=True)` and then `copytree`s into folders OneDrive marked read-only, so the prover of V2b will meet the same crash at
the plan's 6.4. A Fable session should change `verdict.py` (clear the read-only mark before the removal, or do not archive again when the archive's hashes
already equal the verdict's) BEFORE V2b's proving pass - a commit of its own (chapter 15), never a builder's (L11).
NOTE 2: `python proving/verdict.py --verify V2d-b_60d9483_1` (the RED verdict of the first pass, not asked of this audit) prints "MISMATCH ...: stored
RED, recomputed RED; logs unchanged". No log changed: the stored verdict's last red is "no deliberate-break result", the recomputation reads the batch's
ONE break result file - today that of d8101c8 - and says "the deliberate breaks were not run on the code of this commit". A verdict of a commit that was
repaired can no longer be verified by this tool: keep the break result with the archived logs, or leave the break lines out of the comparison of a
superseded verdict. The machinery's, for the same Fable session as NOTE 1.
NOTE 3: A SCENE THE PLACING DROPS LOSES ITS PROMISE MARK AND NOTHING RE-AIMS IT. `whatifs/motion.py` `place`: `out[i]["type"] = "still";
out[i].pop("anim", None); out[i].pop("promise", None)` (pinned by `test_a_scene_is_bought_only_where_it_is_shown_whole_and_its_room_is_kept_for_it` and
by break R05); `episode.produce` re-aims the promise (`ROOM.promise_shot`) only BEFORE `MOT.place`. Then check `viewer_promise` says "an animated scene
exists, but none shows the thumbnail's promise" and the video is held at the script gate, its script and voice paid. NOT REACHABLE WITH TODAY'S CELLS: a
scene after second 0 is put only on a line that fits, and at second 0 (a video under an override) only a number graphic can end the scene's room, which
`GRAPHICS_FREE_SEC` 60 removes from the first minute. It opens when that cell is turned to 0 (a lever of D13; that direction needs the owner) or
`VIEWER_SEAT_ON` is FALSE. An improvement, a new design: after `MOT.place`, when a scene was dropped and no shot carries the promise, re-aim it or leave
the mark on the first picture.
NOTE 4: IN PRODUCTION THE SCENES' SECONDS ARE WORDS, NOT A VERDICT. `contract.p_moving_share` holds a video only under `MOVING_SEEN_MIN_PCT` (90) of ALL
paid seconds; the batch's own test pins that a scene cut to 4.1 of 5 s beside one whole living clip is "91%" and passes
(`test_the_measure_counts_each_stretch_whole_and_each_clip_up_to_its_own_seconds`). The floor of 99% on the scene seconds exists only in the proving
block (`proving/blocks/V2d-b.json`, now the floor of every block), which judges the 28 offline long videos of a sweep, never a real one. Today the
placing keeps every scene whole by construction; a hard rule at the final gate on the scenes' seconds would be a new limit and a new lever (the repair
was forbidden to move a limit, rightly) - for the batch that owns the moving share's levers (open issue 168) or V2b if its camera path touches the cut.
NOTE 5: AFTER A CLIP ENDS ON A LONGER LINE THE PICTURE JUMPS BACK TO THE CLIP'S FIRST FRAME (read in the code, not seen on a film: the offline lines
are short). `episode._render` with `motion.cuts`: when a line is `TAIL_MIN_S` (1.0 s) or more longer than its clip, the rest is drawn from
`files["img"][i]` - the start picture the clip was made from - as a still with a camera move. The repair added a case: a line of L seconds that ends at
a graphic, another clip or a reserved line, with less than a quarter second over a whole second, now buys one second less for `SPARE_S` (a line of 6.0 s
buys 5: `test_placing_never_buys_a_second_no_line_can_show`, "[None, None, 5, None]"), so a viewer sees five seconds of motion and then a full second
of its first frame. The renderer can already play a clip up to a quarter slower without a jump (`render.clip_segment`: `min(1.25, ...)`; 5 s over
6.25 s). An improvement, a new design: cut a tail only when the rest is more than a quarter of the clip's length. It is V2b's subject (redesign 10.7:
each shot begins where the last ended).
NOTE 6: THE BUILDERS' RECIPE WAS NOT UPDATED BY THE REPAIR. `reality-engine/CLAUDE.md`, recipe "The motion ladder", does not say that `motion.place`
reserves every scene's run-on lines before any living clip, that a clip is bought only where its room shows it with `SPARE_S`, or that the renderer's
merge is `motion.merge` (never a line that carries a paid clip). `BUILD_STATE.md` says it under NEXT ("What V2d-b leaves ready"); the recipe is what a
builder reads again before its first edit. One sentence, to be added in V2b's BUILD phase (V2b's camera path goes through `motion.place`).
NOTE 7: `.git/worktrees/` of the checkout still holds the names `fix1`, `red60`, `wt`, `wt1`, `wt2`, `wt21`, `wt22` (earlier sessions' frozen copies
and this audit's `wt`); `git worktree list` shows the checkout alone and `git worktree prune` answers "Permission denied" for three of them (open issue
175: the folder syncs). Nothing in the tree; they can be deleted by hand once OneDrive lets go.

WHAT THE AUDIT DID (chapter 14 and amendment A7; 14 Nov 2026; a Fable 5.2 session that wrote none of V2d-b)
(1) THE VERDICT, RECOMPUTED: after NOTE 1's restore, `python proving/verdict.py --verify V2d-b_5827d97_1` printed
"VERIFIED V2d-b_5827d97_1.json: stored GREEN, recomputed GREEN; logs unchanged" (exit 0; GitHub's run 159 read again by the script).
(2) THE JUDGES' REPORT (`proving/verdicts/V2d-b_5827d97_judges.json`): 8 changes, 0 unexplained - one test of `tests/test_v92_shots.py` gone with the
two drawing functions it tested (a new test proves they stay gone), `tests/conftest.py` (`OLD_MOTION`: the older tests keep the path they were written
for), `tests/paid_calls.py` (ten more stills at most, counted and explained), `tools/sweep.py` (a new judge that makes an id BAD - stricter),
`tools/rehearsal.py` (new asserts - stricter), three Settings defaults (the living model leaves the research-only one). Each read in the diff
22fb8fd..d8101c8: none weakens a judge. What the report cannot see - assertions changed inside tests - was read line by line in 60d9483..d8101c8: five
removed lines, each named in the record before it was changed (the fallback of `pick_slots`; 6 s to 5 s twice and 24 to 23 s for `SPARE_S`; the budget
11 to 10; the merge rule's text moved to `motion.merge`). No limit, no cell, no skip, no special case of the red id. L7 holds.
(3) THE DESIGN: no design review exists for V2d-b (it was built before the plan; the repair's note was not reviewed, item 34 (c) of `02`). The memo, the
repair's note (three ways scored, D chosen) and the Step 5 table were read against redesign 11.5, 11.9 and the V2d-b end note of 11.10 and against
`02` items 16, 19 and 20: nothing contradicts them, and every departure is named (the licensed model instead of the research-only one; 20% as the floor
and 40% as a target the money does not reach - open issue 167; a Short's own gate; "no people" as a word list - open issue 166; L1 moved to DRAWN BY
CODE). The repair is the stricter of its three ways and takes the viewer's side (the peaks are seen whole, or not bought).
(4) THE CODE AGAINST THE RECORD: `whatifs/motion.py` whole, `anim.pick_slots` and `apply`, `episode._render` and `_finish`, `contract.p_moving_share`,
`tools/sweep.py` `motion_of`, `tests/test_v12_motion.py` whole. Every sentence of the repair's note and of 6a is kept by the code: no fallback in
`pick_slots` after second 0; the scenes' room reserved before any living clip; `take()` the one rule with `SPARE_S`; `motion.merge` spares a clip's
line; `_tiles` counts the whole stretch and a held picture under grain is still not counted; each clip counts up to its own seconds (one stretch a clip:
the renderer plays a clip in one segment); the seconds paid come from the clip files, not from the render's record (see F1 for its missing test). No
second guard was found hiding a first (the pair the repairer's break run found is gone). Two wiring links were attacked with one-line breaks in the
auditor's scratch copy: the Director's fit rule (`fit=None` in `anim.apply`: 2 failed, 57 passed - caught, by two whole productions) and the paid
seconds (59 passed - MISSED: F1).
(5) ONE SWEEP ID OF THE AUDITOR'S OWN CHOICE, ALONE, on a frozen copy of 5827d97, an id that is not one of the block's 58: `tools/sweep.py --one
EP209903171142 --work <dir>` -> exit 0, outcome "ok", 44 PASS / 12 N/A / 0 FAIL: "56.2 of 82.8 s move = 67.9% (floor 20%; the lever asks 40%, this
month's money planned 34.2%): footage 15.3 s, living 25.9 s, scene 15 s; 100% of the 40 s paid are seen moving; the scenes on screen 15 of 15 s (100%)".
Checked against a second source: the run's own cost log has 3 hero clips of 5 s and 5 living clips of 5 s = 40 s paid. The frozen copy's tree was clean
after the run; the copy is removed.
(6) NOT COVERED BY THIS AUDIT, said plainly: a real clip, a nine-minute film, a real fetch (fake mode only - open issues 165, 167, 181); the first
build's 108 breaks (run by the first builder's own script; only the 39 of the repair are on file).
USAGE: at the auditor's start the 5-hour window 2%, weekly all models 0%, weekly Fable 1%, its context 9%; the figures at its end are in its closing message.
