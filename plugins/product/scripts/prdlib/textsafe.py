"""One helper for each text that prints a value that someone else wrote.

A frontmatter value or a value that the caller gives can hold a line break or a
terminal sequence. Printed raw, it splits one finding into 2 lines, or it
moves the cursor. `escape_controls` writes each such character as `\\xNN`, so
that one finding is one line. Issue 1906.
"""
import re

# C0 controls (a line break, ESC), DEL, and C1 controls (0x9b starts a CSI,
# and some terminals read it as ESC [). A space and a printable character are
# not in the pattern. Never cut it to the C0 range: tests/test_control_escape.py
# holds a test for 0x7f and 0x9b.
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def escape_controls(value: object) -> str:
    """The text of `value`, with each control character written as `\\xNN`."""
    return CONTROL_RE.sub(lambda m: f"\\x{ord(m.group()):02x}", str(value))
