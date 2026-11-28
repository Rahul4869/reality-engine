"""The memory of a run, measured (v12 U1, J 276): the WHOLE process tree of a command every 2 s and the machine's available memory, until the process ends; one json, one line, the command's own exit code. See docs/CURRENT/SYSTEM.md."""
# The owner's 02 item 101 ("I have only 16 GB"). `mem_probe.py --label <x> -- <command ...>` starts the command, or `--pid <n>` watches a running one;
# every SAMPLE_S seconds it sums the working sets of the whole tree and reads the machine's available memory; it ends WHEN THE PROCESS ENDS (it waits on the
# process, never on a log line), writes NOTES/MEM_<label>.json and prints one line. Its exit code is the command's own: it can never change a verdict. No
# new dependency: Windows through ctypes (kernel32 / psapi), Linux through /proc. What follows from a measurement (more or fewer workers) is a line for the
# owner with the file behind it - never a change made by a session.
import argparse, json, os, subprocess, sys, time

BUDGET_MB = 10000              # THE RULE: the run's whole tree at its peak ...
FLOOR_MB = 1500                # ... and the memory left to the machine at its lowest (6 GB of the 16 stay for Windows, Defender, OneDrive and the app)
SAMPLE_S = 2.0
HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(os.path.dirname(os.path.dirname(HERE)), "NOTES")      # the handoff folder's notes, beside the repo
MB = 1024 * 1024

if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    _k32 = ctypes.WinDLL("kernel32", use_last_error=True); _psapi = ctypes.WinDLL("psapi", use_last_error=True)

    class _PE(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    class _PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage")]

    class _MSX(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] + [(n, ctypes.c_ulonglong) for n in (
            "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE; _k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.Process32FirstW.argtypes = _k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PE)]
    _k32.OpenProcess.restype = wintypes.HANDLE; _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]; _k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _k32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MSX)]
    _psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
    _BAD = ctypes.c_void_p(-1).value; _QUERY = 0x1000 | 0x0010; _SYNC = 0x00100000      # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, SYNCHRONIZE

    def _parents():
        snap = _k32.CreateToolhelp32Snapshot(0x2, 0); out = {}
        if not snap or snap == _BAD: return out
        try:
            e = _PE(); e.dwSize = ctypes.sizeof(_PE); ok = _k32.Process32FirstW(snap, ctypes.byref(e))
            while ok:
                out[int(e.th32ProcessID)] = int(e.th32ParentProcessID); ok = _k32.Process32NextW(snap, ctypes.byref(e))
        finally: _k32.CloseHandle(snap)
        return out

    def _rss(pid):
        h = _k32.OpenProcess(_QUERY, False, pid)
        if not h: return 0
        try:
            c = _PMC(); c.cb = ctypes.sizeof(_PMC)
            return int(c.WorkingSetSize) if _psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb) else 0
        finally: _k32.CloseHandle(h)

    def _available():
        m = _MSX(); m.dwLength = ctypes.sizeof(_MSX)
        return int(m.ullAvailPhys) if _k32.GlobalMemoryStatusEx(ctypes.byref(m)) else 0

    class _Watched:
        """A running process by its pid: waited on through its handle (the end is seen at once), its exit code read when it ends."""
        def __init__(self, pid):
            self.pid = pid; self.h = _k32.OpenProcess(_SYNC | 0x1000, False, pid)
            if not self.h: raise SystemExit(f"mem_probe: no process {pid}")
        def wait(self, s):
            return _k32.WaitForSingleObject(self.h, int(s * 1000)) == 0
        def code(self):
            c = wintypes.DWORD(0); _k32.GetExitCodeProcess(self.h, ctypes.byref(c)); _k32.CloseHandle(self.h); return int(c.value)
else:
    def _parents():
        out = {}
        for d in os.listdir("/proc"):
            if not d.isdigit(): continue
            try:
                with open(f"/proc/{d}/stat", encoding="utf-8", errors="replace") as f: out[int(d)] = int(f.read().rsplit(")", 1)[1].split()[1])
            except Exception: continue
        return out

    def _rss(pid):
        try:
            with open(f"/proc/{pid}/status", encoding="utf-8", errors="replace") as f:
                for ln in f:
                    if ln.startswith("VmRSS:"): return int(ln.split()[1]) * 1024
        except Exception: pass
        return 0

    def _available():
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                for ln in f:
                    if ln.startswith("MemAvailable:"): return int(ln.split()[1]) * 1024
        except Exception: pass
        return 0

    class _Watched:
        """A running process by its pid (not a child of the probe): its end is seen within SAMPLE_S; Linux gives no exit code of another's process (0)."""
        def __init__(self, pid):
            self.pid = pid
            if not os.path.exists(f"/proc/{pid}"): raise SystemExit(f"mem_probe: no process {pid}")
        def _gone(self):
            try:
                with open(f"/proc/{self.pid}/stat", encoding="utf-8", errors="replace") as f: return f.read().rsplit(")", 1)[1].split()[0] in ("Z", "X")
            except Exception: return True
        def wait(self, s):
            end = time.monotonic() + s
            while time.monotonic() < end:
                if self._gone(): return True
                time.sleep(0.2)
            return self._gone()
        def code(self): return 0


class _Child:
    """A command the probe started: waited on through subprocess (the end is seen at once), its own exit code."""
    def __init__(self, cmd): self.p = subprocess.Popen(cmd); self.pid = self.p.pid
    def wait(self, s):
        try: self.p.wait(timeout=s); return True
        except subprocess.TimeoutExpired: return False
    def code(self): return self.p.returncode


def tree(root):
    """The pids of the whole tree under `root` (itself included), from one reading of every process's parent."""
    kids = {}
    for pid, pp in _parents().items():
        if pid != pp: kids.setdefault(pp, []).append(pid)
    out, todo = [], [root]
    while todo:
        p = todo.pop()
        if p in out: continue
        out.append(p); todo += kids.get(p, [])
    return out


def sample(root):
    """(the tree's working sets in bytes, the largest one process's, how many processes) and the machine's available memory - one reading."""
    sizes = [r for r in (_rss(p) for p in tree(root)) if r > 0]
    return sum(sizes), max(sizes or [0]), len(sizes), _available()


def rule(peak_tree_mb, min_available_mb):
    """THE RULE it prints: FITS when the tree's peak is within BUDGET_MB and the machine never had less than FLOOR_MB available."""
    return "FITS" if peak_tree_mb <= BUDGET_MB and min_available_mb >= FLOOR_MB else "DOES NOT FIT"


def main(argv=None):
    ap = argparse.ArgumentParser(description="the memory of a run: the whole process tree, every 2 s, until the process ends")
    ap.add_argument("--label", default=""); ap.add_argument("--pid", type=int, default=0); ap.add_argument("--out", default=NOTES)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if bool(cmd) == bool(a.pid): ap.error("give either -- <command ...> or --pid <n>")
    w = _Child(cmd) if cmd else _Watched(a.pid); label = a.label or f"pid{w.pid}"
    t0 = time.monotonic(); peak = (0, 0, 0); one = 0; low = None; n = 0; ended = False
    while not ended:
        try:
            tot, big, k, av = sample(w.pid); n += 1; one = max(one, big)
            if tot > peak[0]: peak = (tot, big, k)
            if av: low = av if low is None else min(low, av)
        except Exception as e: print(f"mem_probe: a sample failed ({type(e).__name__})", file=sys.stderr)
        ended = w.wait(SAMPLE_S)
    rc = w.code(); secs = round(time.monotonic() - t0, 1)
    res = {"peak_tree_mb": round(peak[0] / MB), "peak_one_process_mb": round(one / MB), "processes_at_peak": peak[2],
           "min_available_mb": round((low or 0) / MB), "samples": n, "seconds": secs}
    try:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, f"MEM_{label}.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    except Exception as e: print(f"mem_probe: the json was not written ({type(e).__name__})", file=sys.stderr)
    print(f"mem_probe {label}: peak tree {res['peak_tree_mb']:,} MB ({res['processes_at_peak']} processes; the largest one {res['peak_one_process_mb']:,} MB), "
          f"least available {res['min_available_mb']:,} MB, {n} samples in {secs:g} s: {rule(res['peak_tree_mb'], res['min_available_mb'])} "
          f"(the rule: the tree <= {BUDGET_MB:,} MB and available >= {FLOOR_MB:,} MB); exit code {rc}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
