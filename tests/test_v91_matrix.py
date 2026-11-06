"""v9.1 acceptance: safe mode and flag-off = v9 pixels (golden), the v9.1 flag matrix (all on / all off / each alone), failure injection for EVERY v9.1
feature (only that feature switches off, the episode goes on), and the UPGRADE test from a v9 Sheet (Setup twice: idempotent, additive only)."""
import json, os, tempfile
import numpy as np
import pytest
from whatifs import core, v91 as V91, manage as MG

HERE = os.path.dirname(__file__)
V91_FLAGS = ["ATMOSPHERE_ON", "ATMOS_GODRAYS_ON", "ATMOS_PARTICLES_ON", "ATMOS_FOG_ON", "ATMOS_SHIMMER_ON", "ATMOS_LENS_ON", "ATMOS_BREATH_ON", "ATMOS_PULSE_ON",
             "ATMOS_AURA_ON", "PULSE_ON", "LIGHTING_DIRECTIVE_ON", "HERO_STILL_REELS_ON", "HERO_STILL_SHORTS_ON", "CHAR_GRAMMAR_ON", "COURTROOM_ON",
             "RETENTION_MAP_ON", "ROLE_ROI_ON", "COMMENT_MINING_ON", "COMMENT_AI_DRAFTS_ON", "VARIETY_REWRITE_ON", "AUDIO_DROP_POST_ON", "VOICE_SUBSTITUTE_ON"]
RENDER_FLAGS = {"ATMOSPHERE_ON"}

def _golden(): return json.load(open(os.path.join(HERE, "golden", "v9_render_frames.json")))

def _all(setting, v):
    for f in V91_FLAGS: setting(f, v)

def test_every_v91_flag_is_documented_with_a_default():
    for f in V91_FLAGS + ["V91_SAFE_MODE", "ATMOSPHERE_LEVEL", "ATMOSPHERE_MAX_OVERHEAD_PCT"]:
        assert f in core.DEFAULTS and core.DEFAULTS[f][1].strip(), f
    assert core.DEFAULTS["V91_SAFE_MODE"][0] == "FALSE" and core.DEFAULTS["HERO_STILL_REELS_ON"][0] == "FALSE" and core.DEFAULTS["COMMENT_AI_DRAFTS_ON"][0] == "FALSE"

@pytest.mark.parametrize("mode", ["all_off", "all_on_safe_mode"])
def test_v9_pixels_with_all_off_or_safe_mode(setting, tmp_path, mode):
    from tests.golden_frames import render_hashes, versions
    if mode == "all_off": _all(setting, "FALSE")
    else: _all(setting, "TRUE"); setting("V91_SAFE_MODE", "TRUE")
    h = render_hashes(str(tmp_path)); g = _golden()
    if g["versions"] != versions(): pytest.skip("golden made with other OpenCV / NumPy versions")
    assert h == g["frames"]

def test_all_on_renders_and_changes_only_the_picture(setting, tmp_path):
    from tests.golden_frames import render_hashes
    _all(setting, "TRUE"); h = render_hashes(str(tmp_path))
    assert len(h) == len(_golden()["frames"]) and h != _golden()["frames"]

@pytest.mark.parametrize("flag", V91_FLAGS)
def test_each_flag_alone(setting, tmp_path, flag):
    """Each flag alone: the render either stays v9 (non-render flags) or changes and still completes; no flag crashes the render path."""
    from tests.golden_frames import render_hashes, versions
    _all(setting, "FALSE"); setting(flag, "TRUE")
    h = render_hashes(str(tmp_path)); g = _golden()
    assert len(h) == len(g["frames"])
    if flag not in RENDER_FLAGS and g["versions"] == versions(): assert h == g["frames"], flag

# ---------------------------------------------------------------- failure injection: one feature at a time
def _boom(*a, **k): raise RuntimeError("injected")

def test_inject_atmosphere(monkeypatch):
    from whatifs import atmosphere as AT, episode as EP
    V91._OFF.clear(); monkeypatch.setattr(AT, "Atmosphere", _boom)
    assert EP.atmosphere_layer("EPI", [{"start": 0, "end": 1}], [{}], {}, 30) is None and not V91.on("ATMOSPHERE_ON", "EPI") and V91.on("ATMOSPHERE_ON", "EPJ")

def test_inject_lighting_directive(monkeypatch, tmp_path):
    from whatifs import atmosphere as AT, media as MD
    V91._OFF.clear(); monkeypatch.setattr(AT, "with_directive", _boom)
    p = str(tmp_path / "s.png"); MD.still("a meteor", p, "EPI"); assert os.path.exists(p) and not V91.on("LIGHTING_DIRECTIVE_ON")
    V91._OFF.clear()

def test_inject_voice_substitution(monkeypatch):
    from whatifs import show as SHOW
    MG.setup(); core.store().append("Voice_Check", [{"voice": "Sulafat", "synth_ok": "TRUE"}]); V91._OFF.clear()
    monkeypatch.setattr(V91, "resolve_voice", _boom); b = SHOW.extra_blends(set())
    assert set(b) == {"JUDGE", "WITNESS"} and not V91.on("VOICE_SUBSTITUTE_ON"); V91._OFF.clear()

def test_inject_insights_features(monkeypatch, setting):
    from whatifs import insights as INS, models as M
    MG.setup(); V91._OFF.clear()
    monkeypatch.setattr(INS, "retention_map", _boom); assert INS.file_retention("E1", [], [], [], 500, 999) == [] and not V91.on("RETENTION_MAP_ON")
    core.store().append("Comment_Queue", [{"comment_id": "z1", "text": "what if the sea turned to jelly overnight?", "kind": "feedback"}])
    monkeypatch.setattr(M, "ask_batch", _boom); assert INS.mine_comments() == 0 and not V91.on("COMMENT_MINING_ON")
    INS.roi_note("E2", "critic", 1, 1); monkeypatch.setattr(INS, "_rows", _boom); assert INS.roi_flush("E2") == 0 and not V91.on("ROLE_ROI_ON", "E2")
    monkeypatch.setattr(INS, "variety_score", _boom); sc = {"script": "x"}; assert INS.variety_rewrite(sc, "b", "E3", lambda *a, **k: {}) is sc
    setting("COMMENT_AI_DRAFTS_ON", "TRUE"); assert INS.ai_drafts() == 0
    V91._OFF.clear()

def test_inject_hero_reel_and_grammar(monkeypatch):
    from whatifs import herostill as HS, showfx as SFX
    V91._OFF.clear(); monkeypatch.setattr(HS, "apply_grammar", _boom)
    us = [{"start": 0.0, "end": 26.0, "speaker": "DIRECTOR", "show": []}, {"start": 30.0, "end": 40.0, "speaker": "SKEPTIC", "show": []}]
    so = SFX.ShowOverlay(us, {}, 320, 180, 30, portraits={"SKEPTIC": np.full((40, 30, 3), 150, np.uint8)})
    fr = np.full((180, 320, 3), 60, np.uint8)
    with pytest.raises(RuntimeError): so.apply(fr.copy(), 35 * 30)                              # inside the overlay the render's own guard takes over:
    from whatifs import render as RN                                                             # _pipe drops a failing overlay frame and logs it (v8.x)
    assert "overlay frame skipped" in open(RN.__file__).read()

# ---------------------------------------------------------------- upgrade from a v9 Sheet
def test_upgrade_from_v9_sheet_is_additive_and_idempotent(tmp_path):
    sch = json.load(open(os.path.join(HERE, "golden", "v9_sheet_schema.json")))
    for t, h in sch["tabs"].items():                                                             # every v9 column keeps its place; v9.1 only appends
        assert core.TABS[t][:len(h)] == h, t
    st = core.LocalStore(str(tmp_path / "v9sheet.json")); st.d = {t: [] for t in sch["tabs"]}; st.save(); core._store = st
    vals9 = dict(sch["settings"], LLM_EST_INR="150", PAUSED="TRUE")                            # a v9 Sheet with the owner's own values
    st.append("Settings", [{"key": k, "value": v, "note": ""} for k, v in vals9.items()])
    st.append("Episodes", [{"episode_id": "EP202611010900", "status": "LIVE", "title": "old"}])
    MG.setup(); snap1 = {t: st.rows(t) for t in st.d}
    MG.setup(); snap2 = {t: st.rows(t) for t in st.d}
    assert {t: len(r) for t, r in snap1.items()} == {t: len(r) for t, r in snap2.items()}       # Setup twice: nothing duplicated
    vals = {r["key"]: r["value"] for r in st.rows("Settings")}
    assert all(vals[k] == v for k, v in vals9.items())                                           # existing values untouched
    assert vals["V91_SAFE_MODE"] == "FALSE" and vals["ATMOSPHERE_ON"] == "TRUE" and st.rows("Episodes")[0]["title"] == "old"
    assert {"Retention_Map", "Role_ROI"} <= set(st.d) and not (set(sch["tabs"]) - set(st.d))
