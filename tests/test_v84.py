"""v8.4: natural pacing. Same episode id -> identical audio timing (a retry must match the saved shot list); different episodes -> different timing;
everything stays inside speech limits; the sense of the line shapes the pause; PACING_MODE=classic still works; reels are seeded per episode."""
import json, numpy as np
from whatifs import voice as V, reels

class _BE:
    def __init__(self): self.packs = {"NARRATOR": 0}
    def register_speaker(self, s, b): self.packs[s.upper()] = 1
    def synth(self, text, speed, speaker="NARRATOR"):
        n = int(24000 * 0.075 * len(text.split()) / speed); return (0.1 * np.sin(np.arange(n) / 9)).astype(np.float32), []

B = V.Blend("n", {"af_heart": 1.0}); SB = {"DIRECTOR": B, "SKEPTIC": B}
SCRIPT = "\n".join(["[DIRECTOR] " + " ".join(["word"] * n) + p for n, p in [(14, "."), (22, "?"), (5, "."), (28, "."), (9, "!"), (16, "."), (7, "."), (12, ".")] * 4]
                   + ["[SKEPTIC] Seriously?", "[DIRECTOR] Yes."] * 6)

def _run(tmp_path, seed, name="a"):
    r = V.narrate(SCRIPT, B, str(tmp_path / name), style="slow_burn", seed=seed, backend=_BE(), speaker_blends=SB)
    return r.duration, json.load(open(r.timeline_path))["units"]

def test_same_episode_id_gives_identical_timing(tmp_path):
    d1, u1 = _run(tmp_path, "EP1", "a"); d2, u2 = _run(tmp_path, "EP1", "b")
    assert d1 == d2 and [(u["start"], u["end"], u["speed"]) for u in u1] == [(u["start"], u["end"], u["speed"]) for u in u2]

def test_different_episodes_get_different_timing(tmp_path):
    runs = [_run(tmp_path, f"EP{k}", f"n{k}")[1] for k in range(6)]
    assert len({tuple(u["speed"] for u in r) for r in runs}) == 6 and len({round(r[-1]["end"], 1) for r in runs}) >= 5

def test_every_value_stays_inside_speech_limits(tmp_path):
    for k in range(8):
        _, u = _run(tmp_path, f"EP{k}", f"l{k}")
        assert all(0.85 <= x["speed"] <= 1.15 for x in u)
        assert all(0.0 <= x["pause_before"] <= 1.8 + 0.5 for x in u[1:])          # +0.5: explicit tag pauses on top of the natural gap

def test_average_length_is_not_changed_by_the_new_pacing(tmp_path, setting):
    def avg(mode):
        setting("PACING_MODE", mode); return np.mean([_run(tmp_path, f"EP{k}", f"{mode}{k}")[0] for k in range(10)])
    a, b = avg("classic"), avg("natural")
    assert abs(a - b) / a < 0.05                                                      # scripts were sized for the old average; it must hold

def test_the_sense_of_the_line_shapes_the_pause(tmp_path):
    after_q, after_dot, quick, normal = [], [], [], []
    for k in range(10):
        _, u = _run(tmp_path, f"EP{k}", f"s{k}")
        for i in range(1, len(u)):
            if u[i]["speaker"] != u[i - 1]["speaker"] and len(u[i]["text"].split()) <= 5: quick.append(u[i]["pause_before"])
            elif u[i]["speaker"] == u[i - 1]["speaker"] and u[i - 1]["text"].endswith("?"): after_q.append(u[i]["pause_before"])
            elif u[i]["speaker"] == u[i - 1]["speaker"] and u[i - 1]["text"].endswith("."): after_dot.append(u[i]["pause_before"])
    assert np.mean(after_q) > np.mean(after_dot)                                      # a question earns a beat
    assert np.mean(quick) < np.mean(after_dot)                                        # a short reply from the other voice comes in fast

def test_classic_mode_still_works_and_differs(tmp_path, setting):
    setting("PACING_MODE", "classic"); _, c = _run(tmp_path, "EP1", "c")
    setting("PACING_MODE", "natural"); _, n = _run(tmp_path, "EP1", "n")
    assert len(c) == len(n) and [u["speed"] for u in c] != [u["speed"] for u in n]

def test_reels_are_seeded_per_episode(tmp_path, monkeypatch):
    seen = []
    def spy(lines, blend, out_base, **kw): seen.append(kw["seed"]); raise RuntimeError("stop")
    monkeypatch.setattr(reels, "narrate", spy)
    for ep in ("EP111", "EP222"):
        try: reels.build_reel(1, {"lines": ["[tension] A line."], "shots": [0]}, ["x.mp4"], "c.jpg", B, "urgent", str(tmp_path / ep))
        except RuntimeError: pass
    assert len(seen) == 2 and seen[0] != seen[1] and "EP111" in seen[0] and "reel1" in seen[0]
