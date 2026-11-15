import glob, json, os, re, sys
# The shadow read of 1 transcript (STORY-562): run.py calls it with call.run, so the read has a time limit.
#   python3 transcript.py <sessionId> <T>
# It reads the transcript <projects>/*/<sessionId>.jsonl up to the check time T and prints 1 JSON object:
#   errors: the API error entries (an assistant entry with isApiErrorMessage true, the STORY-518 spike)
#   quote:  the text "API Error" is in a user or assistant entry that is not an API error entry (a quote)
#   stuck:  the last user or assistant entry is an API error entry (the oracle of STORY-95 row 12)
# It reads only the user and assistant entries of the main session (isSidechain not true) with a timestamp at or before T.
# On a failure it prints the cause on stderr and exits 1. It prints no text and no path of the transcript.
PROJECTS = os.path.expanduser(os.environ.get("BG_WATCH_PROJECTS", "~/.claude/projects"))
TS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")   # the format of each timestamp (probe 2 of the spec)
AE = re.compile(r"API Error", re.I)                              # the text of build_info.py
sid, T = sys.argv[1], sys.argv[2]
# A sessionId is a UUID. Any other value goes into no glob.
if not re.fullmatch(r"[0-9A-Fa-f-]{8,64}", sid): sys.exit("bad sessionId")
paths = glob.glob(os.path.join(glob.escape(PROJECTS), "*", sid + ".jsonl"))
if len(paths) != 1: sys.exit("no transcript" if not paths else f"{len(paths)} transcripts")
errors, quote, stuck = 0, False, False
try:
    with open(paths[0], encoding="utf-8", errors="replace") as f:
        for line in f:
            try: e = json.loads(line)
            except ValueError: continue   # the last line can be half written
            if not isinstance(e, dict) or e.get("isSidechain"): continue
            if e.get("type") not in ("user", "assistant"): continue   # the turns of the conversation only
            ts = e.get("timestamp")
            if not isinstance(ts, str) or not TS.match(ts) or ts > T: continue
            err = e.get("type") == "assistant" and e.get("isApiErrorMessage") is True
            if err: errors += 1
            elif AE.search(line): quote = True
            stuck = err
except OSError as x:
    sys.exit(f"read failed: {x.strerror or type(x).__name__}")
print(json.dumps({"errors": errors, "quote": quote, "stuck": stuck}))
