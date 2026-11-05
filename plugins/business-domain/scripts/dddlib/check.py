"""`ddd.py check`: the domain linter.

Each rule is a function that takes the bundle and returns its findings. The
exit code is 0 with no error, 1 with an error, and 2 for wrong input. A
warning does not change the exit code, unless `--strict` is given.
"""
import re
from collections import defaultdict
from pathlib import Path

import yaml

from . import rules_graph, rules_names, rules_warn
from .bundle import Bundle, read, sort_key
from .issues import ERROR, Issue
from .page import FRONTMATTER_RE, line_of, read_text
from .regen import differences
from .schema import edges, types, validate_frontmatter

LOG_DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")


def e1(bundle: Bundle) -> list:
    """The frontmatter does not parse, or `type` is missing."""
    return [Issue(ERROR, "E1", path, 1, message)
            for path, message in bundle.broken.items()]


def e2(bundle: Bundle) -> list:
    """The frontmatter does not agree with the generated JSON Schema, or a
    `distinct` list names one page two times."""
    out = []
    for path, page in bundle.pages.items():
        for field_name, message in validate_frontmatter(page.type, page.frontmatter):
            out.append(Issue(ERROR, "E2", path, line_of(page, field_name), message))
        for field_name, rule in edges().items():
            value = page.frontmatter.get(field_name)
            if rule["distinct"] and isinstance(value, list):
                for item in sorted({str(v) for v in value if value.count(v) > 1}):
                    out.append(Issue(ERROR, "E2", path, line_of(page, field_name),
                                     f"{field_name}: names {item} two times"))
    return out


def e3(bundle: Bundle) -> list:
    """The file name, the type, and the directory do not agree, two pages
    have one ID, or two live Source pages have one `resource`."""
    out = []
    for path, page in bundle.pages.items():
        spec = types().get(page.type)
        if spec is None:
            continue  # E2 reports an unknown type
        if path.parent != bundle.dir / spec["directory"]:
            out.append(Issue(ERROR, "E3", path, line_of(page, "type"),
                             f"a {page.type} page belongs in "
                             f"{spec['directory']}/"))
        if not re.fullmatch(rf"{spec['prefix']}-\d{{2,}}", page.id):
            out.append(Issue(ERROR, "E3", path, 1,
                             f"the file name of a {page.type} page is "
                             f"{spec['prefix']}-<NN>.md"))
    by_id = defaultdict(list)
    for path in list(bundle.pages) + list(bundle.broken):
        by_id[path.stem].append(path)
    for page_id, paths in by_id.items():
        first, *rest = sorted(paths)
        for path in rest:
            out.append(Issue(ERROR, "E3", path, 1,
                             f"the ID {page_id} is also the ID of "
                             f"{first.relative_to(bundle.root).as_posix()}"))
    by_resource = defaultdict(list)
    for page in bundle.pages.values():
        resource = page.frontmatter.get("resource")
        if page.type == "Source" and page.live and isinstance(resource, str):
            by_resource[resource].append(page)
    for resource, pages in by_resource.items():
        first, *rest = sorted(pages, key=lambda p: sort_key(p.id))
        for page in rest:
            out.append(Issue(ERROR, "E3", page.path, line_of(page, "resource"),
                             f"the resource {resource} is also the resource "
                             f"of {first.id}"))
    return out


def e10(bundle: Bundle) -> list:
    """A generated part does not agree with what regen writes now."""
    return [Issue(ERROR, "E10", path, 1,
                  "the generated part is stale. Run `ddd.py regen`.")
            for path in differences(bundle)]


def e11(bundle: Bundle) -> list:
    """An OKF section 11 rule: the root index holds `okf_version` only, a
    directory index has no frontmatter, and log.md is newest first."""
    out = []
    root_index = bundle.dir / "index.md"
    if root_index.is_file():
        match = FRONTMATTER_RE.match(read_text(root_index))
        if match:
            try:
                data = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                data = {"<unparseable>": None}
            if not isinstance(data, dict):
                data = {"<not a mapping>": None}
            extra = sorted(str(key) for key in set(data) - {"okf_version"})
            if extra:
                out.append(Issue(ERROR, "E11", root_index, 1,
                                 f"the root index.md holds keys other than "
                                 f"okf_version: {', '.join(extra)}"))
    for index in sorted(bundle.dir.rglob("index.md")):
        if index != root_index and FRONTMATTER_RE.match(read_text(index)):
            out.append(Issue(ERROR, "E11", index, 1,
                             "a directory index.md has no frontmatter"))
    log = bundle.dir / "log.md"
    if log.is_file():
        dates = [(number, match.group(1)) for number, line
                 in enumerate(read_text(log).splitlines(), start=1)
                 if (match := LOG_DATE_RE.match(line))]
        for (_n, newer), (number, older) in zip(dates, dates[1:]):
            if newer < older:
                out.append(Issue(ERROR, "E11", log, number,
                                 f"the date {older} comes after {newer}. "
                                 f"log.md is newest first."))
    return out


RULES = ([e1, e2, e3, e10, e11] + rules_graph.RULES + rules_names.RULES
         + rules_warn.RULES)


def run(root: Path) -> list:
    bundle = read(root)
    issues = [issue for rule in RULES for issue in rule(bundle)]
    return sorted(issues, key=lambda i: (str(i.path), i.line, i.code, i.message))


def report(root: Path, issues: list, strict: bool) -> int:
    for issue in issues:
        print(issue.text(root))
    errors = sum(1 for i in issues if i.level == ERROR)
    warnings = len(issues) - errors
    print(f"{errors} errors, {warnings} warnings")
    return 1 if errors or (strict and warnings) else 0
