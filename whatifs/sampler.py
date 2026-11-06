"""whatifs/sampler.py v8.9 (rotating guest, tier field; v8.7: rhythm blueprint + sound density + playbook trials; hook within 3-8 s) - per-episode draw (runtime, counts, strategies). Bandit with exploration; leader capped near 60%."""
from __future__ import annotations
import hashlib, json, random
from whatifs.core import S, store

def _rng(seed): return random.Random(int(hashlib.md5(seed.encode()).hexdigest()[:12], 16))

def pick(dim, rng, avoid=()):
    rows = [r for r in store().rows("Strategies") if r["dimension"] == dim and r["status"] == "ACTIVE"]
    if not rows: return None
    scored = []
    for r in rows:
        n = float(r.get("score_n") or 0); s = float(r.get("score_sum") or 0)
        v = rng.gauss(s / n if n else 0.5, 0.35 / (1 + n) ** 0.5) - (0.15 if r["name"] in avoid else 0)
        scored.append((v, r["name"]))
    scored.sort(reverse=True)
    if len(scored) > 1 and rng.random() < 0.4: return scored[rng.randrange(1, len(scored))][1]
    return scored[0][1]

def draw(episode_id, ptype):
    rng = _rng(episode_id); recent = {}
    for e in store().rows("Episodes")[-6:]:
        try:
            for k, v in json.loads(e.get("draw_json") or "{}").get("strategies", {}).items(): recent.setdefault(k, []).append(v)
        except Exception: pass
    lo, hi = S("RUNTIME_MIN_SEC", int), S("RUNTIME_MAX_SEC", int)
    runtime = int(rng.triangular(lo, hi, lo + (hi - lo) * 0.45))
    st = {d: pick(d, rng, recent.get(d, [])[-2:]) for d in ("story", "hook", "voice", "reel", "humour", "thumb", "title", "banter")}
    st["family"] = pick("family", rng, recent.get("family", [])[-3:])
    if ptype == "body" and st["humour"] == "medium": st["humour"] = "light"
    reel2 = pick("reel", rng, [st["reel"]]) or st["reel"]
    out = {"episode_id": episode_id, "ptype": ptype, "runtime_sec": runtime,
            "words": int(runtime / 60 * S("WPM_ESTIMATE", float) * rng.uniform(0.95, 1.03)),
            "stills": rng.randint(S("STILLS_MIN", int), S("STILLS_MAX", int)), "living": S("LIVING_STILLS", int),
            "kling": S("KLING_CLIPS", int), "beats": rng.randint(6, 10), "hook_sec": round(rng.uniform(3, 8), 1),
            "strategies": st, "reel_formats": [st["reel"], reel2], "shot_sec": round(rng.uniform(4.5, 7.0), 1)}
    from whatifs.data import STRATEGIES
    from whatifs import growth as GR
    for dim in ("rhythm", "sound"):           # v8.7: older Sheets get these rows from the daily learning job; until then a seeded choice from the seed list
        st[dim] = pick(dim, rng, recent.get(dim, [])[-2:]) or sorted(STRATEGIES[dim])[rng.randrange(len(STRATEGIES[dim]))]
    plans = []
    for e in store().rows("Episodes")[-6:]:
        try: plans.append(json.loads(e.get("draw_json") or "{}").get("rhythm_plan") or {})
        except Exception: pass
    out["rhythm_plan"] = GR.rhythm_plan(st["rhythm"], rng, plans)
    try:
        from whatifs import playbook as PB
        out["playbook"] = PB.for_episode(episode_id)
    except Exception: out["playbook"] = {}
    from whatifs.data import GUESTS                     # v8.9: the Curious One is a new guest each episode, least recently used first (ties: the episode's coin)
    last = {}
    for k, e in enumerate(store().rows("Episodes")[-8:]):
        try: g = json.loads(e.get("draw_json") or "{}").get("guest")
        except Exception: g = None
        if g: last[g] = k
    out["guest"] = sorted(GUESTS, key=lambda g: (last.get(g, -1), rng.random()))[0]
    try:                                                # v8.10: expert + guest from the Cast tab (guests never repeat within GUEST_NO_REPEAT videos)
        from whatifs import cast as CAST
        if CAST.enabled(): out["cast"] = CAST.pick(rng)
    except Exception: pass
    out["tier"] = "public"                              # v8.9: reserved for premium (members-only) episodes later; see CLAUDE.md "Premium tier"
    return out

