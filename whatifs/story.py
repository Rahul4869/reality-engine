"""One story (D5): the thumbnail a viewer taps is the picture the long video opens on - the first picture of the promoted Short whose footage opens it - and its runner-up is another look at the same scene. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
from whatifs.core import S

OTHER_LOOK = "a closer look from another angle"      # the runner-up's second half when the packager wrote nothing else for it
B_MAX = 160                                          # characters of the packager's own words after the scene's words in the runner-up (the scene's words are NEVER cut)
BRIEF = ("THUMBNAIL SCENE (fixed: the picture this video opens on, the one real viewers stayed for): \"{words}\". Write thumb_text for THIS scene. For the "
         "runner-up write thumb_prompt_b as ANOTHER LOOK AT THE SAME SCENE - closer or wider, the same place, the same impossible thing - and thumb_text_b as "
         "other words for it; never another scene: whichever thumbnail a viewer taps, the video opens on what it showed."
         " This replaces the rule above that the runner-up is built on a DIFFERENT idea: here it is the SAME scene, seen another way.")

def on():
    """Is the thumbnail the picture the film opens on? (cell ONE_STORY_ON)"""
    return S("ONE_STORY_ON", bool)

def _one(x): return " ".join(str(x or "").split())

def first_picture(opening):
    """The words the Short's first clip was really drawn from: the key `picture` of the archive's manifest (opening.manifest); '' when it holds none."""
    return (opening or {}).get("picture", "")

def words_for(d, opening):
    """The scene's words (spaces made one) when this video is one story - switched on, opening on a Short's footage, the archive holds picture words -
    else ''. The ONE condition of the packager's sentence and of `align`."""
    from whatifs import opening as OPEN
    if not on() or OPEN.source(d)[0] != "short": return ""
    return _one(first_picture(opening))

def brief(d, opening):
    """The packager's sentence (room.package joins it with its other texts before the JSON), or '' when the video is not one story."""
    w = words_for(d, opening)
    return BRIEF.format(words=w) if w else ""

def align(pkg, d, opening):
    """Both thumbnails are the opening's scene BY CONSTRUCTION, whatever the packager wrote: thumb_prompt = the scene's words; thumb_prompt_b = the same words
    + '; ' + another look (the packager's own runner-up, else its own scene where it differs, else OTHER_LOOK - only this part is cut, at B_MAX); thumb_text_b
    = its own, else thumb_text; and the key one_story = {short, words}. No picture more is paid: the same two. A video that is not one story gets its
    package back AS IT CAME - the same object, no key set (under an override its own promise scene opens it and is drawn)."""
    w = words_for(d, opening)
    if not w or not isinstance(pkg, dict): return pkg
    own_b, own = _one(pkg.get("thumb_prompt_b")), _one(pkg.get("thumb_prompt"))
    r = own_b or own or OTHER_LOOK
    if r.startswith(w): r = r[len(w):].lstrip(" ;,.:-") or OTHER_LOOK
    pkg["thumb_prompt"] = w
    pkg["thumb_prompt_b"] = w + "; " + r[:B_MAX]
    pkg["thumb_text_b"] = pkg.get("thumb_text_b") or pkg.get("thumb_text") or ""
    pkg["one_story"] = {"short": str(d["ladder"]), "words": w}
    return pkg

def report(d, pkg, opening):
    """(ok, why) for check one_story, judged on the package and the opening the script gate holds - before any picture is paid. ok None = not judged."""
    from whatifs import opening as OPEN
    if not on(): return None, "one story is switched off (ONE_STORY_ON)"
    kind, r = OPEN.source(d)
    if kind == "override": return None, "made under an override: its own promise scene opens it (viewer_promise, promise_paid)"
    if kind != "short": return None, OPEN.none_words(kind, r)
    w = _one(first_picture(opening))
    if not w: return None, "the Short's archive holds no picture words"
    pkg = pkg if isinstance(pkg, dict) else {}
    one = pkg.get("one_story") if isinstance(pkg.get("one_story"), dict) else {}
    if str(one.get("short") or "") != str((d or {}).get("ladder") or "") or str(pkg.get("thumb_prompt") or "") != w:
        return False, "the thumbnail's scene is not the picture this video opens on"
    b = str(pkg.get("thumb_prompt_b") or "")
    if b.strip() and not b.startswith(w + "; "): return False, "the runner-up thumbnail is not the opening's scene"
    return True, f"the thumbnail is drawn from the first picture of Short {one['short']}, the picture this video opens on: '{w}'"
