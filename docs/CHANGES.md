# Changes (newest first). Claude Code adds one dated entry per merged change: what, why, cost, how to switch it off.

## 2026-10-31 v8.9.1 - fixes from the external review
- Fixed 8 confirmed defects (test clip in production, Repair Bot filter, tease lost on failure, Sheets past column Z, Meta posting + Drive privacy, stereo mix, strategy scoring, guest pronoun / hook row). No cost change, no new setting. See REVISION_NOTES v8.9.1 and K78.

## 2026-10-31 · v8.9
- Cinematic look: one locked dark style on every in-video picture and clip (`STYLE_LOCK`), brighter variant for thumbnails. Free.
- Camera: 8-move library, strongest in the opening and before reactions, calm shots livelier too; the Director can suggest a move per still and code validates it (`CAMERA_MOTION`, gentle = old moves). Free, no count changes.
- Living stills: atmospheric motion prompts + a slow push on playback, same count. Free.
- Voices: clearer recipes, no echo in the master, a rotating guest for the Curious One (`GUEST_ROTATION_ON`). Free.
- Each video ends by teasing the next episode, which is then made from that premise (`NEXT_TEASE_ON`). Free.
- Preventive plan check before any picture money; Instagram captions capped at 5 hashtags. Free.
- Change handler: this file, `CLAUDE.md`, change-ready email + one-click Merge workflow (`PR_MAIL_ON`). Free (GitHub Actions).
