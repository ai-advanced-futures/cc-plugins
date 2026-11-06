# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the result file name for one run of an adopting command.

usage: uv run result_name.py <finished_at> <command> <subject> [run_id]
       uv run result_name.py now

The name is the one that result_file_name() of the checker
tests/plugin_result/plugin_result_check.py builds. `now` prints the UTC time to the
second, for a run whose `date` call was denied. Standard library only.
"""
import re
import sys
from datetime import datetime, timezone

_NAME_TIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})")
_SLUG_LIMIT = 40


def subject_slug(subject):
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    slug = slug[:_SLUG_LIMIT].strip("-")
    return slug or "subject"


def command_part(command):
    parts = command.split(":")
    return "-".join(parts[1:]) if len(parts) > 1 else command


def result_name(finished_at, command, subject, run_id=None):
    match = _NAME_TIME.match(finished_at)
    if not match:
        raise ValueError("finished_at is not an ISO time: %r" % finished_at)
    stamp = "%s%s%sT%s%s%sZ" % match.groups()
    base = "%s-%s-%s" % (stamp, command_part(command), subject_slug(subject))
    if run_id:
        base = "%s-%s" % (base, run_id)
    return base + ".json"


def main(argv):
    if argv == ["now"]:
        print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        return 0
    if len(argv) not in (3, 4):
        sys.stderr.write(__doc__)
        return 2
    try:
        print(result_name(*argv))
    except ValueError as err:
        sys.stderr.write("%s\n" % err)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
