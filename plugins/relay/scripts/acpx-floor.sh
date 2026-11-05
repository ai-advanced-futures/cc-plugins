#!/usr/bin/env bash
# acpx version floor — the single site that states the minimum acpx relay needs.
#
# Every other floor mention in this plugin is prose that points here. Before this
# script existed the floor lived in five files that disagreed (0.7.0 in
# check-readiness and flows/package.json, 0.12.0 in the two setup skills) and no
# code ever checked it, so a machine on a stale acpx failed later, deep inside a
# dispatch, with an error that named neither acpx nor the version.
#
# Usage:
#   source acpx-floor.sh && relay_acpx_floor_check || exit 1   # from another script
#   bash acpx-floor.sh                                         # from a skill/doc step
#
# On success it prints `RELAY_ACPX_VERSION=<version>` on stdout and returns 0.
# On failure it prints one `[relay] error:` line on stderr and returns 1.

RELAY_ACPX_MIN=0.21.1

# Why 0.21.1 and not 0.19.3:
#   0.19.4 moves the Claude adapter @agentclientprotocol/claude-agent-acp from
#          ^0.76.0 to ^0.81.2 for current models, and keeps sessions saved under an
#          earlier built-in command discoverable after an upgrade. It keeps local
#          records separate when an adapter reuses a session ID, and retires an
#          adapter when a model-selection request times out.
#   0.19.5 serializes `sessions ensure`, so two callers cannot make two records for one
#          scope. The three session drivers call it.
#   0.20.0 updates the ACP SDK.
#   0.21.1 moves the Claude adapter to ^0.95.0. It is the newest release at the
#          time of the bump (2026-11-03): no CLI change relay depends on. The floor
#          tracks the version relay is live-proved against.
#
# Why 0.19.3 and not 0.16.0:
#   0.18.0 requires a final ACP response before it reports a turn complete, so a
#          turn relay reads as finished has really finished.
#   0.19.0 keeps partial assistant text when a turn fails, so non-empty stdout no
#          longer proves success. relay reads a verdict on exit code 0 alone.
#   0.19.1 stops session lookup at a worktree's `.git` file instead of walking to
#          the main checkout. Before it, a run inside `.claude/worktrees/<x>` could
#          resume an open main-checkout record of the same name and then work in the
#          main checkout.
#   0.19.1 also carries `sessions watch`, the NDJSON event stream that
#          scripts/acpx-wait.sh reads. It is the only new command relay uses.
#   0.19.2 lets `sessions watch` find a queue owner that is gone, even when the
#          system reused its PID number. It also drains kept events when a session
#          closes.
#   0.19.3 keeps queue-owner cleanup safe on macOS when a second stop signal
#          arrives. `resume` and `sessions ensure` now retire the previous owner
#          first, when you run them from another working directory.
#
# Why 0.16.0 and not 0.13.2 (the previous step):
#   0.14.0 gives one-shot `exec` a repeatable `--config-option <key=value>`, applied
#          after `--model` and before the prompt. That is the same
#          session/set_config_option call the session drivers make with `set`, so
#          the one-shot codex paths can set `mode` and `reasoning_effort` the way the
#          codex session driver does, and the CODEX_CONFIG env blob is gone.
#   0.15.1 caps incoming ACP messages at 64 MiB by default
#          (ACPX_MAX_ACP_MESSAGE_BYTES raises it). relay's envelope path was
#          live-proved under that default.
#   0.16.0 is the newest release at the time of the bump (2026-09-16): session,
#          filesystem and queue hardening, no CLI change relay depends on. The
#          floor tracks the version relay is live-proved against.
#
# Why 0.13.2 and not 0.12.0 (the previous step):
#   0.12.1 refreshed acpx's own adapter pins — codex ^0.0.44 -> ^1.1.5. The
#          ^0.0.44 pin was broken, and relay carried an `--agent` override to
#          work around it (relay 4.6.1). At this floor the override is gone.
#   0.13.1 re-applies the pinned model on reconnect and keeps messageId/_meta on
#          message chunks, which is what acpx-envelope.sh groups by.
#   0.13.2 restores the saved model and config options after a reconnect and
#          REPORTS a replay failure instead of silently running on defaults.
#          delegate-and-watch routes that report to its `errored` bucket.

# Compare two dotted versions. Returns 0 when $1 >= $2.
relay_acpx_version_ge() {
    [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]
}

relay_acpx_floor_check() {
    local found
    if ! found=$(acpx --version 2>/dev/null); then
        printf '[relay] error: acpx is not on PATH. Run: npm install -g acpx@latest\n' >&2
        return 1
    fi
    # `acpx --version` prints a bare semver; extract the first dotted-number token
    # defensively so a future `name X.Y.Z` banner cannot be concatenated into a
    # string that sorts ABOVE the floor and silently bypasses the gate.
    found=$(printf '%s' "$found" | head -1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -1)
    if [ -z "$found" ]; then
        printf '[relay] error: acpx --version printed no version. Run: npm install -g acpx@latest\n' >&2
        return 1
    fi
    if ! relay_acpx_version_ge "$found" "$RELAY_ACPX_MIN"; then
        printf '[relay] error: acpx %s is below the floor %s. Run: npm install -g acpx@latest\n' \
            "$found" "$RELAY_ACPX_MIN" >&2
        return 1
    fi
    printf 'RELAY_ACPX_VERSION=%s\n' "$found"
    return 0
}

# Executed directly (not sourced): run the check and exit on its result.
# ${BASH_SOURCE[0]} != $0 when this file is sourced.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    relay_acpx_floor_check || exit 1
fi
