"""U1 fix 276 (02 item 101, "I have only 16 GB"): tools/mem_probe.py measures the memory of a run - the WHOLE process tree every 2 s and the machine's
available memory - ends when the process ends, writes MEM_<label>.json, prints one line with THE RULE, and returns the command's own exit code."""
import json, os, subprocess, sys, time
from tools import mem_probe as MP

KEYS = {"peak_tree_mb", "peak_one_process_mb", "processes_at_peak", "min_available_mb", "samples", "seconds"}
GRAND = "import time; b = bytes([1]) * (200 * 1024 * 1024); time.sleep(3)"          # a GRANDCHILD holding 200 MB (every page written) for 3 s


def _child(code, mark):
    """A child that starts the grandchild, waits for it, writes when it ends (time.monotonic: one clock for every process) and exits with `code`."""
    return [sys.executable, "-c", f"import subprocess, sys, time; subprocess.call([sys.executable, '-c', {GRAND!r}]); "
                                  f"open({mark!r}, 'w').write(repr(time.monotonic())); sys.exit({code})"]


def test_the_whole_tree_is_measured_and_the_tool_returns_the_commands_own_exit_code_when_it_ends(tmp_path, capsys):
    for code in (0, 3):
        mark = str(tmp_path / f"end{code}")
        rc = MP.main(["--label", f"t{code}", "--out", str(tmp_path), "--", *_child(code, mark)]); back = time.monotonic()
        assert rc == code, (rc, code)
        assert back - float(open(mark).read()) < 5, back - float(open(mark).read())                      # within 5 s of the child's end
        j = json.load(open(tmp_path / f"MEM_t{code}.json", encoding="utf-8"))
        assert set(j) == KEYS and 200 <= j["peak_tree_mb"] < 600 and j["processes_at_peak"] >= 2 and j["samples"] >= 2, j
        assert j["peak_one_process_mb"] >= 200 and j["min_available_mb"] > 0, j
        line = capsys.readouterr().out.strip().splitlines()
        assert len(line) == 1 and line[0].startswith(f"mem_probe t{code}: peak tree ") and line[0].endswith(f"exit code {code}"), line


def test_with_the_budget_at_100_mb_the_printed_rule_is_does_not_fit(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(MP, "BUDGET_MB", 100)
    assert MP.main(["--label", "small", "--out", str(tmp_path), "--", *_child(0, str(tmp_path / "e"))]) == 0
    assert ": DOES NOT FIT (the rule: the tree <= 100 MB and available >= 1,500 MB)" in capsys.readouterr().out
    monkeypatch.undo()
    assert (MP.BUDGET_MB, MP.FLOOR_MB) == (10000, 1500)
    assert MP.rule(10000, 1500) == "FITS" and MP.rule(10001, 1500) == "DOES NOT FIT" and MP.rule(500, 1499) == "DOES NOT FIT"


def test_a_running_process_is_watched_by_its_pid_until_it_ends(tmp_path):
    p = subprocess.Popen(_child(3, str(tmp_path / "e")))
    rc = MP.main(["--pid", str(p.pid), "--label", "bypid", "--out", str(tmp_path)]); p.wait()
    j = json.load(open(tmp_path / "MEM_bypid.json", encoding="utf-8"))
    assert 200 <= j["peak_tree_mb"] < 600 and j["processes_at_peak"] >= 2, j
    assert rc == (3 if os.name == "nt" else 0), rc                                                      # Linux gives no exit code of a process the tool did not start


def test_a_failed_sample_or_an_unwritable_json_never_changes_the_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(MP, "sample", lambda root: 1 / 0)
    blocked = tmp_path / "a_file"; blocked.write_text("x")
    assert MP.main(["--label", "x", "--out", str(blocked), "--", sys.executable, "-c", "import sys; sys.exit(5)"]) == 5
    err = capsys.readouterr().err
    assert "a sample failed (ZeroDivisionError)" in err and "the json was not written" in err, err


def test_the_json_goes_to_the_notes_folder_beside_the_repo_by_default():
    root = os.path.dirname(os.path.dirname(os.path.abspath(MP.__file__)))
    assert MP.NOTES == os.path.join(os.path.dirname(root), "NOTES") and MP.SAMPLE_S == 2.0
