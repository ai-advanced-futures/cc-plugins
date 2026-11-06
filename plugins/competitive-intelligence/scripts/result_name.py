# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the result file name for one run of an adopting command.

usage: uv run result_name.py <finished_at> <command> <subject> [run_id]
       uv run result_name.py now
       uv run result_name.py run-id <value>

The name is the one that result_file_name() of the checker
tests/plugin_result/plugin_result_check.py builds. `now` prints the UTC time to the
second, for a run whose `date` call was denied. `run-id` prints the value when it can name
the session folder of a plugin run. It exits 2 when the value is not a plain name, or is a
name that the plugin uses in .competitive-intelligence/ (case is ignored, because the file
system of macOS ignores it). It exits 3 when .competitive-intelligence/<value> exists under
the git root (the working folder when git finds none), because a run never writes over an
earlier session. It makes no folder. The run_id and the command part go into the
file name, so each must be a plain name: 1 to 64 of A-Z, a-z, 0-9, '.', '_', '-', and
not '.' or '..'. Standard library only.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

_NAME_TIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})")
_SLUG_LIMIT = 40
_PLAIN = re.compile(r"[A-Za-z0-9._-]{1,64}")
# The names that the plugin uses at the top of .competitive-intelligence/: the result folder,
# the monitor history, each .json file (the vendor archetype files), and the name of the session
# of a person's run (YYYYMMDDTHHMMSSZ). A session folder with one of them mixes its files with
# the files of the plugin (#549). tests/unit/test_result_name_cli.py finds each name in the text.
_RESERVED = frozenset({"results", "monitoring-history"})
_PERSON_SESSION = re.compile(r"\d{8}T\d{6}Z", re.IGNORECASE)


def plain_name(value, what):
    """Return value when it is a plain name. fullmatch refuses a final new line, which $ would let through."""
    if not _PLAIN.fullmatch(value) or value in (".", ".."):
        raise ValueError(
            "%s is not a plain name (1 to 64 of A-Z, a-z, 0-9, '.', '_', '-'; not '.' or '..'): %r"
            % (what, value)
        )
    return value


def session_name(value):
    """Return value when it can name the session folder of a plugin run."""
    plain_name(value, "run_id")
    low = value.lower()
    if low in _RESERVED or low.endswith(".json") or _PERSON_SESSION.fullmatch(value):
        raise ValueError(
            "run_id is a name that the plugin uses in .competitive-intelligence/ (results, "
            "monitoring-history, a .json file, or the name of a person's session): %r" % value
        )
    return value


def git_root():
    """The git root of the working folder, or the working folder when git finds none."""
    try:
        done = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    except OSError:
        return os.getcwd()
    top = done.stdout.strip()
    return top if done.returncode == 0 and top else os.getcwd()


def subject_slug(subject):
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    slug = slug[:_SLUG_LIMIT].strip("-")
    return slug or "subject"


def command_part(command):
    parts = command.split(":")
    return plain_name("-".join(parts[1:]) if len(parts) > 1 else command, "the command part")


def result_name(finished_at, command, subject, run_id=None):
    match = _NAME_TIME.match(finished_at)
    if not match:
        raise ValueError("finished_at is not an ISO time: %r" % finished_at)
    stamp = "%s%s%sT%s%s%sZ" % match.groups()
    base = "%s-%s-%s" % (stamp, command_part(command), subject_slug(subject))
    if run_id is not None:
        base = "%s-%s" % (base, plain_name(run_id, "run_id"))
    return base + ".json"


def main(argv):
    if argv == ["now"]:
        print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        return 0
    is_run_id_check = len(argv) == 2 and argv[0] == "run-id"
    if not is_run_id_check and len(argv) not in (3, 4):
        sys.stderr.write(__doc__)
        return 2
    try:
        value = session_name(argv[1]) if is_run_id_check else result_name(*argv)
    except ValueError as err:
        sys.stderr.write("%s\n" % err)
        return 2
    if is_run_id_check and os.path.lexists(os.path.join(git_root(), ".competitive-intelligence", value)):
        sys.stderr.write(
            "the session folder .competitive-intelligence/%s/ exists: an earlier run used this "
            "run_id, and a run never writes over it\n" % value
        )
        return 3
    print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
