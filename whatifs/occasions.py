"""Calendar-aware special reels: the special-reel slots go first to the month's best-loved occasions. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, json
from whatifs.core import S, log, store, now_utc, set_setting

FAMILY_ASK = "Subscribe, so this little family gets to celebrate more of these with you."
OCCASIONS = {   # key: (name, how to compute, brief). Religious festivals: celebratory and respectful, never parody of rituals or figures.
    "halloween": ("Halloween", "10-31", "Nana Rosa and Vale go trick-or-treating at a spooky house (scarecrows, pumpkins with glowing red eyes, fog). They knock, shout 'Trick or treat!', the door opens on Grimm's wild horror-movie lab (green fumes, sparking coils, bubbling flasks); they shriek and run. Final beat: all three shoulder to shoulder, laughing: 'Happy Halloween!'"),
    "christmas": ("Christmas", "12-25", "Grimm tries to disprove Santa's delivery physics on a chalkboard; Vale finds the 'evidence' (cookie crumbs); Nana hangs her teacup on the tree. Ends in a warm group moment under the lights: 'Merry Christmas from the court.'"),
    "new_year": ("New Year", "01-01", "A courtroom countdown: Grimm objects to midnight itself, Nana overrules time, Vale counts on three fingers; confetti and fireworks: 'Happy New Year, jury.'"),
    "valentines": ("Valentine's Day", "02-14", "Vale deduces who in the jury has a crush (charming, harmless); Grimm insists love is just chemistry, then blushes; Nana pours two cups of tea."),
    "april_fools": ("April Fools' Day", "04-01", "Grimm 'switches off gravity' in the courtroom; Vale and Nana play along floating; reveal it's a prank on Grimm."),
    "pi_day": ("Pi Day", "03-14", "Nana slices a pie into exactly 3.14 pieces; Grimm demands more digits; Vale observes the crust."),
    "earth_day": ("Earth Day", "04-22", "The court puts pollution on trial; small, hopeful, witty; ends with the three planting a tiny tree."),
    "science_day": ("World Science Day", "11-10", "The court celebrates curiosity: each character names the one experiment that changed them, quick and warm."),
    "childrens_day_in": ("Children's Day (India)", "11-14", "Flashback-style: the three as curious kids in a science fair; Nana judging even then."),
    "teachers_day_in": ("Teachers' Day (India)", "09-05", "The cast thanks the teachers who believed in them (Vale's first teacher, the three-finger rule)."),
    "mothers_day": ("Mother's Day", "may-2-sun", "Vale and Grimm surprise Nana with breakfast; she pretends to be unimpressed, then smiles."),
    "fathers_day": ("Father's Day", "jun-3-sun", "Grimm builds an over-complicated gadget as a gift; it works once."),
    "thanksgiving": ("Thanksgiving", "nov-4-thu", "The court lists what it is thankful for; Grimm objects to gratitude, then admits one thing."),
    "perseids": ("Perseid meteor shower", "08-12", "The three lie on the courthouse roof watching meteors; Grimm explains, Vale counts, Nana wishes."),
    "solstice_dec": ("Winter solstice", "12-21", "The longest night: the court keeps a candle vigil with physics jokes."),
    "diwali": ("Diwali", "lunar", "The courtroom glows with rows of diyas; Grimm's 'scientific' sparkler experiment; rangoli drawn as equations; sweets shared; warm group moment: 'Happy Diwali from the court.'"),
    "holi": ("Holi", "lunar", "Colours as chemistry: Grimm explains pigments and gets drenched in colour; Nana and Vale laugh; everyone colourful: 'Happy Holi!'"),
    "eid": ("Eid al-Fitr", "lunar", "The cast shares sweets and good wishes in the courtroom; Grimm learns to say a warm 'Eid Mubarak'; gentle and respectful."),
    "lunar_new_year": ("Lunar New Year", "lunar", "Red lanterns in the courtroom, a dumpling-folding contest Grimm takes too seriously; 'Happy Lunar New Year.'"),
    "easter": ("Easter", "easter", "An egg hunt in the courthouse; Vale deduces every hiding place; Grimm hides one so well no one finds it."),
}
DEFAULT_PRIORITY = "halloween,christmas,new_year,diwali,holi,valentines,april_fools,lunar_new_year,eid,easter,mothers_day,thanksgiving,pi_day,science_day,childrens_day_in,teachers_day_in,fathers_day,earth_day,perseids,solstice_dec"

def _easter(y):
    a = y % 19; b, c = divmod(y, 100); d, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31; day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)

def _nth_weekday(y, month, n, weekday):
    d = dt.date(y, month, 1); off = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=off + 7 * (n - 1))

def dates_for_year(y):
    """{key: date} for the year. Lunar festivals come from OCCASION_DATES (JSON {"diwali": {"2026": "2026-11-08"}, ...}); unknown years are skipped."""
    try: lunar = json.loads(S("OCCASION_DATES") or "{}")
    except Exception: lunar = {}
    out = {}
    M = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    W = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    for k, (_, rule, _b) in OCCASIONS.items():
        try:
            if rule == "lunar":
                v = (lunar.get(k) or {}).get(str(y))
                if v: out[k] = dt.date.fromisoformat(v)
            elif rule == "easter": out[k] = _easter(y)
            elif "-" in rule and rule[:3] in M:
                mo, n, wd = rule.split("-"); out[k] = _nth_weekday(y, M[mo], int(n), W[wd])
            else:
                mo, d = rule.split("-"); out[k] = dt.date(y, int(mo), int(d))
        except Exception: continue
    return out

def refresh_lunar_dates(now=None):
    """Early December: one web-searched Claude call adds next year's lunar festival dates (validated: inside next year) and tells the owner (FYI)."""
    now = now or now_utc()
    if now.month != 12 or now.day > 14: return False
    y = now.year + 1
    try: cur = json.loads(S("OCCASION_DATES") or "{}")
    except Exception: cur = {}
    keys = [k for k, (_n, rule, _b) in OCCASIONS.items() if rule == "lunar"]
    if all(str(y) in (cur.get(k) or {}) for k in keys): return False
    from whatifs.models import ask
    out = ask("occasions_check", "Return JSON only: {key: 'YYYY-MM-DD'} for the requested festivals in the requested year, from official or widely published calendars.",
              json.dumps({"year": y, "festivals": {k: OCCASIONS[k][0] for k in keys}}), want_json=True, max_tokens=600, search=True, fake_key="occasions_check")
    added = []
    for k in keys:
        v = str((out or {}).get(k) or "") if isinstance(out, dict) else ""
        try: d = dt.date.fromisoformat(v)
        except ValueError: continue
        if d.year == y: cur.setdefault(k, {})[str(y)] = v; added.append(f"{OCCASIONS[k][0]} {v}")
    if added:
        set_setting("OCCASION_DATES", json.dumps(cur))
        from whatifs import notify as NT
        NT.send("occasion_dates", "Next year's festival dates were added: " + ", ".join(added) + ". Correct any in Settings, OCCASION_DATES.", tier="fyi", dedupe_key=f"occdates|{y}")
    return bool(added)

def plan_month(y, m):
    """[(date, occasion_key or '')] for the month's special slots: occasions first (by priority), then SPECIALS_DAYS."""
    n = S("SPECIALS_PER_MONTH", int); prio = [p.strip() for p in str(S("OCCASION_PRIORITY") or DEFAULT_PRIORITY).split(",") if p.strip()]
    occ = [(d, k) for k, d in dates_for_year(y).items() if d.month == m and k in OCCASIONS]
    occ.sort(key=lambda x: prio.index(x[1]) if x[1] in prio else 999)
    slots = occ[:n]
    for day in [int(x) for x in str(S("SPECIALS_DAYS") or "").split(",") if x.strip().isdigit()]:
        if len(slots) >= n: break
        try: d = dt.date(y, m, day)
        except ValueError: continue
        if all(abs((d - s[0]).days) >= 5 for s in slots): slots.append((d, ""))
    return sorted(slots)

def slot_for(today):
    """The occasion key for today ('' = a regular special) or None when today is not a special day."""
    for d, k in plan_month(today.year, today.month):
        if d == today: return k
    return None

def topical_hook():
    """This week's safe topical hook from the trend scout (science/space items only), or ''."""
    rows = store().rows("Trend_Brief")[-30:]
    for r in reversed(rows):
        txt = f"{r.get('item', '')} {r.get('detail', '')}".lower()
        if any(w in txt for w in ("space", "nasa", "eclipse", "meteor", "comet", "planet", "moon", "science", "telescope", "asteroid", "aurora")) \
           and not any(w in txt for w in ("died", "dead", "killed", "crash", "war", "attack", "disaster", "victim")):
            return str(r.get("item", ""))[:160]
    return ""

def heads_up(now=None):
    """Three days before an occasion special: one 'This week' card with the idea ([OK] / [Change idea]); silence = it goes ahead."""
    now = now or now_utc(); target = (now + dt.timedelta(days=3)).date()
    k = slot_for(target)
    if not k: return None
    from whatifs import notify as NT
    name, _r, brief = OCCASIONS[k]
    return NT.send("occasion", f"Coming on {target:%a %d %b}: a {name} special with the cast. Idea: {brief}", [("OK", "OK"), ("Change idea", f"DISCUSS {k}")],
                   tier="week", default="it goes ahead as planned", expires_h=60, dedupe_key=f"occasion|{k}|{target.isoformat()}")
