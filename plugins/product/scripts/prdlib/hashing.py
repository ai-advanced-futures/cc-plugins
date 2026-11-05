"""The drift hash.

The input is the body only: no frontmatter field, no `# <ID>` heading, and no
generated block. A person can then tune a title or a description for routing
and no roadmap item gets a false flag. The length is 6, as in v3.
"""
import hashlib
import re

GENERATED_BLOCK_RE = re.compile(
    r"<!--\s*(LINKS|STATUS):START.*?-->.*?<!--\s*\1:END\s*-->", re.DOTALL)
HASH_LENGTH = 6


def _is_id_heading(line: str, page_id: str) -> bool:
    """True for `# <ID>` and for `# <ID>: <title>`, and for nothing else.

    The spec removes that one line, so a person can tune a title for routing
    and no roadmap item gets a false flag. Another heading is body text.
    """
    if not line.startswith("# "):
        return False
    rest = line[2:].strip()
    return rest == page_id or rest.startswith(page_id + ":")


def normalize(body: str, page_id: str | None = None) -> str:
    text = GENERATED_BLOCK_RE.sub(" ", body)
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if page_id and lines and _is_id_heading(lines[0], page_id):
        lines.pop(0)
    return re.sub(r"\s+", " ", "\n".join(lines)).strip()


def short_digest(text: str) -> str:
    """The SHA-256 of `text`, cut to HASH_LENGTH. The one place the cut is
    made, so every stored hash of this plugin has the same width."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:HASH_LENGTH]


def body_hash(body: str, page_id: str | None = None) -> str:
    """The first 6 hex characters of the SHA-256 of the normalized body.

    Give the page ID whenever the caller has it, which is every caller that
    reads a page from disk. Without it the ID heading stays in the hash.
    """
    return short_digest(normalize(body, page_id))
