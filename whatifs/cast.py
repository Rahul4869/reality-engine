"""The Cast tab: recurring experts and rotating guests, no-repeat guest rotation, and the cast brief for the writer. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json
from whatifs.core import S, store, safe_rows, log, iso

def rows(active_only=True):
    out = []
    for r in safe_rows("Cast"):
        if not str(r.get("id") or "").strip() or not str(r.get("voice") or "").strip(): continue
        if active_only and str(r.get("active", "TRUE")).strip().upper() not in ("TRUE", "YES", "1", "ON", ""): continue
        r = dict(r); r["role"] = str(r.get("role") or "").strip().lower(); out.append(r)
    return out

def enabled():
    if not S("CAST_ON", bool): return False
    rs = rows(); return any(r["role"] == "expert" for r in rs) and any(r["role"] == "guest" for r in rs)

def _w(r):
    try: return max(0.0, float(r.get("weight") or 1))
    except Exception: return 1.0

def recent_cast(n=30):
    """[(expert_id, guest_id)] of the last n episodes, oldest first."""
    out = []
    for e in store().rows("Episodes")[-n:]:
        try: c = (json.loads(e.get("draw_json") or "{}") or {}).get("cast") or {}
        except Exception: c = {}
        if c: out.append((c.get("expert"), c.get("guest")))
    return out

def pick(rng, recent=None):
    """Choose this episode's expert and guest. Guests: never one of the last GUEST_NO_REPEAT; least recently used first; weight then the episode's coin break
    ties. Experts: EXPERT_PICK = rotate (least recently used, weight ties) or fixed:<id>. Returns {"expert": id, "guest": id} or {} when the tab is unusable."""
    rs = rows()
    ex = [r for r in rs if r["role"] == "expert"]; gu = [r for r in rs if r["role"] == "guest"]
    if not ex or not gu: return {}
    from whatifs import show as SHOW
    if SHOW.on():                                                   # v9: core cast only - Vale and Grimm keep ONE voice every episode (no guest rotation)
        ch = {c.get("speaker"): str(c.get("cast_id") or "").strip() for c in SHOW.characters()}
        e = next((r for r in ex if r["id"] == ch.get("DIRECTOR")), ex[0]); g = next((r for r in gu if r["id"] == ch.get("SKEPTIC")), gu[0])
        return {"expert": e["id"], "guest": g["id"]}
    recent = recent_cast() if recent is None else recent
    lastg = {g: k for k, (_, g) in enumerate(recent) if g}; laste = {e: k for k, (e, _) in enumerate(recent) if e}
    block = {g for _, g in recent[-max(0, S("GUEST_NO_REPEAT", int)):] if g}
    pool = [r for r in gu if r["id"] not in block] or gu          # more blocked than exist: least recently used still wins below
    g = sorted(pool, key=lambda r: (lastg.get(r["id"], -1), -_w(r), rng.random()))[0]
    mode = str(S("EXPERT_PICK") or "rotate").strip()
    fixed = mode.split(":", 1)[1].strip() if mode.lower().startswith("fixed:") else ""
    e = next((r for r in ex if r["id"] == fixed), None) or sorted(ex, key=lambda r: (laste.get(r["id"], -1), -_w(r), rng.random()))[0]
    return {"expert": e["id"], "guest": g["id"]}

def get(cid):
    return next((r for r in rows(active_only=False) if r.get("id") == cid), None)

def mark_used(cast):
    """Write last_used for the two characters (called when an episode is scheduled)."""
    for cid in (cast or {}).values():
        try: store().update("Cast", "id", cid, {"last_used": iso()})
        except Exception as e: log(f"cast last_used not saved: {e}", "WARN")

def character_text(r, label):
    return (f"{label} = {r.get('display_name')} ({r.get('role')}): personality: {r.get('personality')}; speech habits: {r.get('speech_habits')}; "
            f"signature quirk (use it ONCE, naturally): {r.get('signature_quirk')}; intro line idea: \"{r.get('intro_line')}\"")

def brief(cast):
    """The writer's brief for the two speaking characters. '' when the cast is not in use."""
    if not cast or not S("CAST_ON", bool): return ""
    e, g = get(cast.get("expert")), get(cast.get("guest"))
    if not e or not g: return ""
    return ("TODAY'S CAST (write every line IN THAT CHARACTER'S VOICE; labels stay [DIRECTOR] for the expert and [SKEPTIC] for the guest):\n"
            + character_text(e, "[DIRECTOR]") + "\n" + character_text(g, "[SKEPTIC]") +
            "\nThe expert welcomes the guest by name in ONE short line inside the first 30 s (no greeting to the viewer before the impossible thing is shown). "
            "The guest's quirk shows up once; the expert's quirk once. Both are invented adults, never real people, never children. "
            "In POV scenes the guest REACTS PHYSICALLY in character (breath, gasp, nervous laugh) and the Director narrates in the present tense, second person.")

def voices(cast):
    """{'DIRECTOR': (voice, style_direction, gender, name), 'SKEPTIC': (...)} or {}."""
    e, g = get((cast or {}).get("expert")), get((cast or {}).get("guest"))
    if not e or not g: return {}
    t = lambda r: (str(r.get("voice")).strip(), str(r.get("style_direction") or "").strip(), str(r.get("gender") or "").strip().lower(), str(r.get("display_name") or "").strip())
    return {"DIRECTOR": t(e), "SKEPTIC": t(g)}

def ensure_seed(st=None):
    """Setup / the daily learning job: an empty Cast tab gets the 20 placeholder rows once (the owner replaces them)."""
    st = st or store()
    try:
        if not st.rows("Cast"):
            from whatifs.data import cast_seed_rows
            st.append("Cast", cast_seed_rows()); return True
    except Exception as e: log(f"cast seed skipped: {e}", "WARN")
    return False
