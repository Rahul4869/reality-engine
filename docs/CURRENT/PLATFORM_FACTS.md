# PLATFORM FACTS (dated; code reads Settings flags, never these sentences)

Each fact: what, since when, source, last checked. When a fact changes, the Guardian/Advisor raises a card and a build updates the matching flag.

| Fact | Value | Since | Source | Checked |
|---|---|---|---|---|
| Uploads from unverified API projects locked to private | **No** (flag `UPLOAD_LOCK`, proven per project by the ₹0 upload check) | 2026-11-02 | YouTube Data API revision history | 2026-11-07 |
| Custom thumbnails for Shorts via `thumbnails.set` | Yes, only after processing has succeeded | 2026-11-03 | YouTube Data API revision history; thumbnails.set reference | 2026-11-07 |
| Public views count from the first frame (incl. autoplay); earnings and YPP use engaged views / engaged watch hours | Yes | 2026-08-24 (announced 2026-08-19) | YouTube blog via vidIQ, RouteNote, Newsshooter | 2026-11-07 |
| A Short's engaged view = the viewer stayed to watch past the initial seconds, NOT including loops (a loop adds public views, never engaged views) | Yes | 2026-08-24 | YouTube Help 12220281 "Understand your YouTube content performance" | 2026-11-11 |
| YouTube Analytics API data is 48 to 72 hours late; the end date of a report stops at the last fully processed day; real-time statistics of one video come from the Data API `videos.list` (so a Short's numbers are read by processed day, and only public views are real-time) | Yes | 2026-09-09 (documented) | YouTube Analytics API "Data Model", section "Data freshness and latency" | 2026-11-11 |
| The Analytics API has no metric for "stayed to watch" / "viewed against swiped away"; a Short's `views` count every start and replay, `engagedViews` keeps the old meaning | Yes | 2025-04-30 | YouTube Analytics API metrics reference and revision history | 2026-11-11 |
| `videos.insert` and `search.list` have their own quota buckets | Yes | 2026-06-01 | YouTube Data API revision history | 2026-11-07 |
| YPP ad tier for new applicants | 1,000 subs + 8,000 qualified watch hours/365 d, or 20M qualified Shorts views/90 d | 2027-02-01 | YouTube Help "Changes to the YouTube Partner Program" | 2026-11-07 |
| YPP ad tier until 31 Jan 2027 | 1,000 subs + 4,000 h/365 d, or 10M Shorts views/90 d | — | same | 2026-11-07 |
| Shorts Creator Pool earnings need | 10M qualified Shorts views per 90 d | 2027-02-01 | same | 2026-11-07 |
| Workers Free CPU per request | 10 ms (PIN hashing set to 30,000 iterations) | — | Cloudflare Workers limits | 2026-11-07 |
| A custom thumbnail for a Short may be set (`thumbnails.set`) only AFTER YouTube has processed the video (`processingDetails.processingStatus` = `succeeded`); set earlier it "might not be applied" and no error says so (so it is a row that waits; `whatifs/release.py`) | Yes | 2026-11-03 | YouTube Data API, thumbnails.set reference and revision history | 2026-11-12 |
| An upload with a square or vertical aspect ratio of at most three minutes is filed as a Short; no API field says whether a video is a Short and no hashtag decides it (so it is proven on our own file: `release.fit`) | Yes | 2024-10-15 | YouTube Help 15424877; YouTube Data API videos resource | 2026-11-12 |
| An Instagram Reel container takes `trial_params` {graduation_strategy: MANUAL or SS_PERFORMANCE} (a Trial Reel is shown to non-followers only), `audio_name` (the audio can be named once), `cover_url` or `thumb_offset`, `is_ai_generated`; Instagram shows NO field to read a Trial Reel or the audio name back | Yes | - | Instagram Platform: IG User Media reference, content publishing guide, IG Media reference | 2026-11-12 |
| A Facebook Reel is 3 to 90 seconds, upright, at least 540 x 960, 24 to 60 frames a second; `is_ai_generated` is a parameter of the publishing call; 30 API posts a day (Instagram: 100) | Yes | - | Meta, Facebook Reels publishing guide | 2026-11-12 |
