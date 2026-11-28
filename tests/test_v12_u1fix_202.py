"""U1 J 202 (#230): A REPLAYED REHEARSAL ID CAN END GREEN. `runner.born_under_org` exempts an episode whose id is older than ORG_SINCE (a half-made film
on a real Sheet); a replay of a past id in a fresh store was therefore never judged by the organisation's checks. `tools/rehearsal.py` now wraps it
for the length of the run (`replaying`): that one id is born under the organisation, every other id asks the real function, and the wrap is undone
after the run, also after a raise. ORG_SINCE is not moved and no production file changes."""
import inspect
import pytest
from whatifs import core
from whatifs.org import runner as RUN
from tools import rehearsal as RH

PAST = "EP202611170204"


def test_a_past_id_is_judged_inside_a_replay_and_only_it(setting):
    setting("ORG_SINCE", core.iso())
    assert RUN.born_under_org(PAST) is False                                                     # the fact of the issue
    with RH.replaying(PAST):
        assert RUN.born_under_org(PAST) is True and RUN.born_under_org("EP202611160900") is False
    assert RUN.born_under_org(PAST) is False
    with pytest.raises(RuntimeError):
        with RH.replaying(PAST):
            assert RUN.born_under_org(PAST) is True; raise RuntimeError("a run that raised")
    assert RUN.born_under_org(PAST) is False


@pytest.mark.parametrize("ep", ["EP209912310000", None], ids=["future_id", "no_id"])
def test_an_id_that_is_not_in_the_past_wraps_nothing(ep, setting):
    setting("ORG_SINCE", core.iso()); real = RUN.born_under_org
    with RH.replaying(ep):
        assert RUN.born_under_org is real
    assert RUN.born_under_org is real


def test_the_rehearsal_enters_the_replay_before_its_setup():
    src = inspect.getsource(RH.run)
    assert src.index("replay.enter_context(replaying(ep_id))") < src.index("MG.setup()") and "replay.close()" in src
