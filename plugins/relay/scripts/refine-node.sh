#!/usr/bin/env bash
# relay: the shell work of one critic pass of a refine loop.
# EXECUTED, never sourced:
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-node.sh" <subject> <snapshot> <findings>
#
# The body lives here, not inline in the generated Workflow script and not in
# prose appended to a node prompt, for the reason `verify-loop-node.sh` gives:
# inline bash in a generated script cannot be unit-tested, so the shape the
# skill documents and the shape a run executes can differ and nothing finds it.
# One script also means one body for both engines. The in-session leaf and the
# `acpx` watcher run the same line, so neither needs a written-file exception
# to the role contract: the script writes the snapshot, the role never does.
#
# It does two things and prints one line:
#   1. Copy <subject> to <snapshot>, creating the snapshot directory first.
#      Every later critic and the fixer's ORIGINAL_SNAPSHOT read that file.
#   2. Run `refine-verdict.sh` on <findings> and print the line it returns,
#      unchanged. `refine-verdict.sh` stays pure — it writes nothing.
#
# EXIT CODES — these two and no others:
#   0  the verdict line is the only thing on stdout.
#   1  a bad argument, or the snapshot could not be written. stdout is empty
#      and the reason is on stderr. The node reports `errored`; it never
#      reports a verdict it did not get.
set -u

_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -ne 3 ] || [ -z "${1:-}" ] || [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
  echo "refine-node.sh: usage: refine-node.sh <subject> <snapshot> <findings>" >&2
  exit 1
fi

_subject="$1"
_snapshot="$2"
_findings="$3"

if [ ! -f "$_subject" ]; then
  echo "refine-node.sh: subject not found: $_subject" >&2
  exit 1
fi

if ! mkdir -p "$(dirname "$_snapshot")"; then
  echo "refine-node.sh: cannot create the snapshot directory for: $_snapshot" >&2
  exit 1
fi

if ! cp "$_subject" "$_snapshot"; then
  echo "refine-node.sh: cannot write the snapshot: $_snapshot" >&2
  exit 1
fi

exec bash "$_here/refine-verdict.sh" "$_findings"
