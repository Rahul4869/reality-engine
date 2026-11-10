"""Repairs for problems full QC finds, in a fixed order with limits: free fixes first, paid fixes only up to a rupee cap. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
from whatifs.core import log, scrub

FREE_CODES = {"loudness", "true_peak", "no_audio", "captions", "black", "frozen", "duration_mismatch", "frame_count", "av_offset"}
PAID_CODES = {"kling_short", "asset_missing", "vision_mismatch", "vision_artifact", "reuse_run"}

def auto_fix(job, chk, paid_cap_inr, recheck, rounds=2):
    """job: object with remix(lufs), rebuild_captions(), rerender_times(list), rebuild_video(), repair_assets(codes, idx, cap_inr) -> rupees spent.
    recheck(): returns a fresh full_check result. Returns (chk, notes, spent_inr)."""
    notes, spent = [], 0.0
    for rnd in range(rounds):
        probs = chk["problems"]; codes = {p["code"] for p in probs}
        if not codes: break
        changed = False
        try:
            if codes & {"loudness", "true_peak", "no_audio"}:
                job.remix(-14.5 if rnd == 0 else -16.0); notes.append("re-mixed the audio"); changed = True
            if "captions" in codes: job.rebuild_captions(); notes.append("rebuilt the captions"); changed = True
            if codes & {"black", "frozen"}:
                from whatifs import qc
                tt = qc.scan_times(job.master); times = tt["black"] + tt["frozen"]
                if times: job.rerender_times(times); notes.append(f"re-rendered the segments around {len(times)} bad stretch(es)"); changed = True
            if codes & {"duration_mismatch", "frame_count", "av_offset"}:
                job.rebuild_video(); notes.append("re-stitched the video against the narration clock"); changed = True
            paid = [p for p in probs if p["code"] in PAID_CODES]
            if paid and spent < paid_cap_inr:
                idx = sorted({i for p in paid for i in (p.get("idx") or [])})
                s = job.repair_assets({p["code"] for p in paid}, idx, paid_cap_inr - spent); spent += s
                if s > 0: notes.append(f"re-made pictures/clips (Rs {s:.0f})"); changed = True
        except Exception as e:
            log(f"auto-fix step failed: {scrub(e)[:200]}", "WARN"); notes.append("a fix step failed: " + scrub(e)[:80])
        if not changed: break
        chk = recheck()
        if chk["ok"]: break
    return chk, notes, spent
