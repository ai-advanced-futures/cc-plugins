import json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.expanduser(os.environ.get("BG_WATCH_STATE", "~/.claude/bg-watch"))
os.makedirs(STATE, exist_ok=True)
P = lambda n: os.path.join(STATE, n)
KEEP_INPUTS = 500
QUESTION = "Which session is stuck: nothing real happened after its last API Error?"
# The free search term: the sessions with no real line after the last API Error, which are the sessions of the built-in rule.
FREE_TERM = "real_lines_after_last_error=0 |"
# stderr stays visible, so that a failure of build_info.py shows its cause
subprocess.run([sys.executable, os.path.join(HERE, "build_info.py")],check=True,stdout=subprocess.DEVNULL)
info = {}
for line in open(P("sessions.jsonl")):
    o = json.loads(line); info[o["id"]] = o
known = set(json.load(open(P("agents.json"))))
flag = sorted(k for k, o in info.items() if o["stuck"])   # second opinion only: jag decides
# compact records for jag: one per session, decision fields first; each check keeps its own input file
now = datetime.now(timezone.utc)
os.makedirs(P("jag-input"), exist_ok=True)
inp = os.path.join(P("jag-input"), now.strftime("%Y%m%dT%H%M%S.%fZ") + ".txt")
with open(inp,"w") as f:
    for sid, o in info.items():
        nxt = (o["what_follows_last_error"] or ["nothing"])[0][:60]
        f.write(f'SESSION {sid} {o["name"]} | state={o["state"]} | real_lines_after_last_error={o["real_lines_after_last_error"]} | next_after_error: {nxt}\n---\n')
for old in sorted(os.listdir(P("jag-input")))[:-KEEP_INPUTS]:
    os.remove(os.path.join(P("jag-input"), old))

def jag(args):
    # 8000 characters hold about 20 sessions; a larger input gets a larger limit, so jag leaves out no session
    cmd = ["jag","--json","--max-chars",str(max(8000, 4*os.path.getsize(inp))),*args,inp]
    t = time.monotonic()
    r = subprocess.run(cmd,capture_output=True,text=True)
    try: out = json.loads(r.stdout)
    except ValueError: out = r.stdout   # keep the raw text for the jag log
    return cmd, r.returncode, out, round(time.monotonic()-t, 2)

def picked(res):
    # no_good_answer=true means no session is stuck. jag --ask returns whole blocks with each SESSION line matched,
    # so a match alone does not select a session. A matched session counts only when its own fact says that no real
    # line follows its last API Error. The input holds no built-in stuck value, so jag still decides from the facts.
    if not isinstance(res, dict) or res.get("no_good_answer"): return []
    return sorted({words[1] for x in res.get("results", []) for l in x.get("lines", [])
                   if l.get("is_match") and len(words := l.get("text", "").split()) > 1 and words[1] in info
                   and info[words[1]]["real_lines_after_last_error"] == 0})

ask_error = None
if not info:   # nothing to judge: no model call
    mode, cmd, code, res, secs, stuck = "no session with an API Error", None, 0, None, 0, []
elif shutil.which("jag") is None:   # jag not installed: use the script's own stuck flag
    mode, cmd, code, res, secs, stuck = "built-in stuck flag (jag not installed)", None, 127, None, 0, flag
else:
    cmd, code, res, secs = jag(["--ask",QUESTION,"SESSION"]); mode = "jag --ask"
    if isinstance(res, dict) and res.get("error"): ask_error = res["error"]
    if code in (3, 4, 5, 6, 126):   # jag cannot run (key, credit, service, start): free jag search of the same fact
        if ask_error is None: ask_error = res
        cmd, code, res, s2 = jag(["-F",FREE_TERM]); secs += s2; mode = "jag free mode (--ask failed)"
    stuck = picked(res)
left_out = res.get("left_out", 0) if isinstance(res, dict) else 0
disagree = sorted(set(flag) ^ set(stuck))
# history + rescue (claude respawn only: no claude stop, no --all, never rm); sessions that no longer exist
# leave the history
hist = json.load(open(P("failure-history.json"))) if os.path.exists(P("failure-history.json")) else {}
hist = {k: v for k, v in hist.items() if k in known}
agents_now = lambda: {s["id"]: s for s in json.loads(subprocess.run(["claude","agents","--json","--all"],capture_output=True,text=True).stdout or "[]") if s.get("id")}
rescued, failed = {}, {}
for sid, o in info.items():
    h = hist.setdefault(sid, {"name": o["name"], "count": 0, "keys": []})
    h["name"] = o["name"]; h["count"] = max(h["count"], o["api_errors_in_log"]); h["faulty_last_check"] = sid in stuck
if stuck:
    # read the status again: the logs and jag take time, and a session can start a turn in that time
    fresh = agents_now()
    for sid in stuck:
        # Only an idle session gets a respawn. busy: a respawn cuts its turn. No status: no live process (stopped).
        # Another value: unknown. Each of them is left alone, and the table names it.
        status = fresh.get(sid, info[sid]).get("status") or ""
        if status != "idle":
            info[sid]["status"] = status or "stopped"; continue
        r = subprocess.run(["claude","respawn",sid],capture_output=True,text=True)
        if r.returncode: failed[sid] = (r.stderr or r.stdout).strip()[:110]
        else: rescued[sid] = "?"
    if rescued:
        fresh = agents_now()
        rescued = {sid: fresh.get(sid, {}).get("state") or "?" for sid in rescued}
json.dump(hist, open(P("failure-history.json"),"w"), indent=1)
with open(P("jag-log.jsonl"),"a") as f:
    f.write(json.dumps({"at": now.isoformat(), "mode": mode, "cmd": cmd, "exit": code, "seconds": secs,
                        "input": inp, "output": res, "ask_error": ask_error, "left_out": left_out,
                        "flag_stuck": flag, "jag_stuck": stuck, "disagree": disagree}, ensure_ascii=False)+"\n")
print(f"jag mode: {mode} | exit {code} | stuck: {len(stuck)}")
if isinstance(ask_error, dict):
    print("jag error cause:", ask_error.get("cause")); print("jag error fix:", ask_error.get("fix"))
if left_out:
    print(f"jag left out {left_out} result(s): the size limit was too small, so these sessions were not judged")
print("jag disagrees:", ", ".join(disagree) or "none")
print("jag log:", P("jag-log.jsonl"))
print("| Session | Name | Total failures seen | Status now |\n|---|---|---|---|")
for sid, h in sorted(hist.items(), key=lambda kv: -kv[1]["count"]):
    if sid in stuck:
        now_s = "STUCK (+1), " + (f"restarted: {rescued[sid]}" if sid in rescued
                                  else f"respawn failed: {failed[sid]}" if sid in failed
                                  else f"skipped ({info[sid]['status']})")
    elif sid in info: now_s = "recovered"
    else: now_s = "recovered (not in log window)"
    print(f'| `{sid}` | {h["name"]} | {h["count"]} | {now_s} |')
print("RETRY_TO:", json.dumps([info[s]["name"] for s in rescued]))
