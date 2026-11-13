"""v12 V2d-a THE MONEY AND THE MODEL: the hero clip model is picked by value from a table of what the provider's pages say, a clip is bought by the
second, every estimate is one table of lines the paid-call counter can check, and the month's split says what fits. Each rule both ways. No keys, no network."""
import datetime as dt, inspect, json, os, subprocess
import pytest
from whatifs import core, clips as CL, costguard as CG, governor as G, media as MD, steward as STW, scout as SC, shorts2 as SH, formats as FMT, manage as MG, episode as EP, models as M
from whatifs import tts_gemini as T, preflight as PF, notify as NT, publish as PUB, ladder as LAD, opening as OPEN, replan as RP
from whatifs.org import shortseat as SEAT, registry as REG
from tests.conftest import OLD_CLIPS
from tests.test_v12_short import good, tl
from tests.paid_calls import watch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEY, H3, H3MAX, PIX, KLING = (r["id"] for r in json.loads(core.DEFAULTS["CLIP_MODELS"][0]))
DEC = dt.datetime(2026, 12, 1, 6, 0, tzinfo=dt.timezone.utc)
REAL_SCHEMA = SC.fal_schema          # the offline listing: a schema that says what the model's own row says

@pytest.fixture
def market(setting):
    """The cells as the code ships them (the older tests pin the model and the flat price they were written for: tests/conftest.py)."""
    for k in OLD_CLIPS: setting(k, core.DEFAULTS[k][0])
    setting("MONTH_CAP_OVERRIDES", "")
    return setting

def _rows(**change):
    rows = [dict(r) for r in json.loads(core.DEFAULTS["CLIP_MODELS"][0])]
    for mid, upd in change.items(): next(r for r in rows if r["id"] == {"hey": HEY, "h3": H3, "max": H3MAX, "pix": PIX, "kling": KLING}[mid]).update(upd)
    return rows

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _clip(path, w, h, sec=1):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=10:duration={sec}", "-pix_fmt", "yuv420p", path], check=True); return path

# ------------------------------------------------------------------ the clip market is data
def test_the_table_is_data_read_from_the_providers_pages_and_no_model_is_named_in_the_code(market, setting):
    rows = CL.table(); assert [r["id"] for r in rows] == [HEY, H3, H3MAX, PIX, KLING]
    for r in rows:
        assert CL.usd_s(r) and r["min_s"] <= r["max_s"] and r["start"] == "image_url" and r["shape"] in ("follows", "inferred", "unstated"), r["id"]
        assert r["page"] == "https://fal.ai/models/" + r["id"] and r["read"] == "2026-11-13" and (r["res"] == "-" or r["res_field"] == "resolution"), r["id"]
    assert CL.row(KLING)["elo"] is None and CL.row(HEY)["elo"] == 1124 and CL.row(H3)["elo"] == 1133 and CL.row(PIX)["elo"] == 959          # as read on 13 Nov 2026
    src = open(os.path.join(ROOT, "whatifs", "clips.py"), encoding="utf-8").read()
    assert not [w for w in ("heygen", "minimax", "kling-video", "pixverse", "fal-ai/") if w in src.lower()], "a model is named in the code of the clip market"
    assert core.DEFAULTS["FAL_HERO_MODEL"][0] == HEY and float(core.DEFAULTS["PRICE_KLING_USD"][0]) == pytest.approx(CL.usd(CL.row(HEY), 5))
    setting("CLIP_MODELS", "not a table"); assert [r["id"] for r in CL.table()] == [HEY, H3, H3MAX, PIX, KLING]          # an unreadable cell: the built-in rows
    setting("CLIP_MODELS", json.dumps([{"id": "x/y", "usd_s": {"-": 0.5}, "res": "-"}])); assert CL.row("x/y") and CL.row(HEY) is None and CL.hero() is None      # a row is data: the cell wins

def test_a_clip_is_bought_in_whole_seconds_inside_the_models_shortest_and_longest_clip(market):
    hey, pix = CL.row(HEY), CL.row(PIX)
    assert [CL.secs(hey, s) for s in (0.4, 3.2, 5.0, 5.01, 9.99, 10.0, 14.2, 17)] == [5, 5, 5, 6, 10, 10, 15, 15]
    assert [CL.secs(pix, s) for s in (0.4, 1.0, 1.01)] == [1, 1, 2]
    assert CL.usd(hey, 6.2) == pytest.approx(7 * 0.02) and CL.usd(CL.row(H3), 5) == pytest.approx(0.30) and CL.usd(CL.row(KLING), 5) == pytest.approx(0.42)
    assert CL.buy(6.2)[1:] == (7, pytest.approx(0.14)) and CL.buy()[1] == CL.SCENE_S == 5 and CL.longest() == 10 and CL.hero_usd_s() == 0.02 and CL.paid_s(6.2, 3) == 21

def test_with_the_market_off_everything_is_as_before(setting):
    assert not CL.on() and CL.hero() is None and CL.buy(8.0) == (None, 5, 0.42) and CL.longest() == 6.5 and CL.hero_usd_s() == pytest.approx(0.084) and CL.paid_s(6.2, 3) == 15
    assert SEAT.clip_max() == SEAT.CLIP_S * SEAT.STRETCH_MAX and CL.review() == {} and CL.preflight()[0] is True
    setting("CLIP_VALUE_ON", "TRUE"); assert CL.hero()["id"] == KLING and CL.buy(8.0)[1:] == (8, pytest.approx(8 * 0.084))      # the market on, the same model: by the second

def test_the_request_is_built_from_the_models_row_not_from_its_name(market):
    assert CL.args(CL.row(HEY), "U", "P", 6.2) == {"prompt": "P", "image_url": "U", "duration": 7, "resolution": "768p"}
    k = CL.args(CL.row(KLING), "U", "P", 6.2); assert k["duration"] == "7" and "resolution" not in k and k["generate_audio"] is False and "watermark" in k["negative_prompt"]
    assert CL.args(CL.row(H3MAX), "U", "P", 5)["prompt_expansion_mode"] == "balanced" and CL.args(CL.row(H3), "U", "P", 5)["resolution"] == "768P"
    other = dict(CL.row(HEY), start="first_frame", res="1080p", res_field="size", dur="str")                                       # another row for the same name: another request
    assert CL.args(other, "U", "P", 5) == {"prompt": "P", "first_frame": "U", "duration": "5", "size": "1080p"}

# ------------------------------------------------------------------ the rule
def test_the_rule_takes_the_best_rank_the_plan_can_pay_and_a_tie_goes_to_the_cheaper(market):
    rows = _rows(); p = CL.pick(rows, 0.0526)
    assert p["row"]["id"] == HEY and p["fits"] and p["under"] == [HEY] and "1124 points" in p["why"] and "0.053" in p["why"]
    p = CL.pick(rows, 0.07); assert p["row"]["id"] == HEY and set(p["tied"]) == {HEY, H3} and "tied by their error bands" in p["why"]          # 1133 +-14 and 1124 +-14 overlap: the cheaper
    apart = _rows(hey={"ci": 2}, h3={"ci": 2}); assert CL.pick(apart, 0.07)["row"]["id"] == H3                                           # no overlap: the higher rank wins, though dearer
    assert CL.pick(apart, 0.0526)["row"]["id"] == HEY                                                                                 # ... unless the plan cannot pay it
    p = CL.pick(rows, 0.01); assert p["row"]["id"] == HEY and p["fits"] is False and p["under"] == [] and "does not fit" in p["why"]       # nothing under the line: quality is kept, the plan shrinks
    assert CL.pick(_rows(hey={"usd_s": {"768p": 0.09}}), 0.01)["row"]["id"] == H3                                                     # ... on the cheapest ranked model
    assert CL.pick([r for r in rows if r["id"] in (KLING, PIX)], 1.0) is None                                                          # no rank / no word on the clip's shape: never picked

def test_points_per_dollar_is_not_the_rule_and_a_lower_rank_never_wins_by_price(market):
    cheap = _rows(pix={"shape": "follows", "usd_s": {"720p": 0.001}})                      # the lowest-ranked model, a hundred times cheaper and otherwise eligible
    ratio = max((r for r in cheap if r.get("elo")), key=lambda r: r["elo"] / CL.usd_s(r)); assert ratio["id"] == PIX          # what "points per dollar" would take
    p = CL.pick(cheap, 0.0526); assert p["row"]["id"] == HEY and PIX in p["under"] and PIX not in p["tied"]
    assert CL.pick(cheap, 0.0526, floor=CL.floor_of(HEY, cheap))["row"]["id"] == HEY and CL.floor_of(HEY) == 1110 and CL.floor_of(KLING) is None
    assert CL.pick(cheap, 0.07, floor=1130)["row"]["id"] == H3 and CL.pick(_rows(), 0.0526, floor=1140) is None                    # under the floor of the model in use: never by code

def test_a_row_that_cannot_be_the_hero_says_why(market):
    assert CL.issues(CL.row(HEY)) == [] and CL.issues(CL.row(H3)) == []
    for change, word in (({"start": ""}, "start picture"), ({"shape": "unstated"}, "shape"), ({"res": "4k"}, "price"), ({"max_s": 3}, "longest clip"),
                         ({"status": "deprecated"}, "lists it as deprecated"), ({"schema": "no field 'image_url' for the start picture"}, "inputs changed")):
        r = dict(CL.row(HEY), **change); assert any(word in x for x in CL.issues(r)), (change, CL.issues(r))
        assert CL.pick(_rows(hey=change), 0.07)["row"]["id"] == H3, change
    assert "failing or retired" in CL.issues(CL.row(HEY), dead={HEY})[0] and CL.pick(_rows(), 0.07, dead={HEY})["row"]["id"] == H3

def test_the_line_is_what_the_months_plan_can_pay_for_a_second_of_hero_clip(market, setting):
    line = G.line_usd_s(); assert 0.040 < line < 0.045 and G.month_room_inr() == 5000 - 100 - 200 - 420, line          # Rs 5,000 less the reserve, the earmark and the organisation's caps
    setting("FAL_HERO_MODEL", H3); assert G.line_usd_s() == pytest.approx(line)                                    # it does not depend on the PRICE of the model in use
    setting("SHORTS_PER_MONTH", "20"); more = G.line_usd_s(); assert more < line
    setting("SHORTS_PER_MONTH", "12"); setting("MONTH_RESERVE_INR", "900"); assert G.line_usd_s() < line
    setting("MONTH_RESERVE_INR", "300"); setting("MONTH_CAP_OVERRIDES", core.now_utc().strftime("%Y-%m") + "=6000"); assert G.line_usd_s() > line
    setting("MONTH_CAP_OVERRIDES", ""); setting("LLM_EST_INR", "400"); assert G.line_usd_s() < line                    # dearer writing leaves less for a second of clip

def test_the_stewards_replacement_for_the_hero_follows_the_same_rule(market, setting, monkeypatch):
    _quiet(monkeypatch); assert CL.choice()["row"]["id"] == HEY
    nxt = STW.next_candidate("hero", after=HEY); assert nxt == {"id": H3, "usd": pytest.approx(0.30)} == STW.next_candidate("hero")      # the best OTHER model by the same rule; three times the price: the price-ratio rule would have refused it
    h = STW.health(); h[HEY] = {"status": "dead"}; STW._save(h)
    p = CL.choice(); assert p["row"]["id"] == H3 and p["fits"] is False                                              # a dead model sets no floor and is not eligible
    assert STW.ensure("hero") == H3 and core.S("FAL_HERO_MODEL") == H3 and core.S("PRICE_KLING_USD", float) == pytest.approx(0.30)
    assert [r["to"] for r in core.store().rows("Model_Changes")] == [H3] and any(r["kind"] == "model_switch" for r in core.store().rows("Owner_Actions"))
    setting("CLIP_VALUE_ON", "FALSE"); setting("FAL_HERO_MODEL", KLING); setting("PRICE_KLING_USD", "0.42")
    assert STW.next_candidate("hero", after=KLING)["id"] == json.loads(core.S("MODEL_LADDERS"))["hero"][1]["id"]       # the market off: the ladder's order, as before

# ------------------------------------------------------------------ the live listing: read, never trusted for the price
def _listing(monkeypatch, status=None, price=0.07, schema=None, ranks=None):
    monkeypatch.setattr(SC, "fal_status", lambda ids: {i: (status or {}).get(i, "active") for i in ids})
    monkeypatch.setattr(SC, "fal_prices", lambda ids: {i: {"unit_price": price(i) if callable(price) else price, "unit": "second", "currency": "USD"} for i in ids})
    monkeypatch.setattr(SC, "fal_schema", lambda i: (schema or {}).get(i, REAL_SCHEMA(i)))
    monkeypatch.setattr(SC, "aa_ranking", lambda: ranks or {})

def _doc(**props): return {"components": {"schemas": {"SomethingInput": {"properties": dict({"prompt": {"type": "string"}}, **props)}}}}

def test_the_listing_is_read_for_what_a_program_can_know_and_its_price_is_never_taken(market, monkeypatch):
    _listing(monkeypatch); rows = CL.refresh(); assert all(r["base"] == 0.07 and not r.get("stale") for r in rows)          # first sight: the listing's base price is KEPT beside the row
    assert CL.usd_s(CL.row(HEY)) == 0.02 and json.loads(core.S("CLIP_MODELS"))[0]["base"] == 0.07                       # ... and the price we estimate with is still the page's
    before = core.S("CLIP_MODELS"); assert CL.refresh() and core.S("CLIP_MODELS") == before                              # nothing changed: the cell is not written again
    _listing(monkeypatch, price=lambda i: 0.14 if i == HEY else 0.07, status={PIX: "deprecated"}, ranks={"minimax h3 (768p)": 1150},
             schema={H3: _doc(first_frame={}, duration={"minimum": 5, "maximum": 12}, resolution={"enum": ["480P", "768P"]}),
                     H3MAX: _doc(image_url={}, duration={"minimum": 5, "maximum": 10}, resolution={"enum": ["480P", "1080P"]})})
    rows = {r["id"]: r for r in CL.refresh()}
    assert "moved its base price from 0.07 to 0.14" in rows[HEY]["stale"] and CL.usd_s(rows[HEY]) == 0.02 and CL.issues(rows[HEY]) == []      # watched, never used
    assert rows[PIX]["status"] == "deprecated" and rows[H3]["max_s"] == 12 and rows[H3]["elo"] == 1150 and rows[H3]["ranked"]
    assert "no field 'image_url'" in rows[H3]["schema"] and "size 768P is not offered" in rows[H3MAX]["schema"] and CL.issues(rows[H3]) and CL.issues(rows[H3MAX])
    _listing(monkeypatch, price=0.07); assert not {r["id"]: r for r in CL.refresh()}[H3].get("schema")                    # the schema is back: the row is eligible again
    monkeypatch.setattr(SC, "fal_status", lambda ids: (_ for _ in ()).throw(RuntimeError("offline"))); assert len(CL.refresh()) == 5      # a listing that does not answer changes nothing

def test_schema_issues_reads_fields_sizes_and_clip_lengths():
    r = dict(json.loads(core.DEFAULTS["CLIP_MODELS"][0])[0])
    assert CL.schema_issues(r, CL._props(_doc(image_url={}, duration={"minimum": 5, "maximum": 15}, resolution={"enum": ["480p", "768p"]}))) == ([], {})
    assert CL.schema_issues(r, CL._props(_doc(image_url={}, duration={"minimum": 3, "maximum": 8}, resolution={"enum": ["768p"]})))[1] == {"min_s": 3, "max_s": 8}
    assert CL.schema_issues(r, {})[0] == ["no input schema on the listing"] and "no field 'resolution'" in CL.schema_issues(r, CL._props(_doc(image_url={})))[0][0]
    assert CL._props({"components": {"schemas": {"Output": {"properties": {"video": {}}}, "Body": {"properties": {"prompt": {}, "image_url": {}}}}}}) == {"prompt": {}, "image_url": {}}

def test_the_weekly_review_switches_through_the_steward_once_and_tells_once_about_a_moved_price(market, setting, monkeypatch):
    _quiet(monkeypatch); _listing(monkeypatch); setting("FAL_HERO_MODEL", KLING); setting("PRICE_KLING_USD", "0.42")
    out = CL.review(); assert out["pick"] == HEY and out["fits"] and core.S("FAL_HERO_MODEL") == HEY and core.S("PRICE_KLING_USD", float) == pytest.approx(0.10)
    ch = core.store().rows("Model_Changes"); assert len(ch) == 1 and ch[0]["from"] == KLING and ch[0]["to"] == HEY and "picked by value" in ch[0]["why"]
    assert sum(1 for r in core.store().rows("Owner_Actions") if r["kind"] == "model_switch") == 1
    assert CL.review()["pick"] == HEY and len(core.store().rows("Model_Changes")) == 1                                    # the pick is the model in use: nothing happens twice
    _listing(monkeypatch, price=lambda i: 0.2 if i == H3 else 0.07); CL.review(); CL.review()
    told = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "clip_price"]; assert len(told) == 1 and "MiniMax H3" in told[0]["text"] and "nothing was switched" in told[0]["text"]
    setting("PRICE_KLING_USD", "0.33"); CL.review(); assert core.S("PRICE_KLING_USD", float) == pytest.approx(0.10)       # the price cell follows the row of the model in use

def test_the_weekly_scout_runs_the_review_and_no_longer_writes_the_listings_price_into_the_estimate(market, setting, monkeypatch):
    _quiet(monkeypatch); _listing(monkeypatch, price=0.14); setting("SCOUT_WEEKDAY", "0"); mon = dt.datetime(2026, 11, 16, 9, 0, tzinfo=dt.timezone.utc)
    res = SC.weekly(mon); assert res["clips"]["pick"] == HEY and "price_check" not in res and core.S("PRICE_KLING_USD", float) == pytest.approx(0.10)
    assert "CL.review(now)" in inspect.getsource(SC.weekly) and "refresh()" in inspect.getsource(CL.review)

def test_preflight_names_a_hero_model_that_left_or_changed(market, setting, monkeypatch):
    _listing(monkeypatch); ok, why = CL.preflight(); assert ok and "listed, active" in why
    _listing(monkeypatch, status={HEY: "deprecated"}); assert CL.preflight() == (False, f"fal lists {HEY} as deprecated")
    _listing(monkeypatch, schema={HEY: _doc(image_url={}, duration={}, resolution={"enum": ["1080p"]})}); ok, why = CL.preflight(); assert not ok and "size 768p is not offered" in why
    monkeypatch.setattr(SC, "fal_status", lambda ids: (_ for _ in ()).throw(RuntimeError("no route"))); assert CL.preflight()[0] is False
    setting("FAL_HERO_MODEL", "nobody/knows"); ok, why = CL.preflight(); assert not ok and "has no row in CLIP_MODELS" in why
    src = inspect.getsource(PF.run); assert "CL.preflight()" in src and 'add("clip model", cok, cwhy, critical=False)' in src          # a warning, never a block

# ------------------------------------------------------------------ bought by the second, measured on the file
def test_offline_a_hero_clip_is_as_long_as_it_was_bought_and_its_seconds_are_on_record_without_a_rupee(market, setting, tmp_path):
    from whatifs import release as REL
    img = MD.fake_image(str(tmp_path / "a.jpg"), 64, 36, 1); p = MD.animate(None, img, "p", str(tmp_path / "a.mp4"), "EPM1", hero=True, seconds=7.3)
    assert abs(REL.probe(p)["sec"] - 8) < 0.2
    MD.animate(None, img, "p", str(tmp_path / "b.mp4"), "EPM1", hero=True); MD.animate(None, img, "p", str(tmp_path / "c.mp4"), "EPM1"); MD.still("x", str(tmp_path / "s.jpg"), "EPM1")
    core.flush_costs(); rows = [(r["item"], float(r["units"]), float(r["inr"])) for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPM1"]
    assert rows == [("hero_clip", 8.0, 0.0), ("hero_clip", 5.0, 0.0), ("living_clip", 1.0, 0.0), ("image", 1.0, 0.0)] and core.month_spend() == 0
    setting("CLIP_VALUE_ON", "FALSE"); p = MD.animate(None, img, "p", str(tmp_path / "d.mp4"), "EPM2", hero=True, seconds=7.3); assert abs(REL.probe(p)["sec"] - 5) < 0.2

def _real(monkeypatch, tmp_path, clip_size):
    """The real request path of a clip, with the provider replaced: what was sent, and a clip of a chosen size 'downloaded'."""
    sent = []
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD, "fal_allowed", lambda: True)
    monkeypatch.setattr(MD, "fal_run", lambda model, args, timeout=0: sent.append((model, args)) or {"video": {"url": "x"}})
    monkeypatch.setattr(MD, "_dl", lambda url, path: _clip(path, *clip_size))
    return sent

def test_a_real_request_is_the_rows_request_and_its_cost_is_seconds_times_the_rows_price(market, monkeypatch, tmp_path):
    sent = _real(monkeypatch, tmp_path, (90, 160)); pic = MD.fake_image(str(tmp_path / "p.png"), 90, 160, 2)
    MD.animate("https://img", pic, "P", str(tmp_path / "o.mp4"), "EPM3", hero=True, seconds=6.2)
    assert sent == [(HEY, CL.args(CL.row(HEY), "https://img", "P", 6.2))] and sent[0][1]["duration"] == 7
    core.flush_costs(); row = next(r for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPM3")
    assert (row["item"], float(row["units"])) == ("hero_clip", 7.0) and float(row["inr"]) == pytest.approx(7 * 0.02 * core.S("USD_INR", float), abs=0.01)

def test_a_clip_of_another_shape_than_its_start_picture_is_a_failed_clip(market, monkeypatch, tmp_path):
    up = MD.fake_image(str(tmp_path / "up.png"), 90, 160, 3)
    assert CL.shape_ok(_clip(str(tmp_path / "u.mp4"), 180, 320), up)[0] and CL.shape_ok(_clip(str(tmp_path / "s.mp4"), 88, 160), up)[0]          # the same shape, another size
    ok, words = CL.shape_ok(_clip(str(tmp_path / "w.mp4"), 160, 90), up); assert not ok and "160 x 90" in words and "90 x 160" in words
    assert CL.shape_ok(str(tmp_path / "missing.mp4"), up) == (True, "not measured")
    _quiet(monkeypatch); _real(monkeypatch, tmp_path, (160, 90))                                    # the model answers with a WIDE clip for an upright picture
    with pytest.raises(RuntimeError, match="another shape than its start picture"): MD.animate("https://img", up, "P", str(tmp_path / "x.mp4"), "EPM4", hero=True, seconds=5)
    assert STW.health()[HEY]["fails"] == 1 and core.S("FAL_HERO_MODEL") == HEY                      # reported to the Steward like any failure; three in a row switch
    _real(monkeypatch, tmp_path, (90, 160)); assert MD.animate("https://img", up, "P", str(tmp_path / "y.mp4"), "EPM4", hero=True, seconds=5)

# ------------------------------------------------------------------ a Short: one clip as long as its shot
def test_a_short_buys_each_shot_one_clip_as_long_as_the_shot_and_slows_nothing(market):
    for fmt in FMT.SHORTS:
        sc = good(fmt); t = tl(sc); pl = SH.plan(sc, t, fmt); shots = pl["shots"]; paid = shots[:-1]; loop = shots[-1]
        for s in paid:
            ln = s["end"] - s["start"]; assert s["buy"] == CL.secs(CL.row(HEY), ln) >= ln and s["slow"] == 1.0 and ln <= 10.01, (fmt, s)
        assert loop["src"] == "loop" and loop["buy"] == 0 and loop["slow"] == 1.0 and loop["end"] - loop["start"] <= paid[0]["buy"] + 0.01          # the loop is no slower than the clip it returns
        assert SEAT.shape_report(sc, fmt, t["units"], SEAT.shape(pl, sc, fmt))["problems"] == [], fmt
        assert sum(s["buy"] for s in paid) == next(l["n"] for l in CG.lines("short", fmt=fmt, shots=shots, seconds=pl["seconds"]) if l["key"] == "hero_clips")
    sc = good("S1"); t = tl(sc, pace=0.9); pl = SH.plan(sc, t, "S1")                                 # a slow voice: beats of more than 10 seconds are split
    assert max(s["end"] - s["start"] for s in pl["shots"]) <= 10.01 and len(pl["shots"]) > 5 and all(s["slow"] == 1.0 for s in pl["shots"][:-1])
    long = dict(pl, shots=[dict(pl["shots"][0], end=12.5)] + pl["shots"][1:])
    assert any("one clip covers at most 10 s" in p for p in SEAT.shape_report(sc, "S1", t["units"], long)["problems"])

def test_with_the_market_off_a_shorts_clips_are_five_seconds_and_slowed_and_an_older_short_keeps_how_it_was_played(setting):
    sc = good("S2"); pl = SH.plan(sc, tl(sc), "S2"); paid = pl["shots"][:-1]
    assert all(s["buy"] == 5 for s in paid) and any(s["slow"] > 1.0 for s in paid) and max(s["slow"] for s in pl["shots"]) <= 1.3 + 1e-6
    assert SH.slow_of({"start": 0.0, "end": 6.5}) == pytest.approx(1.3) and SH.slow_of({"start": 0.0, "end": 4.0}) == 1.0          # a Short planned before this batch has no 'slow' on its plan
    assert SH.slow_of({"start": 0.0, "end": 6.5, "slow": 1.0}) == 1.0 and "SH.slow_of(s)" in inspect.getsource(OPEN.manifest)       # ... and the opening of its long video reads the plan

# ------------------------------------------------------------------ the cost model: one table of lines
def test_every_estimate_is_the_same_table_of_lines(market, setting):
    for kind in ("long", "ladder"):
        L = CG.lines(kind); assert all(l["inr"] == pytest.approx(l["n"] * l["unit_inr"], abs=0.02) for l in L) and len({l["key"] for l in L}) == len(L)
        assert G.full_episode_inr(kind=kind) == CG.total(L) == pytest.approx(sum(l["inr"] for l in L), abs=0.01)
    d = {"stills": 48, "living": 4, "kling": 4, "episode_id": "EPL"}
    assert EP.est_cost_inr(d) == CG.total(CG.lines("long", kling=4, stills=48, living=4)) and G.full_episode_inr() == CG.total(CG.lines(G.long_kind()))
    assert G.min_episode_cost_inr() == CG.total(CG.lines("long", kling=core.S("KLING_MIN_CLIPS", int), stills=core.S("STILLS_MIN", int), living=0)) < G.full_episode_inr()
    for f in FMT.SHORTS: assert SH.est_inr(f) == round(CG.total(CG.lines("short", fmt=f)), 1)
    sh = FMT.short_shares(); assert G.short_inr() == pytest.approx(sum(SH.est_inr(f) * w for f, w in sh.items()) / sum(sh.values()), abs=0.1) and RP.short_inr() == G.short_inr()
    E = CG.estimate_lines(); assert abs(sum(E.values()) - G.full_episode_inr(kind="long") - E["community"]) < 1.0 and E["tts"] == pytest.approx(CG.voice_inr(540), abs=0.1)
    assert M.ai_estimate_inr() == core.S("LLM_EST_INR", float) + core.S("THINK_EST_INR", float) + core.S("ROOM_EXTRA_EST_INR", float)
    before = G.full_episode_inr(kind="long"); setting("PRICE_GEM_IMAGE_USD", "0.5")
    assert G.full_episode_inr(kind="long") == pytest.approx(before + 4 * (0.5 - 0.067) * core.S("USD_INR", float), abs=0.05)          # a price cell moves its line and nothing else

def test_the_table_read_is_money_only_where_it_runs(market, setting):
    keys = lambda: {l["key"] for l in CG.lines("long")}
    assert core.S("ROOM_MODE") == "v2" and core.S("TABLE_READ_MODE") == "on" and "table_read" not in keys() and not CG.table_read_runs()      # the room in use never runs it
    base = G.full_episode_inr(kind="long"); setting("ROOM_MODE", "v1")
    assert "table_read" in keys() and G.full_episode_inr(kind="long") == pytest.approx(base + 55) and M.ai_estimate_inr() == pytest.approx(170 + 40 + 20 + 55)
    assert CG.table_read_runs(False) is False and CG.total(CG.lines("long", table_read=False)) == pytest.approx(base)                       # the older room's alternate arm: off for this episode
    setting("TABLE_READ_MODE", "off"); assert "table_read" not in keys()

def test_a_long_video_about_a_promoted_short_is_its_own_kind(market, setting):
    lo = {l["key"]: l for l in CG.lines("long")}; la = {l["key"]: l for l in CG.lines("ladder")}; u = core.S("USD_INR", float)
    assert (lo["hero_clips"]["n"], la["hero_clips"]["n"]) == (20, 15) and (lo["start_frames"]["n"], la["start_frames"]["n"]) == (4, 3) and "hook_lab" in lo and "hook_lab" not in la
    assert lo["hero_clips"]["calls"] == {"clip_kling": 4} and la["hero_clips"]["calls"] == {"clip_kling": 3} and la["start_frames"]["calls"] == {"image_ref": 3}
    assert CG.total(list(lo.values())) - CG.total(list(la.values())) == pytest.approx(5 * 0.02 * u + 0.067 * u + core.S("HOOK_LAB_EST_INR", float), abs=0.02)
    setting("LADDER_ON", "TRUE"); assert G.long_kind() == "long"                                    # nothing promoted yet: the next long video opens on its own pictures (an override)
    core.store().append("Ladder", [{"id": "SHK1", "premise": "p", "state": "PROMOTED"}]); assert G.long_kind() == "ladder" and G.full_episode_inr() == CG.total(list(la.values()))
    setting("OWNER_NEXT_PREMISE", "his own topic"); assert G.long_kind() == "long"
    setting("OWNER_NEXT_PREMISE", ""); setting("OPENING_SHORT_ON", "FALSE"); assert G.long_kind() == "long"

def test_start_pictures_stills_and_the_voice_are_counted_at_what_is_really_paid(market, setting, monkeypatch):
    L = {l["key"]: l for l in CG.lines("long")}; u = core.S("USD_INR", float)
    assert L["start_frames"]["inr"] == pytest.approx(4 * 0.067 * u, abs=0.01) and L["stills"]["unit_inr"] == pytest.approx(0.006 * u) and L["stills"]["n"] == 52
    assert L["key_art"]["n"] == G.premium_images() == 2 and L["living_clips"]["n"] == 8 and L["probe"]["calls"] == {"text:probe_gemini": 1, "text:probe_claude": 1}
    one = T.est_inr(540); assert L["voice"]["inr"] == pytest.approx(2 * one, abs=0.01)             # the narration and one re-take
    setting("TTS_RETAKES", "0"); assert CG.voice_inr(540) == pytest.approx(one)
    setting("TTS_RETAKES", "1"); monkeypatch.setattr(T, "now_utc", lambda: dt.datetime(2027, 1, 2, tzinfo=dt.timezone.utc)); assert CG.voice_inr(540) == pytest.approx(4 * one)      # the price doubles on 1 Jan 2027: the estimate follows
    setting("TTS_ENGINE", "kokoro"); assert CG.voice_inr(540) == 0 and "TTS_EST_INR" not in core.DEFAULTS
    assert G.tier_saving(G.TIERS[1]) == pytest.approx(u * (4 * 0.006 + 4 * 0.02), abs=0.01)         # a tier's saving at the still price really paid

def test_a_short_has_lines_of_its_own(market, setting):
    for fmt, secs_, pics in (("S1", 28, 4), ("S2", 36, 4), ("S3", 28, 1)):          # the middle of the band, every beat a paid clip of whole seconds (the loop's saving is not counted: upward only)
        L = {l["key"]: l for l in CG.lines("short", fmt=fmt)}; assert list(L) == ["hero_clips", "pictures", "writing", "voice"]
        assert (L["hero_clips"]["n"], L["hero_clips"]["unit"], L["hero_clips"]["item"], L["pictures"]["n"]) == (secs_, "s", "hero_clip", pics), (fmt, L["hero_clips"])
        assert L["writing"]["inr"] == core.S("REPLAN_SHORT_INR", float) and L["writing"]["calls"] == {"text:short_writer": core.S("SHORTS_VARIANTS", int) + 1}
        lo, hi = FMT.short_len(fmt); assert L["voice"]["inr"] == pytest.approx(2 * T.est_inr((lo + hi) / 2), abs=0.01) and L["voice"]["calls"] == {"voice_job": 1}
    assert 90 < SH.est_inr("S1") < 100 and SH.est_inr("S2") > SH.est_inr("S1") > SH.est_inr("S3")
    setting("CLIP_VALUE_ON", "FALSE"); setting("FAL_HERO_MODEL", KLING); setting("PRICE_KLING_USD", "0.42")
    old = {l["key"]: l for l in CG.lines("short", fmt="S1")}; assert old["hero_clips"]["n"] == 30 and old["hero_clips"]["calls"] == {"clip_kling": 6} and 280 < SH.est_inr("S1") < 295

def test_reconcile_names_a_paid_item_without_a_line_and_a_counted_line_that_was_exceeded(market):
    def paid(ep, *rows): core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": ep, "item": i, "provider": p, "units": n, "inr": 0} for i, p, n in rows])
    L = CG.lines("ladder"); paid("EPR1", ("hero_clip", "fal", 5), ("hero_clip", "fal", 10), ("image_ref", "google", 3), ("image", "fal", 60), ("living_clip", "fal", 9), ("image_premium", "fal", 2), ("claude_writer", "anthropic", 900))
    r = CG.reconcile("EPR1", L, "ladder"); assert r["unlisted"] == [] and r["over"] == [] and r["paid"]["hero_clip"] == 15 == r["lines"]["hero_clip"] and "claude_writer" not in r["paid"]
    row = next(x for x in core.store().rows("Cost_Log") if x["episode_id"] == "EPR1" and x["item"] == "cost_lines_summary")
    assert (row["basis"], row["provider"], float(row["inr"])) == ("summary", "summary", 0.0) and row["role"].startswith("ladder: {") and float(row["est_inr"]) == CG.total(L)
    paid("EPR2", ("hero_clip", "fal", 20), ("image_ref", "google", 4), ("stock_clip", "fal", 1)); r = CG.reconcile("EPR2", L, "ladder")
    assert r["unlisted"] == ["stock_clip"] and r["over"] == ["hero_clip: 20 paid, 15 estimated", "image_ref: 4 paid, 3 estimated"]
    assert CG.reconcile("EPR1", L)["paid"]["hero_clip"] == 15 and core.month_spend() == 0           # a summary row is never spend and is never read as a paid item
    from tools.sweep import money_of
    ok, words = money_of(core, ["EPR1"]); assert ok and "15 of 15 estimated seconds of hero clip" in words
    ok, words = money_of(core, ["EPR1", "EPR2", "EPR9"]); assert not ok and "paid with no line in the estimate: stock_clip" in words and "more paid than estimated" in words and "EPR9: no estimate" in words

# ------------------------------------------------------------------ the month's split
def test_the_months_split_says_how_many_shorts_fit(market, setting, monkeypatch):
    monkeypatch.setattr(G, "episodes_left_this_month", lambda: 4)
    sp = G.split(DEC); assert sp["fits"] and sp["fit"] == sp["plan"] == 12 and sp["long_left"] == 4 and sp["reserve_inr"] == 300 and sp["free_inr"] > 900, sp
    assert sp["need_long_inr"] == pytest.approx(4 * G.full_episode_inr() * 1.1, abs=1) and sp["short_inr"] == pytest.approx(G.short_inr(), abs=0.1)
    setting("FAL_HERO_MODEL", H3); sp = G.split(DEC); assert not sp["fits"] and sp["fit"] == 8, sp           # at USD 0.06 a second: eight, not twelve
    setting("FAL_HERO_MODEL", KLING); sp = G.split(DEC); assert not sp["fits"] and sp["fit"] == 5, sp        # at the price of the model this batch replaced: five
    setting("SHORTS_PER_MONTH", "4"); assert G.split(DEC)["fits"] and G.split(DEC)["fit"] == 4
    setting("SHORTS_PER_MONTH", "12"); setting("MONTH_RESERVE_INR", "0"); assert G.split(DEC)["fit"] == 6
    mid = DEC.replace(day=16); setting("MONTH_RESERVE_INR", "300"); assert G.split(mid)["reserve_inr"] == pytest.approx(300 * 16 / 31, abs=1)      # the reserve belongs to the days left

def _made(n, now, apart_h=60):
    core.store().append("Specials", [{"ts": core.iso(now - dt.timedelta(hours=apart_h * (i + 1))), "id": f"SHM{i}", "kind": "short", "format": "S1", "status": "POSTED", "made": "x", "premise": f"p{i}"} for i in range(n)])

def test_the_cadence_makes_what_fits_spread_over_the_month_and_the_owner_is_told_once(market, setting, monkeypatch):
    _quiet(monkeypatch); now = DEC.replace(day=11); fit = {"fits": False, "fit": 5, "plan": 12, "days_left": 21, "short_inr": 233.0, "long_left": 3, "need_long_inr": 1700.0, "room_inr": 2500.0}
    monkeypatch.setattr(G, "split", lambda n=None: dict(fit)); _made(3, now)                              # three made this month (two of them in the last 7 days), the last 60 hours ago; five fit
    due, why = SH.cadence(now); assert not due and "252 hours apart" in why, why                          # 2 more in 21 days: one every 252 hours, not every 48
    fit["fit"] = 3; due, why = SH.cadence(now); assert not due and "this month's money pays 3 Shorts" in why and "12 were planned" in why
    fit.update(fits=True, fit=12); assert SH.cadence(now)[0]                                              # the plan fits: the cadence of three a week, 48 hours apart
    fit.update(fits=False, fit=5); setting("SPLIT_ON", "FALSE"); assert SH.cadence(now)[0]                # the switch off: as before this batch
    setting("SPLIT_ON", "TRUE"); assert SH.made_this_month(now) == 3 and SH.made_this_month(now.replace(month=11)) == 0
    assert G.split_tell(now) is True and G.split_tell(now) is False and core.S("SPLIT_TOLD_MONTH") == "2026-12"
    told = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "split"]; assert len(told) == 1 and "pays 5 Shorts, not the 12 planned" in told[0]["text"] and "no quality check was lowered" in told[0]["text"]
    fit.update(fits=True); setting("SPLIT_TOLD_MONTH", ""); assert G.split_tell(now) is False             # the plan fits: nobody is told
    assert "GVR.split_tell()" in inspect.getsource(MG) and "G.split(now)" in inspect.getsource(SH.cadence)

def test_a_short_whose_real_plan_the_month_cannot_pay_is_not_made_and_no_picture_is_paid(market, setting, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    q2(monkeypatch); _bench("What if the Moon left tonight?"); calls = []
    monkeypatch.setattr(MD, "animate", lambda *a, **k: calls.append("clip")); real = SH.est_inr
    monkeypatch.setattr(SH, "est_inr", lambda fmt, pl=None: real(fmt, pl) + (5000 if pl else 0))          # the plan turns out far dearer than the format's estimate
    r = SH.run(force=True, publish=False, now=DEC); assert r == {"ok": False, "skipped": "budget", "why": r["why"], "id": r["id"]} and calls == []
    row = next(x for x in core.store().rows("Specials") if x["id"] == r["id"]); assert row["status"].startswith("FAILED (money:") and not SH._made(row) and SH._failed(row)

# ------------------------------------------------------------------ a live Sheet is moved once
def test_the_one_time_move_picks_the_model_and_marks_the_old_cells_once(market, setting, monkeypatch):
    _quiet(monkeypatch); st = core.store()
    setting("V12V2D_MOVE_DONE", ""); setting("FAL_HERO_MODEL", KLING); setting("PRICE_KLING_USD", "0.42"); setting("LLM_EST_INR", "176")
    st.append("Settings", [{"key": "TTS_EST_INR", "value": "30", "note": "allowance per video for the voice"}])
    done = MG.v12v2d_upgrade(st); assert done == ["LLM_EST_INR", "TTS_EST_INR", "FAL_HERO_MODEL"], done
    assert core.S("FAL_HERO_MODEL") == HEY and core.S("PRICE_KLING_USD", float) == pytest.approx(0.10) and core.S("LLM_EST_INR") == "170" and core.S("V12V2D_MOVE_DONE")
    tts = next(r for r in st.rows("Settings") if r["key"] == "TTS_EST_INR"); assert tts["value"] == "30" and tts["note"].startswith("RETIRED (v12 V2d)")
    assert [(r["from"], r["to"]) for r in st.rows("Model_Changes")] == [(KLING, HEY)] and any(r["kind"] == "model_switch" for r in st.rows("Owner_Actions"))
    setting("FAL_HERO_MODEL", KLING); setting("LLM_EST_INR", "176"); assert MG.v12v2d_upgrade(st) == [] and core.S("FAL_HERO_MODEL") == KLING      # never twice: his later choice stands
    setting("V12V2D_MOVE_DONE", ""); setting("LLM_EST_INR", "200"); setting("FAL_HERO_MODEL", HEY); assert MG.v12v2d_upgrade(st) == [] and core.S("LLM_EST_INR") == "200"      # a value he typed is left alone
    assert inspect.getsource(MG).count("v12v2d_upgrade(st)") == 3                                   # the definition and both setup sites

# ------------------------------------------------------------------ whole productions: the counter and the estimate agree
def _covered(counter, L):
    """Every paid call the counter saw has a line of the estimate that stands for it; a counted line is never exceeded. Returns the problems."""
    exact = {}; bad = []
    for l in L:
        for k, n in l["calls"].items():
            if n is not None: exact[k] = exact.get(k, 0) + n
    text = any(set(CG.TEXT) <= set(l["calls"]) for l in L) or any(k.startswith("text:") for k in exact)
    for k, n in counter.items():
        if k in exact:
            if k in ("clip_kling", "image_ref", "image_premium", "voice_job") and n != exact[k]: bad.append(f"{k}: {n} paid, {exact[k]} in the estimate")
            elif n > exact[k] and not k.startswith("text:"): bad.append(f"{k}: {n} paid, {exact[k]} in the estimate")
        elif not (k.startswith(CG.TEXT) and text): bad.append(f"{k}: paid {n} time(s), no line in the estimate")
    return bad

def _summary(ep):
    row = next(x for x in core.store().rows("Cost_Log") if x["episode_id"] == ep and x["item"] == "cost_lines_summary")
    return json.loads(str(row["role"]).partition(": ")[2]), row

def test_whole_shorts_pay_exactly_the_seconds_their_plan_said(market, setting, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    q2(monkeypatch); _bench("What if the Moon left tonight?", "What if gravity doubled for one hour?", "What if the Sun went out?")
    for i, fmt in enumerate(("S1", "S2", "S3")):
        setting("SHORT_FORMAT_FORCE", fmt); c = watch(monkeypatch); r = SH.run(force=True, publish=False, now=DEC + dt.timedelta(days=3 * i)); assert r.get("ok"), r
        j, row = _summary(r["id"]); mk = next(json.loads(t["measures"]) for t in core.store().rows("Takeaways") if t["episode_id"] == r["id"] and t["trigger"] == "make")
        assert j["unlisted"] == [] and j["over"] == [] and j["paid"]["hero_clip"] == j["lines"]["hero_clip"] == mk["paid_s"] and j["paid"]["image"] == j["lines"]["image"] == mk["pictures"]
        assert c["clip_kling"] == mk["clips"] and c["voice_job"] == 1 and c["text:short_writer"] <= core.S("SHORTS_VARIANTS", int) + 1 and row["role"].startswith(f"short {fmt}: ")
        assert float(row["est_inr"]) <= SH.est_inr(fmt) + 0.05 and mk["paid_s"] >= float(r["sec"]) - 6.6, (fmt, row["est_inr"], SH.est_inr(fmt))      # the estimate said before the script covers what the plan bought
        monkeypatch.undo(); q2(monkeypatch)

def test_whole_long_videos_the_counter_and_the_lines_agree_call_by_call(market, setting, monkeypatch, tmp_path):
    from tools.sweep import climb, money_of
    from tests import test_v12_opening_e2e as E2E
    E2E._start(monkeypatch, setting); A, B, sid = "EP209903010900", "EP209903080900", "SH209903010900"
    assert climb(core, A) is True; c = watch(monkeypatch); r = EP.produce(E2E._slot(10), episode_id=A); a = dict(c); assert r.get("ok"), r
    L = CG.lines("ladder"); assert _covered(a, L) == [], (_covered(a, L), a)
    assert (a["clip_kling"], a["image_ref"], a["image_premium"], a["voice_job"], a.get("text:hooks", 0)) == (3, 3, 2, 1, 0), a
    j, row = _summary(A); assert j["unlisted"] == [] and j["over"] == [] and j["paid"]["hero_clip"] == 15 == j["lines"]["hero_clip"] and row["role"].startswith("ladder: ")
    assert j["paid"]["image"] <= j["lines"]["image"] and j["paid"].get("living_clip", 0) <= j["lines"]["living_clip"]
    ok, words = money_of(core, [A, sid]); assert ok and f"{A} (ladder): 15 of 15" in words and f"{sid} (short" in words, words
    E2E._new_sheet(tmp_path, "sheet_b.json"); LAD.override("owner", "make it anyway"); c.clear()                # another Sheet: a long video under an override opens on its own pictures
    r2 = EP.produce(E2E._slot(10), episode_id=B); b = dict(c); assert r2.get("ok"), r2
    L2 = CG.lines("long"); assert _covered(b, L2) == [], (_covered(b, L2), b)
    assert (b["clip_kling"], b["image_ref"], b["image_premium"], b["voice_job"]) == (4, 4, 2, 1) and b.get("text:hooks", 0) >= 1, b
    j2, row2 = _summary(B); assert j2["unlisted"] == [] and j2["over"] == [] and j2["paid"]["hero_clip"] == 20 == j2["lines"]["hero_clip"] and row2["role"].startswith("long: ")
    assert float(row2["est_inr"]) > float(row["est_inr"]) > 300                                     # each at its own tier; what the two kinds differ by is pinned in the kind's own test
    extra = dict(b, clip_kling=5); assert _covered(extra, L2) == ["clip_kling: 5 paid, 4 in the estimate"]
    assert _covered(dict(b, stock=1), L2) == ["stock: paid 1 time(s), no line in the estimate"]

# ------------------------------------------------------------------ wiring
def test_the_batch_is_wired_protected_and_documented():
    prot = open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read()
    assert '"whatifs/clips.py"' in prot and '"whatifs/costguard.py"' in prot and "whatifs/clips.py" in REG.DEPTS["D6"]["wraps"]
    for k in ("CLIP_VALUE_ON", "CLIP_MODELS", "SPLIT_ON", "MONTH_RESERVE_INR", "HOOK_LAB_EST_INR", "PROBE_EST_INR", "TTS_RETAKES", "SPLIT_TOLD_MONTH", "V12V2D_MOVE_DONE"):
        assert k in core.DEFAULTS and core.DEFAULTS[k][1], k
    assert OLD_CLIPS["CLIP_VALUE_ON"] == "FALSE" and OLD_CLIPS["FAL_HERO_MODEL"] == KLING and core.DEFAULTS["CLIP_VALUE_ON"][0] == core.DEFAULTS["SPLIT_ON"][0] == "TRUE"
    sw = open(os.path.join(ROOT, "tools", "sweep.py"), encoding="utf-8").read(); assert sw.count("money_of(core, ") == 3 and '"money_agreed"' in sw
    assert "CG.reconcile(ep, " in inspect.getsource(SH.run) and "CG.reconcile(ep, " in inspect.getsource(EP) and "seconds=sec" in inspect.getsource(SH.make)
    facts = open(os.path.join(ROOT, "docs", "CURRENT", "PLATFORM_FACTS.md"), encoding="utf-8").read()
    assert "BASE price" in facts and "2026-11-13" in facts and HEY in facts
