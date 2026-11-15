import json
import call
# The read of `claude agents --json --all` for build_info.py and run.py (STORY-508). A read is good only when the
# command exits 0 and prints a JSON list within its time limit (STORY-518, call.py). An empty output, a failed read or a read
# that times out is not "no session": it gives None and the cause, on 1 line of at most 110 characters with its prefix.
one = lambda s: " ".join((s or "").split()) or "no output"
def read():
    lim = call.limit(call.AGENTS)
    r = call.run(["claude","agents","--json","--all"], lim)
    if r is None: return None, call.cause(lim)
    if r.returncode: return None, f"exit {r.returncode}: {one(r.stderr or r.stdout)}"[:110]
    try: d = json.loads(r.stdout)
    except ValueError: return None, f"not JSON: {one(r.stdout)}"[:110]
    if not isinstance(d, list): return None, f"not a JSON list: {one(r.stdout)}"[:110]
    return d, ""
