#!/usr/bin/env bash
# relay: resolve the git directory that holds one run's refine findings.
# EXECUTED, never sourced:
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-paths.sh" <worktree>
#
# Prints the absolute git directory of <worktree> to stdout and nothing else.
# For a worktree that path resolves outside the working tree
# (<main>/.git/worktrees/<name>), so the findings files and subject snapshots
# the refine loops write are never staged and never committed.
#
# EXIT CODES — these two and no others:
#   0  the path is the only thing on stdout.
#   1  <worktree> is missing or is not a repository. stdout is empty and the
#      reason is on stderr. The generator treats this as a fatal setup error
#      and stops the run; it never falls back to a relative findings path.
set -u

if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then
  echo "refine-paths.sh: usage: refine-paths.sh <worktree>" >&2
  exit 1
fi

_worktree="$1"

if ! _git_dir="$(git -C "$_worktree" rev-parse --absolute-git-dir 2>/dev/null)"; then
  echo "refine-paths.sh: not a git repository: $_worktree" >&2
  exit 1
fi

printf '%s\n' "$_git_dir"
