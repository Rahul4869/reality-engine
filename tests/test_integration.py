"""Wiring + safety checks across modules."""
import os, re
from whatifs import core

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_new_tabs_and_settings_exist():
    for t in ("Research_Brief", "Hook_Candidates", "Cut_Map"): assert t in core.TABS
    for k in ("RESEARCH_ON", "HOOKS_ON", "CUTMAP_ON", "HOOK_APPLY_MODE", "CUTMAP_MIN_GAP_SEC"): assert k in core.DEFAULTS
    assert core.S("CUTMAP_MIN_GAP_SEC", float) == 0.8

def test_safe_append_creates_a_missing_tab_on_an_older_sheet():
    st = core.store(); del st.d["Cut_Map"]
    assert core.safe_append("Cut_Map", [{"episode_id": "E", "cut_id": "C001"}]) is True and st.d["Cut_Map"]

def test_safe_helpers_never_raise(monkeypatch):
    st = core.store(); monkeypatch.setattr(st, "append", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sheet down")))
    monkeypatch.setattr(st, "ensure_tabs", lambda: (_ for _ in ()).throw(RuntimeError("still down")))
    assert core.safe_append("Cut_Map", [{"episode_id": "E"}]) is False
    monkeypatch.setattr(st, "rows", lambda t: (_ for _ in ()).throw(RuntimeError("down"))); assert core.safe_rows("Cut_Map") == []

def test_scrub_removes_keys_from_logs(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_KEY", "sk-abcdefghijklmnop"); assert "sk-abcdefghijklmnop" not in core.scrub("error with sk-abcdefghijklmnop inside")

def test_research_only_talks_to_public_hosts_and_never_reddit():
    src = open(os.path.join(ROOT, "whatifs", "research.py")).read()
    hosts = {u.split("/")[2] for u in set(re.findall(r"https?://[\w./-]+", src))}
    assert hosts <= {"www.googleapis.com", "trends.google.com", "api.stackexchange.com", "www.youtube.com", "example.invalid"}, hosts
    assert "reddit" not in src.lower()

def test_new_modules_do_not_read_secrets_or_log_hook_text():
    for f in ("hooks", "research", "cutmap"):
        src = open(os.path.join(ROOT, "whatifs", f + ".py")).read()
        assert not re.search(r"os\.environ\[", src), f
    hk = open(os.path.join(ROOT, "whatifs", "hooks.py")).read()
    for m in re.finditer(r"log\(f?\"[^\n]*", hk): assert "['line']" not in m.group(0) and '["line"]' not in m.group(0)

def test_prompts_mention_no_model_names():
    from whatifs import prompts as P
    assert not re.search(r"claude-\d|gemini-\d", " ".join(v for v in vars(P).values() if isinstance(v, str)))

def test_episode_wires_the_new_stages():
    from whatifs import episode as EP
    assert hasattr(EP, "HOOKS") and hasattr(EP, "CUTMAP") and hasattr(EP, "_review_files")

def test_rehearsal_pipeline_writes_all_three_reports():
    """Runs the real produce() flow offline and checks every new artefact exists with the right content."""
    import datetime as dt, json, shutil
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs.core import store, set_setting, now_utc
    from whatifs import manage as MG, episode as EP
    real = V.KokoroBackend; V.KokoroBackend = lambda blend: ToneVoice()
    try:
        MG.setup(); set_setting("VOICE", "C")
        r = EP.produce((now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert r.get("ok"), r
        d = os.path.dirname(r["master"])
        hooks = json.load(open(os.path.join(d, "hooks.json"))); cm = json.load(open(os.path.join(d, "cutmap.json")))
        assert len(hooks["candidates"]) == 10 and all(c["words"] < 10 for c in hooks["candidates"]) and hooks["status"] in ("applied", "needs_human_choice")
        assert cm["apply_policy"].startswith("REVIEW ONLY") and cm["method"] in ("timeline+audio", "timeline", "audio_only")
        st = store()
        for tab in ("Research_Brief", "Hook_Candidates"): assert st.rows(tab), tab
        assert os.path.exists(os.path.join(d, "cutmap.md"))
        assert any(f.startswith("research_") and f.endswith(".md") for f in os.listdir(os.environ["WI_WORK"]))
    finally:
        V.KokoroBackend = real



def test_reality_engine_is_default_and_can_be_disabled(monkeypatch):
    from whatifs import format_engine
    monkeypatch.delenv("WHATIFS_PRESENTATION_FORMAT", raising=False)
    assert format_engine.mode() == "reality_engine"
    assert "[DIRECTOR]" in format_engine.instructions("writer")
    monkeypatch.setenv("WHATIFS_PRESENTATION_FORMAT", "classic")
    assert format_engine.mode() == "classic"
    assert "classic What If narration" in format_engine.instructions("writer")


def test_reality_engine_speaker_blends_are_supported_for_reels():
    import inspect
    from whatifs import reels
    from whatifs.voice import narrate
    assert "speaker_blends" in inspect.signature(reels.build_reel).parameters
    assert "speaker_blends" in inspect.signature(narrate).parameters


def test_episode_schema_includes_presentation_format():
    from whatifs.core import TABS
    assert "presentation_format" in TABS["Episodes"]
