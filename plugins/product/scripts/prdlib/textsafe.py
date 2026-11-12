"""One helper for each text that prints a value that someone else wrote.

A frontmatter value or a value that the caller gives can hold a line break or a
terminal sequence. Printed raw, it splits one finding into 2 lines, or it
moves the cursor. `escape_controls` writes each such character as `\\xNN`, so
that one finding is one line. Issue 1906.
"""
import re

# The characters that must not print raw or sit in a single-line field: the C0
# controls (a line break, ESC), DEL, the C1 controls (0x9b starts a CSI, and
# some terminals read it as ESC [), and the 2 Unicode line separators U+2028
# and U+2029. A space and a printable character are not in the pattern. A line
# break in a single-line field is a line of its own in a generated file, and CR
# and NEL make `regen` unstable (issue 1915). Never cut the range to C0:
# tests/test_control_escape.py holds a test for 0x7f and 0x9b.
_CONTROL_CLASS = r"\x00-\x1f\x7f-\x9f"
SINGLE_LINE_BAD_RE = re.compile(f"[{_CONTROL_CLASS}\u2028\u2029]")


def _escape_one(match: "re.Match[str]") -> str:
    code = ord(match.group())
    return f"\\x{code:02x}" if code <= 0xFF else f"\\u{code:04x}"


def escape_controls(value: object) -> str:
    """The text of `value`, with each control character and each Unicode line
    separator written as `\\xNN` (or `\\uNNNN` for U+2028 and U+2029)."""
    return SINGLE_LINE_BAD_RE.sub(_escape_one, str(value))


def first_bad_character(value: str):
    """The first character of `value` that a single-line field must not hold,
    named as `U+XXXX` so that the message holds no control character. None
    when `value` is clean."""
    found = SINGLE_LINE_BAD_RE.search(value)
    return None if found is None else f"U+{ord(found.group()):04X}"


def fold_single_line(value: object) -> str:
    """The text of `value` as one line: each run of whitespace, each control
    character and U+2028 and U+2029 become one space. For text that comes
    from GitHub, which is not ours to refuse."""
    return " ".join(SINGLE_LINE_BAD_RE.sub(" ", str(value)).split())
