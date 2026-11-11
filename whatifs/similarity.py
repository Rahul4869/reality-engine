"""Script similarity guard: a MinHash fingerprint of every final script, compared with the last 10. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, re
from whatifs.core import S, log, store, iso

K = 64

def _shingles(text, n=5):
    w = re.findall(r"[a-z']+", re.sub(r"\[[^\]]*\]", " ", str(text or "").lower()))
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}

def signature(text):
    sh = _shingles(text)
    if not sh: return []
    return [min(int(hashlib.md5(f"{k}|{s}".encode()).hexdigest()[:12], 16) for s in sh) for k in range(K)]

def similarity(a, b):
    if not a or not b or len(a) != len(b): return 0.0
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)

def check(script_text, episode=""):
    """Returns (max_similarity, most_similar_episode). Stores the signature. Never raises."""
    try:
        sig = signature(script_text)
        if not sig: return 0.0, ""
        best, who = 0.0, ""; rows = store().rows("Script_Fingerprints")
        mine = [r for r in rows if episode and str(r.get("episode_id") or "") == str(episode)]
        for r in [r for r in rows if not (episode and str(r.get("episode_id") or "") == str(episode))][-10:]:      # v12 B6a: never compared with its OWN earlier draft
            try: other = [int(x) for x in str(r.get("sig") or "").split(",") if x]
            except ValueError: continue
            s = similarity(sig, other)
            if s > best: best, who = s, r.get("episode_id", "")
        row = {"ts": iso(), "episode_id": episode, "sig": ",".join(str(x) for x in sig)}
        if mine: store().update("Script_Fingerprints", "episode_id", episode, row)          # a re-scripted episode replaces its fingerprint (one per episode)
        else: store().append("Script_Fingerprints", [row])
        if best > S("SCRIPT_SIMILARITY_MAX", float):
            from whatifs.core import note_degraded
            note_degraded(f"script {best:.0%} similar to {who}")
            from whatifs import notify as NT
            NT.send("similar_script", f"The script of {episode} is {best:.0%} similar to {who}. YouTube penalises repetitive videos: the next case will be steered to a different structure.",
                    tier="now", dedupe_key=f"similar|{episode}")
        return best, who
    except Exception as e:
        log(f"similarity check skipped: {str(e)[:120]}", "WARN", episode); return 0.0, ""
