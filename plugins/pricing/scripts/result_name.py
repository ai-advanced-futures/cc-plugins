# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the result file name for one run of an adopting command.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py <finished_at> <command> <subject> [run_id]
       uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now
       uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py run-id <value>

The name is the one that result_file_name() of the checker
tests/support/schemas/plugin-result/plugin_result_check.py builds. `now` prints the UTC time to the
second, for a run whose `date` call was denied. `run-id` prints the value when it is a
run id of the result-file standard, and exits 2 when it is not. The run_id and the command
part go into the file name. The run_id must be a run id of the standard: the `_RUN_ID`
pattern of the checker, 4 to 64 of a-z, 0-9 and '-', with a-z or 0-9 first and last. The
command part must be a plain name: 1 to 64 of A-Z, a-z, 0-9, '.', '_', '-', and not '.' or
'..'. Standard library only.
"""
import re
import sys
from datetime import datetime, timezone

_NAME_TIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})")
_SLUG_LIMIT = 40
_PLAIN = re.compile(r"[A-Za-z0-9._-]{1,64}")
# The same pattern as `_RUN_ID` of the checker tests/support/schemas/plugin-result/plugin_result_check.py. A test compares the 2.
_RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,62}[a-z0-9]\Z")


def plain_name(value, what):
    """Return value when it is a plain name. fullmatch refuses a final new line, which $ would let through."""
    if not _PLAIN.fullmatch(value) or value in (".", ".."):
        raise ValueError(
            "%s is not a plain name (1 to 64 of A-Z, a-z, 0-9, '.', '_', '-'; not '.' or '..'): %r"
            % (what, value)
        )
    return value


def run_id_name(value):
    """Return value when it is a run id of the result-file standard. match with \\Z, as the checker does."""
    if not _RUN_ID.match(value):
        raise ValueError(
            "run_id is not a run id of the result-file standard (4 to 64 of a-z, 0-9, '-'; "
            "a-z or 0-9 first and last): %r" % (value,)
        )
    return value


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
        base = "%s-%s" % (base, run_id_name(run_id))
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
        print(run_id_name(argv[1]) if is_run_id_check else result_name(*argv))
    except ValueError as err:
        sys.stderr.write("%s\n" % err)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
