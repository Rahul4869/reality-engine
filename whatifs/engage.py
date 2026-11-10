"""Engagement engine and emotion beats: typed, in-character audience prompts and one earned emotion beat in the writer brief. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, re
from whatifs.core import S, log

EMOTIONS = [("awe", 5), ("triumph", 2), ("tenderness", 2), ("courage", 1), ("bittersweet", 1)]
LIBRARY = {
    "prediction": "Guilty or innocent? Say it in the comments before Vale shows the next exhibit.",
    "side_taking": "Team Grimm or Team Vale? The losing side buys Nana's tea.",
    "personal_stake": "Would YOU last 90 seconds? Comment your time.",
    "expert_flex": "Spot the one wrong number in Grimm's speech.",
    "share_trigger": "Send this to the friend who'd panic first.",
    "subscribe_identity": "Jury duty is every Tuesday and Saturday. Take your seat.",
}

def pick_emotion(episode):
    """Deterministic per episode, weighted (awe most often); never the same type as the previous episode when EMOTION_NO_REPEAT."""
    total = sum(w for _, w in EMOTIONS); h = int(hashlib.md5(str(episode).encode()).hexdigest()[:8], 16) % total
    acc = 0
    for name, w in EMOTIONS:
        acc += w
        if h < acc: choice = name; break
    last = str(S("EMOTION_LAST") or "")
    if S("EMOTION_NO_REPEAT", bool) and choice == last and choice != "awe":
        choice = "awe"
    return choice

def brief(episode=""):
    out = []
    if S("ENGAGE_RULES_ON", bool):
        out.append("AUDIENCE PROMPTS (v10): use at most two in-character prompts from this library, phrased freshly in the speaker's voice, at moments "
                   "where they add suspense (never in the first 20 seconds, never two within a minute): "
                   + " | ".join(f"{k}: {v}" for k, v in LIBRARY.items())
                   + ". Never promise anything for a like, subscribe or share. Only ask viewers to comment, predict, take a side or share with a friend.")
    if S("EMOTION_BEAT_ON", bool):
        emo = pick_emotion(episode)
        out.append(f"EMOTION BEAT (v10): include ONE earned {emo.upper()} moment, 20 seconds at most, in act 3 or just before the verdict, built from a "
                   "concrete sensory or personal detail (not a speech about feelings). No real tragedies, no self-harm themes, no injury detail. "
                   "Keep the wit around it; never saccharine.")
    return "\n".join(out)

def _spoken(lines):
    return [i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("##") and not l.strip().lower().startswith("[pause")]

def enforce(script_text, episode=""):
    """Returns (new_text, removed_count). Removes extra or badly placed like/subscribe/share asks; keeps [JURY] prompts."""
    from whatifs import cta as CTA
    lines = str(script_text or "").split("\n"); sp = _spoken(lines)
    if not sp: return script_text, 0
    first = int(len(sp) * S("ENGAGE_NO_ASK_FIRST_PCT", float))
    gap = S("ENGAGE_MIN_GAP_LINES", int); cap = S("ENGAGE_MAX_CTA", int)
    asks = []
    for pos, i in enumerate(sp):
        _, _, _, text = CTA._peel(lines[i])
        is_cta = bool(CTA.kind_of_text(text)); is_jury = "[JURY]" in lines[i]
        if is_cta or is_jury: asks.append((pos, i, is_cta))
    drop, kept_cta, last_pos, kinds = set(), 0, None, set()
    for pos, i, is_cta in asks:
        kind = CTA.kind_of_text(CTA._peel(lines[i])[3]) if is_cta else None
        if is_cta and (pos < first or kept_cta >= cap or kind in kinds or (last_pos is not None and pos - last_pos < gap)):
            drop.add(i); continue
        if is_cta: kept_cta += 1; kinds.add(kind)
        last_pos = pos
    if not drop: return script_text, 0
    log(f"engagement: {len(drop)} audience ask(s) removed (too early, too close or over the cap)", "INFO", episode)
    return "\n".join(l for k, l in enumerate(lines) if k not in drop), len(drop)
