import json, subprocess
# The read of `claude agents --json --all` for build_info.py and run.py (STORY-508). A read is good only when the
# command exits 0 and prints a JSON list. An empty output or a failed read is not "no session": it gives None and
# the cause, on 1 line of at most 110 characters with its prefix.
one = lambda s: " ".join((s or "").split()) or "no output"
def read():
    r = subprocess.run(["claude","agents","--json","--all"],capture_output=True,text=True)
    if r.returncode: return None, f"exit {r.returncode}: {one(r.stderr or r.stdout)}"[:110]
    try: d = json.loads(r.stdout)
    except ValueError: return None, f"not JSON: {one(r.stdout)}"[:110]
    if not isinstance(d, list): return None, f"not a JSON list: {one(r.stdout)}"[:110]
    return d, ""
