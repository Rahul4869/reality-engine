"""
tools/plan_guard.py  v8.0
Runs on every GitHub save. RED = something broke the locked plan (Kernel v7.3 rule numbers). Operator only reports GREEN/RED.
"""
import ast, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.abspath(__file__)
J = "".join  # patterns are assembled so this file never matches itself
RULES = [
    (J([r"claude-", r"(?:3|4|5|opus|sonnet|haiku)"]), "K11: model name typed in code (must come from Models tab)"),
    (J([r"gemini-", r"\d"]),                          "K11: model name typed in code (must come from Models tab)"),
    (J([r"v1\.1-", r"ultra"]),                        "K22: banned expensive image model (money rules)"),
    (J([r"edge", r"[-_]tts"]),                        "K17: banned voice engine (Kokoro blend only)"),
    (J([r"critic_verdict\s*[:=]\s*[\"']", r"APPROVED"]), "K14: faked critic verdict (independent critic)"),
    (J([r"runtime_min\s*[:=]\s*", r"\d"]),            "K12: fixed runtime (must be sampled)"),
    (J([r"tbl", r"end"]),                             "K20: frame blending / watermark tampering"),
    (J([r"c2pa", r".{0,20}(strip|remove|erase)"]),    "K20: provenance stripping"),
    (J([r"map_metadata\s+", r"-1"]),                  "K20: metadata wiping"),
]
BANNED_NAME_WORDS = ["payment", "card", "billing", "password", "secret", "token", "bank", "transfer", "pwc", J(["conf", "ident", "ial"])]
SCAN_EXT = (".py", ".yml", ".yaml", ".gs", ".js", ".json")
TEXT_EXT = (".md", ".txt", ".yml", ".yaml", ".py", ".json", ".cfg", ".toml")      # v8.0: the flagged word must not appear in any text file either

def main() -> int:
    bad = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "__pycache__", "node_modules", ".venv")]
        for f in fn:
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT)
            low = rel.lower()
            for wd in BANNED_NAME_WORDS:
                if wd in low: bad.append(f"{rel}: file name contains a flagged word ('{wd}')")
            if os.path.abspath(p) != SELF and f.endswith(TEXT_EXT):
                if re.search(J(["conf", "ident", "ial"]), open(p, encoding="utf-8", errors="ignore").read(), re.I): bad.append(f"{rel}: contains a flagged word")
            if os.path.abspath(p) == SELF or not f.endswith(SCAN_EXT): continue
            txt = open(p, encoding="utf-8", errors="ignore").read()
            for pat, why in RULES:
                for m in re.finditer(pat, txt, re.I):
                    ln = txt[:m.start()].count("\n") + 1
                    bad.append(f"{rel}:{ln}: {why}")
            if f.endswith(".py"):
                try:
                    tree = ast.parse(txt); seen = set()
                    for node in tree.body:
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            if node.name in seen: bad.append(f"{rel}:{node.lineno}: duplicate definition '{node.name}'")
                            seen.add(node.name)
                except SyntaxError as e:
                    bad.append(f"{rel}:{e.lineno}: Python syntax error")
    if bad:
        print("PLAN GUARD: RED"); [print("  -", b) for b in bad]; return 1
    print("PLAN GUARD: GREEN"); return 0

if __name__ == "__main__":
    sys.exit(main())

