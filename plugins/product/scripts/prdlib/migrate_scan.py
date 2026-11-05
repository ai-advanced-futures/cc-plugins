"""`migrate --scan`: read the two v3 files and report. It writes nothing.

The report tells the user what the migration will do and what stops it. The
exit code is the verdict: 0 only when a migration with no map is possible.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import UsageError
from .migrate_blocks import RECIPES, best_recipe, parse_blocks, recipe_hash
from .migrate_map import type_of
from .migrate_roadmap import (ACCEPTANCE_RE, CHECKBOX_RE, DEPS_RE,
                              MILESTONE_RE, SIZE_RE, TABLE_END, TABLE_START,
                              TARGET_RE, TRACE_RE, parse_roadmap)
from .tree import V3_PRD, V3_ROADMAP, product_dir

HEADING_RE = re.compile(r"^(?P<hashes>#+)\s+(?P<title>.+?)\s*$")
# The v3 lens catalog. Each lens owns one section heading, so the scan counts
# the lens headings of a PRD and the migration reads their text.
LENS_HEADINGS = (
    "Problem", "Personas", "Journeys", "Capabilities", "Scope",
    "Success Metrics", "Business Model", "Go-to-Market",
    "Risks & Assumptions",
)
# The v3 fixed sections. The migration reads these too: the constraints are
# blocks, and step 5 makes a page of each Decisions Log row and each Open
# Questions bullet.
FIXED_SECTIONS = ("Product Constraints", "Decisions Log", "Open Questions")
LENS_SECTIONS = {name.casefold() for name in LENS_HEADINGS}
# The text under the level-1 heading, above the first `## ` heading.
# migrate_build._product_parts carries it into product.md as the summary, so
# the scan counts it as read text and not as archive-only text. The name
# cannot collide with a heading title, because a title holds no NUL.
SUMMARY_SECTION = "\x00summary"
READ_SECTIONS = {name.casefold() for name in LENS_HEADINGS + FIXED_SECTIONS}
READ_SECTIONS.add(SUMMARY_SECTION)
# The checker warns at this size, and step 2 of the migration proposes a
# division. The scan names each block that reaches it.
LONG_BLOCK_WORDS = 600


# The kind of stop that `--accept-unmarked-drift` waives. Every other kind
# is a hard stop. The writer and hard_stops() both name this constant, so a
# reworded report line cannot silently make a waivable stop a hard one.
UNMARKED = "unmarked"


@dataclass
class Stop:
    """One finding that stops the migration. `kind` is for the code and
    `text` is for the person, so neither has to be read out of the other."""
    kind: str
    text: str


@dataclass
class ScanReport:
    lines: list = field(default_factory=list)   # the printed report, in order
    stops: list = field(default_factory=list)   # each Stop, in order
    unknown: list = field(default_factory=list)  # each prefix with no type
    recipe: str = ""                            # the recipe of the vote, or ""

    def exit_code(self) -> int:
        """0 only when a migration with no map is possible."""
        return 1 if self.stops or self.unknown else 0

    def stop_lines(self) -> list:
        return [stop.text for stop in self.stops]

    def hard_stops(self) -> list:
        """The stops that no option waives: a duplicate ID and a trace target
        that no block holds. `--accept-unmarked-drift` waives the unmarked
        differences, and nothing else."""
        return [stop for stop in self.stops if stop.kind != UNMARKED]

    def verdict(self) -> str:
        if self.stops:
            return "RESULT: the migration cannot run"
        if self.unknown:
            return "RESULT: a map is necessary"
        return "RESULT: the migration can run"


def _read_v3(root: Path) -> tuple[str, str | None]:
    """The text of prd.md, and of roadmap.md when that file exists."""
    prd = product_dir(root) / V3_PRD
    if not prd.is_file():
        raise UsageError(f"docs/product/{V3_PRD} does not exist. There is "
                         f"nothing to scan.")
    roadmap = product_dir(root) / V3_ROADMAP
    return (prd.read_text(encoding="utf-8"),
            roadmap.read_text(encoding="utf-8") if roadmap.is_file() else None)


def _frontmatter_end(text: str) -> int:
    """The index after the last line of the frontmatter, or 0 when the file
    has none."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


def _lens_headings(text: str) -> int:
    """The number of `## <Lens>` headings of the v3 lens catalog. A PRD that
    keeps its own sections has 0, and no lens text goes to product.md."""
    found = 0
    for line in text.split("\n")[_frontmatter_end(text):]:
        heading = HEADING_RE.match(line)
        if heading and len(heading.group("hashes")) >= 2 \
                and heading.group("title").casefold() in LENS_SECTIONS:
            found += 1
    return found


def _block_lines(blocks: list) -> set:
    """The 1-based line of each line that a requirement block holds."""
    held = set()
    for block in blocks:
        for offset in range(len(block.text.split("\n"))):
            held.add(block.line + offset)
    return held


def _archive_prd_lines(text: str, blocks: list) -> int:
    """The lines of prd.md that stay in the archive only (D33).

    A line is read when it is frontmatter, a heading, part of a requirement
    block, part of the summary under the level-1 heading, or part of a lens
    section or a fixed section. Every other line that holds text goes to the
    archive. A blank line counts for nothing.
    """
    held = _block_lines(blocks)
    lines = text.split("\n")
    start = _frontmatter_end(text)
    section, archive = "", 0
    for index in range(start, len(lines)):
        line = lines[index]
        heading = HEADING_RE.match(line)
        if heading:
            section = SUMMARY_SECTION \
                if len(heading.group("hashes")) == 1 \
                else heading.group("title").casefold()
            continue
        if not line.strip() or (index + 1) in held:
            continue
        if section not in READ_SECTIONS:
            archive += 1
    return archive


def _archive_roadmap_lines(text: str) -> int:
    """The lines of roadmap.md that stay in the archive only (D33).

    A line is read when it is in the status table, or it is a milestone
    heading, a checkbox, an Acceptance Criteria line, or a Trace, Deps, Size,
    or Target detail. Every other line that holds text goes to the archive. A
    blank line counts for nothing.
    """
    details = (MILESTONE_RE, CHECKBOX_RE, ACCEPTANCE_RE, TRACE_RE, DEPS_RE,
               SIZE_RE, TARGET_RE)
    archive, in_table = 0, False
    for line in text.split("\n"):
        if TABLE_START in line:
            in_table = True
            continue
        if TABLE_END in line:
            in_table = False
            continue
        if in_table or not line.strip():
            continue
        if any(pattern.match(line) for pattern in details):
            continue
        archive += 1
    return archive


def _prefix_lines(blocks: list, mapping: dict | None) -> tuple[list, list]:
    """One line for each prefix, in document order, and each unknown prefix."""
    order, first = [], {}
    for block in blocks:
        if block.prefix not in first:
            order.append(block.prefix)
            first[block.prefix] = [block, 0]
        first[block.prefix][1] += 1
    lines, unknown = [], []
    for prefix in order:
        block, count = first[prefix]
        kind = type_of(block, mapping)
        if kind is None:
            unknown.append(prefix)
        noun = "block" if count == 1 else "blocks"
        lines.append(f"prefix {prefix}: {count} {noun}, "
                     f"type {kind or 'unknown'}")
    return lines, unknown


def _duplicate_lines(blocks: list) -> list:
    """One line for each ID that two blocks or more hold, in document order."""
    where, order = {}, []
    for block in blocks:
        if block.id not in where:
            where[block.id] = []
            order.append(block.id)
        where[block.id].append(block.line)
    return [f"duplicate ID: {name} "
            f"(lines {', '.join(str(n) for n in where[name])})"
            for name in order if len(where[name]) > 1]


def scan(root: Path, mapping: dict | None = None,
         recipe: str | None = None) -> ScanReport:
    """Read the two v3 files and build the report. It writes nothing."""
    prd_text, roadmap_text = _read_v3(root)
    blocks = parse_blocks(prd_text)
    by_id = {block.id: block for block in blocks}
    items = parse_roadmap(roadmap_text) if roadmap_text is not None else []
    report = ScanReport()
    lines, stops = report.lines, report.stops

    lines.append(f"files: {V3_PRD} yes, {V3_ROADMAP} "
                 f"{'yes' if roadmap_text is not None else 'no'}")
    lines.append(f"frontmatter: {'yes' if _frontmatter_end(prd_text) else 'no'}")
    lines.append(f"lens headings: {_lens_headings(prd_text)}")

    prefix_lines, report.unknown = _prefix_lines(blocks, mapping)
    lines.extend(prefix_lines)

    for line in _duplicate_lines(blocks):
        lines.append(line)
        stops.append(Stop("duplicate", line))

    # A trace that names an ID no block holds stops the migration: the user
    # corrects the v3 file and commits it. The script does not invent a page.
    seen = set()
    for item in items:
        for name, _digest in item.traces:
            if name in by_id or (item.id, name) in seen:
                continue
            seen.add((item.id, name))
            line = f"trace target with no block: {name} ({item.id})"
            lines.append(line)
            stops.append(Stop("trace-target", line))

    # The vote runs over the traces that name a block, which is the rule of
    # best_recipe. A target with no block is a stop of its own, so it does not
    # make each recipe look worse than it is.
    stored = {name: digest for item in items for name, digest in item.traces
              if name in by_id}
    chosen = recipe or ""
    if stored:
        best, counts = best_recipe(blocks, stored)
        for name in RECIPES:
            lines.append(f"hash recipe {name}: {counts[name]} of {len(stored)}")
        chosen = recipe or best
        lines.append(f"hash recipe chosen: {chosen}")
    report.recipe = chosen

    if roadmap_text is not None:
        has_table = TABLE_START in roadmap_text and TABLE_END in roadmap_text
        if not has_table:
            # No table means no mark information, not a difference on each
            # trace. The scan says so and stops nothing.
            lines.append("no status table: the marks are unknown")
        elif chosen:
            for item in items:
                for name, digest in item.traces:
                    if name not in by_id or name in item.marked:
                        continue
                    if recipe_hash(by_id[name], chosen) == digest:
                        continue
                    line = f"unmarked difference: {item.id} -> {name}"
                    lines.append(line)
                    stops.append(Stop(UNMARKED, line))

    lines.append(
        f"archive-only lines: {V3_PRD} "
        f"{_archive_prd_lines(prd_text, blocks)}, {V3_ROADMAP} "
        f"{_archive_roadmap_lines(roadmap_text) if roadmap_text else 0}")

    for block in blocks:
        words = len(block.text.split())
        if words >= LONG_BLOCK_WORDS:
            lines.append(f"long block: {block.id} ({words} words)")
    return report
