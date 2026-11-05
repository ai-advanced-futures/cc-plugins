"""The migration builds the whole tree in a temporary directory.

Nothing in docs/product/ changes until the assertions pass. A failed run
deletes the temporary tree, so the repository keeps its v3 files.
"""
import re
import shutil
import tempfile
from pathlib import Path

import yaml

from . import DataError, UsageError, git
from .logbook import init_log
from .migrate_blocks import (first_sentence, parse_blocks, recipe_hash,
                             recipe_text, short_title)
from .migrate_map import FIXED_PREFIXES, types_for
from .migrate_roadmap import NO_DEPS, parse_roadmap
from .migrate_scan import (HEADING_RE, LENS_HEADINGS, LENS_SECTIONS,
                           _block_lines)
from .page import (Page, load_page, normalise, safe_dump, safe_load,
                   split_frontmatter, write_page)
from .registry import BY_PREFIX, TYPES
from .tree import (BUNDLES, PRODUCT_DIR, RESERVED_PAGES, V3_PRD, V3_ROADMAP,
                   iter_pages, product_dir)

# A level-1 heading. A PRD with no frontmatter takes its title from the first
# one.
TITLE_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
# A top-level bullet of the Open Questions list.
QUESTION_RE = re.compile(r"^-\s+(?P<text>.+?)\s*$")
# The line that product.md holds so a reader finds the text of D33.
ARCHIVE_LINE = "The v3 file is in [the archive](../archive/prd-v3.md)."
# The same line for PROJECT-01.md, which is one directory deeper.
ROADMAP_ARCHIVE_LINE = \
    "The v3 file is in [the archive](../../archive/roadmap-v3.md)."
# A milestone keeps its number, so `M0` gives `MILESTONE-00`.
MILESTONE_NUMBER_RE = re.compile(r"^M(?P<number>\d+)$")
# `target_date` takes the `- **Target**: <date>` line only when the line
# holds a full date. `- **Target**: TBD` leaves the field absent, and warning
# W3 reports it. [inferred]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# The description line of a v3 feature or story. Absent, the title is the
# description, because every page declares one. [inferred]
DESCRIPTION_RE = re.compile(
    r"^\s*-\s*\*\*Description\*\*:\s*(?P<text>.+?)\s*$", re.MULTILINE)
DECISIONS_SECTION = "Decisions Log"
QUESTIONS_SECTION = "Open Questions"
# The column order of the v3 Decisions Log table.
DECISION_COLUMNS = ("Decision", "Rationale", "Alternatives", "Date")
# An alternatives cell that holds one of these names no alternative.
ALTERNATIVE_SEPARATOR = ";"
# The one command that undoes the whole migration, before the commit. The
# move writes new directories and stages one rename, so the undo needs both
# halves: restore takes the staged rename back, clean removes the new tree.
ROLLBACK = ("git restore --staged --worktree docs/product && "
            "git clean -fd docs/product")
# The two names the v3 files take in the archive.
ARCHIVE_NAMES = ((V3_PRD, "prd-v3.md"), (V3_ROADMAP, "roadmap-v3.md"))
# The three directories the run moves from the temporary tree.
MOVED = ("prd", "roadmap", "archive")


def _lens_key(heading: str) -> str:
    """The frontmatter key of one v3 lens heading. `Success Metrics` gives
    `success-metrics`, as the v3 files write it."""
    return re.sub(r"-+", "-",
                  re.sub(r"[^a-z0-9]+", "-", heading.casefold())).strip("-")


# [inferred] The spec names the `lenses` map but no list of keys. These are
# the lens headings of the v3 catalog, in the order of that catalog.
LENS_KEYS = tuple(_lens_key(name) for name in LENS_HEADINGS)


def assign_ids(blocks, types: dict) -> dict:
    """old ID -> new ID.

    An ID with a v3 lens prefix keeps its number: `CAP-3` becomes
    `CAPABILITY-03`, which a reader of the old roadmap still knows. Each ID
    that the map typed gets the next free number of its type, in document
    order, because a `REQ-DP` number has no meaning in the new type.
    """
    out, taken = {}, {}
    for block in blocks:
        if block.prefix in FIXED_PREFIXES:
            type_name = types[block.id]
            out[block.id] = f"{TYPES[type_name].prefix}-{block.number:02d}"
            taken.setdefault(type_name, set()).add(block.number)
    for block in blocks:
        if block.id in out:
            continue
        type_name = types[block.id]
        used = taken.setdefault(type_name, set())
        number = 1
        while number in used:
            number += 1
        used.add(number)
        out[block.id] = f"{TYPES[type_name].prefix}-{number:02d}"
    return out


def _frontmatter(text: str) -> tuple[dict | None, int]:
    """(the v3 frontmatter mapping or None, the index of the first body line)."""
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return None, 0
    try:
        data = safe_load(fm_text)
    except yaml.YAMLError as error:
        raise UsageError(f"docs/product/{V3_PRD}: the frontmatter does not "
                         f"parse: {error}")
    start = text[:len(text) - len(body)].count("\n")
    return (data if isinstance(data, dict) else {}), start


def _trim(lines: list) -> str:
    """The lines as one paragraph block, with no blank line at either end."""
    return "\n".join(lines).strip("\n")


def _section(lines: list, start: int, title: str) -> list:
    """The lines under the `## <title>` heading, to the next heading."""
    out, inside = [], False
    for index in range(start, len(lines)):
        heading = HEADING_RE.match(lines[index])
        if heading:
            inside = heading.group("title").strip().casefold() == title.casefold()
            continue
        if inside:
            out.append(lines[index])
    return out


def _product_parts(text: str, blocks, start: int) -> tuple[str, list]:
    """(the product summary, one (heading, text) pair for each lens section).

    The summary is the text under the level-1 heading and above the first
    `## ` heading. A lens section gives the text that is not a requirement
    block. Every other line stays in the archive only (D33).
    """
    held = _block_lines(blocks)
    lines = text.split("\n")
    summary, sections, target = [], [], None
    for index in range(start, len(lines)):
        heading = HEADING_RE.match(lines[index])
        if heading:
            name = heading.group("title").strip()
            if len(heading.group("hashes")) == 1:
                target = summary
            elif name.casefold() in LENS_SECTIONS:
                target = []
                sections.append((name, target))
            else:
                target = None
            continue
        if target is None or (index + 1) in held:
            continue
        target.append(lines[index])
    return _trim(summary), [(name, _trim(body)) for name, body in sections]


def _created(root) -> str | None:
    """The date of the commit that added the v3 PRD, or None.

    An empty answer, a missing `git`, and a directory that is not a git
    repository all give None, and product.md then has no `created` field.
    """
    found = git.output(root, "log", "--diff-filter=A", "--format=%cs", "--",
                       f"{PRODUCT_DIR}/{V3_PRD}")
    if found is None:
        return None
    dates = [line.strip() for line in found.split("\n") if line.strip()]
    # `git log` prints the newest commit first, so the commit that added the
    # file is the last line.
    return dates[-1] if dates else None


def _product_page(tree, root, text: str, blocks) -> Page:
    """product.md, from the v3 frontmatter when the file has one."""
    frontmatter, start = _frontmatter(text)
    lines = text.split("\n")
    heading = ""
    for index in range(start, len(lines)):
        found = TITLE_RE.match(lines[index])
        if found:
            heading = found.group("title")
            break
    if frontmatter is None:
        # No frontmatter means no coverage data. Each lens is not started,
        # and the description is empty until step 3 of the skill writes one.
        # Warning W6 reports the empty description meanwhile.
        fields = {
            "type": "Product", "title": heading, "description": "",
            "status": "draft",
            "lenses": {key: {"status": "not-started"} for key in LENS_KEYS},
        }
        created = _created(root)
        if created:
            fields["created"] = created
    else:
        fields = {
            "type": "Product",
            "title": str(frontmatter.get("product") or heading),
            "description": str(frontmatter.get("description") or ""),
            "status": "draft",
        }
        for key in ("created", "updated"):
            # The v3 file holds both dates. Dropping them loses user data,
            # and Product declares both fields. [inferred]
            if frontmatter.get(key):
                fields[key] = str(frontmatter[key])
        if frontmatter.get("lenses"):
            # YAML reads an unquoted `updated: 2026-09-01` as a date object.
            # Every field of this schema is a string, so the coverage map
            # goes through the one reader that gives the ISO form back.
            fields["lenses"] = normalise(frontmatter["lenses"])
    summary, sections = _product_parts(text, blocks, start)
    chunks = [f"# {fields['title']}"]
    if summary:
        chunks.append(summary)
    for name, body in sections:
        if body:
            chunks.extend([f"## {name}", body])
    chunks.append(ARCHIVE_LINE)
    return Page(path=tree / "prd" / "product.md", frontmatter=fields,
                body="\n\n".join(chunks) + "\n")


def _block_page(tree, block, type_name: str, new_id: str) -> Page:
    """One requirement block as one page.

    The description is the first sentence of the `v3` recipe text, which is
    the block without its list marker and its bold ID span, so the
    description opens with the prose and not with `- **CAP-3**:`. [inferred]
    The body holds the block as it stands: the script does not divide a block
    and does not restyle it. Step 3 of the skill does that.
    """
    spec = TYPES[type_name]
    return Page(
        path=tree / spec.bundle / spec.directory / f"{new_id}.md",
        frontmatter={"type": type_name, "title": block.title,
                     "description": first_sentence(recipe_text(block, "v3")),
                     "status": "draft", "aliases": [block.id]},
        body=f"\n# {new_id}: {block.title}\n\n{block.text}\n",
    )


def _table_rows(lines: list) -> list:
    """Each row of data of one markdown table, as a list of cells.

    A markdown table holds a header row and a `|---|` row before its first
    row of data, so the reader starts after the `|---|` row.
    """
    rows, started = [], False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not started:
            if cells and all(cell and set(cell) <= set("-: ") for cell in cells):
                started = True
            continue
        rows.append(cells)
    return rows


def _decision_pages(tree, lines: list, start: int) -> list:
    """One page for each row of the Decisions Log, from DECISION-01."""
    pages = []
    for number, cells in enumerate(
            _table_rows(_section(lines, start, DECISIONS_SECTION)), start=1):
        cells = cells + [""] * (len(DECISION_COLUMNS) - len(cells))
        title, rationale, alternatives, date = cells[:4]
        if not title:
            continue
        fields = {"type": "Decision", "title": short_title(title),
                  "description": rationale or title,
                  # The row records a decision that the product took, so the
                  # page is stable and not draft. [inferred]
                  "status": "stable"}
        if alternatives.casefold() not in NO_DEPS:
            fields["alternatives"] = [
                part.strip() for part in
                alternatives.split(ALTERNATIVE_SEPARATOR) if part.strip()]
        if date:
            # An empty date leaves the field absent, and the checker reports
            # it. The script does not invent a date. [inferred]
            fields["decided_at"] = date
        identifier = f"DECISION-{number:02d}"
        pages.append(Page(
            path=tree / "prd" / "decisions" / f"{identifier}.md",
            frontmatter=fields,
            body=f"\n# {identifier}: {fields['title']}\n\n"
                 f"{rationale or title}\n"))
    return pages


def _question_pages(tree, lines: list, start: int) -> list:
    """One page for each bullet of Open Questions, from QUESTION-01."""
    section = _section(lines, start, QUESTIONS_SECTION)
    bullets = []
    for line in section:
        match = QUESTION_RE.match(line)
        if match:
            bullets.append([match.group("text")])
        elif bullets and line.startswith((" ", "\t")) and line.strip():
            bullets[-1].append(line.strip())
    pages = []
    for number, parts in enumerate(bullets, start=1):
        text = " ".join(parts)
        identifier = f"QUESTION-{number:02d}"
        pages.append(Page(
            path=tree / "prd" / "questions" / f"{identifier}.md",
            frontmatter={"type": "Question", "title": short_title(text),
                         "description": text,
                         # draft means open. The skill answers it later.
                         "status": "draft"},
            body=f"\n# {identifier}: {short_title(text)}\n\n{text}\n"))
    return pages


def build_prd(tree, root, text: str, blocks, types: dict, ids: dict) -> list:
    """Write the PRD bundle of the temporary tree. Returns the paths written.

    `root` is the repository that holds the v3 file. The `created` date of a
    PRD with no frontmatter comes from the git history of that repository, so
    the caller gives it instead of the script reading the directory the
    process happens to sit in. [inferred]

    The script never guesses `kind`, `role`, or a relationship. Text that is
    not a block, a lens section, or one of the two lists stays in the archive
    only (D33).
    """
    lines = text.split("\n")
    _, start = _frontmatter(text)
    pages = [_product_page(tree, root, text, blocks)]
    for block in blocks:
        pages.append(_block_page(tree, block, types[block.id], ids[block.id]))
    pages.extend(_decision_pages(tree, lines, start))
    pages.extend(_question_pages(tree, lines, start))
    for page in pages:
        write_page(page)
    # OKF reserves log.md in every bundle, as `init` writes it in both. Without
    # it the PRD bundle has no Event log between step 2 and step 4, and a skill
    # that appends a Save line there writes into a file that does not exist.
    init_log(tree / "prd" / "log.md")
    return [page.path for page in pages]


def _roadmap_path(new_id: str) -> str:
    """The bundle-relative path of one roadmap page, as a relationship
    field holds it: `/features/FEATURE-01.md`."""
    return f"/{BY_PREFIX[new_id.split('-')[0]].directory}/{new_id}.md"


def _roadmap_ids(items) -> dict:
    """v3 ID -> new ID.

    A milestone keeps its number, as `CAP-3` keeps its number in the PRD:
    `M1` gives `MILESTONE-01`. A feature and a story take a flat number in
    document order, because a v3 `F1.2` number holds the milestone of the
    feature and the new ID does not.
    """
    out, counts = {}, {"feature": 0, "story": 0}
    for item in items:
        if item.kind == "milestone":
            found = MILESTONE_NUMBER_RE.match(item.id)
            if found is None:
                # The parser reads a `### M<n>` heading only, so this is a
                # guard and not a path a v3 file reaches. It raises, because
                # a milestone that the map drops is a lost page.
                raise UsageError(f"{item.id} is not a milestone number of "
                                 f"the form M<n>.")
            out[item.id] = f"MILESTONE-{int(found.group('number')):02d}"
            continue
        counts[item.kind] += 1
        prefix = TYPES[item.kind.capitalize()].prefix
        out[item.id] = f"{prefix}-{counts[item.kind]:02d}"
    return out


def _milestone_of(items) -> dict:
    """v3 ID -> the v3 ID of the milestone above it, or None.

    A story names its feature, and the feature names the milestone, so the
    story takes the milestone of its feature.
    """
    out = {}
    for item in items:
        if item.kind == "milestone":
            out[item.id] = item.id
        elif item.kind == "feature":
            out[item.id] = item.parent
        else:
            out[item.id] = out.get(item.parent)
    return out


def _item_description(item) -> str:
    """The `- **Description**:` line of the item, or its title."""
    found = DESCRIPTION_RE.search(item.body)
    return found.group("text") if found else item.title


def _item_traces(item, ids: dict) -> list:
    """Each `**Trace**:` entry of the item, through the ID map.

    The stored v3 hash stays: `migrate --finish` writes the new one, because
    step 3 of the skill changes page bodies and an earlier hash would be
    false. A trace that names an ID no block holds raises: `migrate --scan`
    reports that case as a stop, and the script does not invent a page.
    """
    out = []
    for name, digest in item.traces:
        if name not in ids:
            raise UsageError(
                f"{item.id} traces {name}, which {PRODUCT_DIR}/{V3_PRD} has "
                f"no block for. Run `migrate --scan` and correct the v3 "
                f"files.")
        new_id = ids[name]
        directory = BY_PREFIX[new_id.split("-")[0]].directory
        out.append({"to": f"prd:/{directory}/{new_id}.md", "hash": digest})
    return out


def _dependencies(item, roadmap_ids: dict) -> tuple[list, list]:
    """(the blocked_by paths, the body sentences) of one item.

    A milestone has no `blocked_by` field, so each dependency of a milestone
    becomes one sentence in its body. A dependency that names no item of the
    v3 roadmap becomes one sentence too: the script does not invent a page,
    and a sentence keeps the text that the user wrote. [inferred]
    """
    paths, sentences = [], []
    for name in item.deps:
        new_id = roadmap_ids.get(name)
        if new_id is None:
            sentences.append(f"This {item.kind} depends on {name}. The v3 "
                             f"roadmap holds no item of that name.")
        elif item.kind == "milestone":
            sentences.append(f"This milestone depends on {new_id}.")
        else:
            paths.append(_roadmap_path(new_id))
    return paths, sentences


def _body(new_id: str, title: str, chunks: list) -> str:
    """The page body: the ID heading, then each chunk that holds text."""
    parts = [f"# {new_id}: {title}"] + [c for c in chunks if c]
    return "\n" + "\n\n".join(parts) + "\n"


def _chunks(fields: dict, sentences: list) -> list:
    """The body chunks of one roadmap page: the description, then each
    dependency sentence. A description that is the title says nothing more
    than the heading, so the body does not repeat it. [inferred]"""
    description = fields["description"]
    if description == fields["title"]:
        return sentences
    return [description] + sentences


def _item_page(tree, item, new_id: str, fields: dict, chunks: list) -> Page:
    spec = TYPES[item.kind.capitalize()]
    return Page(path=tree / spec.bundle / spec.directory / f"{new_id}.md",
                frontmatter=fields, body=_body(new_id, item.title, chunks))


def _milestone_page(tree, item, new_id, ids, roadmap_ids) -> Page:
    """One `### M<n>` as one Milestone page. A milestone has no state: the
    `Not Planned` value of the table is a milestone with no items."""
    fields = {"type": "Milestone", "title": item.title,
              "description": _item_description(item), "status": "draft",
              "aliases": [item.id]}
    if item.target_date and DATE_RE.match(item.target_date):
        fields["target_date"] = item.target_date
    traces = _item_traces(item, ids)
    if traces:
        fields["traces"] = traces
    _, sentences = _dependencies(item, roadmap_ids)
    return _item_page(tree, item, new_id, fields, _chunks(fields, sentences))


def _work_page(tree, item, new_id, ids, roadmap_ids, milestone_of) -> Page:
    """One feature or story as one work item page.

    A Feature has no `parent`: the migration writes no Epic page, because a
    v3 theme is a milestone and no signal tells a theme from a phase (D13).
    A Story names its feature.
    """
    fields = {"type": item.kind.capitalize(), "title": item.title,
              "description": _item_description(item), "status": "draft",
              "aliases": [item.id], "state": item.state}
    if item.kind == "story":
        if item.parent in roadmap_ids:
            fields["parent"] = _roadmap_path(roadmap_ids[item.parent])
        if item.size:
            fields["size"] = item.size
    milestone = milestone_of.get(item.id)
    if milestone in roadmap_ids:
        fields["milestone"] = _roadmap_path(roadmap_ids[milestone])
    paths, sentences = _dependencies(item, roadmap_ids)
    if paths:
        fields["blocked_by"] = paths
    traces = _item_traces(item, ids)
    if traces:
        fields["traces"] = traces
    return _item_page(tree, item, new_id, fields, _chunks(fields, sentences))


def _criterion_page(tree, text: str, new_id: str, owner_path: str) -> Page:
    """One criterion checkbox as one AcceptanceCriterion page. A checked
    checkbox has no effect: this page holds no state."""
    title = short_title(text)
    return Page(
        path=tree / "roadmap" / "criteria" / f"{new_id}.md",
        frontmatter={"type": "AcceptanceCriterion", "title": title,
                     "description": text, "status": "draft",
                     "item": owner_path},
        body=_body(new_id, title, [text]))


def _project_page(tree, text: str | None) -> Page:
    """PROJECT-01.md, as `init` writes it. With a v3 roadmap it holds one
    line more, so a reader finds the archive (D33)."""
    product = tree / "prd" / "product.md"
    name = ""
    if product.is_file():
        name = str(load_page(product).frontmatter.get("title") or "")
    title = f"{name} roadmap" if name else "The roadmap"
    chunks = ["One roadmap bundle is one GitHub Project. Add the "
              "`github` field when the Project exists."]
    if text is not None:
        chunks.append(ROADMAP_ARCHIVE_LINE)
    return Page(
        path=tree / "roadmap" / "projects" / "PROJECT-01.md",
        frontmatter={"type": "Project", "title": title,
                     "description": f"The one GitHub Project of "
                                    f"{name or 'the product'}.",
                     "status": "draft"},
        body=_body("PROJECT-01", title, chunks))


def build_roadmap(tree, text: str | None, items, ids: dict) -> list:
    """Write the roadmap bundle of the temporary tree. Returns the paths.

    `text` is the v3 roadmap, or None when the repository has none. With no
    v3 roadmap the bundle is the bundle of `init`: the log and the Project
    page, and no other directory.

    `ids` is the PRD ID map, which each trace goes through. Text that is not
    a milestone, a feature, or a story stays in the archive only (D33).
    """
    roadmap_ids = _roadmap_ids(items)
    milestone_of = _milestone_of(items)
    pages = [_project_page(tree, text)]
    criteria = 0
    for item in items:
        new_id = roadmap_ids[item.id]
        if item.kind == "milestone":
            pages.append(
                _milestone_page(tree, item, new_id, ids, roadmap_ids))
        else:
            pages.append(_work_page(tree, item, new_id, ids, roadmap_ids,
                                    milestone_of))
        for criterion in item.criteria:
            criteria += 1
            pages.append(_criterion_page(tree, criterion,
                                         f"CRITERION-{criteria:02d}",
                                         _roadmap_path(new_id)))
    for page in pages:
        write_page(page)
    init_log(tree / "roadmap" / "log.md")
    return [page.path for page in pages]


def assertions(tree: Path, blocks, items) -> list:
    """Each finding of step 2 item 8. An empty list means the tree is good.

    The migration moves nothing until this list is empty. These five
    questions are what a person would check by hand, so the script checks
    them: no ID is lost, no trace points at nothing, no block is dropped, no
    text is changed, and no roadmap item is missing.
    """
    findings = []
    pages = {path: load_page(path) for path in tree.rglob("*.md")
             if path.name not in RESERVED_PAGES
             and "archive" not in path.parts}
    aliases = {}
    for path, page in pages.items():
        for alias in page.frontmatter.get("aliases") or []:
            aliases.setdefault(alias, []).append(path)
    # 1. each old ID is an alias exactly one time
    for block in blocks:
        holders = aliases.get(block.id, [])
        if len(holders) != 1:
            findings.append(
                f"the alias {block.id} is on {len(holders)} pages, not 1")
    for item in items:
        holders = aliases.get(item.id, [])
        if len(holders) != 1:
            findings.append(
                f"the alias {item.id} is on {len(holders)} pages, not 1")
    # 2. each old trace resolves
    for path, page in pages.items():
        for trace in page.frontmatter.get("traces") or []:
            target = str(trace.get("to", "")).replace("prd:/", "prd/")
            if not (tree / target).is_file():
                findings.append(f"{path.stem} traces {trace.get('to')}, "
                                f"which is not in the tree")
    # 3. the number of blocks equals the number of requirement pages
    requirement_pages = [p for p in pages
                         if p.parts[-3] == "prd" and p.name != "product.md"
                         and p.parts[-2] not in ("decisions", "questions")]
    if len(requirement_pages) != len(blocks):
        findings.append(f"{len(blocks)} blocks gave "
                        f"{len(requirement_pages)} requirement pages")
    # 4. each page body holds the normalized text of its block
    for block in blocks:
        holders = aliases.get(block.id, [])
        if not holders:
            continue
        body = " ".join(pages[holders[0]].body.split())
        if " ".join(recipe_text(block, "v3").split()) not in body:
            findings.append(f"the body of {block.id} is not the v3 text")
    # 5. each roadmap item of v3 has one page
    for item in items:
        if not aliases.get(item.id):
            findings.append(f"the roadmap item {item.id} has no page")
    return findings


def write_archive(tree: Path, ids: dict, mapping: dict | None) -> None:
    """archive/id-map.md and the copy of the migration map. The map is a
    record of the type decisions, so the user can read them later."""
    archive = tree / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    lines = ["# The ID map", "",
             "Each ID of the v3 files, and the page that holds it now.", "",
             "| Old ID | New ID | Path |", "|---|---|---|"]
    for old_id in sorted(ids):
        new_id = ids[old_id]
        spec = BY_PREFIX[new_id.split("-")[0]]
        lines.append(f"| {old_id} | {new_id} | "
                     f"{spec.bundle}/{spec.directory}/{new_id}.md |")
    (archive / "id-map.md").write_text("\n".join(lines) + "\n",
                                       encoding="utf-8")
    if mapping is not None:
        (archive / "migrate-map.yaml").write_text(
            safe_dump(mapping, sort_keys=False, allow_unicode=True,
                           default_flow_style=False),
            encoding="utf-8")


def write_drift_record(tree: Path, ids: dict, items, blocks,
                       recipe: str) -> None:
    """archive/migrate-drift.yaml: one entry for each trace of the v3 roadmap.

    `migrate --finish` reads this file, because step 3 of the skill changes
    page bodies and only the v3 check knows whether a trace was drifted
    before that. Both keys are new IDs: `items` holds the v3 IDs, so each one
    goes through the roadmap map and each target through `ids`.
    """
    by_id = {block.id: block for block in blocks}
    roadmap_ids = _roadmap_ids(items)
    entries = []
    for item in items:
        # _item_traces gives the new target path of each trace, in the order
        # of item.traces, and raises for a target that no block holds.
        for (name, digest), trace in zip(item.traces, _item_traces(item, ids)):
            entries.append({"item": roadmap_ids[item.id], "to": trace["to"],
                            "drifted": recipe_hash(by_id[name], recipe)
                            != digest})
    archive = tree / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "migrate-drift.yaml").write_text(
        safe_dump(entries, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8")


def _require_clean_product(root: Path) -> None:
    """Refuse a docs/product/ that holds a change no commit holds.

    The run prints one rollback command, and that command takes the
    directory back to the last commit. With an uncommitted change there, the
    rollback would delete the user's work. Outside a git repository, or with
    no git on PATH, this does nothing: no rollback command can run there.

    `git.output` gives None for a failed command, so a failed `git status`
    would read as a clean directory. `git.run` keeps the two apart.
    """
    if not git.is_repository(root):
        return
    result = git.run(root, "status", "--porcelain", "--", PRODUCT_DIR)
    if result is None or result.returncode != 0:
        raise UsageError(
            f"git status failed for {PRODUCT_DIR}/, so the run cannot show "
            f"that the rollback command keeps your work. Repair the "
            f"repository first.")
    if result.stdout.strip():
        raise UsageError(
            f"{PRODUCT_DIR}/ has a change that is not committed. Commit it "
            f"first, so the rollback command works.")


def _count(tree: Path) -> int:
    """The number of pages of the built tree. A reserved page is not one."""
    return sum(1 for bundle in BUNDLES if (tree / bundle).is_dir()
               for _ in iter_pages(tree / bundle))


def _move_into_place(root: Path, tree: Path) -> None:
    """Move the built bundles and the archive into docs/product/. This is
    the one action that changes the repository."""
    destination = product_dir(root)
    destination.mkdir(parents=True, exist_ok=True)
    for name in MOVED:
        source = tree / name
        if not source.is_dir():
            continue
        target = destination / name
        if target.is_dir():
            # shutil.move puts the source inside a directory of the same
            # name, which would give docs/product/archive/archive/ for a
            # repository that already holds an archive directory. Move the
            # entries, so the new files land beside the old ones.
            for entry in sorted(source.iterdir()):
                shutil.move(str(entry), str(target / entry.name))
            continue
        shutil.move(str(source), str(target))


def _archive_v3_files(root: Path) -> None:
    """Move prd.md and roadmap.md into docs/product/archive/.

    `git mv` keeps the history of the file with the file. Outside a git
    repository, and when git refuses, the file moves all the same.
    """
    archive = product_dir(root) / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    for name, archive_name in ARCHIVE_NAMES:
        source = product_dir(root) / name
        if not source.is_file():
            continue
        target = archive / archive_name
        if not git.ok(root, "mv", f"{PRODUCT_DIR}/{name}",
                    f"{PRODUCT_DIR}/archive/{archive_name}"):
            source.replace(target)


def run(root: Path, report, mapping=None, dry_run: bool = False,
        accept_unmarked: bool = False) -> int:
    """Step 2 of the migration.

    The tree is built in a temporary directory outside docs/product/, so a
    failure at any step leaves the repository with no change. The move is the
    last action.
    """
    # The order of these three guards is fixed. A dirty working tree exits 2
    # before any data check, because the user must commit first whatever else
    # is wrong; a missing type exits 1 like `--scan`; a stop exits 1 last.
    _require_clean_product(root)
    if report.unknown:
        raise DataError("a migration map is necessary. No type for: "
                        + ", ".join(sorted(report.unknown)))
    if report.stops and not (accept_unmarked and not report.hard_stops()):
        raise DataError("the scan stops the migration:\n"
                        + "\n".join(report.stop_lines()))
    text = (product_dir(root) / V3_PRD).read_text(encoding="utf-8")
    roadmap_path = product_dir(root) / V3_ROADMAP
    roadmap_text = roadmap_path.read_text(encoding="utf-8") \
        if roadmap_path.is_file() else None
    blocks = parse_blocks(text)
    types = types_for(blocks, mapping)
    ids = assign_ids(blocks, types)
    items = parse_roadmap(roadmap_text) if roadmap_text else []
    tmp = Path(tempfile.mkdtemp(prefix="prd-migrate-"))
    try:
        build_prd(tmp, root, text, blocks, types, ids)
        build_roadmap(tmp, roadmap_text, items, ids)
        write_archive(tmp, ids, mapping)
        write_drift_record(tmp, ids, items, blocks, report.recipe)
        findings = assertions(tmp, blocks, items)
        if findings:
            for line in findings:
                print(f"ASSERTION: {line}")
            raise DataError("the migration stopped. The repository has no "
                            "change.")
        if dry_run:
            print(f"the tree is good: {_count(tmp)} pages. Nothing moved.")
            return 0
        _move_into_place(root, tmp)
        _archive_v3_files(root)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("the migration wrote docs/product/prd/ and docs/product/roadmap/.")
    print("Next: /product:migrate step 3, then `prd.py migrate --finish`.")
    print(f"To undo, before you commit: {ROLLBACK}")
    return 0
