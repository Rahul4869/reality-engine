"""The motion ladder (Visual Production, D6): the moving seconds of a video as a budget - placed by code on lines that can show a whole clip, cut by one rule the renderer and the checks share, and found again on the finished file. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import math, subprocess
from whatifs.core import S, log

MOVING = ("kling", "living")      # the shot types that carry a clip made by a model
CELL_S = 0.5                      # the finished file is judged in half seconds ...
READ_FPS = 8                      # ... read at eight pictures a second ...
GAP = 2                           # ... each half second by two of its pictures a quarter second apart (both inside it: never across a cut)
EDGE_S = 0.05                     # the first of the two is at least this far inside its half second (film and clip can be a frame apart at a cut)
GRID = 96                         # the long side of the small grey copy two pictures are compared on (the encoder's grain is averaged away)
REGION = (0.2, 0.8, 0.15, 0.85)   # the part of a wide film that is compared (x from, x to, y from, y to): its middle - no chip, no bar, no caption
BAND = (0.0, 1.0, 0.30, 0.52)     # the part of an upright Short that is compared: the band that never carries words (under the promise text, above the captions)
# From which mean change (grey levels of 255) between its two pictures a half second MOVES is a Settings cell with the measurements in its note:
# MOVING_CHANGE_MIN for a long video (the renderer's grain makes a held picture change a little), SHORT_CHANGE_MIN for a Short (no grain: a held picture is 0.000).
NEXT_MIN_S = 1.0                  # a still whose line a clip runs into keeps at least this long of its own (else the clip covers it whole)
TAIL_MIN_S = 1.0                  # what is left of a line after its clip is cut as a still of its own only from this length on (a shorter rest: the clip is played that little slower)

def on():
    from whatifs import clips as CL
    return CL.ladder()

# ------------------------------------------------------------------ the lines of a video and what a clip can show on them
def lines_of(units, total):
    """[(start, end)] of every line's PICTURE: a picture changes where the next line starts (the narration is the master clock), the last ends with the film."""
    b = [0.0] + [float(u["start"]) for u in units[1:]] + [float(total)]
    return [(b[i], max(b[i], b[i + 1])) for i in range(len(units))]

def plain(shot):
    """A still a clip may run into: a made picture with nothing of its own that must be seen at its first frame."""
    return shot.get("type") == "still" and not shot.get("short") and not shot.get("promise") and not shot.get("anim")

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

def scene_fit(shots, units, total=None):
    """For the Animation Director: can an animated scene on line i be shown WHOLE (its own line and the stills it may run into are as long as a scene)?"""
    from whatifs import clips as CL
    sp = lines_of(units, float(total if total is not None else (units[-1].get("end") or units[-1].get("start") or 0) if units else 0))
    return lambda i: i < len(sp) and room_s(i, shots, sp) >= CL.SCENE_S - 0.25

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
    n = min(len(out), len(sp)); used = 0; busy = set(); placed = []
    moving = [(sp[i][0] + sp[i][1]) / 2 for i in range(n) if out[i].get("type") == "kling" or out[i].get("short")]
    asked = [i for i in range(n) if out[i].get("type") == "living" and not out[i].get("short")]
    for i in asked: out[i]["type"] = "still"; out[i].pop("buy", None)
    def can(i): return out[i].get("type") == "still" and not out[i].get("short") and not out[i].get("promise") and not out[i].get("anim") and i not in busy
    def take(i):
        nonlocal used
        own = sp[i][1] - sp[i][0]; r = room_s(i, out, sp, busy)
        if r < lo - 0.25: return False                                   # even the model's shortest clip could not be shown whole here
        b = CL.secs(lr, min(max(own, lo), cap))
        while b > lo and b > r + 0.25: b -= 1                            # never buy a second that no line can show
        if b > r + 0.25 or used + b > budget: return False
        out[i].update(type="living", buy=int(b)); used += int(b); placed.append(i); moving.append((sp[i][0] + sp[i][1]) / 2)
        busy.update(covers(i, b, out, sp, busy)); return True
    for i in asked:
        if can(i): take(i)
    while budget - used >= lo:
        cand = [i for i in range(n) if can(i) and room_s(i, out, sp, busy) >= lo - 0.25]
        if not cand: break
        def far(i):
            t = (sp[i][0] + sp[i][1]) / 2
            return (min((abs(t - m) for m in moving), default=float(total)), sp[i][1] - sp[i][0], -i)
        took = False
        for i in sorted(cand, key=far, reverse=True):
            if take(i): took = True; break
        if not took: break
    plan["living"] = len(placed); plan["living_bought_s"] = used
    if asked or placed:
        log(f"motion ladder: {len(placed)} stills brought to life for {used} of {budget} planned seconds"
            + (f"; {len([i for i in asked if i not in placed])} of the Director's living shots sit on lines too short for a whole clip and stay stills" if [i for i in asked if i not in placed] else ""))
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

def _cells(fr, t0, t1):
    """[(start of the half second, the change between its two pictures)] for every half second that lies wholly inside [t0, t1)."""
    import numpy as np
    out = []; c = float(t0)
    while c + CELL_S <= float(t1) + 1e-6:
        k1 = int(math.ceil((c + EDGE_S) * READ_FPS - 1e-9)); k2 = k1 + GAP
        if k2 < len(fr): out.append((round(c, 3), float(np.mean(np.abs(fr[k2] - fr[k1])))))
        c += CELL_S
    return out

def long_report(master, spans, paid_s=None, duration=None):
    """WHAT REALLY MOVES IN A FINISHED LONG VIDEO. `spans` = [(start, end, kind)] - the stretches in which the renderer played a clip made by a model
    (kind 'footage' = its Short's, 'scene', 'living'), as the render recorded them. A half second counts as MOVING when it lies inside such a
    stretch AND the film's picture changes in it (MOVING_CHANGE_MIN) - a clip that ran out, froze or was replaced by a held picture is not counted.
    Returns {duration, moving_s, share_pct, by (seconds per kind), played_s (per kind, as recorded), frozen: [(second, kind)], paid_s, seen_pct}."""
    fr, dur = _read(master, REGION); dur = float(duration or dur); by = {}; played = {}; frozen = []; lim = S("MOVING_CHANGE_MIN", float)
    for a, b, kind in spans or []:
        played[kind] = played.get(kind, 0.0) + (float(b) - float(a))
        for c, ch in _cells(fr, a, b):
            if ch >= lim: by[kind] = by.get(kind, 0.0) + CELL_S
            else: frozen.append((round(c, 1), kind))
    mv = sum(by.values()); own = sum(v for k, v in by.items() if k != "footage")
    return {"duration": round(dur, 1), "moving_s": round(mv, 1), "share_pct": round(100.0 * mv / max(0.1, dur), 1), "by": {k: round(v, 1) for k, v in sorted(by.items())},
            "played_s": {k: round(v, 1) for k, v in sorted(played.items())}, "frozen": frozen[:8], "paid_s": None if paid_s is None else round(float(paid_s), 1),
            "seen_pct": None if not paid_s else round(100.0 * own / float(paid_s), 1)}

def short_report(path):
    """WHAT REALLY MOVES IN A FINISHED SHORT: every half second of the file, judged in the band of the picture that never carries words.
    Returns {duration, cells, moving, share_pct, still: [the seconds at which nothing changes]}."""
    fr, dur = _read(path, BAND); cells = _cells(fr, 0.0, min(dur, len(fr) / READ_FPS))
    still = [c for c, ch in cells if ch < S("SHORT_CHANGE_MIN", float)]
    return {"duration": round(dur, 1), "cells": len(cells), "moving": len(cells) - len(still), "share_pct": round(100.0 * (len(cells) - len(still)) / max(1, len(cells)), 1), "still": still[:8]}
