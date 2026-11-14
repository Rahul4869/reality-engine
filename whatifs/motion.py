"""The motion ladder (Visual Production, D6): the moving seconds of a video as a budget - placed by code on lines that can show a whole clip, cut by one rule the renderer and the checks share, and found again on the finished file. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import math, subprocess
from whatifs.core import S, log

MOVING = ("kling", "living")      # the shot types that carry a clip made by a model
CELL_S = 0.5                      # the finished file is judged in half seconds ...
READ_FPS = 8                      # ... read at eight pictures a second ...
GAP_LONG = 6                      # ... a long video by two pictures three quarters of a second apart: its renderer adds grain, and a HELD picture under grain still changes a
                                  # little from frame to frame - over three quarters of a second real motion has left that noise behind (measured, see MOVING_CHANGE_MIN)
GAP_SHORT = 4                     # ... a Short by two pictures half a second apart: it has no grain, a held picture does not change at all (two such half seconds in a row = a second held)
RUN = 2                           # a stretch does NOT move when this many half seconds in a row do not change (a second or more: one quiet half second is no freeze)
EDGE_S = 0.05                     # no picture is taken closer than this to where a stretch begins or ends (film and clip can be a frame apart at a cut)
GRID = 96                         # the long side of the small grey copy two pictures are compared on
REGION = (0.2, 0.8, 0.15, 0.85)   # the part of a wide film that is compared (x from, x to, y from, y to): its middle - no chip, no bar, no caption
BAND = (0.0, 1.0, 0.30, 0.52)     # the part of an upright Short that is compared: the band that never carries words (under the promise text, above the captions)
# From which mean change (grey levels of 255) between its two pictures a half second MOVES is a Settings cell with the measurements in its note:
# MOVING_CHANGE_MIN for a long video, SHORT_CHANGE_MIN for a Short.
NEXT_MIN_S = 1.0                  # a still whose line a clip runs into keeps at least this long of its own (else the clip covers it whole)
TAIL_MIN_S = 1.0                  # what is left of a line after its clip is cut as a still of its own only from this length on (a shorter rest: the clip is played that little slower)
SPARE_S = 0.25                    # a clip is bought only where its lines can show it whole AND this much more: a clip file can be a few frames longer than the seconds bought
                                  # (v12 V2d-b red 1: a quarter second LESS was allowed, and a paid clip was cut by construction)

def on():
    from whatifs import clips as CL
    return CL.ladder()

# ------------------------------------------------------------------ the lines of a video and what a clip can show on them
def lines_of(units, total):
    """[(start, end)] of every line's PICTURE: a picture changes where the next line starts (the narration is the master clock), the last ends with the film."""
    b = [0.0] + [float(u["start"]) for u in units[1:]] + [float(total)]
    return [(b[i], max(b[i], b[i + 1])) for i in range(len(units))]

def plain(shot):
    """A still a clip may run into: a made picture with nothing of its own that must be seen at its first frame. v12 V2b: never an act's first picture
    (the camera path's `path.first`): no scene and no living clip covers the first line of the next act."""
    return shot.get("type") == "still" and not shot.get("short") and not shot.get("promise") and not shot.get("anim") and not (shot.get("path") or {}).get("first")

def cap_s(row=None):
    """The longest ONE clip of a still brought to life: the model's longest clip, and never longer than two picture states may hold (check visual_change)."""
    from whatifs import clips as CL
    return float(min(CL.longest(row) if row else CL.LONGEST_S, 2 * S("VISUAL_CHANGE_MAX_S", float)))

def room_s(i, shots, sp, busy=()):
    """How many seconds a clip that STARTS on line i can be shown: its own line, and on into the plain stills that follow it (never into a line that
    carries a clip, a graphic, real footage or a character, and never into a line another clip already runs into)."""
    r = sp[i][1] - sp[i][0]; j = i + 1
    while j < len(shots) and plain(shots[j]) and j not in busy: r += sp[j][1] - sp[j][0]; j += 1
    return r

def covers(i, secs, shots, sp, busy=()):
    """The lines after i that a clip of `secs` seconds starting on line i runs into (wholly or in part)."""
    out = []; left = secs - (sp[i][1] - sp[i][0]); j = i + 1
    while left > 1e-6 and j < len(shots) and plain(shots[j]) and j not in busy: out.append(j); left -= sp[j][1] - sp[j][0]; j += 1
    return out

def scene_s():
    """The seconds one animated scene of a long video is bought at (the hero model's row: never under its shortest clip)."""
    from whatifs import clips as CL
    r = CL.hero()
    return float(CL.secs(r, CL.SCENE_S)) if r else float(CL.SCENE_S)

def scene_fit(shots, units, total=None):
    """For the Animation Director: can an animated scene on line i be shown WHOLE (its own line and the plain stills it may run into hold the whole
    scene and SPARE_S)? A scene goes only where this is true - a scene no line can show whole is not bought."""
    sp = lines_of(units, float(total if total is not None else (units[-1].get("end") or units[-1].get("start") or 0) if units else 0)); need = scene_s() + SPARE_S
    return lambda i: i < len(sp) and room_s(i, shots, sp) >= need - 1e-6

def merge(bounds, shots, merged, keep=MOVING):
    """THE RENDERER'S MERGE, one rule for the renderer and the tests: a line shorter than UNIT_MERGE_SEC continues the picture before it (no sub-second
    flash) - never a line whose shot is of a type in `keep` (a line that carries a paid clip: its clip would start late and lose its end; with the motion
    ladder off only a scene, as before). `bounds` is changed in place; the merged lines are added to `merged`."""
    lim = S("UNIT_MERGE_SEC", float)
    for i in range(1, len(bounds) - 1):
        if i < len(shots) and bounds[i + 1] - bounds[i] < lim and shots[i].get("type") not in keep and i - 1 not in merged:
            bounds[i] = bounds[i + 1]; merged.add(i)
    return bounds

# ------------------------------------------------------------------ the placing: living seconds on the lines that can show them
def place(shots, units, total, plan):
    """THE LIVING SECONDS OF A LONG VIDEO, PLACED BY CODE (pure but for the Settings it reads; before any picture is paid). `plan["living_s"]` is the
    budget. The Director's own living shots are kept where a whole clip can be shown; then, until the seconds are used, the still that is farthest
    in time from everything that already moves is brought to life (the longer line when two are as far). Each clip is bought at the whole seconds
    of its line - never under the model's shortest clip, never over cap_s - and a living shot that cannot be shown whole becomes a still again.
    Returns the shots; the plan gets `living` (the clips placed) and `living_bought_s`."""
    from whatifs import clips as CL
    lr = CL.living()
    if lr is None or not shots or not units: return shots
    out = [dict(s) for s in shots[:len(units)]] + [dict(s) for s in shots[len(units):]]
    if plan.get("living_s") is None: plan["living_s"] = int(plan.get("living") or 0) * int(CL.SCENE_S)      # a plan saved before the motion ladder says clips, not seconds
    budget = int(plan.get("living_s") or 0); sp = lines_of(units, total); lo = int(lr.get("min_s") or CL.SCENE_S); cap = cap_s(lr)
    n = min(len(out), len(sp)); used = 0; busy = set(); placed = []; freed = []; dropped = []
    asked = [i for i in range(n) if out[i].get("type") == "living" and not out[i].get("short")]
    for i in asked: out[i]["type"] = "still"; out[i].pop("buy", None)
    need = scene_s() + SPARE_S                                          # v12 V2d-b red 1: THE SCENES' ROOM IS RESERVED FIRST - the lines each animated scene runs on into are never
    for i in [k for k in range(n) if out[k].get("type") == "kling" and not out[k].get("short")]:      # taken by a living clip (one did, and three scenes of 5 s were shown for 1.5 to 4.4 s)
        r = sp[i][1] - sp[i][0]; j = i + 1
        while r < need - 1e-6 and j < n and j not in busy and not out[j].get("short") and not out[j].get("promise") and not out[j].get("anim") \
                and (plain(out[j]) or out[j].get("type") in ("stock", "reaction")):
            if not plain(out[j]):                                          # an anchor of real footage or a cutaway inside a scene's seconds becomes a plain still the scene runs over
                freed.append(f"{j} ({out[j]['type']})"); out[j]["type"] = "still"; out[j]["prompt"] = out[j].get("prompt") or str(units[j].get("text") or "")
                for k_ in ("search", "stock_s", "speaker"): out[j].pop(k_, None)
            r += sp[j][1] - sp[j][0]; j += 1
        if r < need - 1e-6:                                                # even so it cannot be shown whole: NOT BOUGHT (a paid scene that is cut is money nobody sees)
            out[i]["type"] = "still"; out[i].pop("anim", None); out[i].pop("promise", None); dropped.append(i)
            if plan.get("kling"): plan["kling"] = max(0, int(plan["kling"]) - 1)
            continue
        busy.update(covers(i, need, out, sp, busy))
    moving = [(sp[i][0] + sp[i][1]) / 2 for i in range(n) if out[i].get("type") == "kling" or out[i].get("short")]
    def can(i): return out[i].get("type") == "still" and not out[i].get("short") and not out[i].get("promise") and not out[i].get("anim") and i not in busy
    def take(i):
        nonlocal used
        own = sp[i][1] - sp[i][0]; r = room_s(i, out, sp, busy)
        b = CL.secs(lr, min(max(own, lo), cap))
        while b > lo and b + SPARE_S > r + 1e-6: b -= 1                  # never buy a second that its lines cannot show (with SPARE_S to the frame)
        if b + SPARE_S > r + 1e-6 or used + b > budget: return False
        out[i].update(type="living", buy=int(b)); used += int(b); placed.append(i); moving.append((sp[i][0] + sp[i][1]) / 2)
        busy.update(covers(i, b + SPARE_S, out, sp, busy)); return True
    for i in asked:
        if can(i): take(i)
    while budget - used >= lo:
        cand = [i for i in range(n) if can(i)]                            # take() alone decides whether a line's room shows a whole clip (a second filter here hid a broken one: red 1)
        if not cand: break
        def far(i):
            t = (sp[i][0] + sp[i][1]) / 2
            return (min((abs(t - m) for m in moving), default=float(total)), sp[i][1] - sp[i][0], -i)
        took = False
        for i in sorted(cand, key=far, reverse=True):
            if take(i): took = True; break
        if not took: break
    plan["living"] = len(placed); plan["living_bought_s"] = used
    if asked or placed or freed or dropped:
        log(f"motion ladder: {len(placed)} stills brought to life for {used} of {budget} planned seconds"
            + (f"; {len([i for i in asked if i not in placed])} of the Director's living shots sit on lines too short for a whole clip and stay stills" if [i for i in asked if i not in placed] else "")
            + (f"; line(s) {', '.join(freed)} became plain stills inside a scene's seconds" if freed else "")
            + (f"; {len(dropped)} scene(s) at {dropped} cannot be shown whole and are NOT bought" if dropped else ""))
    return out

# ------------------------------------------------------------------ the cutting: one rule for the renderer and for the checks
def carry(bounds, shots, secs, merged=None):
    """A PAID CLIP IS SHOWN WHOLE: where a clip is longer than its own line it runs on into the plain stills that follow - the next picture starts when
    the clip is over (a still keeps at least NEXT_MIN_S of its own, else the clip covers it and the line has no picture state of its own: `merged`).
    `bounds` (the picture's cut points, one per line start plus the end) is changed in place; `secs` = {line: the seconds of its clip}."""
    n = len(bounds) - 1
    for i in sorted(secs):
        if i >= n or not secs[i]: continue
        a = bounds[i]; end = a + float(secs[i])
        if end <= bounds[i + 1] + 1e-6: continue
        j = i + 1; cut = None
        while j < n and j < len(shots) and plain(shots[j]) and j not in secs and bounds[j] < end - 1e-6:
            if bounds[j + 1] - end >= NEXT_MIN_S: cut = end; break
            j += 1
        new = cut if cut is not None else (bounds[j] if j <= n else bounds[n])
        for k in range(i + 1, j + (1 if cut is not None else 0)):
            if k <= n and bounds[k] < new:
                bounds[k] = new
        if merged is not None:
            for k in range(i + 1, j):
                if k < n and bounds[k + 1] - bounds[k] <= 1e-6: merged.add(k)
    return bounds

def cuts(n_total, clip_s, fps, tail_pieces):
    """The frames at which one line that carries a clip is cut: [0, the clip's own length, ...]. The clip plays whole at its own speed as ONE picture
    state; only what is left of a longer line (from TAIL_MIN_S on) is cut as a still, by `tail_pieces(seconds)`."""
    n0 = min(int(n_total), max(1, int(round(float(clip_s) * fps)))); rest = int(n_total) - n0
    if rest < int(round(TAIL_MIN_S * fps)): return [0, int(n_total)]
    extra = max(1, int(tail_pieces(rest / fps)))
    return [0, n0] + [n0 + int(rest * j / extra) for j in range(1, extra + 1)]

# ------------------------------------------------------------------ the measure: what the finished file shows
def _read(path, region):
    """Small grey pictures of a file, READ_FPS a second, cut to `region`: (frames [n, h, w] float32, its duration)."""
    import numpy as np
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0", path],
                        capture_output=True, text=True, timeout=120)
    nums = [x for x in pr.stdout.replace("\n", ",").split(",") if x.strip()]
    w0, h0 = int(nums[0]), int(nums[1]); dur = float(nums[2]) if len(nums) > 2 else 0.0
    k = GRID / max(w0, h0); w = max(8, int(round(w0 * k / 2) * 2)); h = max(8, int(round(h0 * k / 2) * 2))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={READ_FPS},scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True, timeout=3600).stdout
    n = len(raw) // (w * h); fr = np.frombuffer(raw[:n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)
    x0, x1, y0, y1 = region
    return fr[:, int(h * y0):max(int(h * y0) + 1, int(h * y1)), int(w * x0):max(int(w * x0) + 1, int(w * x1))], (dur or n / READ_FPS)

def _cells(fr, t0, t1, gap):
    """[(start of the half second, the change between two pictures `gap` frames apart)] for every half second that lies wholly inside [t0, t1). Both
    pictures are taken inside the stretch, EDGE_S away from its ends: the pair starts in the half second where it can and is moved back where the
    stretch ends before the second picture. A stretch too short for a pair gives nothing."""
    return [(c, ch) for c, ch, ln in _tiles(fr, t0, t1, gap) if ln >= CELL_S - 1e-6]

def _tiles(fr, t0, t1, gap):
    """THE WHOLE STRETCH in half seconds: [(start, change, length)] - the last piece as long as what is left of the stretch (v12 V2d-b red 1: counting
    whole half seconds only lost the rest of every stretch - 2.7 s of the red film). Each piece is judged by the same pair of pictures inside the
    stretch, EDGE_S away from its ends; a stretch too short for a pair gives nothing (it is not counted: `unmeasured_s`)."""
    import numpy as np
    lo = int(math.ceil((float(t0) + EDGE_S) * READ_FPS - 1e-9)); hi = min(len(fr) - 1, int(math.floor((float(t1) - EDGE_S) * READ_FPS + 1e-9)))
    out = []; c = float(t0)
    while c < float(t1) - 1e-6:
        k1 = int(math.ceil((c + EDGE_S) * READ_FPS - 1e-9)); ka = max(lo, min(k1, hi - gap)); kb = min(ka + gap, hi)
        if kb - ka >= min(gap, GAP_SHORT) and kb > ka: out.append((round(c, 3), float(np.mean(np.abs(fr[kb] - fr[ka]))), min(CELL_S, float(t1) - c)))
        c += CELL_S
    return out

def _quiet(cells, lim):
    """The half seconds that do NOT move: those below `lim` that stand in a row of RUN or more (a second or more without change)."""
    low = [c for c, ch in cells if ch < lim]; s = set(low)
    return [c for c in low if any(all(round(c + (j - k) * CELL_S, 3) in s for j in range(RUN)) for k in range(RUN))]

def long_report(master, spans, paid_s=None, duration=None):
    """WHAT REALLY MOVES IN A FINISHED LONG VIDEO. `spans` = [(start, end, kind[, the seconds of its clip file])] - the stretches in which the renderer
    played a clip made by a model (kind 'footage' = its Short's, 'scene', 'living'), as the render RECORDED them (`job.segmeta`; the clip files are not
    opened - their lengths are what was paid). A piece of a stretch counts as MOVING when the film's picture changes there (MOVING_CHANGE_MIN over three
    quarters of a second; a second or more without change does not count) - a clip that ran out, froze or was replaced by a held picture is found.
    Every stretch is counted WHOLE (`_tiles`), and a clip counts towards the seconds paid never more than its own length: a clip played slower over a
    longer line pays for no other clip that was cut (v12 V2d-b red 1).
    Returns {duration, moving_s, share_pct, by (seconds per kind), played_s (per kind, as recorded), frozen: [(second, kind)], paid_s, seen_pct,
    scene_shown_s (the scenes' seconds on screen as recorded, each up to its own length), unmeasured_s}."""
    fr, dur = _read(master, REGION); dur = float(duration or dur); by = {}; played = {}; frozen = []; lim = S("MOVING_CHANGE_MIN", float); own = 0.0; shown = 0.0; gone = 0.0
    for sp_ in spans or []:
        a, b, kind = float(sp_[0]), float(sp_[1]), sp_[2]; clip = float(sp_[3]) if len(sp_) > 3 and sp_[3] else None
        played[kind] = played.get(kind, 0.0) + (b - a)
        tiles = _tiles(fr, a, b, GAP_LONG); still = set(_quiet([(c, ch) for c, ch, _ in tiles], lim)); got = 0.0
        for c, _ch, ln in tiles:
            if c in still: frozen.append((round(c, 1), kind))
            else: got += ln
        by[kind] = by.get(kind, 0.0) + got; gone += max(0.0, (b - a) - sum(ln for _c, _ch, ln in tiles))
        if kind != "footage": own += min(got, clip) if clip else got
        if kind == "scene": shown += min(b - a, clip) if clip else (b - a)
    by = {k: v for k, v in by.items() if v > 1e-9}; mv = sum(by.values())
    return {"duration": round(dur, 1), "moving_s": round(mv, 1), "share_pct": round(100.0 * mv / max(0.1, dur), 1), "by": {k: round(v, 1) for k, v in sorted(by.items())},
            "played_s": {k: round(v, 1) for k, v in sorted(played.items())}, "frozen": frozen[:8], "paid_s": None if paid_s is None else round(float(paid_s), 1),
            "seen_pct": None if not paid_s else round(100.0 * own / float(paid_s), 1), "scene_shown_s": round(shown, 2), "unmeasured_s": round(gone, 2)}

def short_report(path):
    """WHAT REALLY MOVES IN A FINISHED SHORT: every half second of the file, judged in the band of the picture that never carries words. A second or
    more without change (SHORT_CHANGE_MIN) is a held picture. Returns {duration, cells, moving, share_pct, still: [the seconds at which nothing changes]}."""
    fr, dur = _read(path, BAND); cells = _cells(fr, 0.0, min(dur, len(fr) / READ_FPS), GAP_SHORT)
    still = _quiet(cells, S("SHORT_CHANGE_MIN", float))
    return {"duration": round(dur, 1), "cells": len(cells), "moving": len(cells) - len(still), "share_pct": round(100.0 * (len(cells) - len(still)) / max(1, len(cells)), 1), "still": still[:8]}
