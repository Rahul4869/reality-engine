"""v9.2 item 3: designed voices by ID / AI Studio name with the closest-prebuilt fallback, the owner's names seeded once, loudness levelling."""
import numpy as np
import pytest
from whatifs import core, voiceq as VQ, show as SHOW, manage as MG, v91 as V91

LIST = [{"id": "voice_g3", "display_name": "Dr Grimm 3"}, {"id": "voice_v1", "display_name": "Inspector Vale 1"}, {"id": "Kore", "display_name": "Kore"}]

def test_resolve_by_id_or_ai_studio_name():
    assert VQ.resolve_designed("voice_abc", LIST) == "voice_abc" and VQ.resolve_designed("dr grimm 3", LIST) == "voice_g3"
    assert VQ.resolve_designed("Dr Grimm 2", LIST) == "" and VQ.resolve_designed("Kore", LIST) == ""

def test_designed_voice_used_only_when_checked_else_closest_prebuilt():
    MG.setup(); core.store().append("Voice_Check", [{"voice": v, "synth_ok": "TRUE"} for v in ("voice_g3", "Algenib", "Sadaltager")])
    assert VQ.voice_for("SKEPTIC", "Dr Grimm 3", set(), LIST) == ("voice_g3", "designed")
    v, how = VQ.voice_for("DIRECTOR", "Inspector Vale 1", set(), LIST)                  # listed but never passed Voice_Check
    assert how == "substitute" and v == "Sadaltager"
    assert VQ.voice_for("SKEPTIC", "Dr Grimm 3", {"voice_g3"}, LIST)[1] != "designed"   # never two characters on one voice

def test_owner_names_seeded_once_and_never_over_his_own():
    MG.setup(); g = {r["id"]: r["gvoice"] for r in core.store().rows("Characters")}
    assert g["GRIMM"] == "Dr Grimm 3" and g["VALE"] == "Inspector Vale 1" and g["ROSA"] == "Nana Rosa 1" and g["ARCHIVIST"] == "The Archivist 2"
    core.store().update("Characters", "id", "ROSA", {"gvoice": "voice_mine"}); MG.setup()
    assert next(r for r in core.store().rows("Characters") if r["id"] == "ROSA")["gvoice"] == "voice_mine"

def test_level_hits_peak_and_matches_loudness_between_characters():
    sr = 24000; t = np.arange(sr) / sr
    loud = (0.99 * np.sin(2 * np.pi * 180 * t)).astype(np.float32); quiet = (0.08 * np.sin(2 * np.pi * 120 * t)).astype(np.float32)
    before = (VQ.stats(loud), VQ.stats(quiet))
    a, b = VQ.level(loud, sr), VQ.level(quiet, sr); sa, sb = VQ.stats(a), VQ.stats(b)
    print("VOICE_LEVEL before", before, "after", (sa, sb))
    assert sa["peak_db"] <= -1.0 + 1e-3 and sb["peak_db"] <= -1.0 + 1e-3 and abs(sa["rms_db"] - sb["rms_db"]) < 1.5 and before[0]["peak_db"] > -0.2

def test_limiter_never_exceeds_ceiling_on_spikes():
    a = np.zeros(4800, np.float32); a[1000] = 1.0; a[2000:2100] = 0.95
    assert np.max(np.abs(VQ.limiter(a, 24000, -1.0))) <= 10 ** (-1 / 20) + 1e-6

def test_safe_mode_keeps_v91_voices(setting):
    setting("V91_SAFE_MODE", "TRUE"); assert not V91.on("DESIGNED_VOICES_ON") and not V91.on("VOICE_LEVEL_ON")
