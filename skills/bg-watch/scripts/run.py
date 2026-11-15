import fcntl, json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import call, claude_agents
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.expanduser(os.environ.get("BG_WATCH_STATE", "~/.claude/bg-watch"))
os.makedirs(STATE, exist_ok=True)
P = lambda n: os.path.join(STATE, n)
# 1 check at a time (STORY-508). build_info.py gets the lock file too (pass_fds), so the lock ends only when
# run.py and build_info.py have both ended, also after a kill. No other child gets it: a session that claude respawn
# starts must not hold the lock.
# check.lock, not run.lock: a scheduler can hold its own lock file around the call that runs this script, and this
# script cannot take a lock that its caller holds. Never delete check.lock: a new file would let 2 checks run.
LOCK = open(P("check.lock"), "a")
try: fcntl.flock(LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("another check is running"); print("RETRY_TO: []"); sys.exit(0)
KEEP_INPUTS = 500
QUESTION = "Which session is stuck: nothing real happened after its last API Error?"
# The free search term: the sessions with no real line after the last API Error, which are the sessions of the built-in rule.
FREE_TERM = "real_lines_after_last_error=0 |"
# stderr stays visible, so that a failure of build_info.py shows its cause
build = subprocess.run([sys.executable, os.path.join(HERE, "build_info.py")],stdout=subprocess.DEVNULL,pass_fds=(LOCK.fileno(),))
# a code below 0 is a signal: sys.exit(-9) would give the shell exit 247
if build.returncode: sys.exit(build.returncode if build.returncode > 0 else f"bg-watch: build_info.py stopped on signal {-build.returncode}")
info = {}
for line in open(P("sessions.jsonl")):
    o = json.loads(line); info[o["id"]] = o
known = set(json.load(open(P("agents.json"))))
# the live sessions whose claude logs call timed out or failed: no verdict in this check (STORY-518)
nj = json.load(open(P("not-judged.json")))
unjudged = {o["id"]: o for o in nj["sessions"]}
logs_unjudged = set(unjudged)   # claude logs did not judge these sessions: no shadow read (STORY-562)
flag = sorted(k for k, o in info.items() if o["stuck"])   # second opinion only: jag decides
# compact records for jag: one per session, decision fields first; each check keeps its own input file
now = datetime.now(timezone.utc)
T = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)   # the format of a transcript timestamp
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
    lim = call.limit(call.JAG)
    r = call.run(cmd, lim)
    # a call that times out or has no time left gives the code "timeout", and its cause in place of the output
    if r is None: return cmd, "timeout", call.cause(lim), round(time.monotonic()-t, 2)
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
no_answer = False
if not info:   # nothing to judge: no model call. A session whose read failed is not in info, so the mode line names them.
    mode = "no session with an API Error" + (f" in the logs that were read ({len(unjudged)} not judged)" if unjudged else "")
    cmd, code, res, secs, stuck = None, 0, None, 0, []
elif shutil.which("jag") is None:   # jag not installed: use the script's own stuck flag
    mode, cmd, code, res, secs, stuck = "built-in stuck flag (jag not installed)", None, 127, None, 0, flag
else:
    cmd, code, res, secs = jag(["--ask",QUESTION,"SESSION"]); mode = "jag --ask"
    if isinstance(res, dict) and res.get("error"): ask_error = res["error"]
    # jag cannot run (key, credit, service, start) or times out: free jag search of the same fact
    if code in (3, 4, 5, 6, 126, "timeout"):
        if ask_error is None: ask_error = res
        cmd, code, res, s2 = jag(["-F",FREE_TERM]); secs += s2; mode = "jag free mode (--ask failed)"
    stuck = picked(res)
    # jag gave no answer: a timeout, a call with no time left, an output that is not a JSON object, an exit code that is
    # not 0, 1, 7 or 8, or an error. Then no session of the jag input gets a verdict in this check: no restart, not
    # "recovered", and no history change (STORY-518). The real jag prints "results" in each output, also with an error, so
    # the rule reads the exit code and "error". A free search that finds no match exits 1 with "error": null and
    # "results": [], and that is an answer. 7 (the cost limit) and 8 (the size limit) are answers too: jag says "The
    # results are valid. Use them." The block after this one finds the sessions that such an answer does not show
    # (STORY-563).
    no_answer = not isinstance(res, dict) or code not in (0, 1, 7, 8) or res.get("error") is not None
    if no_answer:
        stuck = []   # no verdict: an output with no answer can hold matched lines, and they restart no session
        jag_cause = "jag timeout" if code == "timeout" else "jag failed"
        for sid, o in info.items(): unjudged[sid] = {"id": sid, "name": o["name"], "cause": jag_cause}
        nj["sessions"] += [unjudged[sid] for sid in info]
        # the next check reads the logs of these sessions first, as for a failed read (build_info.py)
        json.dump(nj, open(P("not-judged.json"), "w"))
left_out = res.get("left_out", 0) if isinstance(res, dict) else 0
# jag left out results (the size limit: left_out, top_result_cut) or did not score them (the cost limit: results_skipped)
# (STORY-563). jag gives a verdict on a session only in a line that it shows. Only a session with 0 real lines after its
# last error can be stuck (picked()), so each such session that no line of a result names gets no verdict in this check,
# as for no answer: no restart, not "recovered", and no history change. jag scores each kept result before the size limit
# leaves results out, so with no_good_answer only skipped results (the cost limit) give no verdict.
if isinstance(res, dict) and not no_answer and (
        res.get("results_skipped") or (not res.get("no_good_answer") and (left_out or res.get("top_result_cut")))):
    shown = {w[1] for x in res.get("results", []) for l in x.get("lines", [])
             if len(w := l.get("text", "").split()) > 1 and w[0] == "SESSION"}
    missed = [sid for sid, o in info.items() if sid not in shown and o["real_lines_after_last_error"] == 0]
    for sid in missed: unjudged[sid] = {"id": sid, "name": info[sid]["name"], "cause": "jag left out"}
    if missed:
        nj["sessions"] += [unjudged[sid] for sid in missed]
        # the next check reads the logs of these sessions first, as for a failed read (build_info.py)
        json.dump(nj, open(P("not-judged.json"), "w"))
# no answer: no opinion of jag. A session that jag did not judge is not a disagreement.
disagree = [] if no_answer else sorted((set(flag) ^ set(stuck)) - set(unjudged))
# history + rescue (claude respawn only: no claude stop, no --all, never rm); sessions that no longer exist
# leave the history
hist = json.load(open(P("failure-history.json"))) if os.path.exists(P("failure-history.json")) else {}
hist = {k: v for k, v in hist.items() if k in known}
def agents_now():
    # None when the read fails: an empty output or a failed read is not "no session" (claude_agents.read)
    d, cause = claude_agents.read()
    if d is None: print("the read of claude agents --json --all failed:", cause)
    return None if d is None else {s["id"]: s for s in d if s.get("id")}
rescued, failed = {}, {}
for sid, o in info.items():
    if sid in unjudged: continue   # no answer of jag: the history stays
    h = hist.setdefault(sid, {"name": o["name"], "count": 0, "keys": []})
    h["name"] = o["name"]; h["count"] = max(h["count"], o["api_errors_in_log"]); h["faulty_last_check"] = sid in stuck
if stuck:
    # read the status again: the logs and jag take time, and a session can start a turn in that time
    fresh = agents_now()
    for sid in stuck:
        if fresh is None:   # no fresh status: a respawn could cut a turn that started after the first read
            info[sid]["status"] = "agents read failed"; continue
        # Only an idle session gets a respawn. busy: a respawn cuts its turn. No status: no live process (stopped).
        # Another value: unknown. Each of them is left alone, and the table names it.
        status = fresh.get(sid, info[sid]).get("status") or ""
        if status != "idle":
            info[sid]["status"] = status or "stopped"; continue
        lim = call.limit(call.RESPAWN)
        r = call.run(["claude","respawn",sid], lim)
        if r is None: failed[sid] = call.cause(lim)
        elif r.returncode: failed[sid] = (r.stderr or r.stdout).strip()[:110]
        else: rescued[sid] = "?"
    if rescued:
        fresh = agents_now() or {}   # a failed read leaves the state of each rescued session as "?"
        rescued = {sid: fresh.get(sid, {}).get("state") or "?" for sid in rescued}
json.dump(hist, open(P("failure-history.json"),"w"), indent=1)
# Shadow mode (STORY-562): read the transcript of each live session that claude logs judged, up to the check time T,
# and write both results to the jag log row. It runs after the verdicts and the restarts, so it takes no time from
# them, and nothing in it changes a verdict, a restart, the table or another state file. Each read has its own limit
# and all reads share 1 budget, both inside the check limit (call.limit). A failed or late read writes its cause.
def read_transcript(s):
    sid = s["id"]
    o = {"id": sid, "logs_error": sid in info, "logs_stuck": bool(info.get(sid, {}).get("stuck")),
         "errors": None, "quote": None, "stuck": None, "cause": ""}
    try:
        if not s.get("sessionId"):
            o["cause"] = "no sessionId"; return o
        left = t_end - time.monotonic()
        if left <= 0:   # the budget of the shadow reads is spent, not the check limit (call.cause)
            o["cause"] = f"not started: the transcript budget of {call.secs(call.TRANSCRIPT_TOTAL)} is spent"; return o
        lim = call.limit(min(call.TRANSCRIPT, left))
        r = call.run([sys.executable, os.path.join(HERE, "transcript.py"), s["sessionId"], T], lim)
        if r is None: o["cause"] = call.cause(lim)
        elif r.returncode: o["cause"] = ((r.stderr or "").strip().splitlines() or [f"exit {r.returncode}"])[0][:110]
        else:
            try: o.update({k: json.loads(r.stdout)[k] for k in ("errors", "quote", "stuck")})
            except (ValueError, KeyError, TypeError): o["cause"] = "the output of transcript.py is not its JSON"
    except Exception as x:   # a fault of 1 read (for example a sessionId that is not text) stops no check: the row,
        # the count lines, the table and RETRY_TO still come
        o.update({"errors": None, "quote": None, "stuck": None, "cause": f"shadow error: {type(x).__name__}"})
    return o
t0 = time.monotonic(); t_end = t0 + call.TRANSCRIPT_TOTAL
try: live = json.load(open(P("live.json")))
except (OSError, ValueError): live = []
with ThreadPoolExecutor(8) as pool:
    shadow = list(pool.map(read_transcript, [s for s in live if s["id"] not in logs_unjudged]))
with open(P("jag-log.jsonl"),"a") as f:
    f.write(json.dumps({"at": now.isoformat(), "mode": mode, "cmd": cmd, "exit": code, "seconds": secs,
                        "input": inp, "output": res, "ask_error": ask_error, "left_out": left_out,
                        "flag_stuck": flag, "jag_stuck": stuck, "disagree": disagree,
                        "not_judged": nj["sessions"],
                        "transcript": {"at": T, "seconds": round(time.monotonic() - t0, 2), "sessions": shadow}},
                       ensure_ascii=False)+"\n")
print(f"jag mode: {mode} | exit {code} | stuck: {len(stuck)}")
if isinstance(ask_error, dict):
    print("jag error cause:", ask_error.get("cause")); print("jag error fix:", ask_error.get("fix"))
if left_out:
    print(f"jag left out {left_out} result(s): the size limit was too small")
print("jag disagrees:", ", ".join(disagree) or "none")
print("jag log:", P("jag-log.jsonl"))
causes = [o["cause"] for o in nj["sessions"]]
# each session that is not judged counts on 1 line: a timeout of claude logs or of jag counts on the timeout line
print(f'{sum(c in ("timeout", "jag timeout") for c in causes)} of {nj["live"]} not judged: timeout')
print(f'{causes.count("logs failed")} of {nj["live"]} not judged: logs failed')
print(f'{causes.count("jag failed")} of {nj["live"]} not judged: jag failed')
print(f'{causes.count("jag left out")} of {nj["live"]} not judged: jag left out')
print("| Session | Name | Total failures seen | Status now |\n|---|---|---|---|")
for sid, h in sorted(hist.items(), key=lambda kv: -kv[1]["count"]):
    if sid in stuck:
        now_s = "STUCK (+1), " + (f"restarted: {rescued[sid]}" if sid in rescued
                                  else f"respawn failed: {failed[sid]}" if sid in failed
                                  else f"skipped ({info[sid]['status']})")
    elif sid in unjudged: now_s = f'not judged: {unjudged[sid]["cause"]}'
    elif sid in info: now_s = "recovered"
    else: now_s = "recovered (not in log window)"
    print(f'| `{sid}` | {h["name"]} | {h["count"]} | {now_s} |')
for sid, o in unjudged.items():   # a session with no failure history: 1 line too
    if sid not in hist: print(f'| `{sid}` | {o["name"]} | 0 | not judged: {o["cause"]} |')
print("RETRY_TO:", json.dumps([info[s]["name"] for s in rescued]))
