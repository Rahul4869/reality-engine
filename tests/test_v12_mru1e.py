"""MR-U1e: the month's plan AS SHIPPED pays the hero clip the channel is built on (tools/rehearsal.py:160 at the shipped defaults, look bar on, drawn arm on)."""
import pytest
from whatifs import core, clips as CL, governor as G, costguard as CG
from tests import conftest as CF

PINNED = [k for d in (CF.OLD_CLIPS, CF.OLD_MOTION, CF.OLD_INSIDE, CF.OLD_VIEW, CF.OLD_STRATEGY, CF.OLD_DRAWN, CF.OLD_LOOK, CF.OLD_LIVING, CF.OLD_SCREENS, CF.OLD_V4B)
          for k in d if not k.endswith("_FLIPS_DONE")] + ["FORMAT_FORCE", "LADDER_ON", "DEEP_TRIAL_ON", "CREATIVE_REVIEW_FIRST_N", "MONTH_CAP_OVERRIDES"]

@pytest.mark.parametrize("drawn", ["25", "100"])                     # 25 = shipped; 100 = what the rehearsal sets at :137
def test_the_shipped_months_plan_pays_the_hero_model(setting, drawn):
    for k in PINNED:
        if k in core.DEFAULTS: setting(k, core.DEFAULTS[k][0])        # undo the older tests' pins: the cells as the code ships them
    setting("DRAWN_SHARE_PCT", drawn)
    L = CG.lines("long"); keys = {l["key"] for l in L}
    assert {"look", "drawn_scenes", "hero_clips"} <= keys, keys       # the full-quality plan: look bar and drawn scenes are in the estimate
    pk = CL.choice(); line = G.line_usd_s()
    assert pk and pk["row"]["id"] == core.DEFAULTS["FAL_HERO_MODEL"][0] and pk["fits"], (line, pk and pk["why"])
    assert line >= CL.usd_s(pk["row"]) and G.split()["fits"], (line, G.split())
