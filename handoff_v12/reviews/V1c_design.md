VERDICT: CHANGES REQUIRED
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
