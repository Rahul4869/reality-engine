# PLATFORM FACTS (dated; code reads Settings flags, never these sentences)

Each fact: what, since when, source, last checked. When a fact changes, the Guardian/Advisor raises a card and a build updates the matching flag.

| Fact | Value | Since | Source | Checked |
|---|---|---|---|---|
| Uploads from unverified API projects locked to private | **No** (flag `UPLOAD_LOCK`, proven per project by the ₹0 upload check) | 2026-11-02 | YouTube Data API revision history | 2026-11-07 |
| Custom thumbnails for Shorts via `thumbnails.set` | Yes, only after processing has succeeded | 2026-11-03 | YouTube Data API revision history; thumbnails.set reference | 2026-11-07 |
| Public views count from the first frame (incl. autoplay); earnings and YPP use engaged views / engaged watch hours | Yes | 2026-08-24 (announced 2026-08-19) | YouTube blog via vidIQ, RouteNote, Newsshooter | 2026-11-07 |
| `videos.insert` and `search.list` have their own quota buckets | Yes | 2026-06-01 | YouTube Data API revision history | 2026-11-07 |
| YPP ad tier for new applicants | 1,000 subs + 8,000 qualified watch hours/365 d, or 20M qualified Shorts views/90 d | 2027-02-01 | YouTube Help "Changes to the YouTube Partner Program" | 2026-11-07 |
| YPP ad tier until 31 Jan 2027 | 1,000 subs + 4,000 h/365 d, or 10M Shorts views/90 d | — | same | 2026-11-07 |
| Shorts Creator Pool earnings need | 10M qualified Shorts views per 90 d | 2027-02-01 | same | 2026-11-07 |
| Workers Free CPU per request | 10 ms (PIN hashing set to 30,000 iterations) | — | Cloudflare Workers limits | 2026-11-07 |
