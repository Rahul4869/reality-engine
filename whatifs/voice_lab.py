"""whatifs/voice_lab.py v8.10 (Gemini cast samples + voice check; v8.7) - 4 original voices + 1 flat comparison. Samples are emailed + uploaded to Drive + kept as a GitHub artifact.
v8.7 review fix: in rehearsal mode (WI_FAKE=1) the tone placeholders go to the work folder, so a local rehearsal never overwrites the repo's voice_samples folder."""
import os, subprocess
from whatifs.voice import Blend, narrate
from whatifs.episode import BLENDS
from whatifs.core import set_setting, iso, FAKE, WORK, S

DEMO = """[calm] Right now, about eight billion people have fingernails. And every week... we cut a little bit off.
[tension] So picture this. At exactly noon, everyone on Earth drops their clippings into the ocean. At once.
[pause:long]
[reveal] That's roughly two hundred tonnes of keratin, hitting the water in the same second.
[aside] And the ocean does... [beat] absolutely nothing. Which, if you've ever sent a long heartfelt text and got back "k", is a feeling you already know.
[tension] But two hundred tonnes doesn't just vanish. It sinks. And down there, something is waiting for it.
"""

def main(backend=None):
    out = os.path.join(WORK, "voice_samples") if FAKE else "voice_samples"; os.makedirs(out, exist_ok=True); links = []
    def mp3(wav):
        m = wav[:-4] + ".mp3"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", m], check=True); os.remove(wav); return m
    for k, parts in BLENDS.items():
        r = narrate(DEMO, Blend(k, parts), f"{out}/voice_{k}", style="slow_burn", seed="lab", backend=backend); links.append((k, mp3(r.wav_path), r.voiceprint))
    r = narrate(DEMO, Blend("C", BLENDS["C"]), f"{out}/voice_E_no_pacing", humanize=False, seed="lab", backend=backend); links.append(("E", mp3(r.wav_path), "flat"))
    links += cast_samples(out) if backend is None else []        # v8.10: the Gemini cast (one short exchange per guest with an expert)
    if not S("VOICE_SAMPLES_AT"): set_setting("VOICE_SAMPLES_AT", iso())        # v10.2 (#9): a re-run of Setup never restarts the wait
    if not FAKE:
        from whatifs import publish as PUB
        html = ["<p>Listen on your phone with earphones. Then open the Sheet, Settings tab, and type A, B, C or D in the VOICE cell (or A+C to mix two).</p><ul>"]
        for k, path, vp in links:
            if not path: html.append(f"<li>{k}: {vp}</li>"); continue
            try: _, url = PUB.drive_upload(path, os.path.basename(path), public=True); html.append(f"<li><a href='{url}'>Voice {k}</a> ({vp})</li>")
            except Exception as e: html.append(f"<li>Voice {k}: see GitHub artifact ({e})</li>")
        html.append("</ul><p>E is voice C with the human pacing switched off, for comparison. If you don't choose within 72 hours, A is used.</p>")
        PUB.email("Fallback narrator voice (optional - your designed character voices are used)", "".join(html))      # v10.2 (#9)
    return links

if __name__ == "__main__":
    main()



def cast_samples(out):
    """v8.10: with TTS_ENGINE = gemini and the Cast tab in use: check every cast voice (Voice_Check tab), then voice each guest's intro with an expert so the
    owner can listen. About 3 s of speech per sample (well under Rs 1 for all). Never raises: a failure is reported in the list instead."""
    from whatifs.core import S, log, scrub
    if str(S("TTS_ENGINE") or "").strip().lower() != "gemini": return []
    from whatifs import cast as CAST
    from whatifs.tts_gemini import voice_check
    if not CAST.enabled(): return []
    res = []
    try:
        okn, tot, probs = voice_check(); res.append(("voice check", "", f"{okn}/{tot} cast voices work" + (": " + "; ".join(probs[:4]) if probs else "")))
    except Exception as e: res.append(("voice check", "", scrub(e)[:160])); return res
    rows = CAST.rows(); experts = [r for r in rows if r["role"] == "expert"]
    for k, g in enumerate([r for r in rows if r["role"] == "guest"]):
        e = experts[k % len(experts)]
        sb = {"DIRECTOR": Blend("e", {"am_michael": 1.0}, gvoice=e["voice"], gstyle=e.get("style_direction", "")),
              "SKEPTIC": Blend("g", {"af_heart": 1.0}, gvoice=g["voice"], gstyle=g.get("style_direction", ""))}
        script = f"[DIRECTOR] [calm] {e.get('intro_line') or 'Welcome back.'} Today with us: {g.get('display_name')}.\n[SKEPTIC] [wow] {g.get('intro_line') or 'Hi!'}"
        import hashlib, json as _json                                          # v9.2: an unchanged sample (same voices, styles, words) is not made again
        key = hashlib.sha256("|".join([str(e["voice"]), str(g["voice"]), str(e.get("style_direction", "")), str(g.get("style_direction", "")), script]).encode()).hexdigest()[:12]
        try: done = _json.loads(S("VOICE_SAMPLES_DONE") or "{}")
        except Exception: done = {}
        if S("VOICE_SAMPLES_REUSE", bool) and key in done:
            res.append((f"{e['id']}+{g['id']}", done[key], f"{e.get('display_name')} + {g.get('display_name')} (unchanged, kept)")); continue
        try:
            r = narrate(script, sb["DIRECTOR"], f"{out}/cast_{e['id']}_{g['id']}", seed="castlab", speaker_blends=sb)
            res.append((f"{e['id']}+{g['id']}", r.wav_path if FAKE else _mp3(r.wav_path), f"{e.get('display_name')} + {g.get('display_name')}"))
            try:
                from whatifs.core import set_setting
                done[key] = res[-1][1]; set_setting("VOICE_SAMPLES_DONE", _json.dumps(dict(list(done.items())[-40:])))
            except Exception: pass
        except Exception as x: log(f"cast sample {g['id']} failed: {scrub(x)[:120]}", "WARN"); res.append((g["id"], "", "failed"))
    return res

def _mp3(wav):
    m = wav[:-4] + ".mp3"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", m], check=True); os.remove(wav); return m
