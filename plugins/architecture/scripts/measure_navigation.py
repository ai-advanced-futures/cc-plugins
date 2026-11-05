#!/usr/bin/env python3
"""Measure 10 questions on the navigation fixture at tests/nav.

The script is read-only. It reads the generated index that phase 2 pinned at
tests/nav/expected-index.md, the register of tests/nav/repo and the ADR
bodies. It writes no file.

It counts bytes, not tokens. No tokenizer is installed in this repository, and
a byte count gives the same number on every machine. The output says so.
"""
import argparse
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN_ROOT / "templates" / "verbatim" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import adr_lib  # noqa: E402

DEFAULT_CORPUS = PLUGIN_ROOT / "tests" / "nav"
QUESTIONS = 10
HEAD_LIMIT = 60          # the head_limit that the skill sets on each Grep

# Words that carry no subject. The term selection drops them.
STOP_WORDS = frozenset("""
a all an and are as at be by for from has have how in into is it its new no
not of on one only or per that the this to two use used uses when why with
without
""".split())


def question_terms(adrs, limit=QUESTIONS):
    """One search term for each of the first `limit` ADRs, in file-name
    order. The term is the word of the title that the fewest titles hold. A
    tie goes to the word that comes first in the title. Thus no person writes
    the question set by hand, and the set does not move between runs."""
    frequency = {}
    for adr in adrs:
        for word in set(adr_lib.words(adr.title or adr.filename)):
            frequency[word] = frequency.get(word, 0) + 1
    selected = []
    for adr in adrs[:limit]:
        candidates = [word for word in adr_lib.words(adr.title or adr.filename)
                      if word not in STOP_WORDS and len(word) >= 3]
        if not candidates:
            candidates = adr_lib.words(adr.filename)
        selected.append((adr, min(candidates,
                                  key=lambda w: (frequency.get(w, 0),
                                                 candidates.index(w)))))
    return selected


def load(corpus_dir: Path):
    """The live ADRs in file-name order, then the archived ADRs in file-name
    order. The fixture holds 8 live ADRs, because `register.exclude` keeps one
    file out of the navigation files (U36), and 10 questions need 10 ADRs. The
    skill searches the archive index too (section 12.1, step 2.a.5), so an
    archived ADR is a correct question subject."""
    repo = corpus_dir / "repo"
    corpus = adr_lib.load_corpus(repo_root=repo)
    paths = list(adr_lib.discover(corpus)) + list(adr_lib.discover_archived(corpus))
    adrs = [adr_lib.parse_adr(path, corpus.id_scheme) for path in paths]
    return corpus, adrs


INDEX_LINE_RE = re.compile(
    r"^\* \[(?P<label>.*?)\]\((?P<href>[^)]*)\) - (?P<status>\S+?)\.(?P<text>.*)$")
# An ADR line links to a file. An area summary line links to an anchor of the
# same file, and it carries a count, not a status.
ADR_BULLET_RE = re.compile(r"^\* \[.*?\]\((?!#)")


class Sources:
    """The files that every question Greps, read one time.

    The measurement asks 10 questions of the same few files. Holding the lines
    here, and not the paths, keeps the disk reads at one for each file.
    """

    def __init__(self, corpus, index_path: Path, links_path: Path):
        self.index = Source(index_path, "index.md")
        self.links = Source(links_path, "links.tsv")
        self.register = Source(corpus.register)
        self.adrs = [Source(path) for path in sorted(corpus.dir.glob("*.md"))]


class Source:
    """One file that the questions Grep, read one time.

    The measurement Greps the same few files for each of the 10 questions. It
    holds the lines, not the path, so a question costs no disk read.
    """

    def __init__(self, path: Path, display: str = None):
        self.display = display or path.name
        self.lines = (path.read_text(encoding="utf-8").splitlines()
                      if path.is_file() else [])


def grep(source: Source, pattern):
    """The lines that the Grep tool would return, with its `path:line:`
    prefix, and the byte count of that output. `head_limit` cuts the result,
    as the tool does."""
    hits = [f"{source.display}:{number}:{line}"
            for number, line in enumerate(source.lines, 1)
            if pattern.search(line)]
    hits = hits[:HEAD_LIMIT]
    return hits, sum(len(hit.encode("utf-8")) + 1 for hit in hits)


def decision_bytes(path: Path) -> int:
    """The bytes of the section that step 5 of the skill Reads: the
    `## Decision` section, or the block from the H1 line to the first `## `
    heading when the file has no such heading, with the H1 line limit."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.strip() == adr_lib.DECISION_HEADING), None)
    if start is None:
        start = next((index for index, line in enumerate(lines)
                      if line.startswith("# ")), 0)
    end = next((index for index in range(start + 1, len(lines))
                if lines[index].startswith("## ")), len(lines))
    end = min(end, start + adr_lib.H1_WINDOW)
    return sum(len(line.encode("utf-8")) + 1 for line in lines[start:end])


def title_only(line: str) -> str:
    """The part of an index line that a title-only index would hold: the
    label, the link and the status. The derived text and the tail go."""
    match = INDEX_LINE_RE.match(line)
    if match:
        return f"* [{match['label']}]({match['href']}) - {match['status']}."
    if ADR_BULLET_RE.match(line):
        raise ValueError(
            "adr_index.index_line writes a shape this script cannot read: "
            + line)
    return line


def measure(adr, term, sources):
    """One row. `Index bytes` is the index Grep, the out-edge Grep of
    links.tsv and the Decision section of the ADR. `Register bytes` is the
    register Grep, the `^title:` Grep that step 2b.3 runs when the register
    gives nothing, and the same Decision section. The register path has no
    edge file."""
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    index_hits, index_bytes = grep(sources.index, pattern)
    edge = re.compile(r"^(?:[^\t]*/)?" + re.escape(adr.filename) + r"\t")
    _edge_hits, edge_bytes = grep(sources.links, edge)
    register_hits, register_bytes = grep(sources.register, pattern)
    fallback = 0
    if not register_hits:
        title_pattern = re.compile(r"^title:.*" + re.escape(term), re.IGNORECASE)
        for source in sources.adrs:
            fallback += grep(source, title_pattern)[1]
    body = decision_bytes(adr.path)
    index_files = 1 if index_hits else 0
    register_files = 1 if (register_hits or fallback) else 0
    title_hits = sum(1 for hit in index_hits
                     if pattern.search(title_only(hit.split(":", 2)[2])))
    return [len(index_hits),
            index_bytes + edge_bytes + (body if index_files else 0),
            index_files,
            len(register_hits),
            register_bytes + fallback + (body if register_files else 0),
            register_files,
            title_hits]


def text_summary(index: Source, measured):
    """The cost and the gain of the derived text of section 11.1, against an
    index that shows the status and the title only."""
    lines = index.lines
    with_text = sum(len(line.encode("utf-8")) + 1 for line in lines)
    without = sum(len(title_only(line).encode("utf-8")) + 1 for line in lines)
    hits_with = sum(1 for row in measured if row[0])
    hits_title = sum(1 for row in measured if row[6])
    reached_with = sum(row[0] for row in measured)
    reached_title = sum(row[6] for row in measured)
    return [("index.md bytes", with_text, without),
            ("Questions with an index hit", hits_with, hits_title),
            ("Index lines that the term reaches", reached_with, reached_title)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure 10 questions on the navigation fixture")
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS),
                        help="the directory that holds repo/ and the expected files")
    args = parser.parse_args()
    corpus_dir = Path(args.corpus).resolve()
    corpus, adrs = load(corpus_dir)
    if len(adrs) < QUESTIONS:
        print(f"ERROR: the fixture has {len(adrs)} ADRs; "
              f"{QUESTIONS} questions need {QUESTIONS}", file=sys.stderr)
        return 2

    index_path = corpus_dir / "expected-index.md"
    links_path = corpus_dir / "expected-links.tsv"
    for path in (index_path, links_path):
        if not path.is_file():
            print(f"ERROR: the fixture file does not exist: {path}", file=sys.stderr)
            return 2

    print("Unit: bytes. No tokenizer is installed in this repository, so each")
    print("number is a byte count of the text that the tool returns, with the")
    print("`path:line:` prefixes of the Grep tool.")
    print()
    print("| # | Term | Index hits | Index bytes | Index files | Register hits "
          "| Register bytes | Register files | Title-only hits |")
    print("|---|---|---|---|---|---|---|---|---|")
    sources = Sources(corpus, index_path, links_path)
    measured = []
    for number, (adr, term) in enumerate(question_terms(adrs), 1):
        row = measure(adr, term, sources)
        measured.append(row)
        print(f"| {number} | {term} | " + " | ".join(str(value) for value in row) + " |")
    totals = [sum(column) for column in zip(*measured)]
    print("| **Total** |  | " + " | ".join(str(value) for value in totals) + " |")
    print()
    print("Derived text against title only:")
    print()
    print("| Measure | With derived text | Title only |")
    print("|---|---|---|")
    for name, with_text, without in text_summary(sources.index, measured):
        print(f"| {name} | {with_text} | {without} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
