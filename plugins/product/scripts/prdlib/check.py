"""The checker. The exit code is the verdict.

0 = no error. A warning alone still gives 0. 1 = one error or more. With
--strict a warning is an error. Each finding prints
`<LEVEL>: <file>:<line> [<rule>] <message>`. No other script in this
repository emits that shape, so this plan owns it: read it here, not from a
precedent elsewhere in the tree.
"""
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import DataError, git
from .graph import CYCLE_FIELDS, FIELD_TARGETS, find_cycle, level_of, \
    milestone_difference, relative_target, target_path, targets_of
from .page import load_page, normalise, safe_load, split_frontmatter
from .registry import BY_DIRECTORY, CLOSED_STATES, DELIVERED_STATES, TYPES
from .schema import validate_frontmatter
from .times import parse_time
from .tree import BUNDLES, bundle_dir, iter_pages

ERROR = "ERROR"
WARN = "WARN"
SKIP = "SKIP"
NO_ID_PAGES = {"product.md": "Product", "closed.md": "ClosedItems"}
MAX_DESCRIPTION = 200
# The spec files are outside the two bundles. Rule W8 is the one rule that
# reads a path under the repository root and not under a bundle.
SPECS_DIRECTORY = "docs/superpowers/specs"


@dataclass
class Issue:
    file: str
    line: int
    level: str
    rule: str
    message: str

    def text(self) -> str:
        return f"{self.level}: {self.file}:{self.line} [{self.rule}] {self.message}"


def _relative(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def check_page(root: Path, bundle: str, path: Path):
    """(issues, frontmatter, text). The frontmatter is None when rule E1
    fires: the later rules read it, and a page that E1 rejects has nothing to
    give them. Both are handed back, not read again, so one `check` run reads
    and parses each page one time.
    """
    rel = _relative(root, path)
    text = path.read_text(encoding="utf-8")
    fm_text, _body = split_frontmatter(text)
    if fm_text is None:
        return [Issue(rel, 1, ERROR, "E1",
                      "the page has no frontmatter")], None, text
    try:
        # normalise: an unquoted date must reach the schema as its ISO
        # string, not as a date object that rule E2 rejects.
        frontmatter = normalise(safe_load(fm_text))
    except yaml.YAMLError as error:
        return [Issue(rel, 1, ERROR, "E1",
                      f"the frontmatter does not parse: {error}")], None, text
    if not isinstance(frontmatter, dict):
        return [Issue(rel, 1, ERROR, "E1",
                      "the frontmatter is not a mapping")], None, text
    type_name = frontmatter.get("type")
    if not type_name:
        return [Issue(rel, 1, ERROR, "E1",
                      "the frontmatter has no `type`")], None, text

    issues = [Issue(rel, 1, ERROR, "E2", message)
              for message in validate_frontmatter(type_name, frontmatter)]

    spec = TYPES.get(type_name)
    directory = path.parent.name
    if spec is None:
        issues.append(Issue(rel, 1, ERROR, "E3",
                            f"`{type_name}` is not a page type"))
    elif path.name in NO_ID_PAGES:
        # product.md and each generated closed.md are the only pages with no ID.
        if type_name != NO_ID_PAGES[path.name]:
            issues.append(Issue(rel, 1, ERROR, "E3",
                                f"{path.name} holds a "
                                f"{NO_ID_PAGES[path.name]} page"))
    else:
        expected = BY_DIRECTORY.get((bundle, directory))
        if expected is None or expected.name != type_name:
            issues.append(Issue(rel, 1, ERROR, "E3",
                                f"a {type_name} page belongs in "
                                f"{spec.bundle}/{spec.directory}/, not in "
                                f"{bundle}/{directory}/"))
        elif spec.prefix is None:
            issues.append(Issue(rel, 1, ERROR, "E3",
                                "only product.md and closed.md have no ID"))
        elif not path.stem.startswith(spec.prefix + "-"):
            issues.append(Issue(rel, 1, ERROR, "E3",
                                f"the file name must start with {spec.prefix}-"))
    return issues, frontmatter, text


def check_graph(root: Path, pages: dict) -> list[Issue]:
    """pages maps an absolute path to (bundle, frontmatter, text)."""
    issues = []
    type_of = {path: fm.get("type") for path, (_b, fm, _t) in pages.items()}
    edges = {field: {} for field in CYCLE_FIELDS}

    projects = [p for p, t in type_of.items() if t == "Project"]
    # A pair of bundles that holds no page is clean: `init` has not run, and
    # E7 has nothing to say about a graph that does not exist yet. This keeps
    # `test_check_with_bundles_exits_0` of the CLI suite true.
    if pages and len(projects) != 1:
        where = _relative(root, projects[1]) if len(projects) > 1 else \
            "docs/product/roadmap/projects/"
        issues.append(Issue(where, 1, ERROR, "E7",
                            f"projects/ holds exactly one page, "
                            f"not {len(projects)}"))

    for path, (bundle, frontmatter, _text) in pages.items():
        rel = _relative(root, path)
        for field, permitted in FIELD_TARGETS.items():
            for target in targets_of(frontmatter, field):
                resolved = target_path(root, bundle, target)
                if resolved not in pages:
                    issues.append(Issue(
                        rel, 1, ERROR, "E4",
                        f"`{field}` names {target}, which does not exist"))
                    continue
                target_type = type_of[resolved]
                if target_type not in permitted:
                    issues.append(Issue(
                        rel, 1, ERROR, "E4",
                        f"`{field}` does not accept a {target_type} target"))
                if field in edges:
                    edges[field].setdefault(str(path), []).append(str(resolved))
                if field == "parent":
                    own, parent = level_of(type_of[path]), level_of(target_type)
                    if own is None or parent is None or parent >= own:
                        issues.append(Issue(
                            rel, 1, ERROR, "E5",
                            f"the parent {target} is not of a higher level"))
        if frontmatter.get("check") and not str(
                frontmatter.get("check_declared_by", "")).startswith("human:"):
            issues.append(Issue(rel, 1, ERROR, "E8",
                                "a `check` needs a `check_declared_by` that "
                                "starts with human:"))

    for field, rule in CYCLE_FIELDS.items():
        cycle = find_cycle(edges[field])
        if cycle:
            first = Path(cycle[0])
            issues.append(Issue(_relative(root, first), 1, ERROR, rule,
                                f"`{field}` makes a cycle: "
                                + " -> ".join(Path(n).stem for n in cycle)))
    return issues


def check_runs_unchanged(root: Path, pages: dict) -> list[Issue]:
    """E9. A Run is written one time. git is the record of a later change.

    Outside a git repository the rule does not apply, and the one SKIP line
    says so: a rule that cannot run must not look like a rule that passed.
    """
    if not git.is_repository(root):
        return [Issue("", 0, SKIP, "E9", "not a git repository")]
    runs = [p for p, (_b, fm, _t) in pages.items() if fm.get("type") == "Run"]
    if not runs:
        return []
    if git.output(root, "rev-parse", "--verify", "HEAD") is None:
        # No commit yet: nothing is tracked, so nothing can have changed.
        return [Issue("", 0, SKIP, "E9", "the repository has no commit yet")]
    result = git.run(root, "diff", "--name-only", "HEAD", "--",
                     *[str(p) for p in runs])
    if result is None or result.returncode != 0:
        # git ran and failed with a HEAD in place: a corrupt index, a pathspec
        # outside the repository, or git gone from PATH. The rule did not run,
        # so it must not read as a rule that passed.
        return [Issue("", 0, ERROR, "E9",
                      "git diff failed, so the rule did not run: "
                      + (result.stderr.strip() if result else "git is missing"))]
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return [Issue(name, 1, ERROR, "E9",
                  "a Run page is written one time and then read-only")
            for name in sorted(changed)]


def _spec_owners(root: Path) -> dict:
    """Story ID -> each spec file that lists it, in the order of the names.

    A file with no frontmatter, with frontmatter that does not parse, or
    with no `stories` list is skipped: one bad file must not hide a
    duplicate in the others.
    """
    base = root / SPECS_DIRECTORY
    if not base.is_dir():
        return {}
    owners = {}
    for path in sorted(base.glob("*.md")):
        try:
            page = load_page(path)
        except DataError:
            # No frontmatter, frontmatter that does not parse, or frontmatter
            # that is not a mapping. `expire` skips a bad page the same way.
            continue
        listed = page.frontmatter.get("stories")
        if not isinstance(listed, list):
            continue
        for story in listed:
            owners.setdefault(str(story), []).append(_relative(root, path))
    return owners


def check_warnings(root: Path, pages: dict) -> list[Issue]:
    """W2 to W9. Each one is advice. Only --strict makes it an error."""
    issues = []
    children = {}
    for path, (_bundle, frontmatter, _text) in pages.items():
        parent = frontmatter.get("parent")
        if isinstance(parent, str) and parent:
            children.setdefault(parent, []).append(frontmatter)

    now = datetime.now(timezone.utc)
    for path, (bundle, frontmatter, _text) in pages.items():
        rel = _relative(root, path)
        type_name = frontmatter.get("type")

        if type_name in ("Epic", "Feature") and not frontmatter.get("traces"):
            issues.append(Issue(rel, 1, WARN, "W2",
                                f"a {type_name} traces one PRD page or more"))
        if type_name == "Milestone" and not frontmatter.get("target_date"):
            issues.append(Issue(rel, 1, WARN, "W3",
                                "the milestone has no target_date"))
        if frontmatter.get("state") in DELIVERED_STATES:
            own = relative_target(path, bundle_dir(root, bundle))
            for child in children.get(own, []):
                if child.get("state") not in CLOSED_STATES:
                    issues.append(Issue(rel, 1, WARN, "W4",
                                        "the parent is done or released and a "
                                        "child is open"))
                    break
        claim = frontmatter.get("claim")
        lease = parse_time(claim.get("lease_expires_at")) \
            if isinstance(claim, dict) else None
        if lease and lease < now:
            issues.append(Issue(rel, 1, WARN, "W5",
                                "the lease of the claim is in the past"))
        description = str(frontmatter.get("description") or "")
        if not description or len(description) > MAX_DESCRIPTION:
            issues.append(Issue(rel, 1, WARN, "W6",
                                "the description is empty or longer than "
                                f"{MAX_DESCRIPTION} characters"))
        # `ready` alone does not mean specified. `product:work` reads the `spec`
        # field, so a ready Story with no field is work that no agent can
        # take. `/product:plan` promotes a Story before any spec exists, so this
        # warning is expected noise until `/product:specifying-stories` runs.
        if type_name == "Story" and frontmatter.get("state") == "ready" \
                and not frontmatter.get("spec"):
            issues.append(Issue(rel, 1, WARN, "W7",
                                "the Story is ready and has no `spec`. Run "
                                "`/product:specifying-stories` on its Feature."))
        # W9: a Story is in the milestone of its parent (STORY-427). A parent
        # that is not in `pages` gives no W9, because E4 reports the link.
        parent = frontmatter.get("parent")
        if type_name == "Story" and isinstance(parent, str) and parent:
            found = pages.get(target_path(root, bundle, parent))
            if found is not None:
                text = milestone_difference(frontmatter.get("milestone"),
                                            parent, found[1].get("milestone"))
                if text:
                    issues.append(Issue(rel, 1, WARN, "W9", text))
    # W8 reads the spec files, not the bundle pages, so it sits after the
    # page loop. A Story that two specs list would start two builds of one
    # file.
    for story, found in sorted(_spec_owners(root).items()):
        if len(found) > 1:
            issues.append(Issue(found[-1], 1, WARN, "W8",
                                f"{story} is listed by {len(found)} specs: "
                                f"{', '.join(found)}. A Story belongs to one "
                                f"spec."))
    return issues


def check_generated(root: Path, pages: dict) -> list[Issue]:
    """E10. The generated blocks, the indexes, and the computed states agree
    with the stored fields. It calls regen.differences(), the same function
    `regen --check` calls, so the two verdicts cannot disagree. A pair of
    bundles with no page generates nothing, so the rule stays silent there.
    """
    # The import is in the function because regen renders every page of both
    # bundles. Only this rule needs it.
    from .regen import COMPUTED_STATE, differences
    if not pages:
        return []
    messages = {
        COMPUTED_STATE: "`state` is computed and is stale. Run `prd.py regen`.",
    }
    default = "the generated content is stale. Run `prd.py regen`."
    # check_page has already read and parsed every page. Handing that map to
    # differences() keeps the promise check_page makes: one `check` run reads
    # each page one time. The shape must match read_tree(), which holds the
    # body and leaves out the generated closed.md, so regen never reads that
    # page as a source of itself.
    tree = {path: (bundle, frontmatter, split_frontmatter(text)[1])
            for path, (bundle, frontmatter, text) in pages.items()
            if frontmatter.get("type") != "ClosedItems"}
    return [Issue(_relative(root, path), 1, ERROR, "E10",
                  messages.get(reason, default))
            for path, reason in sorted(differences(root, tree).items())]


# The rules that need both bundles at one time. The name is the rule label a
# partial scan reports as skipped, so a rule added here cannot go silent.
WHOLE_GRAPH_RULES = {
    "E4-E8": check_graph,
    "E9": check_runs_unchanged,
    "W1-W9": check_warnings,
    "E10": check_generated,
}


def run(root: Path, bundles=BUNDLES) -> list[Issue]:
    """The E1 to E3 pass over each page, then the graph pass over them all.

    `check_graph` runs only over the two bundles together, because a `traces`
    field names a page of the other bundle. `--bundle prd` keeps the E1 to E3
    pass, which is what a single-bundle scan can answer, and gives one SKIP
    line for each rule it drops: a rule that cannot run must not look like a
    rule that passed.
    """
    issues, pages = [], {}
    for bundle in bundles:
        base = bundle_dir(root, bundle)
        if not base.is_dir():
            continue
        for path in iter_pages(base):
            found, frontmatter, text = check_page(root, bundle, path)
            issues.extend(found)
            if frontmatter is not None:
                pages[path] = (bundle, frontmatter, text)
    if set(bundles) == set(BUNDLES):
        for rule in WHOLE_GRAPH_RULES.values():
            issues.extend(rule(root, pages))
    else:
        issues.extend(
            Issue("", 0, SKIP, name, "a partial scan reads one bundle only")
            for name in WHOLE_GRAPH_RULES)
    return issues


def report(issues: list[Issue], strict: bool, fmt: str) -> int:
    errors = [i for i in issues if i.level == ERROR]
    warnings = [i for i in issues if i.level == WARN]
    if fmt == "json":
        print(json.dumps({"errors": len(errors), "warnings": len(warnings),
                          "issues": [asdict(i) for i in issues]}, indent=2))
    else:
        for issue in issues:
            if issue.level == SKIP:
                # A skipped rule changes no count and no exit code. The line
                # says the rule did not run.
                print(f"SKIP: {issue.rule} ({issue.message})")
            else:
                print(issue.text())
        # The last line is the summary (brain standard section 9).
        print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors or (strict and warnings) else 0
