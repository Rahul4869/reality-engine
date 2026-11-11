"""The Organisation: the departments and work stages every org module shares (Knowledge Palace now; memos, runner and registry build on these). See docs/CURRENT/SYSTEM.md."""

# id -> (name, the stage its playbook is built for when the caller names none)
DEPARTMENTS = {
    "D0":  ("Owner Office", "ops"),
    "D1":  ("Strategy & Planning", "planning"),
    "D2":  ("R&D - Research", "research"),
    "D3":  ("Review Board", "research"),
    "D4":  ("Creative - Ideation & Writers' Room", "writing"),
    "D5":  ("Packaging", "packaging"),
    "D6":  ("Visual Production", "visual"),
    "D7":  ("Sound", "sound"),
    "D8":  ("QA & Enforcement", "qa"),
    "D9":  ("Publishing & Distribution", "publishing"),
    "D10": ("Growth & Learning", "growth"),
    "D11": ("Finance", "finance"),
    "D12": ("Operations", "ops"),
    "D13": ("Audience", "qa"),
    "C":   ("The Council", "planning"),
    "L":   ("The Librarian", "ops"),
}
STAGES = ("ideation", "writing", "packaging", "visual", "sound", "qa", "publishing", "growth", "finance", "ops", "planning", "research")
