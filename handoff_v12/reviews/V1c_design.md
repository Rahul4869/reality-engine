VERDICT: APPROVED
(Round 2, 15 Nov 2026: the five changes of round 1 are in the memo as of commit 8e079c2 - the part "## Round 2 in the record" at the END of
this file holds the verdict that stands, with SIX corrections, each in exact words, to be typed into the memo's text before the first line
of code - the sixth was found after the approval, by the code graph. Everything from the next line to that part is round 1 as
it was written; ITS verdict was CHANGES REQUIRED.)
# V1c THE FLOOR, HIS VERDICT AND THE MAKER'S LINE - design review, round 1 in the record (15 Nov 2026, 08:16 to 08:30 UTC)
The reviewer: a Fable 5.2 session at Effort Extra high that wrote nothing of the memo (it wrote the second and the third pre-review of the draft:
`PREREVIEW2_V1c.md`, `PREREVIEW3_V1c.md`). It changed no code, no test, nothing in `proving/` and no file but this one; it ran nothing of the
pipeline (`proving/next.py` once: the card THE DESIGN REVIEWER of V1c; pre-flight clean; no python process alive before or after).
Reviewed: the record of V1c as of commit 9cdf69e (Steps 1 to 3 from 6042640, part 3.11 from f9fa1e1; the state DESIGN_REVIEW). The code the
memo is written against is 7e83001, V2b's accepted code (`git diff 7e83001 HEAD` touches `handoff_v12/` only): read from a plain export.
FIVE CHANGES, ALL IN OR BESIDE PART 3.11 (the part written in the turn in the record, which no pre-review saw). Parts 3.0 to 3.10 stand: the
twenty changes of the two pre-reviews are all in the record's text. THE THREE THAT A VIEWER, THE MONEY OR A LAW DEPENDS ON: the three animated
scenes of every F1 film and every walk would be asked WITHOUT the show's look words - another look than every still of the same film (change
1); a repaired scene would hand the clip provider the word "google" as its picture's address, and on a second road of the same repair a
trial's scene would be acted out on a picture that does not show its character (change 2); three older tests pin the words F3 changes and the
memo names one of four (change 3).

## The changes (each: the place in the memo, what is wrong, what makes it right)
1. THE VIEWER'S OWN PLACE IS ASKED WITHOUT THE SHOW'S LOOK (3.11, F1, (a) and (b)).
   WRONG: (a) says of the shot's prompt "(the camera-path rules, the look, the style lock are in it)". Read in 7e83001: the prompt carries the
   bible's `look` and the cell `STYLE_LOCK` (`room.normalise_shots`, room.py 741 to 743; `plan_check`, episode.py 558) - it does NOT carry the
   show's look words. `anim.style_words()` (the cell `ART_STYLE`, default "toybox_noir", owner-approved: "stylized 3D stop-motion puppet
   diorama look: felt, clay, painted wood, aged brass") is added by `media.still` AT THE REQUEST (media.py 110 to 113: "the show's ONE look
   (ART_STYLE) on every picture, thumbnails included"), and a staged scene's request ends with `style_lock()` (anim.py 121).
   `anim.gemini_image` (123 to 142) sends its text as it is. So with (b) as written - `str(shot.get("prompt") or line).rstrip() + " " +
   anim.NOBODY` handed to `gemini_image(prompt, [], ...)` - every still of an F1 film and of a walk is asked for the puppet-diorama look, and
   the film's three animated scenes are asked from ANOTHER picture model with no look words at all; each clip is then animated from that
   picture. The fall-back inside the same function (`M.still(prompt, ...)`, anim.py 155) does add them: two roads of one function, two looks.
   WHAT A VIEWER GETS: the film changes its look at its three dearest moments, in four long videos of five - his item 16 ("three shows in one
   upload") by another door, built by the part that closes the audit's F1. No test of (g) would see it: the texts are searched for the act's
   place, the shot's own words, `NOBODY`, the motion sentence and six words of the trial.
   RIGHT: the memo must give a place scene's picture request the look words a still of the same film is asked with - exactly what `media.still`
   appends, in its order and joined as it joins them (the cell `STYLE_LOCK` when the text does not hold it, then `anim.style_words()` when the
   text does not hold them; `rstrip(". ") + ". "`), then `NOBODY`; correct the sentence in (a); TESTS on the request text: all three scenes of
   an F1 film and of a walk hold `anim.style_words()`, the fall-back's text holds them once, a trial's three texts are byte for byte today's;
   a break (the look words left out). AND ONE CLAUSE: `anim.start_frame(shot, path, ep, workdir, aspect)` has no `line` to hand
   `picture_request(shot, line, aspect)` - the memo must say what it hands (the `anim` record's own `line`).
2. THE REPAIR OF A SCENE HAS TWO HOLES (3.11, F1, (d) "ONE RULE FOR THE FIRST PURCHASE AND THE REPAIR"; `Job.repair_assets`, episode.py 349 to 383).
   (i) THE ADDRESS. Line 376 is today `path, url = M.still(...)`; `self._urls[i] = url`; and line 377 hands `self._urls.get(i)` to
   `media.animate` as the picture's address. `anim.start_frame` returns `(path, how)` - `how` is "google+refs", "google" or "fallback-still"
   (anim.py 151, 156) - which is why the first purchase returns the address None (`get_img`, line 282). The memo says only "re-makes its start
   picture through `ANIM.start_frame(s, <its path>, self.ep, self.out)` at line 376". Typed into the line as it stands, the word "google"
   becomes the picture's address: `media.animate` sends it to the clip provider (it falls back to the picture's own file only when the address
   is EMPTY: media.py 142 to 144), the provider refuses, with the Steward on a failure of the hero model is booked for a fault of our own and
   the next row is tried with the same address (162 to 168), the start picture was paid, the scene is not repaired, the film is held. Offline
   `animate` reads no address (139 to 141), and the memo's test compares TEXTS: nothing would see it before the pilot.
   RIGHT: the memo must give the lines - `path, how = ANIM.start_frame(...)`; `f["img"][i] = path`; `s["anim"]["frame"] = how`;
   `self._urls[i] = None` (the file itself is animated) - and a test with `media.animate` replaced that asserts the ADDRESS a repaired scene is
   handed is None; a break.
   (ii) THE THIRD REQUEST. The FIRST loop of `repair_assets` (361 to 368) buys a picture too and (d) does not name it. A scene is a target
   there when its start picture is missing (`f["missing"]`: `start_frame` and its fall-back both failed at the first purchase) and when the
   picture judge flags its frame (`anchor_of(i)` is the scene itself, line 356). Line 365 re-makes it with `M.still("<prompt>. Clear, sharp, no
   text in the picture, accurate to this line: ...")` - neither `picture_request` nor line 376. With the memo's own change of line 377 a
   trial's scene repaired on the first of those roads (its picture is then there, so 376 is skipped) is animated with `acting_prompt` ("Using
   the start frame: Dr. Grimm straightens his red pocket square ...") from a picture that was never the staged set and holds no Dr. Grimm -
   today the two requests of that road at least belong together (`motion + prompt` on a still of the prompt). In F1 and F3 the re-made
   picture is asked without `NOBODY`. "One rule for the first purchase and the repair" is not true of the picture on this road, and the
   audit's "TO CLOSE" (d) asks for one rule.
   RIGHT: the memo must decide what line 365 does for a target that carries `anim` - the reading that keeps one rule: it is re-made through
   `ANIM.start_frame` there as well (the same lines as (i)), every other target as today; the test "first purchase and repair hand over THE
   SAME TEXT" walks BOTH roads of the repair (a missing start picture; a scene the picture judge flagged) in F1, F3 and a trial; a break for
   each. SEEN BESIDE IT, OLDER THAN V1c, to be NAMED as an open issue and not repaired here: a scene flagged as `vision_artifact` is bought
   its picture twice in one repair (365, then 376 because it is in `redo`), and a scene flagged as `vision_mismatch` only is bought a picture
   that its clip, which stays, never shows.
3. F3 CHANGES WORDS THAT FOUR OLDER TESTS PIN, AND THE MEMO NAMES ONE (3.11, F3; question 8; law L7).
   WRONG: the memo names `test_a_whole_trial_under_the_ladder_names_only_the_character_who_is_drawn` as "a test changed by design" and
   `tools/sweep.py` before its change. Searched "ends on a tease" in `tests/`, `tools/` and `whatifs/` of 7e83001: `tests/test_v12_inside.py`
   holds the old words in FOUR tests. (a) line 369, `test_check_format_ending_passes_holds_and_says_na`: asserts the words in the evidence of
   an F2 context - true after the change only where `ROOM.tease_on()` is True in that test's settings. (b) line 536: the one named. (c) lines
   981 to 983 and the comment at 985, `test_the_sweeps_judge_says_the_inside_of_the_format_held_and_holds_an_id_where_it_was_not_walked`: it
   PLANTS the evidence "format F2 ends on a tease" and asserts `ok` and a line that ends "; the trial cuts between its pictures; ends on a
   tease" - under the memo's rule that evidence is refused (it does not hold "is a trial"). (d) line 1079,
   `test_the_sweep_holds_a_trial_whose_camera_is_not_applicable_for_another_reason`: it plants the same evidence and would then fail for two
   reasons - it no longer proves the camera's alone. A builder may change an older assert only where the record named it first: as written the
   builder stops on a `DESIGN QUESTION` at step 0, or changes three asserts of a judge-pinning file that nobody named.
   RIGHT: the memo must name each of the four with what it asserts AFTER the change (for (a): which setting the test runs in and so which of
   the two endings of the sentence it must find; for (c) and (d): the planted evidence in the new words), and say exactly what "the
   evidence's own last clause" is - the text after the last "; " of the `format_ending` evidence - since (c) types the judge's whole line from it.
4. F2's WHOLE PRODUCTION CANNOT SHOW WHAT ITS TEST ASKS (3.11, F2, TESTS).
   WRONG: "a whole F1 production with `CAMERA_PATH_ON` whose offline Director asks for footage (it does, on every seventh line): the log line,
   `camera_path` PASS, no state of type "stock"". The offline Director does ask (fakes.py 301). But a footage shot reaches `path.mark`
   (produce, line 650) only when it survived `stock.shape` (644: never first, never two in a row, a line of `STOCK_MIN_S` to `STOCK_MAX_S`,
   the share) and `inside.open_acts` (648) - and the prover and the audit found that in NONE of the 21 offline long videos on record one did
   (open issue 199; the audit's own id: one footage shot, made a still because it opened its beat). In such a production the new conversion
   converts nothing and its log line is never printed. The typist must then either make the assert conditional - and the production walks
   nothing, which is exactly what the audit found of today's tests ("today no test and no sweep id does") - or invent a way to plant a shot.
   RIGHT: the memo must say how that production gets ONE footage shot to `path.mark` - a named tool of the test, as 3.10 names its patched
   viewing: for example `stock.shape` wrapped so that one shot inside act 2, on a line that does not open its beat, leaves it as type "stock"
   with its `search` - and that the asserts are unconditional: the log line with n >= 1, `camera_path` PASS, the shot a still that holds its
   act's place sentence, no state of type "stock" in the render's record.
5. THREE PLACES WHERE THE TYPIST WOULD STILL DECIDE (one clause each).
   (a) 3.4, `story.align`: "THEN `story.align(pkg, d, opening)`, right after the package is made, makes both thumbnails the opening's scene BY
   CONSTRUCTION" names no condition. Run on every package it gives a video made under an override (`first_picture` is "") the thumbnail
   prompt "" and the key `one_story` - and 3.4's next bullet then draws no promise scene for it. The memo must say that `align` returns the
   package as it came and sets no key unless `ONE_STORY_ON`, the opening is a Short's footage and `words` is not empty; a test: under an
   override the package is the packager's, byte for byte.
   (b) 3.2, `verdicts.downs`: the memo says what `references` returns ([(episode, view id)]) and not what `downs` returns, nor where the title
   in "ranked beside a video you marked not good: '<its title>'" comes from - `floor.verdict(looks, refs, downs)` is pure and `session` is
   handed viewings. One sentence: the shape `downs` returns and the road of the title into the verdict's words.
   (c) 3.11, F1 (f): "`p_camera_path`'s PASS words gain '; <n> scene(s) asked in their act's place'" - the memo must say WHERE: at the END
   of the words. The sweep's judge prints that evidence up to "; every picture" (`tools/sweep.py` 136): a clause placed before those words
   would change the line the block reads on every F1 and F3 id.

## The ten questions of 5.4
1. Does every part serve a viewer or the scoreboard in a way a layman could name? YES - a film two first-time viewers cannot tell from the
   one he rejected is held; one tap of his after every release is the label; his own sentence ends the film; the thumbnail is the picture the
   film opens on; nobody of the trial's cast in a film where nobody is on screen; and (3.11) the three animated scenes are his own place.
2. Does it honour every word of the owner that touches it? NO, in one place - item 16 (three shows in one upload): the scenes of F1 and F3
   leave the trial's sets and, as written, leave the film's look as well (change 1). YES for items 49 (b) (the wrong answer is said plainly,
   the two stale texts are corrected in the build), 50, 51 (c) (the eye's clock: a release never waits for him), 55 to 62 (no credit is a
   crutch, the bar never moves with money), 70 and 71 (3.0: every setting is data with a setup step), 73 (every road on which the floor
   refuses nothing is named under THE WORST VIDEOS), 79, 80 (filed, nothing built), 88 (below).
3. Is every rule ENFORCEABLE as written? NO - four are not typeable without a decision: the picture request of a place scene (1), the repair
   (2), F2's production test (4), `align`'s condition (5 a). Every other rule names its function, its arithmetic, its check, its failing test
   and its break.
4. Does any rule judge TASTE by a cheap model, or let a model's opinion gate a video? NO cheap model: the jury is the Board's two strong
   chains, counted only when the call's provider and role say so. The jury's answer DOES gate a video - that is the floor the brief orders
   (12.3) - and it is fenced: a pairwise question in both orders, planted rungs with answers code knows, a verdict code computes and the
   check recomputes, a void session that holds nothing, his tap as the label that scores it.
5. Judged on the FINISHED FILE, with BOTH kinds of measured pairs? YES for the floor (the first minute of the finished master; offline pairs
   measured in Step 1 part two: four films at 100% of their gaps changing against the stand-in's 48.3% and its twin's 0%) - and said plainly
   that REAL pairs exist only at the pilot (open issue 201, before the hold is trusted). The rule of 3.11 (f) reads the plan's `anim` record
   and its proof is the test on the request texts; what a picture model draws is the pilot's (H33) - said.
6. Money: is every new paid call a LINE, inside Rs 5,000? YES - one new kind (the jury): its line (Rs 40 estimated), its bound (Rs 87 a
   session with one cut look a family; arithmetic checked again: 3 x 0.170 + 3 x 0.124 = USD 0.882), its cap per video (75 x
   `governor.max_long_videos()`), the worst month in rupees. 3.11 adds no call (the place scene is the same paid picture, cost row
   `image_ref`). NO for the paid repair of change 2 (i): a start picture is paid for a clip request that cannot succeed.
7. Does it reuse what earlier batches left ready? YES - the Board's chains and its two counting lines, `probe_run`'s shape, `notify`'s own
   clock, `release.sha`, `contract.await_approval`, the ladder row, the Short's archive, V2b's row keys and recognisers.
8. What does it change that an OLDER test or check pins, and is each named? PARTLY - named: `OLD_VIEW` in `tests/conftest.py`,
   `tests/test_safety.py` 68 (24 to 25 workflows), `tests/paid_calls.py:watch` and `V12V1C_ADDED`, `tools/sweep.py` (`floor_of`,
   `inside_of`), the rehearsal's settings, `contract.review_needed`, one test of `tests/test_v12_inside.py`. NOT named: the three other
   tests of that file that pin "ends on a tease" (change 3).
9. The worst video this design could still let through, in my own words. AS WRITTEN: an F1 film - three long videos in five - whose three
   animated scenes, fifteen of about 510 seconds and the peaks at the retention cliffs, are drawn in another look than everything around
   them, with every check PASS (the check reads the scene's world, the tests read other words): change 1. AFTER THE CHANGES, the ones the
   memo names itself: until his canary file is filed EVERY long video, and after that every video whose jury was void, goes public after
   twenty hours of his silence having passed every measured check and no first-time viewer - the floor is then a report, not a gate, and
   D13's memo names the film; a film that dies after its first minute; and a place scene in which a picture model draws a person anyway
   (H33, his eye at the pilot). His first three videos of the new code never go out without his tap.
10. What can only reality answer, and is it written down? YES - open issues 201 (one answer's worth: q on ten sessions before the hold is
   trusted; what a session costs), 202 (the kit's fetch, the run's log, the link on his phone, the title's length), 203 (his line and his
   ear), 204, 206; H6, H13, H31, H32, H33.

## The reviewer's changes 16 to 20 of the third pre-review, in the record's text
16 CLOSED - Step 3 reads as ONE text: `floor.run(brief, ep, master, out, refs, downs)`, `session(sid, sha, new, canary, twin, refs, downs,
   episode, view="")`, `verdict(looks, refs, downs)`, `maker.take(d, ep, clean)` with `lead(clean)` kept as `mk["lead"]`; 3.9 step 1 names
   `fetch`, `strip`, `floorkit.yml` with its pin, `think=`, `waits=`, `tight=`, `eye_sweep`, its seven cells; step 2 the D pairs; a stand-in
   that plays a paid failure calls `core.cost` before it raises; one count in 3.7; what stood before is outside the memo, at its end.
17 CLOSED - `thumb_prompt_b` = `words + "; " + r[:160]`, `words` never cut, the test with 220 characters and its break.
18 CLOSED - a cut look gets ONE second attempt with `TIGHT_NOTE` (the doorway's kind (2), `tight=`, `_tight`); 3.8 is computed again
   (Rs 87 a session, the cap cell 75: four first sessions fit a month in which every look is cut once).
19 CLOSED - the fetch's way back stands in 3.1, in WHAT ONLY REALITY CAN ANSWER and in open issue 202 (a).
20 CLOSED - the product is 8 + 4k + 4j answers (the table checked: 0.9^12 = 28%, 0.975^16 = 67%, 0.986^16 = 80%), the references start at 1
   with the rule by q written now, `VIEW_FLOOR_DOWNS_MAX` rises only at 0.986 (0.982 without a reference).

## The audit's four findings against its "TO CLOSE"
F1 - DECIDED (a scene is the viewer's own place where the row's `cast` is False; the same key and switch as open issue 196, built in one
   step 0b). Of what "TO CLOSE" lists: (a) the world follows the row - yes; (b) tests on the request texts in F1, F3 and a trial - yes, and
   they miss the look (change 1); (c) a break for each - yes; (d) one rule for the first purchase and the repair - NOT YET (change 2);
   (e) the words of `living_characters` and `camera_path` made true - yes (5 c for where the clause stands); (f) the record's two sentences
   corrected by the build - yes.
F2 - DECIDED, reading (a): real footage never stays inside an act. The failing test, the break, rule 6 and the Director's sentence are
   there; the whole production as worded cannot show it (change 4).
F3 - as the audit writes it; `tools/sweep.py` is named before its change (L7); the record is corrected by one dated line and the notes are
   not edited (L11). The other three pins are not named (change 3).
F4 - as the audit writes it: the two sentences read at format_engine.py 14 to 15 word for word, the test on every role's block, the break.

## Every request that buys a picture or a clip, traced by name through each rule the memo adds (the audit's lesson)
- `media.still`: `_assets.get_img` 283 (anchors only: 3.3's edits of `anchor_shots` and `path.mark` keep a `maker` shot out; a footage shot
  that F2 made a still is a still like any other); `repair_assets` 365 (targets: 3.3's edits (b) and of `qc.vision_indexes` keep his units
  out - and a target with `anim`: change 2 ii) and 376 (a scene without `anim` only, after 3.11); the thumbnails A and B (3.4: the same two
  pictures, prompts by construction; `_thumb_b` reads `thumb_prompt_b`).
- `anim.start_frame` -> `gemini_image` / the fall-back still: `get_img` 282; after 3.11 `repair_assets` 376; `specials.py` 356 (its own
  staged shots: byte for byte). The place scene's text: change 1.
- `anim.acting_prompt` / the new `clip_request` -> `media.animate`: `get_clip` 296; `repair_assets` 377 (the address: change 2 i);
  `specials.py` 358. `sheets.py` 173 calls `frame_prompt` itself: untouched.
- `motion_prompt` -> `media.animate`: `get_clip` 296 for a living clip and a scene without `anim` (`motion.place`'s `can` and `plain` keep a
  `maker` shot out: 3.3).
- `media.stock`: `get_clip` 294, type "stock" only - none is left inside an act of a path format after `path.mark` (F2), and nothing after
  `path.mark` makes one (`anim.apply`, `promise_shot`, `motion.place`, `path.lay` read: none sets that type).
- The Short's own requests (`shorts2.py` 358, 360) and the opening cut from its footage (`opening.cut`: it buys nothing): not touched.
- The writers of the records the new rules read: `shot["anim"]` - `anim.apply` alone, run again on every `produce`; the type "stock" - the
  Director, `stock.shape`, `audience.make_still`, `inside.open_acts`, now `path.mark`; the `format_ending` evidence - `p_format_ending`.

## The seven attacks asked for beyond the ten questions
(a) Exact enough to type? Parts 3.0 to 3.10: yes, read as the typist; the arithmetic of 3.1 and 3.8 was done again. Not typeable as
    written: changes 1, 2, 4 and 5.
(b) False about today's code: "the look, the style lock are in it" (the cell's lock is, the show's look words are not: change 1); "(it
    does, on every seventh line)" is true of what the Director asks and not of what reaches `path.mark` (change 4). TRUE as checked, each at
    its lines: `anim.py` 81 to 106, 117 to 121, 144 to 164; `immersion.apply` 135 to 136; `_assets` 280 to 297; `repair_assets` 376 to 377;
    `path.mark` 83 to 98, `lay` 100 to 109, rule 4 at 138; `stock.shape`'s `back` (31 to 33); the order of `produce` 640 to 658 (the format
    is current at `anim.apply`); `p_format_ending` 497; `inside_of` 131 and 137; `format_engine._for_format`; `p_living` 254 to 270;
    `reaction_shots` 141 to 155; `notify.send` (no `expires_h` = no expiry); `_stage_plan` 146 to 190 against 3.3 and 3.4.
(c) A good video held for a reason the rule does not recognise: none found in 3.11 (rule 6 fails only when the conversion is gone; the
    staged-scene rule only when `anim.apply`'s line is gone). A bad one passed: change 1.
(d) Marks: `maker` as 3.3 lists; a place scene keeps `anim`, gets its act's place sentence and is judged by rule 4; `promise` keeps its
    exemption; `short` untouched.
(e) The order of 3.9: steps 0 and 0b stand in front and depend on nothing later (`OLD_VIEW` begins with `CAST_BY_FORMAT_ON` in 0b); step 0
    is not green as written, because of the three unnamed tests (change 3).
(f) What a viewer and the owner get: in the first lines of the record - true of the memo once change 1 is in.
(g) The worst video: question 9.

## The plan's 12.11 and his item 88 (a), (b)
A BUYER WHO IS NOT HIM: every setting, name and path the memo adds is data with a setup step (3.0: the canary is a file of the buyer's own,
filed by a workflow of his own repository; the references are his own approved videos in his own Drive; `OWNER_VERDICT_SINCE` sets itself;
`MAKER_QUESTION` is a cell; no id, channel name or subject in code or texts). 3.11 adds two English sentences to prompts (`anim.NOBODY`, the
Director's "Never stock") - of the same kind as every prompt text a buyer in another language changes. NO TOOL: the pipeline of the memo
calls no skill, plugin or connector and copies no text of one; the research of Step 1 is pages fetched and read, the two GitHub pages named.

## What is sound and should not move
Design E and the case built against it; the frozen twin as the rung that needs no reference; "a missing answer counts against the session";
a refusal and a pass that both stand across renders, with the log read outside the try; the eye with a clock that follows the slot and a
sweep that tries a failed default again; the hold card that never closes by itself; his line attached to the voice and never to the script,
compared as the voice's own unit texts; `words` never cut; the two decisions of 3.11 themselves (the viewer's own place; no footage inside
an act) and that the trial is kept byte for byte.

## Outside the memo (for the dispatcher; no change of the memo)
`02` item 49 (b) still holds the answer the record calls wrong and carries no note: a session that may edit `02` writes the note of the
build under it (the pattern of the note to items 27, 30 and 32), in the words of the record's settled thing 1.

## The reading
In the two pre-review rounds: the whole handoff reading of chapter 4 (the plan, `00` to `06`, `02` items 1 to 75, the redesign, the record
as it stood, open issues 1 to 197, `reviews/V2b_design.md`) and the code named in `PREREVIEW2_V1c.md`. In this round: the plan's diff
dc491df..HEAD whole (A10, A11, chapter 10, 12.4, 12.5, 12.10); `02` items 76 to 88 whole; `reviews/V2b_audit.md` whole; the record's Steps 1
to 3 whole, line by line as the typist (not by a diff against the draft); open issues 200 to 206; `reviews/V2b_design.md` rounds 3 and 2
(the form) and its seven attacks; of 7e83001 whole: `anim.py`, `path.py`, `media.py`; by the lines named: `episode.py` 134 to 191, 198 to
412, 534 to 561, 632 to 671, 756 to 812, 922 to 932; `stock.py` 1 to 75; `immersion.py` 84 to 147; `room.py` 682 to 773; `contract.py` 253
to 275 and 489 to 543; `format_engine.py` 10 to 18 and 86 to 112; `tools/sweep.py` 113 to 138; `shotplan.py` 141 to 155; `fakes.py` 294 to
312; `org/audience.py` 60 to 100; `qc.py` 100 to 128; `tests/test_v12_inside.py` at its four pins. NOT read against the code in any round,
said plainly: `fakes.py` where `fake_watch` goes, the sweep's `summary` and `climb`, `hours.translate`, `sound.py`, `motion.py` beyond the
three lines that read `anim`, `tools/rehearsal.py` beyond its lines on the tease - the designers read those whole; `wa.py` and `dash.py`
were read by nobody (the record says so).

## USAGE
At the start of this round (08:16 UTC): weekly all models 33%, weekly Fable 57%, this session's context 12% (the app had compacted it).
When this file was written (08:28 UTC): weekly all models 34%, weekly Fable 59%, context 38%. The app shows no 5-hour line. Other Fable
sessions worked beside this one and are not measured apart.

---
## Round 2 in the record (15 Nov 2026, 08:38 to 08:58 UTC; the same reviewer) - VERDICT: APPROVED
Reviewed: the record as of commit 8e079c2 (the state DESIGN_REVIEW in a35b601); `proving/next.py` once (the card THE DESIGN REVIEWER of V1c,
pre-flight clean). The five changes were applied by the dispatcher's Fable session, which wrote none of the rest of the memo - so the whole
difference e50d6fb..8e079c2 of `BUILD_STATE.md` was read from a file (241 lines; 136 in, 25 out; nine places), each changed passage again in
its place, and the new text of 3.1 / 3.2 against 3.1 as it stands. Nothing else of the memo moved; the code is still 7e83001.
THE FIVE CHANGES OF ROUND 1 ARE ALL IN THE MEMO, NONE ARGUED. What was found in the NEW text is five small things, none of which a viewer,
the money or a law depends on and none of which lets a typist build the product wrong: they are listed under "TO CORRECT AT THE BUILD" with
their exact words and do not hold the batch.
SAID PLAINLY - A SIXTH WAS FOUND AFTER THE APPROVAL WAS COMMITTED (1fae761) AND THE STATE MOVED TO BUILD. The plan gained a duty at 08:42 UTC,
inside this round (A11 (h3), the owner's item 89: the code graph's callers beside the search). Doing it afterwards showed that parts 3.3 and
3.4 - which stand since the pre-reviews - change three calls of `_stage_plan` whose SOURCE TEXT older tests pin, and the memo names none of
them: correction 6. It is of the kind round 1 made a numbered change (its change 3: law L7, question 8) and this reviewer missed it in
three readings. No decision of the design moves and the state machine has no road back from BUILD; so the six corrections are given in exact
words and ARE TYPED INTO THE MEMO'S TEXT, EACH AT ITS PLACE, BY A TEXT COMMIT BEFORE THE FIRST LINE OF CODE (the state stays BUILD) - a
continuation typist reads the memo, not this file.

### The five changes of round 1
1. CLOSED - a place scene's picture text is built as `media.still` joins it (the cell's lock when not held, then `anim.style_words()` when not
   held, `rstrip(". ") + ". "`), then `NOBODY`: compared with media.py 108 to 113 line by line; `start_frame` hands the `anim` record's own
   `line`; the fall-back is handed the same text; the tests on the look (each word once, at the default and at "illustrated"; a trial byte
   for byte) and the break. One sentence about the fall-back is true only below 1,514 characters: correction 3 below.
2. CLOSED - ONE helper `scene_picture(i)` for both roads of the repair, with the four lines asked for and the address None; read against
   episode.py 349 to 383: on road 1 it stands in place of lines 365 and 366 for a target with `anim`, on road 2 in place of line 376, and
   line 377 then hands None, so `media.animate` sends the picture's own file (media.py 142 to 144). The tests walk both roads in F1, F3 and a
   trial and assert the address; three breaks; what is older is open issue 207, named and not repaired.
3. CLOSED - the four tests are named, each with its assert after the change; checked against the test file: test (1) runs with `ENDINGS_ON`
   TRUE (its fixture), `LADDER_ON` FALSE (`tests/conftest.py` 34) and `NEXT_TEASE_ON` at its default TRUE - the first clause; `_led` gives
   tuples, so the equality of (2) can hold; "the evidence's own last clause" is now exact (`rsplit("; ", 1)[-1][:120]`) and no clause holds
   "; " inside it. THE ONE THING MORE THAN ASKED - the clause decided from the two cells, in three forms - IS KEPT, and it is not a change of
   design beyond the round: `room.tease_on()` (room.py 445 to 450) reads `FMT.ending()` of the format IN THE MAKING, while this check answers
   for the DRAW's format and is called outside `formats.use` by its own tests; inside the branch it stands in (`ENDINGS_ON` TRUE, the draw's
   format ends on a tease) `tease_on()` for that film IS `NEXT_TEASE_ON and not ladder.on()` - the first clause's condition, word for word;
   the other two say WHY no tease is spoken (the ladder; the cell), which is what the audit's F3 asked of a judge's line. `ladder.on()`
   needs both cells (ladder.py 14 to 16): the test sets both.
4. CLOSED - the production plants its footage shot through a wrapped `inside.open_acts`, the last step before `path.mark` (episode.py 648,
   650: the module's attribute is looked up at the call, so the wrap is taken), `media.stock` is a recorder, every assert is unconditional.
   WHERE the test reads the shot list is wrong (corrections 1 and 2 below) - a fault of the test's wording, not of the rule.
5. CLOSED - (a) `story.align` returns the package as it came, the same object, unless its three conditions hold; the test and the break.
   (b) `verdicts.downs` returns [(episode, view id, title)] and the title travels in ONE new last column `downs` of the new tab `Floor_Log`
   - ATTACKED AGAINST 3.1 AS IT STANDS, AS ASKED, AND IT HOLDS: no word of any verdict names a reference (the why says "lost to <k> video(s)
   you approved"; `vs_refs` and `predict` count), so `verdict` needs of `refs` its length alone; a row's `items` = {label: kind} carries
   "R1" .. "Rk", so a recomputation has k from the row itself; the titles of the down-canaries are the only words a verdict takes from
   outside its looks, and they now stand on the row that `floor.session` alone writes - the rule "ONE writer" of 3.10 (1) is unbroken, the
   tab is new (no older row lacks the column), 3.1's row list and 3.7's tab line carry it. The break (the list not written: the check FAILS
   "the stored verdict is not the code's verdict on its own looks") proves the column is read. (c) the clause stands at the very end, with
   a test that the sweep's line does not move.

### The ten questions of 5.4, round 2
1 yes. 2 yes - item 16 is now honoured where round 1 found it broken: the three scenes are the viewer's own place AND in the film's look.
3 yes - every rule names its function, its arithmetic, its check, its failing test and its break. 4 no cheap model and no opinion without
its fence (round 1, question 4). 5 yes, with the pilot's real pairs before the hold is trusted (open issue 201). 6 yes - one new paid kind
with its line, bound and cap; the repair buys what the first purchase buys, at the address the first purchase uses. 7 yes. 8 YES ONLY ONCE
CORRECTION 6 IS IN THE MEMO - named today: `tests/conftest.py`, `tests/test_safety.py` 68, `tests/paid_calls.py`, four tests of
`tests/test_v12_inside.py`, `tools/sweep.py`, the rehearsal's settings; NOT named in the memo as it stands: one more test of
`tests/test_v12_inside.py` and two of `tests/test_v12_org.py` that pin the source text of three calls. 9 THE WORST VIDEO STILL LET THROUGH is one the memo
names itself: until his canary file is filed every long video, and after that every video whose jury was void, goes public after twenty
hours of his silence having passed every measured check and no first-time viewer (D13's memo names the film; his first three never go out
without his tap); a film that dies after its first minute; a place scene in which a picture model draws a person although it was asked not
to (H33) - and, read in this round, asked WITHOUT that sentence in one rare corner (correction 3). 10 yes - open issues 201 to 207, 208
by correction 3 and 209 by the note under the corrections; H6, H13, H31 to H33.

### TO CORRECT AT THE BUILD (six; each with its exact words; typed into the memo's text at its place by a text commit BEFORE the first
### line of code, marked "(the design review, round 2)"; nobody decides anything; the finisher checks them first)
1. 3.11 F2, THE PRODUCTION'S ASSERTS READ THE WRONG PLACE. "in the saved plan `shots[i]["type"]` is not "stock" ... and its prompt holds
   `path.SENTENCE`": `plan.json` is written ONCE, at the plan stage (`produce`, episode.py 633), BEFORE `stock.shape`, the plant, `path.mark`
   and `path.lay` (644 to 658), and is not written again for a film that passes. Read there, the three asserts on the shot's type, `search`
   and `stock_s` are true whether or not the conversion ran, and the assert on the place sentence fails. THE WORDS: the test reads the shot
   list THE SCRIPT GATE IS HANDED - a spy on `CON.run` that keeps `c["shots"]` at stage "script", the pattern of `tests/test_v12_inside.py`
   527 to 528 - and makes those four asserts there; every other assert as the memo has it. If in that list the planted shot carries `anim`
   (the Animation Director took its line as a scene's slot), the plant takes the SECOND index its own rule finds, written down in the test
   - never a changed assert.
2. 3.11 F2, THE BREAK'S OWN DESCRIPTION. "(the test then finds `camera_path` FAIL by rule 6 and a call of `media.stock`)": with the
   conversion gone the film is HELD at the script gate (`produce` 663 to 666), before any asset is fetched - `media.stock` is not called in
   that break either. THE WORDS: "(the test then finds no log line and `camera_path` FAIL by rule 6; nothing is fetched: the film is held
   at the script gate)". The break stands as it is.
3. 3.11 F1 (b), THE FALL-BACK'S SENTENCE IS TRUE ONLY BELOW 1,514 CHARACTERS. "`atmosphere.with_directive` shortens the DIRECTIVE, never
   the prompt" is that function's docstring; its line 216 (`if room <= 40: return p[:mx]`) cuts the TEXT at its END once the text is longer
   than `mx - 42` - with today's cells (`IMAGE_PROMPT_MAX_CHARS` 1800; the lock is 159 characters and the default look words 81, counted:
   `media.still` hands `mx` = 1800 - 161 - 83 = 1,556) from 1,514 characters on - and `NOBODY` (114 characters) stands at the end. A place
   scene's text is about 1,000 characters by its parts (ESTIMATED, not run: the place sentence about 140, the first-person rule about 200,
   the Director's words and the look about 320, the lock, the look words, `NOBODY`); it passes 1,514 only where the Director's words and
   the bible's look together pass about 800, which a continuity re-plan can do (it appends up to five fixes to the look: episode.py 180).
   So on the fall-back road ALONE, and only for such a text, the still is
   asked without the whole `NOBODY` sentence (the lock and the look words are put back by `media.still`); the picture is still asked from
   the shot's own first-person words, never from the trial's sets. THE WORDS: (i) the sentence in (b) becomes "... its lighting directive
   goes behind the text (`atmosphere.with_directive` shortens the DIRECTIVE first; a text of `mx - 42` characters or more is cut at its
   END - atmosphere.py 216 - where `NOBODY` stands: open issue 208)"; (ii) the fall-back's test also hands each of the production's three
   scene texts through `atmosphere.with_directive(text, S("IMAGE_PROMPT_MAX_CHARS", int) - (len(lock) + 2) - (len(sw) + 2))` and asserts
   `anim.NOBODY` whole in what comes back; (iii) NEW open issue 208, in these words: "(V1c's design review, round 2; READ, NOT RUN -> B7,
   with 207) ON THE FALL-BACK ROAD A PLACE SCENE'S PICTURE REQUEST LOSES ITS LAST SENTENCE FROM 1,514 CHARACTERS ON
   (`atmosphere.with_directive`, line 216, cuts a long text at its end; `media.still` puts the lock and the look words back, nothing puts
   `NOBODY` back). To be decided with the repair loop: where `NOBODY` stands in the text, or a request that is never cut." No code of the
   batch changes for it.
4. 3.2, THE TITLE IN THE WHY. "of `downs` it reads its length j and, for the why, `str(downs[j - 1])`": the letter j is the list's length
   and the number of the down-canary in one sentence. THE WORDS: "the title of D_i is `str(downs[i - 1])`, i counted from 1 - the
   down-canary the family lost to, never the list's last by default".
5. 3.2, "WHEREVER A VERDICT IS COMPUTED AGAIN FROM STORED ROWS" NAMES THREE CALLERS AND THERE ARE FIVE. `verdicts.references` and
   `verdicts.downs` compute "pass" for another episode's newest session from its rows as well. THE WORDS: ONE helper in `floor.py` - the
   rows of one session in, `floor.verdict(looks, <a list as long as the kinds "R1" .. "Rk" in the first row's `items`>,
   json.loads(first["downs"] or "[]"))` out - called by the run's rules (1) and (2), check `viewer_floor`, `verdicts.sync`,
   `verdicts.references` and `verdicts.downs`; a test greps that no other line calls `floor.verdict` on stored rows.
6. 3.3 AND 3.4 CHANGE THREE CALLS OF `episode._stage_plan` WHOSE SOURCE TEXT OLDER TESTS PIN, AND THE MEMO NAMES NONE OF THE PINS (it
   names one pin of this kind, the hook's: `tests/test_v12_inside.py` 889). THE PINS, read in the test files: (a)
   `tests/test_v12_inside.py` 1105 to 1108, `test_both_voice_calls_of_the_plan_stage_hand_the_beats_on`: `src.count("line_beats=beats") ==
   2` and `"line_beats=beats" in after` - 3.3 gives both `narrate` calls `voiced` and `line_beats=vbeats`. (b) `tests/test_v12_org.py` 473
   to 479, `test_every_wrapped_call_site_still_calls_the_function_it_wraps`: the line of `ORG.work("D7", "voice"` must hold `narrate(clean,
   blend()`, the line of `ORG.work("D5", "package"` must hold `ROOM.package(room, chs, d, ep)`, the line of `ORG.work("D6", "plan"` must
   hold `ROOM.plan_shots(room, units, d, plan, ep)` - 3.3 makes the first `voiced` and the third `su`, 3.4 hands `package` the opening.
   (c) `tests/test_v12_org.py` 468, `test_the_registry_is_honest_about_what_runs_under_the_runner`: it cuts the exact text of the package
   call out of the source and asserts that something was cut. As the memo stands, the typist of steps 3 and 4 meets three red older tests
   it may not touch - or keeps the old names to keep them green, and then `clean` carries his line into everything that reads the script.
   THE WORDS (the calls' forms, then each assert after the change - TESTS CHANGED BY DESIGN, named here before they are touched):
   - the two voice calls (episode.py 155, 163): `narrate(voiced, blend(), os.path.join(out, "voice"), line_beats=vbeats, **vkw)`; inside
     the too-short loop line 162 becomes `if longer: script = longer; clean, beat_marks, beats = _strip_beats(script); voiced, vbeats =
     MAKER.attach(clean, beats, mk)`.
   - the two Director calls (176, 181): `ROOM.plan_shots(room, su, d, plan, ep)`.
   - the packager: `def package(room, chapters, draw, episode, opening=None)` and the call `ROOM.package(room, chs, d, ep, opening=opn)` - a
     KEYWORD with the default None, because `tests/test_tableread.py` 122 calls `package` with four arguments and stays as it is.
   - (a) becomes `assert src.count("line_beats=vbeats") == 2 and src.count("line_beats=beats") == 0 and "clean, beat_marks, beats =
     _strip_beats(script)" in after and "voiced, vbeats = MAKER.attach(clean, beats, mk)" in after and "line_beats=vbeats" in after` - what
     it guards stands, one thing stronger: the second voice is made from the lengthened script WITH his line attached again.
   - (b): the three texts become `"narrate(voiced, blend()"`, `"ROOM.package(room, chs, d, ep, opening=opn)"` and `"ROOM.plan_shots(room,
     su, d, plan, ep)"`; the other six of that test stay.
   - (c): both strings of its `src.replace` carry `ROOM.package(room, chs, d, ep, opening=opn)` in place of `ROOM.package(room, chs, d,
     ep)`; nothing else of the test moves.
   - AND TWO PINS THAT STAY TRUE, said so that no typist moves them: in `produce` the call text `ROOM.promise_shot(shots, units,
     S_.get("pkg") or {})` after `ANIM.apply(shots, units, plan)` (`tests/test_v111_enforce.py` 115) - 3.4's condition goes on the `if` in
     front of it (line 654), never into the call; in `tools/rehearsal.py` the line right after `r = EP.produce(slot, episode_id=epid)`
     stays the `assert r.get("ok")` line (`tests/test_v12_motion.py` 734).
   EVERY OTHER TEST THAT PINS SOURCE TEXT OF A FILE THE MEMO EDITS was read for this (searched `getsource(` and the files' names in
   `tests/`): `test_v12_inside.py` 186 (the order in `produce`), 955, 993 to 998 (the sweep's and the rehearsal's calls of `inside_of`),
   `test_v12_money.py` 306, 425, 427, `test_v12_motion.py` 266, 397, 487, 627, 705, `test_v12_exec.py` 327, `test_v12_cutdowns.py` 122,
   `test_safety.py` 25, `test_v891.py` 97 - none pins a line the memo changes, as long as the builder ADDS its lines and rewrites none of
   those.
WHY NONE OF THE SIX HOLDS THE BATCH: 1 and 2 are where a test looks and how a break is described; 4 and 5 are one clause each on a cell
that starts at 0; 3 is a corner of a corner (the fall-back road, a text half again as long as usual) on which the request still asks for
the viewer's own place in the film's look - named as an open issue, as the memo names what a picture model does with the sentence (H33).
6 IS THE WEIGHTIEST: a typist cannot build the PRODUCT wrong by it as long as these words are in the memo before it types - which is why
the six are carried into the memo's text first, and why that is said in the first lines of this round.
SEEN IN THIS ROUND, OLDER THAN V1c - THE BUILDER NAMES IT AS OPEN ISSUE 209, IN THESE WORDS, AND CHANGES NO CODE FOR IT: "(V1c's design
review, round 2; READ, NOT RUN -> his eye at the pilot, with H33; a later design of D6) IN A CAMERA-PATH FORMAT A SHOT THAT WAS A SCENE AT
PLAN TIME CARRIES TWO CAMERAS IN ITS REQUEST. `immersion.apply` gives such a shot the path's motion sentence (lines 135 to 136: 'the camera
moving forward with the viewer's own steps') and, one line above, the first-person rule written for a clip on a moving object
(`pov_prompt` -> `data.POV_KLING`: 'camera mounted on the moving object, accelerating, shaking, debris streaking past the lens') in its
PROMPT. Under V2b's defaults that prompt reached no request of a scene (the audit's F1). With V1c's 3.11 it reaches the start picture and
the clip of a place scene whose line was a scene at plan time - by chance in a film about a promoted Short, and the promise scene of every
film made under an override. A scene the Animation Director promoted from a still carries the still's rule ('the camera IS the viewer's
eyes') and is not touched by this." It holds nothing: the words are V2b's, the request still asks for the viewer's own place, nobody in
it, in the film's look; what a clip model makes of the two sentences together can be judged only on a real clip.

### The code graph's callers beside the search (the plan's A11 (h3); the owner's item 89)
`code-review-graph update --repo reality-engine` (about 08:50 UTC; no python or ffmpeg process alive; one file re-read, 5,798 nodes; the graph's
data lies outside the repository and the tree was untouched), then `query callers_of` and `query tests_for` for the 45 existing functions
the memo changes (a script written with the file tool; its output read from a file). WHERE THE TWO LISTS DIFFER, each difference read:
- `anim.acting_prompt`: the graph names `specials.run` alone. THE SEARCH ADDS `episode._assets.get_clip`, line 296 - called through
  `__import__`, which the graph cannot see - the very request the audit's F1 is about; and `tests/test_v102.py` 24 and 142 (the function
  stays byte for byte).
- `Job.repair_assets`: the graph names one test, `tests/test_v12_opening.py::test_the_paid_repair_never_remakes_a_shot_of_the_footage`.
  THE SEARCH ADDS the production caller, `fixes.auto_fix` line 29 (a call on an object). The test was read: its shots carry no `anim`, so
  its `paid == ["still"]` stands unchanged by 3.11 (d).
- `sound.immersive`: the graph names `contract.p_impact` (line 235) - A CALLER THE MEMO DOES NOT NAME; the search adds `episode._render`
  524 and `tests/test_v810.py` 228. Read: the check recomputes the film's sound design by the same call; 3.3's edit takes its `maker`
  shots from `shots` inside the function, so the film and its check keep one rule. Nothing to change.
- `room.package`: the graph names `tests/test_tableread.py::test_all_other_prompts_have_no_leftover_placeholders` alone; the search adds
  `_stage_plan` 175 AND THE TWO TESTS THAT PIN THAT CALL'S TEXT - followed up: correction 6.
- `sound.plan_sounds` and the five checks (`p_living`, `p_camera_path`, `p_format_ending`, `p_viewer_numbers`, `p_viewer_plain`): the
  graph names no caller (a module alias; rows of `contract.FEATURES`). The search is the list: `_stage_plan` 184 and `tests/test_v87.py`
  224; `tests/test_v12_inside.py` 367 to 370 for `p_format_ending` (round 1's change 3).
WHERE THEY AGREE (the graph's callers, the same as found by search): `anim.apply` - `episode.produce`, two tests; `anim.start_frame` -
`episode.get_img`, `specials.run`; `anim.frame_prompt` - `start_frame`, `sheets.style_samples`; `_assets`, `_finish`, `_stage_plan`,
`path.mark`, `path.lay`, `stock.shape`, `motion.place` - `produce`; `_hold` - `_finish` (two sites; the memo edits the final gate's);
`_render` - `Job.render_all`; `_description` - `_finish`, `tests/test_v83.py`; `anchor_shots` - `anchors_for`, `tests/test_v82.py`;
`path.plan_report` - `p_camera_path`; `await_approval`, `review_needed` - `_finish`; `hold_review` - `contract._answer`; `inside_of` -
`sweep.one` and the two tests of round 1's change 3; `_for_format` - `instructions`; `reaction_shots` - `room.plan_shots`; `_gemini` -
`ask`, `ask_video`, `ask_vision`, `selftest`, one test; `_claude` - `ask`, `claude_both`, `haiku_repair`; `_claude_body` - `_claude`,
`ask_batch`, `prewarm`, `simulate_claude` (every new argument has a default: no caller moves); `ai_estimate_inr` - `costguard.ladder_level`,
`preview_cost_flags`, `CacheManager.rows`, `write_ai_summary` (all four read the higher estimate while the floor is on: intended, 3.8);
`manage.tick` - `cli.main`, the rehearsal, `sweep.release_of`, two tests; `motion.plain` - `carry`, `covers`, `place`, `room_s`;
`vision_indexes` - `vision_check`; `reuse_runs` - `full_check`; `hours.translate` - `hours.tick`; `opening.manifest` - `opening.fetch`;
`preflight.run` - `preflight.check`; `notify._ensure_handlers` - `answer`, `expire_defaults`; `costguard.lines` - the estimate's twelve readers.
THE GRAPH'S "tests for" lists are not a list of what pins a function (from none to 414 tests a function - 400 for `_finish`: every test
that reaches it by any road): the pins of correction 6 were found by searching the test files for the call texts.

### The three places attacked hardest across the rounds, and what was found there
(1) EVERY ROAD ON WHICH THE FLOOR REFUSES NOTHING (his item 73) - found, in the pre-reviews: one failed request made a session void; a
long-thinking look became a paid void; the month's cap closed the floor at the memo's own bound; the eye's default failed once and was
never tried again; in the record: with the organisation off the paid jury held nothing (`floor.plain`). Each now has its rule, its test
and its break, and the roads that remain are named in rupees and in videos under THE WORST VIDEOS.
(2) HIS OWN WORDS, FROM THE CELL TO THE FILM AND THE DESCRIPTION - found: a changed digit passed the check; the trial's name chip stood
over his sentence; the Director and the continuity judge were handed his line; a model translated it in six languages by default; the
quality control rated the film's last picture against his words. Now the check compares the voice's own unit texts, and every step that
reads a still's type, prompt or words skips his shot by name.
(3) EVERY REQUEST THAT BUYS A PICTURE OR A CLIP UNDER THE NEW RULES (the audit's lesson) - found, in round 1: the viewer's own place asked
without the film's look, a repaired scene handed the word "google" as its picture's address, a third request of the repair that no rule
named; in round 2: the fall-back's last sentence can be cut (correction 3).

### For the finishing pass - where a typist is most likely to drift from the memo, to be read first in the diff
`anim.picture_request` (the order lock, look words, `NOBODY`; the three joins; a staged scene byte for byte) and `clip_request` (the motion
sentence only where the shot carries a `path` mark and does not hold it); `scene_picture` (the address None; `anim["frame"]`; road 1 inside
the loop's own try); `path.mark` (footage becomes a picture BEFORE `first` is chosen; a `maker` shot is never `first`); `p_format_ending`'s
three clauses from the two cells and `inside_of`'s `rsplit`; `floor.run` (the log read OUTSIDE the try; one try from rule (3) on; the
viewing filed before the looks and removed again on a void) and `ask_watch`'s three kinds of failure counted by what was PAID;
`floor.session` as the ONE writer of tab `Floor_Log`; `maker.attach` / `mark` (append, never replace; `su` for the Director and the
continuity judge) and the list (a) to (d) of 3.3; `story.align` (the same object back; `words` never cut); `hours.translate` (his
paragraph out before the model, back byte for byte); every "byte for byte with the switch off" backed by a comparing test; each entry of
`OLD_VIEW` added in the step that adds its cell.

### The reading of round 2
The diff e50d6fb..8e079c2 of `BUILD_STATE.md` whole (from a file, never a shortened output) and each changed passage in its place; open
issue 207; of 7e83001: `atmosphere.py` 205 to 219, `room.py` 443 to 450, `ladder.py` 14 to 16, `formats.py` 112 to 117, `episode.py` 668 to
694 again, `checkpoint.save`, `immersion.pov_prompt`, `data.STYLE_LOCK`, the cells `IMAGE_PROMPT_MAX_CHARS` and `LIGHTING_DIRECTIVE_ON`,
`tests/conftest.py` 15 to 35, `tests/test_v12_inside.py` at its fixtures, `_start`, `_led` and lines 524 to 530; the plan's A11 (h) (commit
f1cdf0f, written during this round) and `02` item 89 whole; for the graph's duty: `tests/test_v12_org.py` 460 to 482,
`tests/test_v12_opening.py` 280 to 287, `tests/test_v12_inside.py` 184 to 190, 953 to 960, 991 to 998 and 1098 to 1108, and the other
source pins named under correction 6. Run: `next.py` (the card; the state's move) and the code graph's `update` and `query` - nothing of
the pipeline.

### USAGE of round 2
At its start (08:38 UTC): weekly all models 35%, weekly Fable 60%, this session's context 41%. When this part was written (08:43 UTC):
weekly all models 35%, weekly Fable 60%, context 45%; after the code graph's duty and correction 6 (08:53 UTC): 35%, 61%, context 55%
(one read of the graph's raw output cost about a tenth of that context: its "tests for" lists are long). The app shows no 5-hour line.
