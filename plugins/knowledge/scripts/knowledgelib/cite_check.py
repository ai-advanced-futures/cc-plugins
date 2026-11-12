"""The rule K-cite: a line citation with no commit, and a PR or issue state with no date or commit (STORY-426).

`issues(text, description)` reads the description and the body of one page and gives a list of
(line, message). A page is read only when its folder is in `cite_folders` of the manifest
(`general_check.check_page` makes that choice).
"""
from __future__ import annotations

import re

COMMIT_RE = re.compile(r"(?<![0-9A-Za-z_-])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![0-9A-Za-z_-])")
DATE_RE = re.compile(r"(?<![\d-])\d{4}-\d{2}-\d{2}(?!\d|-\w)")

# Form 1: a path and a line, path:N or path:N-M (also in backticks).
PATH_RE = re.compile(r"(?<![\w/.@:-])(?!\d{4}-\d{2}-\d{2}T\d{2}:)"
                     r"((?=[\w./-]*[A-Za-z])(?=[\w./-]*[/.-])[\w./-]+):(\d{1,9})(?:-(\d{1,9}))?(?![\w:/.-]*\w)")

# Form 2: prose "line N", "lines N-M", "lines N to M", "lines N and M".
NOT_FILE = r"(?:table|output|stdout|stderr|message|log|reply|answer|summary|list|prompt|diff)"
RANGE = r"(?:\s*(?:-|–|to|and)\s*\d+)?"
LINE_RE = re.compile(r"\b[Ll]ines?\s+(?!\d+" + RANGE + r"\s+(?:of|in)\s+(?:the|a|an|its|this|that|each)\s+"
                     + NOT_FILE + r"\b)(\d+)(?:\s*(?:-|–|to|and)\s*(\d+))?\b(?![.,]\d)")

# Form 3: a backticked :N or :N-M (the file is named earlier in the sentence).
TICK_RE = re.compile(r"`:(\d+)(?:-(\d+))?`")

# Form 4: a state word in the sentence of a PR or issue number.
NUMBER_RE = re.compile(r"(?:\b(?:PRs?|[Ii]ssues?)\s+\(?#?\d+(?:(?:,\s*|,?\s+and\s+)#?\d+)*\b|(?<![\w&/])#\d+\b)")
STATE_RE = re.compile(
    r"(?<![\w-])(?:is|are|was|were|be|been|stays?|stayed|remains?|remained|still|now)\s+(?:still\s+)?(open)(?![\w-])"
    r"|(?<![\w-])(open)\s+(?:PRs?|issues?)(?![\w-])"
    r"|(?:^[\s*_>+-]*|[(,;]\s*)(open)(?![\w-])(?=\s*(?:[,;:)*]|$)|\s+(?:after|at|on|since|then|until|findings?)\b)"
    r"|(?:\b(?:PRs?|[Ii]ssues?)\s+#?\d+|(?<![\w&/])#\d+)\s+(open)(?![\w-])"
    r"(?=\s*(?:[,.;:)]|$|\s+(?:as|at|on|until|since|for)\b))"
    r"|(?<![\w-])(open)\s+(?:(?:low|medium|high|critical|security)\s+)*findings?\b"
    r"|(?:\bPRs?\s+#?\d+|(?<![\w&/])#\d+)\s+\((draft)(?![\w-])"
    r"|(?<![\w-])(draft)\s+PRs?\s+#?\d+"
    r"|(?<![\w-])(not (?:yet )?(?:on|in) `?(?:origin/)?main`?|not merged|not done|no build PR)(?![\w-])",
    re.I)

SPLIT_RE = re.compile(r"(?<=[.!?])[)\]\"'`*_]*\s+(?=[A-Z0-9`\"'(\[*_#])")
LINK_TARGET_RE = re.compile(r"(?<=\]\()[^)]*(?=\))")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^\s*#{1,6}\s")
ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s|^\s*>")
SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
LINKS_START_PREFIX = "<!-- LINKS:START"

LINE_MESSAGE = '"{match}" cites a line, and its sentence has no commit. Cite a name, or add the commit that holds the line.'
STATE_MESSAGE = ('"{word}" next to {numbers} can be stale. Read the state again, then write it with the date '
                 'of the read, for example "was open on 2026-11-12", or with a commit.')


def key_line(text, key) -> int:
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(f"{key}:"):
            return number
    return 1


def body_lines(text):
    """Yield (line number, line) for the body: after the frontmatter, up to the LINKS block, with no fenced code."""
    lines = text.splitlines()
    first = 0
    if lines and lines[0].rstrip() == "---":
        for number, line in enumerate(lines[1:], 1):
            if line.rstrip() == "---":
                first = number + 1
                break
    fenced = False
    for number in range(first, len(lines)):
        line = lines[number]
        if line.startswith(LINKS_START_PREFIX):
            return
        if FENCE_RE.match(line):
            fenced = not fenced
            yield number + 1, None
        elif not fenced:
            yield number + 1, line
        else:
            yield number + 1, None


def blocks(text):
    """Split the body into blocks. A block is a list of (line number, text) parts that join with 1 space."""
    current = []

    def flush():
        nonlocal current
        out, current = current, []
        return [out] if out else []

    for number, line in body_lines(text):
        if line is None or not line.strip():
            yield from flush()
        elif HEADING_RE.match(line):
            yield from flush()
            yield [(number, line.strip())]
        elif line.lstrip().startswith("|"):
            yield from flush()
            for cell in CELL_SPLIT_RE.split(line.strip()):
                cell = cell.strip()
                if cell and not SEPARATOR_CELL_RE.match(cell):
                    yield [(number, cell)]
        elif ITEM_RE.match(line):
            yield from flush()
            current = [(number, line.strip())]
        else:
            current.append((number, line.strip()))
    yield from flush()


def sentences(text):
    """Yield (start offset, sentence) for each sentence of a block text."""
    start = 0
    for match in SPLIT_RE.finditer(text):
        yield start, text[start:match.start()]
        start = match.end()
    yield start, text[start:]


def read_sentence(sentence) -> list[tuple[int, str]]:
    """The warnings of 1 sentence as (offset, message), in the order of the offsets."""
    sentence = LINK_TARGET_RE.sub(lambda match: " " * len(match.group()), sentence)
    found = []
    has_commit = COMMIT_RE.search(sentence) is not None
    if not has_commit:
        for pattern in (PATH_RE, LINE_RE, TICK_RE):
            found += [(m.start(), LINE_MESSAGE.format(match=m.group())) for m in pattern.finditer(sentence)]
    state = STATE_RE.search(sentence)
    if state and state.lastindex and not has_commit and not DATE_RE.search(sentence):
        numbers = []
        for match in NUMBER_RE.finditer(sentence):
            numbers += [f"#{n}" for n in re.findall(r"\d+", match.group()) if f"#{n}" not in numbers]
        if numbers:
            word = state.group(state.lastindex)
            found.append((state.start(state.lastindex), STATE_MESSAGE.format(word=word, numbers=", ".join(numbers))))
    return sorted(found, key=lambda item: item[0])


def issues(text, description=None) -> list[tuple[int, str]]:
    """The K-cite findings of a page: a list of (line, message), in the order of the lines."""
    out = []
    if isinstance(description, str):
        line = key_line(text, "description")
        out += [(line, message) for _, sentence in sentences(description) for _, message in read_sentence(sentence)]
    for block in blocks(text):
        joined, starts = "", []
        for number, part in block:
            joined += (" " if joined else "")
            starts.append((len(joined), number))
            joined += part
        for offset, sentence in sentences(joined):
            for where, message in read_sentence(sentence):
                line = [number for start, number in starts if start <= offset + where][-1]
                out.append((line, message))
    return sorted(out, key=lambda item: item[0])
