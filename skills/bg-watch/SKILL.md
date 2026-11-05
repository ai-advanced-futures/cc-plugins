---
name: bg-watch
description: Watch the background Claude Code sessions on this machine. Find a session that stopped on an API error, restart it, and send it `retry`. jag decides which sessions are stuck, and each jag decision goes into a log. Use "start" to run the check on a schedule, "check" to run it one time, and "stop" to cancel the schedule.
when_to_use: The user asks to watch, monitor, or babysit background sessions, to rescue sessions stuck on an API error, or to retry failed bg sessions on a schedule.
argument-hint: "[start [interval] | check | stop]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/run.py)
---

# Watch background sessions

Do the mode in `$ARGUMENTS`. If `$ARGUMENTS` is empty, do `start` with the default interval.

## Mode: start [interval]

1. Get the interval from the second word. The default is `5m`. Change it to a cron expression:
   - `Nm` with N 59 or less: `*/N * * * *`
   - `Nh` with N 23 or less: `0 */N * * *`
   If N does not divide its unit (for example `7m`), use the nearest value that does, and tell the user.
2. Load the tools in one call: ToolSearch `select:CronCreate,CronList,CronDelete,SendMessage`.
3. Call CronList. If a job with the prompt `/bg-watch check` exists, do not make a second one. Tell the user its ID and go to step 5.
4. Call CronCreate with:
   - `cron`: the expression from step 1
   - `prompt`: `/bg-watch check`
   - `recurring`: `true`
5. Tell the user: the job ID, the interval, that the job stops after 7 days or when this session ends, and that `/bg-watch stop` cancels it.
6. Do the `check` mode one time now. Do not wait for the first firing.

## Mode: check

1. Run this command:
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/run.py
   ```
   The script does these steps:
   - It reads each session log with `claude logs`.
   - It sets its own `stuck` flag when an `API Error` line is the last real event in the log. Any API error counts. The footer of a screen redraw (the input box, the status line, and the lines under it) is not a real event.
   - It asks `jag --ask` which sessions are stuck. jag decides from the facts of each session (the count of real lines after the last error and the first one). The input holds no `stuck` value. jag marks each session line of a block, so the script restarts a session that jag marked only when the session has 0 real lines after its last error. The flag is only a second opinion. If `--ask` cannot run, the script uses a free `jag -F "real_lines_after_last_error=0 |"` search. If jag is not installed, it uses the flag.
   - For each stuck session that is not `busy`, it runs `claude stop <id>` and then `claude respawn <id>`.
   - It keeps the failure counts in `~/.claude/bg-watch/failure-history.json`.
   - It adds one line to `~/.claude/bg-watch/jag-log.jsonl`: the jag command, the exit code, the time, the jag output, and the sessions where jag and the flag do not agree. The jag input of each check stays in `~/.claude/bg-watch/jag-input/`.
   - It prints the jag mode, the disagreements, a table, and a last line `RETRY_TO: [names]`.
2. For each name in `RETRY_TO`, send the message `retry` with SendMessage. Use the session name. If two sessions have the same name, use the ref that the error message gives, for example `marina-implementer [e253e8]`.
3. If the table shows a session as `STUCK (+1), skipped (busy)`, wait 30 seconds and run the script again. If the session is still stuck, rescue it with steps 1 and 2.
4. Report to the user:
   - Show the stuck sessions first, with the mark **(+1)** and the words "restarted, now working, `retry` sent".
   - Then show the table of the sessions with the most failures.
   - If the table shows `respawn failed`, give the user the session and the error text. The script did not send `retry` to it.
   - Then a **jag** part: the mode that ran, each session where jag and the flag do not agree, and the path of the jag log. If the script printed `jag error cause` and `jag error fix`, give them to the user. If the script printed `jag left out`, tell the user that jag did not judge all sessions.
   - Tell the user what changed since the last check: new sessions, counts that went up, and sessions that moved into or out of the log window.

## Mode: stop

1. Load CronList and CronDelete with ToolSearch.
2. Call CronList. Find the job with the prompt `/bg-watch check`.
3. Call CronDelete with its ID. Tell the user the ID that you cancelled.

## Rules

- Never run `claude rm`. Never delete a session.
- Do not restart a session with the status `busy`. It can be in the middle of a turn.
- Do not restart a session that jag did not select, even if the flag says it is stuck. Report the disagreement.
- The script skips the session that runs this skill. A session that only quotes error text (for example, a report about errors) can show as a false positive. Tell the user about it, and do not restart it.
- For jag: use `--json --max-chars N`. Do not run `jag --check` or `jag --setup`. Never read or print `~/.config/jag/`.
- A session that gets `retry` does not reply. Use the next check to confirm that it works again.
