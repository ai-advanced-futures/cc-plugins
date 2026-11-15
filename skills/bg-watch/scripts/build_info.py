import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import call, claude_agents
# State lives in one fixed folder; the watcher skips its own session (bg job id = $CLAUDE_JOB_DIR basename).
STATE = os.path.expanduser(os.environ.get("BG_WATCH_STATE", "~/.claude/bg-watch"))
os.makedirs(STATE, exist_ok=True)
SELF = os.path.basename(os.environ.get("CLAUDE_JOB_DIR", "").rstrip("/"))
# One JSON line per session whose log mentions an API Error: concise facts for jag to judge.
NOISE = re.compile(r"^\s*(\d+|[✻✶✳✢✽·]\S*|.*(thinking with|Contemplating|Flibbertigibbeting|Pontificating|tokens\)).*)\s*$")
SKIP = re.compile(r"^(✻|❯|›|…|\?|Checking for updates|\d+ agents|\d*\s*ne+ds? input)")
EVENT = re.compile(r"^(⏺|⎿|✻|›|※)")   # a line that starts a transcript event
BORDER = re.compile(r"^[─━═]{8,}$")   # the border of the input box
agents, cause = claude_agents.read()
if agents is None:   # an empty output or a failed read is not "no session": write no state file, so the history stays
    sys.exit(f"bg-watch: the read of claude agents --json --all failed ({cause}); no state file changed")
# Every known id, so that run.py can drop history of sessions that no longer exist.
with open(os.path.join(STATE, "agents.json"),"w") as f:
    json.dump([s["id"] for s in agents if s.get("id")], f)
# Only a live session (a session with a status) gets a logs call. A session with no status has no live process, and
# claude logs gives no log for it ("job not found"). Its id stays in agents.json above. (STORY-508)
sessions = [s for s in agents if s.get("id") and s["id"] != SELF and s.get("status")]
# A session that the last check did not judge gets the first calls, so that under a steady load the same sessions do not
# stay unjudged in each check (STORY-518). A not-judged.json that cannot be read gives the order of claude agents.
try: prev = {o["id"] for o in json.load(open(os.path.join(STATE, "not-judged.json")))["sessions"]}
except (OSError, ValueError, KeyError, TypeError): prev = set()
sessions.sort(key=lambda s: s["id"] not in prev)
# One `claude logs` call is a full claude start: about 1 s on a quiet machine, about 2 minutes under a high load
# (STORY-518). So read the logs at the same time. Each call has a time limit, and all calls of 1 check share 1 time
# budget: a call that cannot start before the end of the budget is a timeout too.
end = time.monotonic() + call.LOGS_TOTAL
def read_log(s):
    lim = call.limit(min(call.LOGS, end - time.monotonic()))
    r = call.run(["claude","logs",s["id"]], lim)
    if r is None: return None, "timeout"
    if r.returncode or not r.stdout.strip(): return None, "logs failed"   # a live session always has a screen
    return r.stdout, ""
with ThreadPoolExecutor(8) as pool:
    logs = list(pool.map(read_log, sessions))
# A session with a failed read gets no verdict in this check: it is not "no API error" (STORY-518).
with open(os.path.join(STATE, "not-judged.json"),"w") as f:
    json.dump({"live": len(sessions), "sessions": [{"id": s["id"], "name": s.get("name"), "cause": cause}
               for s, (raw, cause) in zip(sessions, logs) if raw is None]}, f)
out = []
for s, (raw, _) in zip(sessions, logs):
    if raw is None: continue
    sid = s["id"]
    t = re.sub(r"\x1b\[[0-9;]*[A-Za-z]","",raw).replace("\r","").replace("⏺","\n⏺")
    lines, in_recap = [], False
    for l in (l.strip() for l in t.split("\n")):
        # a "※recap:" footer can wrap over lines; it ends at "(disable recaps in /config)". It can quote "API Error".
        if l.startswith("※recap"): in_recap = True
        if not in_recap and l and not NOISE.match(l): lines.append(l)
        if in_recap and "disable recaps" in l: in_recap = False
    idx = [i for i,l in enumerate(lines) if re.search(r"API Error", l, re.I)]
    if not idx: continue
    # stuck = the API Error is the last real event (only completion marks, prompts, or queued messages follow)
    # the terminal can drop letters, for example "1 neds input & 10"
    # A line that starts with "❯" opens the footer of a screen redraw (input box, status line, mode line, digit
    # noise). The footer ends at the next line that starts a transcript event. A footer line is not a real line.
    real_after, footer = [], False
    for l in lines[idx[-1]+1:]:
        if l.startswith("❯"): footer = True
        elif footer and EVENT.match(l): footer = False
        if footer or BORDER.match(l) or SKIP.match(l): continue
        real_after.append(l)
    out.append({"id": sid, "name": s.get("name"), "state": s.get("state"), "status": s.get("status",""),
                "api_errors_in_log": len(idx),
                "last_error": lines[idx[-1]][:110],
                "real_lines_after_last_error": len(real_after),
                "stuck": len(real_after) == 0,
                "what_follows_last_error": [l[:110] for l in real_after[:3]]})
with open(os.path.join(STATE, "sessions.jsonl"),"w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False)+"\n")
print(len(out), "sessions with API Error in log")
