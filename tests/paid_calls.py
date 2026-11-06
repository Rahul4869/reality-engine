"""v9.1 paid-call counter: produces ONE episode with the fakes and counts every call that is paid in real life (text-model calls by role, vision checks,
images, image-to-video, TTS requests, batch submissions). Frozen clock + fixed slot, so the count is reproducible."""
import collections, datetime as dt

FROZEN = dt.datetime(2026, 11, 5, 9, 30, 7, tzinfo=dt.timezone.utc)

def count(monkeypatch, tmp_path):
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import core, manage as MG, episode as EP, models as M, media as MD, tts_gemini as T
    c = collections.Counter()
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP, "now_utc", lambda: FROZEN)
    ra = M.ask
    def ask(role, *a, **k): c["text:" + str(role)] += 1; return ra(role, *a, **k)
    monkeypatch.setattr(M, "ask", ask)
    for mod in __import__("sys").modules.values():
        if getattr(mod, "__name__", "").startswith("whatifs.") and getattr(mod, "ask", None) is ra: monkeypatch.setattr(mod, "ask", ask)
    rv = M.ask_vision; monkeypatch.setattr(M, "ask_vision", lambda *a, **k: (c.update(["vision"]), rv(*a, **k))[1])
    rs = MD.still; monkeypatch.setattr(MD, "still", lambda *a, **k: (c.update(["image_premium" if k.get("premium") else "image"]), rs(*a, **k))[1])
    rn = MD.animate; monkeypatch.setattr(MD, "animate", lambda *a, **k: (c.update(["clip_kling" if k.get("hero") else "clip"]), rn(*a, **k))[1])
    if hasattr(M, "ask_batch"):
        rb = M.ask_batch; monkeypatch.setattr(M, "ask_batch", lambda *a, **k: (c.update(["batch"]), rb(*a, **k))[1])
    slot = (FROZEN + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = EP.produce(slot)
    return dict(c), r
