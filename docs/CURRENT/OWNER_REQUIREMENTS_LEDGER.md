# OWNER REQUIREMENTS LEDGER - Reality Engine ("Reality on Trial")
Single source of truth for EVERYTHING the owner asked for, what was decided, and exactly HOW each point is applied in code.
Read this first in every build chat. Never ask the owner to repeat a point listed here. Updated 10 Nov 2026 (v12 build, batch B2).
Companion files (all in docs/CURRENT): ENFORCEMENT_MATRIX.md (requirement -> code check, test-enforced), SYSTEM.md (what the code does, generated
from the code), CONCEPT.md (the show). Anything in docs/ARCHIVE is history and is never followed.

---------------------------------------------------------------------------------------------------------------------------------------
## A. HOW THE OWNER WANTS THE WORK DONE (standing rules)
1. **Hard enforcement, never "for namesake".** Every agreed requirement and every researched breakout technique must be BUILT and HARD-ENFORCED in
   code (blocks the video, or is built into production), with a test proving it. Researching or "including" it is not done. (10 Nov, emphatic)
2. **Breakout is the primary goal; money second; saving money is NOT a goal.** Savings only matter because they buy more breakout attempts. Every output
   (long video, Short, spin-off) is engineered for breakout ("do or die" urgency, pervasive, every aspect, crazy-level techniques).
3. **Do the maximum yourself.** The owner has 1-2 minutes a day, phone only. Any step needing him is pre-filled and babysat step by step.
4. **Never make him retype.** Track everything already said (this file). He hates repeating requirements.
5. **Brutally honest, sharp, witty.** Say what is not built. Never claim done before tests prove it.
6. **Build in stages; test everything for real;** report faults found and fixed; never break what works; full suite + rehearsal before packaging.
7. **Pipeline strictly structured:** timings, buffers, retries, timeouts, fallbacks; no stale references; no silly faults; nothing that makes him come
   back to repair code during setup with Sonnet.
8. **Writers' room must learn** from research / R&D / the channel's own data every time.
9. **Memo / department idea (owner suggestion):** separate sessions passing structured memos, judged objectively by another session in its role -
   adopted where research supports it (parallel drafting + blind cross-family jury), with cost/timing planned.
10. Mobile replies: answer first, short, minimal formatting.

## B. CONCEPT (decided)
- **Channel:** "Reality on Trial" (brand Reality Engine). Courtroom where a science what-if is on trial. Cast: Inspector Vale (calm noir detective),
  Dr. Grimm (theatrical mad scientist; prototypes always fail), Nana Rosa (blunt grandma judge; verdict opens "Here's what's true"), the Archivist
  (narrator / evidence keeper). Look: Toybox Noir (stop-motion puppet). Owner confirmed this as THE build on 9 Nov after exploring alternatives.
- **Explored and NOT adopted (do not re-propose unless asked):** plain what-if / "who would win"; "Science verdict" packaging tweak; "Sentenced" (real
  nature charged with crimes - "boring"); small-claims court. "CASE FILE: YOU" is parked (viewer-as-victim whodunit, nostalgia/ASMR seasoning, personified
  culprits) was liked as a premise but the owner chose to complete Reality on Trial. Its ideas (personified culprits, sensory first-person cold opens,
  nostalgia texture, rituals, ARG lore) are a possible future upgrade, not current scope.
- **Owner's taste (applies to all writing):** people must RELATE and FEEL ("it happens to YOU", first person, inside the scene, my body); the product
  is a feeling (dread, wonder, scale, awe, shock) with witty relatable humour, never a lecture; weird, mind-piercing titles; edgy, non-monotonous;
  characters to love; a return factor; never one more channel in a crowded pool; avoid AI slop and repetitive templates; appeal to non-science
  viewers too; Tier-1 audiences (US/UK/CA/AU), high RPM, sponsor-ready.
- **Inspiration noted (9 Nov):** Instagram pages Soft Respawn and Zuni HR - first-person nostalgia, "ASMR for eyes and ears". Copy grammar, never IP.

## C. MONEY (decided)
- November 2026: Rs 4,000 approved for the rest of the month on top of ~Rs 1,226 spent -> cap 2026-11 = Rs 5,226 (MONTH_CAP_OVERRIDES, written once).
- From 1 Dec 2026: Rs 5,000/month all-in. No new subscriptions. Stack: Claude API, Gemini (text/image/designed TTS), fal (Kling 3.0 Standard
  `fal-ai/kling-video/o3/standard/image-to-video` $0.084/s; FLUX), ffmpeg, GitHub Actions, Google Sheet + Drive, Cloudflare Worker, WhatsApp, Meta.
- Breakout fund: last month's unspent carries over, capped Rs 1,000, ONLY for breakout follow-ups (ids starting BRK). Owner-approved.
- 90% guard: extras pause (spin-offs, tool tests, Shorts above 1/day), one alert; long-episode money is reserved first.
- Freed money is invested by a ladder (breakout follow-ups -> more hook-test Shorts -> more animated Shorts / quality), each step a WhatsApp card the
  owner can veto; changes undo at month end (re-planner).
- Never cut: packaging tests, accuracy pass, the opening Kling scene, the reserve.

## D. GROWTH / YPP FACTS
- YPP until 31 Jan 2027: 1,000 subs + 4,000 long-form hours (or 10M Shorts views/90 days); from 1 Feb 2027: 8,000 hours or 20M Shorts views.
  Shorts hours do not count. Honest odds: 4,000 h by 1 Feb needs a breakout; base case 8,000 h ~months 8-12. Checkpoint 11 Jan.
- Launch cadence: 4 long + ~1.5 Shorts/day + 2 spin-offs (Case Files countdown, Deep Trial) per month; spin-offs also breakout-engineered.
  Confirmed by the owner on 10 Nov 2026 ("4 a month") and enforced: `STANDARD_MAX_LONG_PER_MONTH` = 4, `PUBLISH_DAYS` = Sat (one a week),
  one-time Sheet move `manage.v12_upgrade`, gate `governor.can_start_episode`; lines for viewers say "every week".
- Owner asked how watch hours work with fewer long videos: long videos + spin-offs earn hours; Shorts are discovery that funnels to long videos.

## E. RESEARCH CONCLUSIONS THAT ARE NOW RULES (and where they live)
| Research point | Rule in code |
|---|---|
| Idea-first: greenlight ideas with >=5x outlier evidence | contract `idea_evidence` (once >=10 outliers collected) |
| Packaging before script; promise contract; promise on screen early | packaging before shots (episode.py); contract `promise_paid` (<=30 s); promise re-aimed after the Animation Director |
| Hook: question / "you" stake by 3 s; hook lab | contract `impact_map` (V1), `hook_lab`, `cold_open` |
| Retention: but/therefore, re-hook <= 75 s, loops close, open on YOU, no lore in 20 s | contract `retention` (hard) + one mandatory fix (enforce.fix_all) |
| Laugh density >= 1/15 s (Shorts 1/6 s); joke tournament (many candidates, strong judges see all) | contract `joke_density`; room2.jokes; shorts2._valid |
| Pause-then-punch 300-700 ms | built into voice timing ([PUNCH] marker -> 0.5 s), measured by `impact_map` (V6) |
| One send moment + one awe peak per video | contract `send_and_awe` |
| Visual change every 2-4 s (Shorts 1-2 s), no overload | built into render (shotplan.pieces_for), contract `visual_change` (V2/V5) |
| No frame reads as a still (parallax, particles) | world particle layer (render.Particles), contract `aliveness` (edge-masked detector, 1080p-calibrated) |
| Blink + breathing + mouth flaps on character shots | living.py (locked expression art + variants), contract `living_characters` |
| Sound: per-world beds, story-tied events, rotation (habituation), ASMR only as touches | sound.worlds / story_events (fresh variants), `impact_map` (V8) |
| Variety: no near-copy of recent episodes | `impact_map` (V9, ordered 10-s signature, 0.97) |
| Flash safety | `impact_map` (V10) |
| Breakout Score >= 80 before upload | contract `breakout_bar` (held, weakest part named) |
| One strong writer + diverse drafts + blind cross-family jury (no role-play memos) | room2.write (3 Opus drafts, Gemini Pro + Flash + Sonnet jury, both orders) |
| Critic keeps the policy-safety gate | room.critic after the jury (v11.1 fix) |
| Writers' room learns: proven/promising/retired techniques | enforce.brain_block in every brief; contracts `brain_playbook`, `no_retired`; brain Thompson sampling (20% holdout) |
| 48-h breakout monitor -> follow-ups | breakout.monitor -> card -> 2 BRK Shorts + sequel premise at the top of the bench |
| Reach data (impressions/CTR) | reach.py (Reporting API channel_reach_basic_a1, daily) |
| Spin-offs: Case Files >= 35% new, loops, verdict variety; Deep Trial monthly | spinoff.py gates G0-G3; deeptrial.py |
| Tool scouting (new models, prices, deprecations) | scout.py weekly (fal catalog + pricing; Artificial Analysis /api/v2/media/*/free) |
| Watchdog clock (GitHub cron can be hours late) | Cloudflare Worker scheduled() + tick concurrency group |
| Uploads private + publishAt early; privacyStatus always explicit | publish.yt_upload (already) |
| One current truth: no retired concept in current docs, CLAUDE.md, module docstrings or prompts (owner, 10 Nov) | whatifs/truth.py (registry of retired concepts + scanner); contract `docs_current`; Plan Guard; tests/test_docs_current.py; SYSTEM.md generated by tools/gen_docs.py |

## F. WHAT IS DELIBERATELY NOT BUILT (honest list)
- A bench of fully rendered backup videos (scripts are pre-produced via Script Preview; failures retry from checkpoints; held videos go to the owner).
- Render sharding across parallel runners (render fits the 6-h job with particles adding ~10 min).
- fal billing reconciliation from billing-events (costs are estimated per call and capped).
- Message-Batches pricing for the v2 writers' room (sync calls; slightly more cost, faster).
- YouTube Test & Compare / end screens / a Short's related-video link (no API exists).
- CASE FILE: YOU premise (parked, see B).

## G. OWNER ACTIONS STILL PENDING (babysit these)
1. Upload: the v12 build lands as ONE pull request (branch v12-organisation -> main) at the end of the build; merge only if Checks are green;
   Wednesday-Friday, never during a render. Until then main keeps running the live code.
2. Cloudflare: paste new worker.js, add Cron Trigger */10 * * * *; dispatch token Actions: Read. Optional AA_API_KEY secret.
3. Character sheets (style board -> masters -> approve) - required for living characters; cast intro approve; WhatsApp setup.
4. First 3 long videos + first 3 Shorts wait for the owner's Approve card.

## H. THE ORGANISATION / BRAIN (owner, 10 Nov 2026 - the defining requirement of the v12 build)
The whole project must function like an ORGANISATION: every department (ideation, planning, research/R&D, review/assessment, creative/writers' room,
packaging, visual production, sound, QA/enforcement, publishing, growth/learning, finance, operations) researches automatically, assesses research
automatically, creates, brings research + creative + owner inputs (current and previous) together in brainstorms, decides the best, writes key
takeaways from every session into one ever-growing KNOWLEDGE PALACE (world-building learnings, knowledge, strategies, plans) that every department
(even execution) reads and writes, learns BOTH WAYS from every other department, sends problem memos back for brainstorm-and-repair, and EVERYTHING
learned, brainstormed or decided is EXECUTED AT CODE-LINE LEVEL and HARD-ENFORCED - tested, rehearsed, executed, re-looped until corrected.
Urgency is do-or-die. Spec: handoff 01_MASTER_SPEC_ORGANISATION_BRAIN.md; plan: 03_BATCH_PLAN.md; progress: handoff_v12/BUILD_STATE.md.
Built so far: B1 truth hygiene (one current truth, enforced).
B2 Knowledge Palace core (`whatifs/org/palace.py`, check `palace_health`): every point of this ledger and every research finding is a Palace item with dated evidence and, where it is enforced, a pointer to the code that enforces it.
B3 memos and the department contract (`whatifs/org/schemas.py`, `memos.py`, `registry.py`, `runner.py`; checks `dept_contract`, `takeaways_written`): every step of the long video that belongs to a department, and the daily learning job, runs LOAD -> ACT -> EMIT -> LEARN -> EXECUTE -> REPORT with a proof per step; memos have deadlines that escalate to the owner; a failed check becomes a problem memo for the department that owns it.
Not built yet (B4-B10): the Execution Engine, R&D and the Review Board, the playbook inside the creative departments' model prompts and cited back, the Council, the repair loop, the learning loop with the Librarian, the Owner Office.
