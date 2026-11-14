VERDICT: APPROVED
# V2b INSIDE THE FORMAT - design review, round 3 (14 Nov 2026; the same reviewer; rounds 2 and 1 are kept whole below)
Reviewed: the record of V2b as of commit afc9596 (state DESIGN_REVIEW in 6daf11e). The whole difference from round 2's text was read line by line
(82 lines in, 33 out, in `BUILD_STATE.md` only): each of round 2's six changes is in the memo in the words the review gave - `first` on the act's
first picture with its two tests; the `LEAD` / `WHO` patterns of `cta.is_ask` character for character, with the thirty story sentences and the
sixteen asks as test data; F3's pair as 88.9% and the edge passage 61.5%; the raise for a missing first picture in `episode.produce` after the
checkpoint is saved; `growth.rhythm_brief`, F3_WRITER's sentence, the fourth answer of 3.3 (e) and the reworded F3 test; the five small gaps.
Nothing else was changed, and the one commit between the rounds (71a36a8) is a note of where the designer stood. The 22 changes of rounds 1
and 2 are all answered; none was argued.
THE TEN QUESTIONS, ROUND 3: 1 yes; 2 yes; 3 yes - every rule now names a measure code computes, a check that can fail and, where code can
repair, the repair; 4 no (no taste by a model); 5 yes - each limit stands between its own measured pairs (F1 90.9 / 66.7 against 33 to 35 / 0;
F2 60 against 26; F3 88.9 with its edge at 61.5 against 0) and the camera is judged on the render's own record; 6 yes - no new kind of paid
call, at most one still an act inside the stills line, a retry that buys only what is missing; 7 yes; 8 yes, each named; 9 the worst video
still let through is one the memo names itself: a lecture with a "you" in every sentence, and pictures of one act that a picture model draws
as two places (open issues 185 and 186: V1c's floor and his eye at the pilot); 10 yes (185 to 188, 190 to 192).
THE THREE PLACES ATTACKED HARDEST ACROSS THE ROUNDS, AND WHAT WAS FOUND THERE: (1) what a line knows about its beat - found that the voice job
never saw a heading, so the whole film would have been one act in one place with every check green; now one function gives every line its beat
and a whole-production test with its own break proves two acts and two places. (2) Whatever DELETES a line or HOLDS a film for an ask - found
twice that ordinary sentences ("Nothing like this has ever happened to you", "Follow me.", "You ring the bell and nobody comes.") were taken
for asks; now thirty such sentences and sixteen real asks are test data, and the rule errs toward the writer. (3) An act's first picture from
the plan to the film - found that it could be merged away, covered by a clip of the act before, sit on a cutaway, run out of budget or fail
to be made; now each of the five has its rule, its test and its break.
FOR THE FINISHING PASS (the same session, or a fresh Fable one; amendment A5) - where a typist is most likely to drift from the memo, to be
read first in the diff: `episode._render` (`prev_img` / `prev_i` set BEFORE the `continue`; `move` read right after ITS OWN `parallax_segment`;
`fallback`); `render.camera_path` (no draw of the old path moved when `sign` is None - the reference frames); `motion.plain` (only `path.first`
added, the block's floors of paid seconds untouched); `cta.is_ask` (the patterns character for character) and `cta.strip` on the reply line
of a two-line ask; the three call sites in `room.py`; `formats.tail` in words, never seconds; the raise in `produce`, not in `_assets`; the
fourth answer of 3.3 (e) used only for what it names; every "byte for byte with the switch off" backed by a comparing test.
WHAT A VIEWER GETS (unchanged since round 1, now with nothing in the design that takes it away again): a voice that talks to him, now, and
never lectures for more than a few sentences; every picture from where he stands; a camera that never backs away or tilts and drifts one way
through a scene; no picture left over from the scene before; one ask in the middle instead of three and no promise of a video that may never
be made; an ending on a question to him; no name tag for people he never sees; one video in five as a walk with one voice. NOT delivered, said
plainly: the continuous camera of item 19 (stills cannot, nine animated minutes cost four times the budget); and everything here has only met
the offline stand-ins - a real writer, a real picture model and his own eye first meet it at the pilot.
USAGE when this round was written: the 5-hour window 16%, weekly all models 5%, weekly Fable 8%, context 56% (at the reviewer's start: 7%, 2%, 4%, 9%).

---
# V2b INSIDE THE FORMAT - design review, round 2 (14 Nov 2026; the same reviewer; round 1 is kept whole below) - ITS VERDICT WAS: CHANGES REQUIRED (six changes, all answered in round 3)
Reviewed: the record of V2b as of commit ce20e49 (state DESIGN_REVIEW in f5a27e5). All 16 changes of round 1 were answered in the memo, none argued.
USAGE when this round was written: the 5-hour window 15%, weekly all models 4%, weekly Fable 8%, context 54%.
CHECKED AGAINST THE CODE AND FOUND TRUE NOW: the beat travels through `_strip_beats` -> `line_beats` -> `parse_script(line_beats=)` (every caller of
`narrate` and `parse_script` is the list the memo gives: `episode.py` 153 and 161, `format_engine._units`, `preview.py` 23, `shorts2.py` 215 and 238,
`voice_lab.py`); the place is the bible beat whose `n` equals the beat; the marks are laid before the Animation Director and `motion.place`; the tail
is one measure in words (205 words: 24.6; 1,275 words: 100); the last spoken sentence is judged whatever its length; `CAMERA_MOTION` "gentle" no longer
reaches a path state; the parallax follows the sign; the record has a key of its own and `rerender_times` rewrites it; every line of
`format_engine.REALITY_ENGINE` the memo quotes exists word for word, and so do the four rewrite orders; GOOD-TRIAL counted by hand through the voice's
own sentence cut = 9 of 15 = 60.0%, run 4 (the sentences from outside in a row: the witness, the two of the foil, "It is not falling, Doctor.").
WHAT IS STILL WRONG - five things in the NEW text, each small, each exact below. Two would reach a viewer or the money: the new ask patterns
delete "Follow me." from every walk and "You ring the bell and nobody comes." from every script (change 2), and a missing first picture would
throw away and re-buy every clip of the video (change 4).

## The ten questions of 5.4, round 2
1. Every part serves a viewer or the scoreboard? YES - the Director is now told (3.2), the sign now moves what a viewer sees.
2. Every word of the owner honoured? YES - the emotion beat is decided (kept in F1 without the courtroom word, none in F3); items 16, 19, 20 as in round 1.
3. Every rule enforceable as written? NO - `first` sits on the act's first UNIT, which may be a cutaway or a graphic (change 1); `is_ask` still
   takes story sentences for asks (change 2).
4. Taste judged by a cheap model, or a model's opinion as a gate? NO.
5. Judged on the finished file, both kinds of pairs? YES for F1 and F2 (GOOD-TRIAL 60% and run 4 against 26% and run 8) - NO for one sentence
   about F3: its second good passage measures 61.5%, not "at or above 65" (change 3).
6. Money? YES for the lines (the stills line carries the guarantee's ceiling) - NO for the retry of change 4, which would pay twice.
7. Reuse of what is ready? YES - `motion.plain` now carries the act break through `room_s`, `covers`, the reservation and `carry`.
8. Changes to what older tests pin, each named? YES - `motion.plain`, `audience.make_still`, `parse_script` / `Unit` / the timeline, `p_living` behind its switch, `ctx["states"]` untouched.
9. The worst video still let through? As written: a walk whose guide's "Follow me." lines are silently cut (change 2). After the changes: the two
   the memo names itself - a "you" in every sentence of a lecture (open issue 185, V1c's floor) and a picture model that ignores the place (186).
10. What only reality can answer is written down? YES - 185 widened to the trial, 191 (four voices and no chip), 192 (asks in words code does not know).

## The changes of round 2 (each is "the memo must ..."; the words to put in are given, so that no third question is needed)
1. `first` IS THE ACT'S FIRST PICTURE, NOT ITS FIRST UNIT (3.2, "THE MARKS COME FIRST" (i)). Typed as written, an act that opens on a three-word
   line of a speaker with approved art (a reaction cutaway: `shotplan.reaction_shots` runs in the plan stage, before `mark`) or - with `INSIDE_ON`
   FALSE and `CAMERA_PATH_ON` TRUE - on a graphic or real footage, carries `first` on a shot that is no still: `firsts` (type still only) is empty
   for that act, nothing guarantees its first still a picture, the still shows the act BEFORE's picture and `camera_shown` holds the paid film.
   Replace "`first`: True on the shot of the act's FIRST unit, else False" by: "`first`: True on the act's first shot whose type is still, living
   or kling when `mark` runs (after `mark` a still may become living or kling - still a picture of its own - never a graphic, footage or a
   cutaway), else False; an act with no such shot has no `first`". Tests: an act that opens on a reaction cutaway (art approved in the test);
   an act that opens on a graphic with `INSIDE_ON` FALSE - in both the act's first still is in `anchors_for` and `camera_shown` passes.
2. `cta.is_ask`: THE NEW PATTERNS STILL DELETE STORY LINES (3.3, rule 2). Typed exactly as the memo gives them and tried (the reviewer's
   scratchpad, `memo_check2.py`): "Follow me." / "Follow me to the roof." / "Now follow me across the road." = comment (`follow (?:us|me|...)` -
   the commonest line a guide on a WALK can say); "The air would hit like a wall." / "Raindrops hit like stones." / "You tap like mad on the
   glass." / "You hit that like a brick wall." = like (the unanchored `(?:hit|tap|press|smash)\s+(?:the\s+|that\s+)?like\b`); "You ring the bell
   and nobody comes." / "You press the bell on the bus." = subscribe (a walk starts at a front door); "Tell your friend to run." / "Send it to
   the moon and it comes back." / "Share it with nobody." / "Pass it on the left, the way you always do." = share; "Comment is useless here." =
   comment. The eight of round 1 are right now. Put these patterns in the memo instead (tried on both lists below: no story sentence taken for
   an ask, no ask missed - `memo_check3.py`):
   `LEAD` as it is; `WHO` = `(?:(?:a|the|that|your|one|some|any)\s+)?(?:friends?|person|people|someone|somebody|anyone|anybody|everyone|everybody|whoever|group chat|family)\b`;
   subscribe: `LEAD` + `subscribe\b` | `\b(?:hit|tap|press|smash)\s+(?:the\s+|that\s+)?subscribe\b` | `\bsubscribe button\b` | `\bnotification bell\b` | `\b(?:don't forget|remember|make sure)\s+(?:you\s+)?to\s+subscribe\b`;
   like: `LEAD` + `(?:like this video|leave a like|drop a like|give (?:it|this) a like)\b` | `LEAD` + `(?:hit|tap|smash)\s+like(?=\s+if\b|\s*[.!,;]|\s*$)` | `\blike button\b` | `\bthumbs?[- ]up if\b`;
   share: `LEAD` + `share (?:this|the) video\b` | `LEAD` + `(?:share|send|forward|text|pass)\s+(?:this|it)(?:\s+video)?\s+(?:on\s+)?(?:to|with)\s+` + `WHO`;
   comment: `\bin the comments?\b` | `LEAD` + `(?:leave a comment|drop a comment|comment (?:down )?below)\b` | `LEAD` + `follow (?:us|me) (?:on|for)\b` | `\bfollow (?:the channel|for more)\b`.
   A bell alone is never an ask ("So hit the bell." leaves the MUST list: a doorbell and a bus bell are bells; the pools' own lines are
   recognised by rule 1). TEST DATA, to be added to the eight - MUST NOT be an ask: "Follow me to the roof." / "Follow me." / "Now follow me
   across the road." / "The air would hit like a wall." / "Raindrops hit like stones." / "You tap like mad on the glass." / "You press like
   you mean it, and the door does not move." / "You hit that like a brick wall." / "Hit like a hammer, the wind takes the door." / "Tell your
   friend to run." / "Then tell your friend and watch him laugh." / "Send it to the moon and it comes back." / "Send it to your mother." /
   "Text it to your sister and it arrives yesterday." / "Share it with nobody." / "So share the last of the water." / "Pass it on the left, the
   way you always do." / "Comment is useless here." / "You ring the bell and nobody comes." / "Ring the bell. Nobody comes." / "You press the
   bell on the bus." / "Hit the bell on the counter and it floats away." MUST be an ask: every line of both pools (rule 1); "Subscribe for
   more." / "Please subscribe." / "Don't forget to subscribe." / "Hit the subscribe button." / "So tap like." / "Hit like if you would have
   survived that." / "And smash that like button." / "Send this to the friend who would try it." / "Send it to a friend who asks what if at
   dinner." / "Share this video with someone who would panic." / "Share it with one person." / "Forward this to someone curious." / "Text
   this to your group chat." / "Tell me in the comments what you would do." / "Drop a comment below." / "Follow us for more."
3. F3'S GOOD PAIR: THE FIGURE THE MEMO ASKS FOR IS NOT THE FIGURE IT GETS (3.1, "THE LIMITS, EACH BETWEEN ITS OWN PAIRS"). Counted: GOOD-1 with
   every [SKEPTIC] line removed = 8 of 9 = 88.9%, run 1; GOOD-2 with every [SKEPTIC] line removed = 8 of 13 = 61.5%, run 4. "They must stand at
   or above 65" is false of the second, and the next sentence would stop the build on it. Replace "- the builder measures and writes the two
   figures; they must stand at or above 65" by: "= **8 of 9 = 88.9%, run 1** (its good passage) and **8 of 13 = 61.5%, run 4** (its EDGE
   passage: a walk that ends on four sentences of explanation passes the floor of 60 by 1.5 points and the run limit at the limit - that is
   what the floor is for); bad: BAD-1 (0%, run 8)". The floor 60 and the run limit 4 stand between 88.9 and 0, with the edge on record.
4. A MISSING FIRST PICTURE MUST NOT COST THE VIDEO ITS CLIPS (3.2, "WHEN AN ACT'S FIRST PICTURE CANNOT BE MADE"). "`_assets` treats it as
   required - ... raises the RuntimeError the 15% rule already raises" - that rule does not raise inside `_assets`: it raises in
   `episode.produce` AFTER `CK.save(out, ep, "assets", {"assets.json": _assets_state(files)})` (lines 639 to 641), which is why its message can
   say "the pictures that worked are saved". A raise typed inside `_assets` loses every picture and every clip of that run - the animated
   scenes are the dearest thing a video buys - and the retry pays for all of them again. Replace the sentence by: "`_assets` reports it as it
   reports every missing picture (`files["missing"]`); in `episode.produce`, beside the 15% rule and AFTER the same `CK.save`, a missing
   picture of a shot with `path.first` raises the same RuntimeError ('act A's first picture could not be made - not rendering a film that
   opens an act on another act's picture; will retry (the pictures that worked are saved)')". Test: after the raise `assets.json` holds the
   pictures and clips that were made, and the second `_assets(have=...)` buys the one missing picture and nothing else (the paid-call counter).
5. THE F3 TEST OF 3.3 (d) ASKS FOR WHAT (a) TO (d) DO NOT BUILD. "Its writer's, bible's and critic's prompts hold neither 'SKEPTIC' nor 'two
   roles' nor 'Curious One'" cannot pass: `prompts.BIBLE` asks every bible for `"presenters":{"director":..,"skeptic":..}` and for `"cta"` lines
   "spoken by the Curious One or the Director"; `growth.rhythm_brief` puts "REACTIONS: n short Curious One reaction lines" into every writer's
   brief; the definitions of `data.py` that reach the writer through `defs` name the Curious One (the hook "wrong_guess", the rhythm
   "RB5_case_file", the engagement "guess_first"; the banter ones are answered by "none (one voice)"); `immersion.writer_rules` says "the guest
   reacts PHYSICALLY" and gives the example line "[SKEPTIC] [tension] {slow, low, whisper, breath}". None is a trial's sentence and none is true
   of F3, so by (e) each would be a `DESIGN QUESTION` - six of them, foreseeable today. The memo must put in: (i) `growth.rhythm_brief`: in a
   format with one voice the clause "REACTIONS: ... Curious One reaction lines." is not sent (a test); (ii) `F3_WRITER` gains, before "END ON
   THE ARRIVAL": "Where any rule, definition or example above names the Curious One, a guest, a second role, banter or a reaction line, it
   does not apply to this episode: the guide speaks alone."; (iii) (e) gets a FOURTH answer: "a strategy definition, a JSON key or an example
   that names the second voice (`data.py`, the bible's `presenters` and `cta` keys, `immersion`'s example line): left as it is in this batch,
   overruled by F3_WRITER's sentence, listed in the record and in open issue 187", and its search list gains `data.py` and `tableread.py`;
   (iv) the test of (d) reads: "a whole F3 production makes NO paid call of the role `format`; its writer's prompt holds F3_WRITER's sentence
   of (ii) and none of the lines (c) and (d) remove, nor 'Curious One reaction lines'".
6. FIVE WORDS A TYPIST CANNOT GUESS. (a) 3.6, issue 129: `hook_line` must be what `opening.fetch` calls the hook - the FIRST UNIT of the Short's
   own timeline with its brackets removed - made by ONE function both use, never `formats.short_lines(sc)[0]` (a first line may hold two
   sentences: the writer would be handed more than `hooks.apply_to_script` compares with, and the hook would be said twice). (b) 3.3, "THE LAST
   LINE": `last` is judged after its trailing spaces and closing quotes or brackets are removed (`.rstrip(" \"')]")`, as `short_kept_report`
   does): 'Would you keep it?"' ends on a question. (c) 3.2, check `camera_path` rule 3: say in words what it does with a picture that
   carries no `pov.angle` at all (`IMMERSION_ON` or `POV_VARIETY_ON` FALSE, or `v91.guard` switched the step off for this episode): judged
   only where an angle was assigned - the place sentence still asks for eye level - with the PASS words then "angle not assigned by code".
   (d) 3.3: where `removed` lives between the room and the gate: `d["asks_removed"]` = {kind: count}, written by the three call sites.
   (e) 3.9: step 2 cannot hold 3.3 (d) (F3 is not switched on before step 5) nor the `path.on()` half of 3.3 (c) (`path.py` is step 4): (d)
   belongs to step 5 and the path half of (c) to step 4 - say so in the two steps.

## What round 2 attacked hardest
(1) The new `is_ask` - the memo's patterns typed and run on 27 story sentences and 10 asks: 18 story sentences were taken for asks (change 2).
(2) The marks before `motion.place` - traced through `reaction_shots` (plan stage), `open_acts`, `anim.apply`, `motion.place` (`plain`, the
reservation of a scene's lines, `covers`), `merge`, `carry` and `_render`'s `prev_img`: sound, except where `first` lands on a shot that is not a
picture (change 1). (3) The beat's travel - `line_beats` gives one beat per line of `clean`, `parse_script` enumerates the same lines
(`splitlines` of a text joined with "\n" from `splitlines`), a unit carries its line's beat, `inside.sentences` reads the same parser: sound.

---
# V2b INSIDE THE FORMAT - design review, round 1 (14 Nov 2026) - ITS VERDICT WAS: CHANGES REQUIRED (16 changes, all answered in round 2)
The reviewer: a fresh Fable 5.2 session (Effort High) that did not write the memo (the plan's 5.4, AMENDMENTS 1 AND 2, session 2 of the chain).
Reviewed: the record of V2b in `BUILD_STATE.md` (steps 1 to 3) as of commit 58c6167, base 5827d97.
Read for it: the plan whole; the handoff `CLAUDE.md`; `02` whole; the redesign 4.1, 4.6, 10.7, 11.4, 11.10 with its end notes; in `BUILD_STATE.md` the head
line, the standing rules, the owner's verdict, NEXT down to "what V2d-b leaves ready", the whole record of V2b, open issues 60, 69, 74, 75, 77, 101, 124,
125, 129, 177, 185 to 190; and the code: all of `formats.py`, `org/audience.py`, `org/layman.py`, `enforce.py`, `cta.py`, `shotplan.py`, `immersion.py`,
`overlay.py`; `room.py` (`run_room` to `ensure_tease`, `_director_extra` to the end); `episode.py` (`_stage_plan`, `anchor_shots`, `_assets`, `Job`, `_render`,
`produce`, `_strip_beats`); `render.py` (the camera library, `parallax_segment`); `motion.py` (`merge`, `place`, `carry`); `voice.py` (`parse_script`, `narrate`);
`contract.py` (`p_asks`, `p_tease`, `p_living`, `p_format_kept`, the table, `run`); `prompts.py` (BIBLE, WRITER, DIRECTOR); `engage.py` (`brief`);
`format_engine.check_script`; `hooks.run_hooks`; `ladder.enter` / `pitch`; `truth.unread_settings`. The memo's four passages were counted with the repo's
own regexes (a read-only script in the reviewer's scratchpad; nothing of the pipeline was run).
USAGE: at the start the 5-hour window 7%, weekly all models 2%, weekly Fable 4%, context 9%; when this file was written 10%, 3%, 6%, context 45%.

IN ONE PARAGRAPH: the design is the right one (D: the inside of a format is data that code executes) and most of it can be typed as it stands. But
six sentences of the memo are not true of today's code, and typed as written they give the opposite of what the batch is for: the whole film
becomes ONE act in ONE place and every check passes (change 1), each act is given the NEXT beat's place (2), ordinary story sentences are deleted
from the script as "asks" (4), every offline F1 film fails its own ending check (5), and a writer is told to open on the word "you_pov" (12). A
typist that decides nothing would type exactly that. Nothing below asks for a new rule; every change makes a rule of the memo true or typeable.

## The ten questions of 5.4
1. Does every part serve a viewer or the scoreboard in a way a layman could name? YES, with two parts that are machinery until a picture proves them -
   the place sentence in front of a prompt (the Director who writes the picture is never told the place: change 10) and the `sign` that `camera_shown`
   compares with the plan it came from (true only once the parallax side follows it: change 9).
2. Does it honour every word of the owner that touches it? NO - item 16 ("so many stats", "no audience feel", the name label) and item 19 (first person,
   layman) are served; item 19's "continuous camera" is honestly narrowed (CHANGED FROM THE REDESIGN 1); but open issue 74's EMOTION BEAT - a scope line
   of NEXT's "V2b's scope" - is not in the memo at all, and `engage.brief` still tells every F1 and F3 writer to use audience prompts and to place the
   emotion beat "just before the verdict" (change 13); items 12, 14, 15 (hard enforcement) fail where a check passes on a film that is one act (change 1).
3. Is every rule ENFORCEABLE as written? NO - six are not: the unit's beat (1), the place of an act (2), an act's first picture on screen (3), the ask
   recogniser used to delete and to hold (4), the ask-free window on a short film (5), the last line (6); and the camera rules under `CAMERA_MOTION`
   "gentle" and after a re-render (7, 8).
4. Does any rule judge TASTE by a cheap model, or let a model's opinion gate a video? NO - every measure is a regular expression, a count or the render's
   own record; designs B and C were refused for exactly that reason.
5. Is each measure judged on the finished file / the render's record, and does each new limit have BOTH kinds of measured pairs? NO - `camera_shown`
   reads the record (good), but the record goes stale after `Job.rerender_times` (8); the floor of F1 has both pairs, with hand counts that are wrong
   (change 14: GOOD-1 is 10 of 11, GOOD-2 is 10 of 15 = 66.7%); the floor of F2 (30) and the run limit 4 for a four-voice trial have NO good trial
   passage, and 30 lies under the 40 the memo itself calls bad (change 15).
6. Money: is every new paid second or call a line, inside Rs 5,000? YES for what the memo names (no new call; the writers' fix rides in the one
   `writing` line of `costguard.lines`) - and NO for two things it does not name: in F3 `room.format_pass` makes a PAID fix call, twice a video,
   that asks for the second voice the format forbids (change 13), and "never beyond the budget" for an act's first picture trades a still of
   under Rs 1 for a held video (change 11).
7. Does it reuse what earlier batches left ready? YES for the pattern (`audience` / `layman`: a pure measure, the ONE fix, the check; `segmeta`; the
   format row) - NO for the one warning of the brief's READY line: "`place` decides WHICH stills move - a camera-path rule that wants a say goes
   through it or runs before it". `path.lay` runs AFTER `motion.place` and has no say (change 3). And it writes a second speaker parser beside
   `voice._peel` (change 14).
8. What does it change that an OLDER test or check pins, and is each change named? PARTLY - named: `OLD_INSIDE`, the three shares, `kept_report`,
   `p_tease`, `p_living`, `prompts.WRITER` byte for byte for a trial. NOT named: `ctx["states"]` is a list of 5-tuples that `p_visual_change` unpacks
   (`for a, b, typ, clip, short in ...`) - four more fields "inside" it break that check; `audience.shape`'s inner helper `still` (PROTECTED file) must
   be lifted to be reused; `voice.parse_script` / `Unit` / the timeline entry change for every caller of `narrate`; `p_living`'s chip rule must be
   silent with the switch off or every older test with a speaker tag turns red (change 16).
9. The worst video this design could still let through, and which check holds it? AS WRITTEN: an F1 film that is one act - every picture prefixed
   with ONE beat's place (beat 0 + 1: "your bathroom"), under a story that goes from the bathroom to the street to the planet - passes `camera_path`
   ("1 acts in 1 places") and `camera_shown`; nothing holds it (changes 1, 2). AFTER the changes: a lecture with a throwaway "you" in every sentence ("as you know,
   gravity is ...") passes `viewer_inside` at 100% - the memo says so itself and hands it to V1c's floor (open issue 185): accepted, it is said.
   And a Director whose own prompts name five places inside one act passes on the prefix - open issue 186; change 10 narrows it for the price of a paragraph.
10. What can only reality answer, and is it written down for the pilot? MOSTLY - 185 to 188 and 190 are right. MISSING: a trial made without approved
   cast art now has four voices, nobody on screen and no chip - can a viewer tell who speaks (his ear at the pilot); the floors and the run limit of
   F2 (185 names F1 and F3 only); whether `kind_of_text` meets a real script without deleting a story line (change 4 makes it a test first).

## The changes (each is "the memo must ..."; ordered by what a viewer would suffer)
1. THE UNIT'S BEAT - the sentence about `voice.py` is false, and the batch stands on it. `episode._stage_plan` hands `narrate` the script AFTER
   `episode._strip_beats` removed every line that starts with "##" (lines 150 to 153 and 160 to 161); `voice.parse_script` never sees a heading (if it
   did it would SPEAK it: `_peel` strips the "#" and keeps "BEAT 2"). A counter typed "where the script is cut into units" counts nothing: every unit is
   beat 0, `path.acts` is ONE act, every picture of an F1 or F3 film gets ONE place, and `camera_path` and `camera_shown` both PASS. The unit test the
   memo asks for ("a unit knows its beat") would pass on a script with headings while the production strips them first. (`_strip_beats`' own `marks`
   cannot be used either: they count LINES and are used as unit indexes, and a line of three sentences is three units.) The memo must say exactly
   how a unit learns its beat - the function, who passes what (both `narrate` calls of `_stage_plan`, and every other caller of `narrate` and
   `parse_script` found by search with what it passes), that a heading is never spoken, that `reactions.ensure_units` and `audience.breathe` keep
   the field - and must demand on a WHOLE F1 production: the units carry at least two different beats, the PASS words of `camera_path` name at
   least two places, two pictures of different acts carry different place sentences; and a deliberate break ("the heading never reaches the
   counter") that this whole-production test catches.
2. THE PLACE IS OFF BY ONE. 3.1 says a heading "raises `act` by one (act 0 before the first heading)", so the units under "## BEAT 1" carry 1; 3.2
   takes "the bible beat whose `n` equals the act's first beat + 1" = beat 2 (`prompts.BIBLE`: `"beats":[{"n":1,...}]`). Every act would be told the
   NEXT beat's place and the last act none. (`hooks.apply_to_script` puts the hook AFTER the leading heading, so no unit sits before it.) The memo
   must give one convention - best: the number written in the heading when it has one ("## BEAT 4" is 4: a real writer may skip or merge a beat),
   else the headings counted from 1, 0 before any - and `place_of` = the bible beat whose `n` EQUALS it; with a test on the offline bible that the
   act under "## BEAT 1" gets beat 1's `visual_world`.
3. AN ACT'S FIRST PICTURE CAN BE PAID AND NEVER SHOWN - then `camera_shown` holds a finished, paid film. "Since the first still of every act then
   has a picture of its own, the nearest earlier picture of any later still of that act is a picture of that act" is false twice. (a)
   `motion.merge`: a line shorter than `UNIT_MERGE_SEC` (1.0 s: "Step outside.", "Look up.") gets no picture state - `_render` `continue`s BEFORE
   `prev_img` is set (lines 433 to 436), so the stills after it show the act BEFORE's picture. (b) `motion.place` runs BEFORE `path.lay` and knows no
   act: a scene reserves, and a living clip covers (`room_s`, `covers`, `carry`), the plain stills that follow - also the first still of the NEXT act;
   covered whole it is merged away the same way, and the viewer hears the new act over the old place. The memo must decide and write, with a
   test for each case (a 0.6 s first line of an act; a living clip bought on an act's last line) and a break: what the film shows on an act's first
   line when that line is merged or covered, and how the act's own picture still becomes the picture its later stills show (for example: the acts
   are computed BEFORE `motion.place` - they need only the units - `motion.plain` is false for an act's first picture so that no clip runs into it,
   and `_render` takes `own` as `prev_img` / `prev_i` before its `continue`). The brief's READY line said it: a camera-path rule that wants a say goes
   through `place` or runs before it.
4. THE ASK RECOGNISER DELETES STORY LINES. `cta.kind_of_text` was written to decide whether an ask is already there - a wrong yes cost nothing. 3.3
   uses it to DELETE lines (`cta.strip`, three call sites) and to HOLD a video (`format_ending`'s window). Measured on ordinary first-person
   sentences: "Nothing like this has ever happened to you." = like; "You have never felt anything like it." = like; "Would you like it to stay?" =
   like; "You send it spinning across the room." = share; "You want to tell your friend, but your phone is floating too." = share; "You cannot share
   it with anyone." = share; "You text it to your sister." = share; "Your newspaper subscription is the last normal thing left." = subscribe. In F1
   (keep subscribe) and F3 (keep nothing) each such line would be cut out of the narration without a word - the lesson of V1b and V2c-a, in a
   function that removes. And what F3's own brief forbids ("comment or follow") is NOT recognised: "Tell me in the comments what you would do."
   = None. The memo must define the recogniser that `strip` and the window use - exact patterns, so narrow that a line is an ask only when code can
   RECOGNISE one (a line the code itself inserted from `POOLS` / `TRIAL_POOLS`, or an imperative to like, subscribe, share or comment) - give
   the eight sentences above as test data that must survive `strip` and must not fail `format_ending`, say what happens to the second line of a
   two-line ask ("Please don't call it democracy." left alone is a reply to nothing), and limit `overlay.CtaChip` to `formats.asks()` when
   `ENDINGS_ON` (today a LIKE chip would pop up over "nothing like this" in a film that asks for no like).
5. THE ASK-FREE WINDOW SWALLOWS THE CODE'S OWN ASK. `cta.ensure` puts F1's subscribe ask at 65% of the lines; `format_ending` forbids any ask in the
   last `ENDING_FREE_S` = 40 SECONDS. On an offline film (75 to 105 s; the memo's own example is 82 s) 65% is second 53 and the window starts at
   second 42: every F1 film of the tests, the rehearsal and the sweep fails `format_ending` by the memo's own arithmetic, and the builder would have
   to choose between moving the ask and shrinking the judge (L7). "Outside the tail" is true of `strip`'s 12% of LINES, not of the check's 40 s.
   The memo must give ONE definition used by both (for example: the last `min(ENDING_FREE_S, 12% of the voice's length)` seconds, on the units'
   own start times - units, not script lines, carry times), show the arithmetic for 82 s and for 510 s, and say that what `strip` leaves and
   `ensure` adds can never fail the check (a test).
6. THE LAST LINE RULE HOLDS GOOD ENDINGS. It judges the last COUNTED sentence (four words or more) and wants the word "you" inside it. "Would you?",
   "Keep it?", "Would you stay?" (three words) are not counted, so the sentence BEFORE is judged and a film that ends on the very question the
   format asks for is held; "Keep it, or give it back?" has no "you" and is held. The same for F3's arrival ("You're home."). The memo must
   judge the last SPOKEN sentence whatever its length, and look for the viewer in the last spoken line (or its last two sentences), with those
   four endings as tests that pass and "Subscribe for more." / "Next simulation: ..." as tests that fail.
7. `CAMERA_MOTION` = "gentle" IS A LEVER OF D6 (`levers.LEVERS`, `registry` D6) - a ticket can set it. Then `parallax_segment` returns through
   `_parallax_v87` before `pick_move`: the move is drawn from push / pull / pan_l / pan_r / rise / drift with a random side, `_LAST["move"]` stays
   None, and EVERY F1 and F3 film fails `camera_shown` ("move not in path.MOVES") after its pictures are paid. The memo must say what a path format
   does under "gentle": the older mover takes `sign` and a pool too and records its move, or the lever is refused / ignored for a path format, or
   the check says NA with its reason - one of them, with a test.
8. THE RECORD MUST STAY TRUE AFTER THE RENDER. (a) `Job.rerender_times` (the fix for a black or frozen stretch) re-draws a still with
   `parallax_segment(..., detail=True, focus="center")` - no sign, no pool - and leaves `segmeta` as it was: the film may show a `pull` while the
   record says `drift`, and `camera_shown` passes on the stale line. (b) A segment that fell back (`drawn_` False: `graphic_segment` on the picture)
   would be recorded with the PREVIOUS segment's move. The memo must give `rerender_times` the state's sign and pool and make it rewrite `move`,
   record "" for a fall-back state and say what `camera_shown` does with it, and name where the four fields travel: NOT inside `ctx["states"]`
   (5-tuples that `p_visual_change` unpacks, and None when the motion ladder is off) - a key of their own.
9. "ONE DIRECTION OF TRAVEL" IS NOT WHAT `sign` DOES YET. In `camera_path` the side of the depth parallax is a second, independent draw
   (`par_px = sw * par * rng.choice([-1, 1])`): on `push_parallax`, `orbit` and `whip_settle` the near things slide left or right at random whatever
   `sign` says; `push_parallax` and `handheld` have no sideways travel at all. The memo must make `par_px` follow `sign` when one is given (and keep
   every draw of the old path byte for byte when it is None - the reference frames), and write the two pool expressions exactly: with a pool the
   high-energy choice is `[m for m in MOVES_HIGH if m in pool and m != avoid]`, the calm one the same over `MOVES_CALM`, the fall-back
   `list(pool)` minus `whip_settle`, never `list(MOVES_CALM)`; a suggested move outside the pool is refused.
10. THE DIRECTOR IS NEVER TOLD. The picture's words are the Director's (`prompts.DIRECTOR`, `immersion.director_rules`): "concrete subject, camera,
   lens", "extreme wide lens, motion blur", `"pov": eyes|object|hands|helmet|vehicle|ground`, `camera` = ... pull | kb_roll. The memo puts "ONE
   PLACE FOR THIS ACT: ..., seen at eye level." in front of a prompt that may go on "aerial view of the city, 14mm" - the picture model gets two
   orders and the check reads only the first. The memo must add, word for word, a paragraph to the Director's brief in a "path" / "walk" format
   (where `_immersion_notes` is; `formats.block("director")` or `path.director_rules()`): every picture from the viewer's own standing height, never
   from above, from outside or from an object; every beat stays in the place its `visual_world` names; no `pull`, no `kb_roll`; and say what the
   three animated scenes' motion sentence is in a walk ("camera mounted on the moving object, accelerating, shaking" is today's, in every format).
   A test: the Director's prompt of F1 and F3 holds it, a trial's does not.
11. AN ACT'S FIRST PICTURE IS A GUARANTEE, NOT A SHARE OF WHAT IS LEFT. `firsts` taken "`[:left]` ... never beyond the budget" means: when the opening
   shots have used the budget (`left` is `d["stills"]` after `_apply_tier`, and the opening is taken first), an act's first still gets no picture,
   `camera_path` rule 2 fails, and the video is held before a rupee is spent for want of a still of under Rs 1 - a hold no rewrite repairs.
   `anchor_shots` already knows two such guarantees ("whatever the budget says": the first still, the first still after the footage) and a
   repetition guard that adds up to twelve. The memo must make `firsts` one of them, say the worst case in 3.8 honestly (at most one still an
   act: under Rs 15 a video at the allowance of 13 changes; usually none), give `anchors_for` its real arguments (the units are not in `S_`), and
   say what happens when an act's first picture fails twice to be made (today up to 15% of the pictures may fail and the film goes on).
12. THE SHORT'S HOOK IS NOT ON THE LADDER ROW. `ladder.enter` writes `"hook": rec.get("hook")` and `shorts2` fills it with `arch` - the NAME of the
   hook archetype ("you_pov", "countdown"). The spoken line lives only in the footage archive (`opening.fetch` -> `man["hook"]`), which is fetched in
   the plan stage AFTER the room, and the draw's ladder id is set after the room too. Typed as written ("whose hook the ladder row holds ... the
   builder names the reader") the writer is told: begin "with exactly this line, word for word: \"you_pov\"". The memo must say where the room
   gets the spoken line (the archive fetched before the room for the pitch `ladder.pitch()` returns, or the line kept on the row from now on with
   the older rows falling back to today's insert) and demand a test that builds the ladder row the way `shorts2` / `ladder.enter` really do.
13. THE OTHER PLACES THAT STILL DEMAND AN ASK, THE EMOTION BEAT AND A SECOND VOICE. "The asks are demanded by the writer's base prompt" is half the
   truth. Found by search, each needs a line in the memo: (a) `engage.brief` (in every writer's brief through `_writer_extra`): "AUDIENCE PROMPTS:
   use at most two ... comment, predict, take a side or share with a friend" - beside F3's "NO ASK" and F1's "no share ask"; and "EMOTION BEAT ...
   in act 3 or just before the verdict" - a courtroom word in an F1 / F3 brief, and the emotion beat is a scope line of issue 74 that the memo
   neither builds nor decides (a scope line is never dropped silently: the plan's chapter 12); (b) `prompts.FACTFIX` and `room.oc_rewrite` tell the
   rewriter to keep "the three audience asks"; (c) `format_engine.check_script` (`FORMAT_GATE_ON`): in F3 "one role barely speaks (DIRECTOR n,
   SKEPTIC 0)" is true of EVERY script, so `room.format_pass` pays for a fix that asks the writer to "make the Curious One question assumptions"
   - at both of its call sites - and `FE.instructions` tells the writer, the bible and the critic about "the two roles"; `prompts.WRITER` says
   "Banter style between the two roles". The memo must list every such place (search "SKEPTIC", "Curious One", "two roles", "three audience
   asks", "verdict") and say for each what F1 and F3 get; at the least `check_script` asks the format's row for its voices, with a test that an
   F3 production makes no paid `format` call for a missing second role. Open issue 187 is not an answer to a paid call that fights the format.
14. THE VOICE MEASURE: ONE SPEAKER PARSER, AND THE TRUE FIGURES. (a) "`speaker` = the label of the line" is a second parser: `voice._peel` and
   `parse_script` know the aliases ("[THE CURIOUS ONE]", "**Skeptic:**"), a label alone on its line that belongs to the next line, and two speakers
   on one line. A foil line under "[CURIOUS ONE]" would count as the guide's, its "I" would not count, and a good F1 script could fall under its
   floor for its label style. `inside.sentences` must take its speakers from `voice`'s parser. (b) The four passages must be given line by line
   (GOOD-1 is printed as one paragraph with five labels in it: as ONE line every sentence is the first label's). (c) The hand counts are wrong -
   measured with `layman._SENT` / `_TOK` and the memo's `YOU` / `ME`: "The ceiling arrives slowly." has FOUR words and is counted (outside);
   GOOD-1 = 10 of 11 = 90.9%, longest run from outside 1; GOOD-2 = 10 of 15 = 66.7%, run 4 (it clears the memo's own bar of 65 by 1.7 points,
   not by 6.4); GOOD-2 with the fifth sentence = 10 of 16 = 62.5%, run 5 - fails (b) alone, as said; BAD-1 = 0 of 8, run 8. The memo must carry
   these figures. (d) Rule (c) must say what an act with NO inside sentence at all is (BAD-1 is one: its "because" sentence comes before a first
   inside sentence that never comes) - it fails, said in words; and "fewer than 8 counted sentences is not judged" must say that 8 is judged.
15. F2'S LIMITS HAVE NO GOOD PAIR. Question 5 of the review: both kinds of measured pairs before a limit. For a trial there is one bad figure (the
   offline trial: 26%, a run of 8) and no good one - all four passages are a guide and a foil. The floor 30 lies UNDER the 40 the memo calls bad
   (the offline F1 script, 33 to 35%, would pass it), and "at most 4 sentences in a row from outside" is the same number for one guide's voice and for
   a courtroom of four voices in which a character's "I" never counts. The memo must add a GOOD trial passage written by the designer (a judge, a
   witness, the two leads; measured under F2's rule, its share and its longest run written down), set F2's floor and run limit between that and
   the bad one - a `LECTURE_MAX_SENTENCES` per format if the numbers ask for it - and widen open issue 185 to F2.
16. THE ORDER OF 3.9 AND THE GAPS A TYPIST CANNOT FILL. (a) Step 1 "no behaviour changes yet; the whole older suite is green" cannot be green:
   `truth.unread_settings` refuses a cell no code names (`LECTURE_MAX_SENTENCES`, `ACT_MIN_S`, `PLACE_CHANGES_PER_MIN_MAX`, `ENDING_FREE_S`,
   `V12V2B_MOVE_DONE`, the four switches) and the wiring test refuses the four readers nobody calls yet; the lists may only shrink. Each cell,
   switch, reader and lever must land in the step that first uses it. (b) `p_living`'s chip rule is judged only when `CHIP_DRAWN_ONLY_ON` is TRUE.
   (c) `inside.open_acts` re-uses `audience.shape`'s INNER helper `still`: say that it is lifted to a module function of the PROTECTED file. (d)
   `open_acts` works on the script's beats, `path.acts` on the joined acts: say so. (e) The allowance join: "the SHORTEST remaining act joins the act
   before it" - and when the shortest is the first? (f) A timeline saved before this batch has no `beat` on any unit: both checks NA, not one act
   for the whole film. (g) `teased_pitch` must keep reading the cell: it honours what the video BEFORE promised, whatever the format of this one.
   (h) `path.lay` and the marks: it skips `short`; say in words what it does to a `promise` shot (its prompt is the thumbnail's scene, which may
   be another place) and to an `anim` shot (`anim.start_frame` builds its own start picture), and list by search every step after `lay` that
   reads or rebuilds a prompt.

## The seven attacks asked for beyond the ten questions
(a) Exact enough to type? The arithmetic of 3.2 holds (82 s: max(3, floor(2.05)) = 3, nothing joins; 9 min, 20 headings: 19 changes, allowed 13, six
    join). The passages do not give the stated figures (change 14). Not typeable as written: 1, 2, 5, 8 (where the fields travel), 9 (the pools), 12, 16.
(b) False about today's code: the beat in `voice.py` (1); "the ladder row holds" the hook (12); "outside the tail" for the check's window (5); "the
    nearest earlier picture ... is a picture of that act" (3); "the asks are demanded by the writer's base prompt" as the only place (13); "has three
    words" (14). TRUE as checked: every count of the experiment that code can show without a run - the rotation of angle in `assign_anchors`, `sgn =
    rng.choice`, `pull` and `kb_roll` in the calm pool, `img = own or prev_img`, the three call sites of `CTA.ensure`, `tease_brief` / `ensure_tease`,
    the chip names.
(c) A good video held for a reason the rule does not recognise: 3, 4, 5, 6, 7, 11, 13 (F3), 15. A bad one passed: 1, 2, 9, 10 - and the two the
    memo names itself (a "you" in every sentence; a place that is only a sentence).
(d) Marks: `open_acts` skips `short`, `promise`, `anim` (right); `lay` skips `short` only and rewrites the prompt of `promise` and `anim` shots
    (16 h); `motion.place` treats an act's first still as plain room for a clip (3); a living shot's `buy` is not touched (right).
(e) The order of 3.9: not green after step 1 (16 a); steps 2 to 9 are in dependency order once 1 and 16 are settled.
(f) What a viewer gets, in his words: a voice that talks to HIM, now, and never lectures for more than a few sentences; every picture from where
    he stands instead of five camera heights; a camera that never backs away or tilts and drifts one way through a scene; no picture left over from
    the scene before; one ask in the middle instead of three and a promise of a video that may never be made; the film ends on a question to him;
    no name tag for people he never sees; one video in five is a walk with one voice. What is only machinery until the pilot: "one place" (a
    sentence in a prompt), the walk as a format a real writer has never written, every floor. What he does NOT get, said plainly: the "continuous
    camera" of item 19 - stills cannot do it and nine animated minutes cost four times the budget (the redesign's 10.7).
(g) The worst video: question 9.

## What is sound and should not move
The choice of D and the case built against it; the format row as the one place that decides (four keys, four switches, off = d8101c8); the voice
measured as share, run and "shows before it explains", with the past tense recognised only where code can recognise it and the error given to the
writer; eye level at the source instead of asked of a model; the render record judged, not the plan; no tease the ladder cannot keep (issue 101
decided); a name only for a character who is drawn; one subscribe ask in F1 and none in F3 as the first comparison (H29); nothing new paid; the
honesty of "CHANGED FROM THE REDESIGN", "NOT IN THIS BATCH" and open issues 185 to 190.
