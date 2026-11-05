"""The v3 requirement block.

A block is a top-level list item whose first text is bold and starts with an
ID. The block is the bullet line plus its indented lines. An ID in running
text is a mention, not a block. Three real block forms exist, and the parser
reads all three, because a real PRD uses each one.
"""
import re
from dataclasses import dataclass

from . import UsageError
from .hashing import short_digest

# One or more groups of capital letters and digits, then a number.
ID_RE = re.compile(r"^([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*)-(\d+)$")
# A top-level bullet whose first text is bold. `sep` is the one `:`, `—`, or
# `·` that can follow the bold span.
BULLET_RE = re.compile(r"^- \*\*(?P<bold>.+?)\*\*(?P<sep>\s*[:—·])?(?P<gap>\s*)")
HEADING_RE = re.compile(r"^#{2,}\s+(?P<title>.+?)\s*$")
BOLD_SPLIT_RE = re.compile(r"\s*[—·:]\s*")
SENTENCE_RE = re.compile(r"^(.+?[.!?])(\s|$)")
TITLE_LIMIT = 60

# The closed list of recipe names. `--hash-recipe` accepts these three.
RECIPES = ("v3", "full", "no-bullet")


@dataclass(frozen=True)
class Block:
    id: str
    prefix: str
    number: int
    title: str
    text: str     # the block as it stands in the file
    marker: str   # the exact text the `v3` hash recipe removes
    line: int     # the 1-based line of the bullet
    section: str  # the heading above the block, or ""


def first_sentence(text: str) -> str:
    """The first sentence of the text, or the whole text when it holds no
    sentence end."""
    match = SENTENCE_RE.match(text.strip())
    return match.group(1) if match else text.strip()


def short_title(text: str) -> str:
    """The title rule: the first sentence, without its final dot, cut at the
    title limit. The migration states this rule one time, so a change to the
    limit has one home."""
    sentence = first_sentence(text).rstrip(".")
    return sentence if len(sentence) <= TITLE_LIMIT \
        else sentence[:TITLE_LIMIT].rstrip()


def _title_from(bold: str, rest: str) -> str:
    """The bold span can hold the ID alone, or the ID and a title. With a
    title, that title is the page title. Without one, the title is the first
    sentence of the text, cut at 60 characters."""
    parts = BOLD_SPLIT_RE.split(bold, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip().rstrip(".")
    return short_title(rest)


def _extent(lines: list[str], start: int) -> int:
    """The index after the last line of the block: the bullet line plus its
    indented lines. A blank line inside the block is part of it when an
    indented line follows."""
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.startswith((" ", "\t")):
            end += 1
            continue
        if not line.strip():
            following = end + 1
            if following < len(lines) and lines[following].startswith((" ", "\t")):
                end += 1
                continue
        break
    return end


def parse_blocks(text: str) -> list[Block]:
    """Each requirement block of a v3 PRD, in document order."""
    lines = text.split("\n")
    section, out, index = "", [], 0
    while index < len(lines):
        line = lines[index]
        heading = HEADING_RE.match(line)
        if heading:
            section = heading.group("title")
            index += 1
            continue
        match = BULLET_RE.match(line)
        if not match:
            index += 1
            continue
        bold = match.group("bold").strip()
        identifier = BOLD_SPLIT_RE.split(bold, maxsplit=1)[0].strip()
        found = ID_RE.match(identifier)
        if not found:
            index += 1
            continue
        end = _extent(lines, index)
        rest = line[match.end():]
        out.append(Block(
            id=identifier,
            prefix=found.group(1),
            number=int(found.group(2)),
            title=_title_from(bold, rest),
            text="\n".join(lines[index:end]).rstrip(),
            marker=line[:match.end()],
            line=index + 1,
            section=section,
        ))
        index = end
    return out


def recipe_text(block: Block, recipe: str) -> str:
    """The text that one recipe hashes.

    `v3`: the block without its marker. The marker is the `- ` list marker,
    the full bold span, and one `:`, `—`, or `·` after it, with the spaces
    around them. `full`: the whole block. `no-bullet`: the block without the
    `- ` list marker only. Each recipe then replaces each run of whitespace
    with one space and trims.
    """
    if recipe == "v3":
        text = block.text[len(block.marker):] \
            if block.text.startswith(block.marker) else block.text
    elif recipe == "full":
        text = block.text
    elif recipe == "no-bullet":
        text = block.text[2:] if block.text.startswith("- ") else block.text
    else:
        raise UsageError(
            f"{recipe} is not a hash recipe. Use one of: {', '.join(RECIPES)}.")
    return re.sub(r"\s+", " ", text).strip()


def recipe_hash(block: Block, recipe: str) -> str:
    """The hash of one block with one recipe, in HASH_LENGTH hex characters."""
    return short_digest(recipe_text(block, recipe))


def best_recipe(blocks: list[Block], stored: dict[str, str]) -> tuple[str, dict]:
    """(the recipe that gives the most stored hashes again, the count of each).

    `stored` maps a v3 requirement ID to the hash that a roadmap trace holds.
    Real roadmaps did not all hash the same text, so the script votes instead
    of assuming. A tie takes the first name of RECIPES, so two runs over one
    repository give one answer.
    """
    by_id = {block.id: block for block in blocks}
    counts = {}
    for recipe in RECIPES:
        counts[recipe] = sum(
            1 for identifier, value in stored.items()
            if identifier in by_id and recipe_hash(by_id[identifier], recipe) == value)
    best = max(RECIPES, key=lambda name: (counts[name], -RECIPES.index(name)))
    return best, counts
