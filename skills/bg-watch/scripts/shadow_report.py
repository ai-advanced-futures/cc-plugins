import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
# The comparison of the shadow mode (STORY-562): the transcript against claude logs, over the jag log rows of a time window.
#   python3 shadow_report.py [--since TIME] [--until TIME] [--log FILE]
# TIME is an ISO 8601 time (UTC when it has no zone). The default log is jag-log.jsonl of the state folder.
# Each session of the "transcript" part of a row is 1 pair (check time, session). The classes are those of the STORY-518
# spike, for a pair where claude logs saw an "API Error" line and the transcript read has a result:
#   AGREE  the transcript has an API error entry, and its stuck value is the stuck value of claude logs
#   DIFF   the transcript has an API error entry, and its stuck value is not the stuck value of claude logs
#   MISS   the transcript has no API error entry and no "API Error" text
#   QUOTE  the transcript has no API error entry, but an entry quotes the text "API Error"
# A logs-positive pair is a pair of class AGREE, DIFF or MISS. A QUOTE pair is not one, and the stop rule (the STORY-518
# spec, "The spike", item 5) does not count it. The stop rule gives the result lines.
STATE = os.path.expanduser(os.environ.get("BG_WATCH_STATE", "~/.claude/bg-watch"))
def when(text):
    try: t = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError: raise argparse.ArgumentTypeError(f"not an ISO 8601 time: {text!r}")
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
ap = argparse.ArgumentParser(description="Compare the shadow transcript read with claude logs over the jag log.")
ap.add_argument("--since", type=when, help="the first check time of the window")
ap.add_argument("--until", type=when, help="the last check time of the window")
ap.add_argument("--log", default=os.path.join(STATE, "jag-log.jsonl"), help="the jag log (default: %(default)s)")
a = ap.parse_args()
try: lines = open(a.log, encoding="utf-8").read().splitlines()
except OSError as x: sys.exit(f"shadow_report: cannot read {a.log}: {x.strerror}")
n: "Counter[str]" = Counter(); not_read: "Counter[str]" = Counter()
diffs, misses, rows, bad, no_read = [], [], [], 0, 0
for line in lines:
    try: r = json.loads(line); at = when(r["at"])
    except (ValueError, KeyError, TypeError, argparse.ArgumentTypeError): bad += 1; continue
    if (a.since and at < a.since) or (a.until and at > a.until): continue
    rows.append(r["at"])
    t = r.get("transcript")
    if not isinstance(t, dict): no_read += 1; continue
    for o in t.get("sessions", []):
        n["logs stuck"] += bool(o.get("logs_stuck"))   # also a pair with no transcript result
        if o.get("cause"): not_read[o["cause"].split(":")[0]] += 1; continue
        if not o.get("logs_error"):
            n["transcript only"] += bool(o.get("stuck")); continue
        n["logs stuck read"] += bool(o.get("logs_stuck"))
        if o.get("errors"):
            if o.get("stuck") == o.get("logs_stuck"): n["AGREE"] += 1
            else: n["DIFF"] += 1; diffs.append((r["at"], o["id"], o.get("logs_stuck"), o.get("stuck")))
        elif o.get("quote"): n["QUOTE"] += 1
        else: n["MISS"] += 1; misses.append((r["at"], o["id"]))
pos = n["AGREE"] + n["DIFF"] + n["MISS"]
print("jag log:", a.log)
print(f"rows: {len(rows)} in the window" + (f" ({rows[0]} to {rows[-1]})" if rows else "")
      + f", {len(rows) - no_read} with a shadow read" + (f", {bad} not read (not JSON)" if bad else ""))
for k in ("AGREE", "DIFF", "MISS", "QUOTE"): print(f"{k}: {n[k]}")
print(f"logs-positive pairs (AGREE + DIFF + MISS): {pos}")
print(f"pairs where claude logs saw a stuck session: {n['logs stuck']}, {n['logs stuck read']} of them with a transcript result")
print(f"transcript stuck, no API Error line in claude logs: {n['transcript only']} (outside the stop rule)")
print(f"pairs with no transcript result: {sum(not_read.values())}"
      + "".join(f"; {c}: {k}" for c, k in sorted(not_read.items())))
for at, sid, ls, ts in diffs: print(f"DIFF {at} {sid}: claude logs stuck={ls}, transcript stuck={ts}")
for at, sid in misses: print(f"MISS {at} {sid}")
# Each sentence of the stop rule gives its own line: a MISS and too few pairs can both apply.
if n["MISS"]: print(f"result: not the same as claude logs (MISS = {n['MISS']}): the check keeps claude logs")
if pos < 10: print(f"result: too few positive pairs to claim the same ({pos} logs-positive pairs)")
if not n["MISS"] and pos >= 10:
    if n["DIFF"]: print(f"result: the same as claude logs only if each DIFF above is explained (DIFF = {n['DIFF']}, {pos} logs-positive pairs)")
    else: print(f"result: the same as claude logs (MISS = 0, DIFF = 0, {pos} logs-positive pairs)")
if not n["logs stuck read"]:
    print("note: no pair where claude logs saw a stuck session has a transcript result, so the data does not show whether the transcript sees a stuck session")
