import os, signal, subprocess, sys, time
# The time limits of the claude and jag calls of bg-watch, in seconds (STORY-518). The STORY-518 spec gives the reason
# of each value. A test gives a smaller value with the environment variable of the same name.
def _limit(name, default):
    v = os.environ.get(name, "")
    if not v: return default
    try: s = float(v)
    except ValueError: s = 0
    # At most 1 day: the wait of Python takes at most about 24 days (a poll in milliseconds), and a larger value (1e7, inf)
    # stops the check with OverflowError.
    if not 0 < s <= 86400: sys.exit(f"bg-watch: {name} must be a number of seconds above 0 and at most 86400, not {v!r}")
    return s
AGENTS = _limit("BG_WATCH_LIMIT_AGENTS", 60)            # 1 read of claude agents --json --all
LOGS = _limit("BG_WATCH_LIMIT_LOGS", 180)               # 1 claude logs <id> call
LOGS_TOTAL = _limit("BG_WATCH_LIMIT_LOGS_TOTAL", 360)   # all claude logs calls of 1 check
JAG = _limit("BG_WATCH_LIMIT_JAG", 120)                 # 1 jag call
RESPAWN = _limit("BG_WATCH_LIMIT_RESPAWN", 180)         # 1 claude respawn <id> call
CHECK = _limit("BG_WATCH_LIMIT_CHECK", 540)             # all calls of 1 run of run.py (and of build_info.py)
TRANSCRIPT = _limit("BG_WATCH_LIMIT_TRANSCRIPT", 30)    # 1 shadow read of a transcript (STORY-562)
TRANSCRIPT_TOTAL = _limit("BG_WATCH_LIMIT_TRANSCRIPT_TOTAL", 120)   # all shadow reads of 1 check
secs = lambda s: f"{s:g} s"
# The end of the check. No call starts after it, and a call that runs at that time stops then, so 1 run of run.py ends
# within CHECK + 5 s. The Bash tool of the cron session stops a command after about 12 minutes (the spec, "The limits
# and the budget").
_end = time.monotonic() + CHECK
def limit(own):
    """The limit of 1 call: its own limit, or the time to the end of the check when that is shorter."""
    return min(own, _end - time.monotonic())
def cause(lim):
    """The cause of a call that gave None with the limit lim: a timeout, or no start because the check has no time left."""
    return f"timeout after {secs(round(lim, 1))}" if lim > 0 else f"not started: the check limit of {secs(CHECK)} is reached"

# The process of each call that runs now. Each call runs in its own process group, so a stop of the group of the script
# does not reach it. So at a stop signal the script first stops the group of each call that runs, then exits. A SIGKILL
# cannot be caught: then a call that waits lives on until it ends (the spec, "Risks").
_live: "set[subprocess.Popen[str]]" = set()   # a string: no evaluation at the start, on each Python 3
def _stop(signum, frame):
    for p in list(_live):
        try: os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError): pass   # see run()
    os._exit(128 + signum)
for _s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT): signal.signal(_s, _stop)

def run(cmd, limit):
    """Run cmd with a time limit. Give the CompletedProcess, or None at the limit. A limit that is not above 0 gives None
    with no start.
    The command starts in its own process group, and at the limit a kill of the group also stops its children, for
    example a keychain lookup that waits with no end (docs/adlc.md rule 16). A session that claude respawn starts is
    not in that group: each background session runs in its own process group."""
    if limit <= 0: return None
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    _live.add(p)
    try:
        out, err = p.communicate(timeout=limit)
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)
    except subprocess.TimeoutExpired:
        try: os.killpg(p.pid, signal.SIGKILL)
        # ProcessLookupError: the group is gone. PermissionError: on macOS, a group that holds only zombies, for example
        # a call that ended while a process of its own session keeps the pipes open (PR 2402).
        except (ProcessLookupError, PermissionError): pass
        # No communicate() after the kill: a child that lives on keeps the pipes open, and the read would wait for it.
        # A process in an uninterruptible wait ends after its wait, so the check does not wait more than 5 s for it.
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: pass
        if p.stdout: p.stdout.close()
        if p.stderr: p.stderr.close()
        return None
    finally:
        _live.discard(p)
