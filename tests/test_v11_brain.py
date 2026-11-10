"""v11 (K155) Channel Brain: evidence-based learning that can say 'not learning'. No keys, no network."""
import datetime as dt, json
import numpy as np
import pytest
from whatifs import core, brain as BR

NOW = dt.datetime(2026, 12, 20, 6, 0, tzinfo=dt.timezone.utc)

def _seed(hooks_rates, n_each=6, views=1000, fmt="short"):
    st = core.store(); rng = np.random.default_rng(3); i = 0
    for hook, rate in hooks_rates.items():
        for _ in range(n_each):
            i += 1; key, y = f"V{i}", f"y{i}"
            BR.tag(key, fmt, title="What if the Moon vanished?", premise="moon", hook=hook, sec=30, yt_id=y)
            eng = int(rng.binomial(views, rate))
            st.append("Analytics", [{"episode_id": key, "yt_id": y, "pulled": core.iso(), "views": views, "engaged_views": eng, "avg_view_pct": 70}])

def test_a_real_winner_is_proven_and_a_real_loser_retired(setting):
    _seed({"verdict_first": 0.72, "countdown": 0.55, "you_pov": 0.62})
    res = BR.update_library(NOW, "short")
    assert res["short:hook:verdict_first"] == "proven" and res["short:hook:countdown"] == "retired"
    lib = {r["technique_id"]: r for r in core.store().rows("Technique_Evidence")}
    w = lib["short:hook:verdict_first"]
    assert float(w["p_beats_baseline"]) >= 0.9 and int(w["n_videos"]) == 6 and w["expires_at"] and "verdict" in w["mechanism"]

def test_noise_is_not_called_a_winner(setting):
    _seed({"verdict_first": 0.6, "countdown": 0.6}, n_each=2, views=150)   # tiny, equal data
    res = BR.update_library(NOW, "short")
    assert "proven" not in res.values() and "retired" not in res.values()

def test_thompson_prefers_the_winner_skips_retired_and_keeps_a_holdout(setting):
    _seed({"verdict_first": 0.72, "countdown": 0.5, "you_pov": 0.62}); BR.update_library(NOW, "short")
    picks = [BR.choose("hook", "short", seed=s) for s in range(400)]
    lv = [p["level"] for p in picks if not p["holdout"]]; hold = sum(p["holdout"] for p in picks)
    assert "countdown" not in lv and lv.count("verdict_first") > len(lv) * 0.5
    assert 50 <= hold <= 115                                                   # ~20% holdout

def test_forecasts_are_logged_scored_and_judged_against_the_median(setting):
    _seed({"verdict_first": 0.7}, n_each=10); BR.update_library(NOW, "short")
    for k in range(1, 11): BR.forecast(f"V{k}", "short", hook="verdict_first")
    s = BR.score_forecasts()
    assert s["n"] == 10 and 0 <= s["coverage"] <= 1 and s["mae_naive"] is not None
    v = BR.verdicts(); assert v["learning"].startswith(("learning", "NOT LEARNING"))

def test_no_data_is_said_out_loud(setting):
    f = BR.forecast("NEW1", "short"); assert f["basis"].startswith("no data yet")
    assert BR.verdicts()["learning"] == "too few measured videos to judge"

def test_shorts_from_episodes_specials_and_pilots_are_ingested_once(setting):
    st = core.store()
    st.append("Episodes", [{"episode_id": "E1", "slot_et": "2026-12-10T15:00:00Z", "reel1_yt": "s1", "reel2_yt": "s2", "title": "What if gravity stopped?"}])
    st.append("Specials", [{"id": "SP1", "yt_id": "s3", "ts": "2026-12-10T10:00:00Z", "title": "Meet the court"}])
    assert BR.ingest_shorts(NOW) == 3 and BR.ingest_shorts(NOW) == 0
    feats = {r["video_key"]: r for r in st.rows("Video_Features")}
    assert {"E1#r1", "E1#r2", "SP1"} <= set(feats) and feats["E1#r1"]["topic"] == "physics"
    assert all(r.get("engaged_views") not in ("", None) for r in st.rows("Analytics"))

def test_features_are_deterministic():
    assert BR.title_pattern("What if?") == "question" and BR.title_pattern("10 ways") == "number" and BR.title_pattern("The Moon is guilty") == "verdict"
    assert BR.topic_cluster("a black hole") == "space" and BR.length_band(30, "short") == "short_20_35"
