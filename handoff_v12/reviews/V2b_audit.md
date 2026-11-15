VERDICT: FINDINGS (4)
CLOSED F1: 0e2a5e3 (V1c step 0b, the cast and the scenes by format, typed as the approved V1c memo's 3.5 and 3.11 decide), the new tests fail on the breaks and pass on the code: its 20 breaks S0b-04 to S0b-20 and S0b-23 to S0b-25 (F1 (a) to (g)) CAUGHT on bbd47ef in the run of V1c's whole break list (`proving/breaks.py V1c`, 15 Nov 2026, 20:44 to 22:00 UTC: "251 caught, 3 MISSED, 3 void of 257 listed" - none of the six is a break of F1; the closing run of the whole list is in `proving/notes/V1c_OPUS_DONE.md`). THE FINDING WAS: THE THREE ANIMATED SCENES OF AN F1 FILM AND AN F3 WALK ARE OUTSIDE THE CAMERA PATH AND SHOW THE TRIAL'S CAST IN THE TRIAL'S SETS - the Step 5 row "the Director is told; the scenes move with the viewer" is not executed for the scenes (law L8). WHERE: `immersion.apply` writes `path.KLING_MOTION` into `shot["motion"]`, but with `ANIM_DIRECTOR_ON` (TRUE by default) every animated scene is bought in `episode._assets` through `anim.start_frame` -> `anim.frame_prompt(shot["anim"])` and `anim.acting_prompt(shot)`, which read neither `motion` nor `prompt`, know no format, and take the scene's world from its slot (`anim.world_for`: no speaker label of a script matches `SPEAKER_WORLD`, so slots 1, 2, 3 are "lab", "office", "court" - and under the ladder the three scenes ARE slots 1 to 3). WHAT PROVES IT: `V2b_audit_evidence/measure.out` in the dispatcher's shared notes folder - the unchanged functions on a frozen copy of 7e83001, formats F1 and F3, `path.on()` True: the start pictures ask for "Wide staged scene, 16:9. Dr. Grimm: black high-collar coat ... acting in a gothic stone laboratory at night", "Inspector Vale ... a 1940s detective office", "Nana Rosa ... a warm oak courtroom"; the clip requests for "Dr. Grimm ... throws a lever", "Nana Rosa ... lifts the gavel ... and strikes once"; the batch's sentence and the act's place sentence are in NONE of the six requests; the test `test_the_director_is_told_the_path_and_the_scenes_move_with_the_viewer` asserts the field `motion` only, never a request; the memo's 3.2 says the Animation Director builds an `anim` shot's start picture "from" its prompt - it does not. A VIEWER DEPENDS ON IT: 15 of about 510 seconds, the peaks at the retention cliffs and the dearest seconds a video buys, in four long videos of five - puppet scenes of a laboratory, a detective office and a courtroom inside a film whose writer is told "no court", whose row says nobody is on screen (3.4) and whose checks say PASS "one place per act" and "nobody is on screen" (`format_kept` reads the words, never these pictures). Older than V2b (the Animation Director has known no format since V2a) and the larger sibling of open issue 196; no offline run can show it (the offline start picture is one flat colour).
CLOSED F2: 725459d (V1c step 0, the audit of V2b, typed as the approved V1c memo's 3.11 decides), the new tests fail on the breaks and pass on the code: its 6 breaks S0-01 to S0-06 CAUGHT on bbd47ef in the run of V1c's whole break list (15 Nov 2026, 20:44 to 22:00 UTC). THE FINDING WAS: REAL FOOTAGE MAY STAND INSIDE AN ACT OF A "path" OR "walk" FORMAT, DECIDED BY NOBODY AND RUN BY NOTHING. WHERE: the memo's 3.2 says nothing of a `stock` shot inside an act; `stock.shape` knows no format (`STOCK_ON` TRUE by default: clips of 2 to 4 s, up to 10% of the film); `path.lay`, `path.plan_report` and `path.shown_report` skip the type; `prompts.DIRECTOR` still offers `"stock"` in every format beside `path.director_rules()` ("never a new location, never an aerial or establishing view"; F3_BIBLE: "never a jump"). So a film can cut from "your street" to a NASA or Pexels clip and back inside one act while `camera_path` and `camera_shown` PASS with the words "each showed a picture of its own act". WHAT PROVES IT: the code named; `tests/test_v12_inside.py` holds the word "stock" once (`open_acts`); the one whole production that keeps a clip (`tests/test_v12_motion.py`) runs under `OLD_INSIDE`, the camera path off; no long video of the block kept footage (the prover's issue 199); on my lone id the Director's one stock shot ("ocean waves", shot 9) met no stock rule (the log has no "stock rules" line) and became a still only because it opened a beat ("inside the scene: 1 beat(s) opened on a graphic or real footage" - the same line in 15 of the 20 logs of sweep A): one line later it would have stayed inside act "your bathroom". A failing test: `stock.shape`, `path.mark`, `path.lay` on a shot list whose act 2 holds a stock shot on a 3-second line that does not open the beat - the shot stays `stock` with a `path` mark and both reports name no problem.
CLOSED F3: 725459d (V1c step 0), the new tests fail on the breaks and pass on the code: its 6 breaks S0-07 to S0-12 CAUGHT on bbd47ef in the run of V1c's whole break list (15 Nov 2026, 20:44 to 22:00 UTC). THE FINDING WAS: THE SWEEP'S JUDGE AND THE RECORD SAY A TRIAL "ends on a tease" WHERE NO TEASE IS WRITTEN OR SPOKEN. WHERE: `tools/sweep.py:inside_of` prints the constant `"ends on a tease"` for every trial (it is not read from the ledger) and `contract.p_format_ending` answers N/A "format F2 ends on a tease (its own devices judge it)"; with `ENDINGS_ON` and `LADDER_ON` (both TRUE by default: every sweep id, every rehearsal) `room.tease_on()` is False, `p_tease` says N/A "under the ladder no next topic is promised", and `tools/rehearsal.py` itself asserts that no tease was set. WHAT PROVES IT: `test_a_whole_trial_under_the_ladder_names_only_the_character_who_is_drawn` asserts `end_tease` N/A and no tease in the script beside `format_ending` N/A "ends on a tease"; the verdict's own facts carry the rehearsal line "F2; 56.5% of 23 sentences inside ...; ends on a tease". The untrue sentence is repeated as what a viewer gets in 6b ("every trial 'ends on a tease'"), in `proving/notes/V2b_ACCEPTED.md` ("the trial on its tease") and `V2b_BUILT.md` (line 5 of "What was built"). No viewer and no money depends on it - removing the tease is the design (issue 101) - but a judge's line and the record must say what the film does; what a trial DOES end on under the ladder is said by no line of the sweep.
CLOSED F4: 725459d (V1c step 0), the new tests fail on the breaks and pass on the code: its 2 breaks S0-13 and S0-14 CAUGHT on bbd47ef in the run of V1c's whole break list (15 Nov 2026, 20:44 to 22:00 UTC). THE FINDING WAS: THE WALK'S FORMAT BLOCK STILL NAMES THE SECOND VOICE IN EVERY ROOM PROMPT. WHERE: `format_engine._for_format` in a one-voice format leaves two sentences of `REALITY_ENGINE` untouched: "The Curious One is a young adult, never a child." and "The Director talks like a calm expert friend; the Curious One like a bright, honest friend." (directly before "The guide is the whole show: no second voice"). WHAT PROVES IT: `measure.out` - under `formats.using("F3")` both lines are in `format_engine.instructions()` of the writer, the bible, the director, the critic and the showrunner (only the writer also gets F3_WRITER's overruling sentence); the test is named `test_one_voice_is_never_asked_for_a_second_role_and_is_told_of_none` and passes; the record's search of 3.3 (e) answers all 26 hits of `format_engine.py` as "the lines 3.3 (c) and (d) name" - these two are named by neither and got none of the four answers. Small: a real F3 writer who follows them is caught by `format_kept` and costs a rewrite or a hold (open issue 187).

# V2b INSIDE THE FORMAT - the Fable audit (15 Nov 2026, 07:29 to 08:07 UTC; the plan's chapter 14 with A7 and A10)
The auditor: a fresh Fable 5.2 session at Effort High that wrote none of V2b (not its design, its review, its build, its finish or its proof). It changed no code, no
test and nothing in `proving/`; it wrote this file and, outside the repo, a read-only measuring script and its output.
Accepted commit 01e7798 (its code 7e83001), base 5827d97, acceptance commit cdb9a21. All four findings are about what the DESIGN left undecided or what a sentence
claims; the verdict of the block stands (act 1), no judge was weakened (act 2), the lone id is good (act 5). Nothing here makes the acceptance wrong: fake mode cannot
show F1 or F2 at all, which is why they are findings of a reader and not of a run.

## TO CLOSE (what each closing must show; a finding is closed in V1c's BUILD phase and checked by its finisher)
- F1 NEEDS A DECISION OF V1c's DESIGNER FIRST (it is open issue 196's family: where the trial's cast and world appear in a film that is not a trial - decide both
  together). The reading that keeps V2b's own promise: in a format whose row is not a trial an animated scene is the viewer's own place - its start picture asked from
  the act's place and the scene's line, at eye level, nobody drawn; its clip request the batch's motion sentence; the trial keeps `WORLDS` byte for byte. Whatever
  is decided: (a) the world of a scene follows the format (data of the row or of `anim.py`, never a slot number alone); (b) tests on the REQUEST TEXTS themselves -
  what `anim.start_frame` hands the picture model and what `episode._assets` hands `media.animate` - in F1, F3 and a trial; (c) a break for each; (d)
  `Job.repair_assets` re-makes a scene with `motion + prompt`, another request than the first purchase (`acting_prompt`): one rule for both; (e) the words of
  `living_characters` ("nobody is on screen") and of `camera_path` made true of a film with scenes; (f) the Step 5 row and the memo's sentence about
  `anim.start_frame` corrected in the record ("CORRECTED BY THE BUILD").
- F2 NEEDS THE SAME DESIGNER'S ONE LINE: (a) in a "path" / "walk" format real footage never stays inside an act (it becomes a picture of the act - the reading that
  changes less of what 3.2 promised), or (b) it stays as a counted reality anchor that both checks name in their PASS words. Either way: the failing test above, a
  whole F1 production that walks the decision with `CAMERA_PATH_ON` (today no test and no sweep id does), a break, and the Director told the same thing code does.
- F3: `inside_of` and `p_format_ending` say in a trial what the ledger shows (for example "the trial's own ending; no tease under the ladder", read from the
  `end_tease` row), a test on a trial under the ladder and one without it, and the three sentences of the record corrected. `judge_guard.py` will list
  `tools/sweep.py` again: name the change in V1c's record first (L7).
- F4: the two sentences are left out or reworded in a one-voice format (a trial's and F1's block byte for byte), the test asserts that the block of every role
  names no "Curious One", and the record's answer to the search is corrected.

## THE SIX ACTS
1. `proving/verdict.py --verify V2b_01e7798_1.json` (07:30 UTC; no python or ffmpeg process alive), word for word: "VERIFIED V2b_01e7798_1.json: stored GREEN,
   recomputed GREEN; logs unchanged", exit 0. Open issue 183 did not occur and cannot in this step: `--verify` only reads (`compute`), it archives nothing. The
   archive `proving/logs/V2b_01e7798_1/` is whole; GitHub's run 196 was read again by the recomputation.
2. THE JUDGES' REPORT (6 changes, 0 unexplained) - each read in the whole diff 5827d97..7e83001: `tests/conftest.py` (`OLD_INSIDE`: the four switches FALSE and the
   shares 70 / 30 / 0 for the older tests, named in 3.0); `tools/sweep.py` (`inside_of`, its two calls, the counter: a judge ADDED - its one fault is F3's words);
   `tools/rehearsal.py` (six older asserts changed, each named in step 7 before its change and each for the reason given: one voice in F3, a format's own asks, no
   tease under the ladder, the code check run in the video's own format, no reaction moment without a foil; assert (2) now reads the planned script through
   `cta.is_ask` because a two-line pool ask is cut into units - as strong as before); the three share defaults (the redesign's 10.7, with their one-time move).
   The older tests the report does not list (their assert lines did not fall): `test_v12_cutdowns`, `test_v12_exec` (two pins and the arm's text),
   `test_v12_formats` (F3 can be forced), `test_v12_motion` (the pins, one clause turned round and made stricter, the V2d-b audit's test), `test_v12_release`,
   `test_v83` - every one a count moved by a check or lever the batch added, or a change named in the record first. NO JUDGE IS WEAKER. A note on the machinery,
   not on V2b: `judge_guard.py` calls a change "explained" when the record holds the file's base name anywhere ("sweep") - the audit's reading is the real guard.
3. THE DESIGN, ITS REVIEW AND THE MEMO AGAINST THE REDESIGN AND `02`. Design D (the inside of a format is data that code executes) is the right one and the
   three review rounds found what a typist would have built wrong (one act for the whole film, story lines deleted as asks, an act's first picture lost five
   ways). Item 19's "continuous camera" is narrowed honestly (CHANGED FROM THE REDESIGN 1; the review says "NOT delivered"). Items 12, 14, 15: every rule has
   its code, test and break - EXCEPT where F1 and F2 name it. What the review's question 9 ("the worst video this design could still let through") did not
   see is F1: the review traced stills, living clips and the re-render, never the request of an animated scene; the finisher found the sibling (FF7, the
   cutaways) and stopped one step short. For the next reviews: "every writer of the record" has a twin - EVERY REQUEST THAT BUYS A PICTURE OR A CLIP, by name
   (`media.still`, `anim.start_frame`, `anim.acting_prompt`, `motion_prompt`, `repair_assets`, `media.stock`).
   Not findings, said for the designers: (a) every F1 film ends on the same question and every scene and still carries the same sentences - a format's
   signature today, but item 49 and item 57 (d) ("rails are measures, never templates") make "the same ending in every upload" a row of V5's aspect map;
   (b) the place sentence says "the same light and weather as the shot before" on an act's FIRST picture too; (c) two acts whose headings carry the same number
   (a writer who restarts numbering) are one act to `plan_report` - with issue 190; (d) `cta.ensure` adds nothing when no calm slot lies before the tail, so an
   F1 film can carry no ask and PASS with "asks in this video: none" (H29 then compares less than it says); (e) the memo's `S_["path"]` is in memory only -
   the plan is saved before the marks, and nothing reads it.
4. THE DIFF OF `tests/` AND OF THE PROTECTED FILES (read whole with the file tool from `git diff` files, never from a shortened output): all of `whatifs/`
   (37 files, 23 of them PROTECTED: `episode.py`, `core.py`, `manage.py`, `preview.py`, `immersion.py`, `room.py`, `org/palace.py`, `registry.py`, `runner.py`,
   `levers.py`, `rnd.py`, `canon.py`, `audience.py`, the new `org/inside.py` and `path.py`, `formats.py`, `shorts2.py`, `contract.py`, `truth.py`, `ladder.py`,
   `opening.py`, `costguard.py`, `motion.py`, and `tools/repair.py` itself), `tests/test_v12_inside.py` whole (1,186 lines), the finisher's diff a32d2be..7e83001,
   and in place `episode.py` `Job` / `_assets` / `repair_assets`, `anim.py`, `stock.py`, `fixes.py`, `format_engine.py`, `costguard.lines`, `formats.pick`. The code
   does what Steps 3 to 5 say everywhere I compared it, but for F1 to F4. THE DISPATCHER'S AND THE PROVER'S DOUBTS, ruled on:
   - THE SOURCE PINS: not five - THIRTEEN tests of the file pin source text (the brief's place in the writer's brief, the order in `produce`, `asks=`, the
     emotion beat, the banter fill, both setup sites, the two callers of `hook_of`, `first_line_brief`'s place, the runner's `leave_out`, the format picked
     before D4's run, the sweep's and the rehearsal's calls, the three `_place_asks` sites with the Owner's Cut order, the second voice call). I AGREE THEY ARE
     ENOUGH AS GUARDS: behind each stands a judge of behaviour - `format_ending`, `viewer_inside`, `canon_in_brief` on every production, the block's counter
     `format_inside_held` on the sweep's own calls - and on my lone id the room's THIRD ask-placing site ran (a RETENTION FIX was made) and the film passed
     with "subscribe 1". They prove where a call stands, never what it does; the Owner's Cut site is run by no offline production.
   - FF1 / FF2: the fix is at the cause (the direction is the shot's own mark; the record's move, sign, clip and fallback rewritten) and the four tests run the
     REAL `_render` and `rerender_times`, not doubles of them; `repair_assets` re-renders the whole film and so rewrites the record. No offline run re-draws -
     the quality control never fails offline. Where a block should walk it: B7's own acceptance addition (the plan's 12.8, "a forced failure repaired
     automatically") - its designer plants a black stretch in a camera-path film and reads `camera_shown` after the repair.
   - ISSUE 198 (the offline walk is one text): a limit of the stand-in, no fault. It means the eight F3 productions of the block add little to F1's about the
     VOICE (the floor of 60 stands on two written passages: issue 185), and that F3's stations were never asked of a bible.
   - ISSUE 199 (real footage in 0 of 20 films): BY DESIGN in each of its three causes, read in the logs - no fault of the code. What is truly open is not the
     coverage but the decision: F2.
   - A TRIAL NEAR ITS FLOOR: 52.2 to 66.7% over the trial productions on record (the sweep's four ids, the rehearsals, the builders' own) against a floor of 40 - offline writers; nothing to rule before a real
     writer (issues 185, 191).
   - THE MONEY, Rs 570.48 -> 578.79: every added rupee is on ONE line (`costguard.lines`, the stills line: + allowance + 1 = 14 pictures at about Rs 0.59);
     no paid call was added (`tests/paid_calls.py` untouched; my lone id: "every paid picture and clip had its line", Rs 746 estimated). The line is also
     carried by a trial's estimate, which never spends it (the finisher's "SAID PLAINLY" (b)) - conservative and small, yet against the builders' rule
     "never keep an allowance for a call that no longer runs": V4's split can make it follow the format.
5. ONE SWEEP ID OF MY OWN, ALONE: `EP209901281633` - the first id beyond the block's twenty that draws F1 (the id's SHA-1 modulo 100 is 44; ids 21 to 36
   computed first: F3, F1, F1, F3, F3, F1, F2 ...). WHY: no block of this build has ever produced a long video for an id beyond the first twenty; F1 is three
   long videos of five and carries the most new machinery at once (the acts, the marks, the asks, the ending, two voices); and a hold by `camera_shown` comes
   AFTER every picture and clip is paid - the dearest way to be wrong. HOW: V1c's designer was running its own ids, so I waited on its process ids each time
   (never on a log); a frozen copy `git worktree add --detach <scratchpad>/audit1/wt 7e83001`; from it `PYTHONUTF8=1 WI_FAKE=1 <venv python> tools/sweep.py
   --one EP209901281633 --work <scratchpad>/audit1/one_EP209901281633`, started 07:41:02 UTC, first lines read 20 seconds later (setup, the Short posted, the
   draw), ended 07:44 UTC on its own process, exit 0, 189 s. RESULT: outcome "ok"; checks 47 PASS / 13 N/A, no FAIL (the block's F1 ids: 47 / 13); "inside the
   format held: F1; 87.5% of 16 sentences inside (floor 50%); 3 acts in 3 places (2 changes in 1.2 min, at most 3): your bathroom | your kitchen | your street;
   ends on its question: 'would you keep it?'"; `camera_shown` "11 still states in 3 acts: each showed a picture of its own act, at eye level, travelling one
   way (drift 2, handheld 2, orbit 3, push_parallax 3, whip_settle 1)"; one subscribe ask, the 12th of 15 spoken lines ("We run a new simulation every week.
   Subscribe, and the bell does the remembering for you."), outside the tail; `end_tease` N/A under the ladder; 100% of the 30 paid seconds seen moving, the
   scenes 15 of 15 s; "QC long video: PASS", no re-render; six warning classes, none new to my eye (the one I looked up, the atmosphere's time budget, is in all twenty logs of sweep A). The frozen copy was removed with
   `proving/cleanup.py` at 08:02 UTC ("frozen copies left: none"); `one.log`, `measure.py` and `measure.out` are kept in
   `...\side-session-notes\local_e4e9a03f-1daa-4c3a-9c13-ce51f9c50fdc\V2b_audit_evidence\`.
6. This file.

## THE READING (A10: what chapter 14 lists, each item whole)
`proving/next.py --audit` and its card; the plan whole as of 0a9503f and the two text commits after it (A11 f and g) by their diff; the handoff `CLAUDE.md`;
`02_OWNER_VERBATIM.md` whole as it stood at 07:29 UTC (items 1 to 86; items 87 and 88 were written after my reading and are known to me only through the plan's
A11); in `BUILD_STATE.md` the head line, STANDING RULES, the record of V2b whole (Steps 1 to 7 with every DESIGN QUESTION, `FINISHED BY FABLE`, 6a, 6b), open
issues 169, 183 to 199 and V2a's memo; `reviews/V2b_design.md` whole (three rounds); `proving/notes/V2b_OPUS_DONE.md`, `V2b_BUILT.md`, `V2b_ACCEPTED.md`; the
verdict file and the judges' report; `proving/verdict.py`, `judge_guard.py`, `accept_block.py`, `cleanup.py`, `common.py` (read, not changed); the redesign's 4.1,
10.7 and V2b's end note in 11.10; the repo's `CLAUDE.md`; the diffs and files of act 4; `tools/sweep.py` whole. Tools: only the file tool, search and
PowerShell located and read; no graph, no skill.

## WHAT I COULD NOT JUDGE
- Any picture, clip or voice: nothing real exists. F1 and F2 are read from the requests and the shot list, not seen; what a picture model does with a request
  is the pilot's and the owner's eye.
- A real writer against the four checks (issues 185, 187, 190 to 192, 195).
- The 326 deliberate breaks one by one (I read the record's account and the result's totals in the verdict, not the list); the tests were read, not run by
  me, but for the lone id.
- `00`, `01`, `03`, `04`, `06` and the older records were not read (the audit's reading, A10): a clash of V2b with one of them that the designer's whole
  reading did not catch would not have been caught here either.

## USAGE
At the start (07:29 UTC): weekly all models 29%, weekly Fable 49%, this session's context 9%. At the end (08:03 UTC, read before this file was written): weekly all models 32%, weekly Fable 55%
(other Fable sessions worked beside this one - V1c's designer of record and the dispatcher - not measured apart), this session's context 73%. The 5-hour window
is not shown by the app.
