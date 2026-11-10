"""The save operations of business-case (standard section 8)."""
from __future__ import annotations

from pathlib import Path

import yaml

from bclib import DataError, UsageError, logbook, manifest, regen, schema
from bclib.bundle import DEFAULT_DIR, DIR_RE, GRAPH, bundle_dir, read, ref, registry_add
from bclib.ids import next_id, require_type, resolve
from bclib.page import dump, ordered, parse, write_text

PROTECTED_KEYS = ("type", "generated", "protected")


def stamp(actor=None) -> dict:
    return {"by": actor or schema.plugin_actor(), "at": logbook.stamp()}


def check_dir(directory) -> str:
    value = str(directory)
    # Test the text as given: a strip would hide a final new line.
    if not DIR_RE.fullmatch(value):
        raise UsageError(f"the folder must match [A-Za-z0-9._/-]{{1,100}}: {directory!r}")
    if not value or value.startswith("/") or ".." in Path(value).parts:
        raise UsageError(f"the folder must be relative to the project root and stay inside it: {directory!r}")
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def make_folders(folder) -> None:
    for spec in schema.types().values():
        (folder / spec["directory"]).mkdir(parents=True, exist_ok=True)


def init(root, directory=DEFAULT_DIR, actor=None) -> Path:
    directory = check_dir(directory)
    folder = Path(root) / directory
    if (folder / manifest.NAME).exists():
        raise UsageError(f"{directory} already has a manifest.md. Run upgrade, not init.")
    if folder.is_dir() and any(folder.iterdir()):
        raise UsageError(f"{directory} is not empty. Run upgrade on an existing bundle.")
    make_folders(folder)
    registry_add(root, GRAPH, directory)
    logbook.append(folder / "log.md", "Setup", f"made the bundle {directory}", actor or schema.plugin_actor())
    regen.write(root, folder)
    manifest.write(folder, manifest.fields())
    return folder


def upgrade(root, directory=None) -> list[str]:
    """Bring a bundle to the standard: folders, registry entry, manifest fields. Return the changes."""
    if directory is not None:  # an empty --dir is a wrong value, not "no value"
        directory = check_dir(directory)
        folder = Path(root) / directory
    else:
        folder = bundle_dir(root)
        directory = folder.relative_to(root).as_posix()
    changes = []
    if registry_add(root, GRAPH, directory):
        changes.append("wrote the registry entry")
    for spec in schema.types().values():
        target = folder / spec["directory"]
        if not target.is_dir():
            target.mkdir(parents=True)
            changes.append(f"made the folder {spec['directory']}/")
    current = manifest.read(folder)
    wanted = manifest.fields()
    if current is None:
        manifest.write(folder, wanted)
        changes.append("wrote manifest.md")
    else:
        merged = dict(current)
        for key, value in wanted.items():
            if key in ("generated", "retired_ids"):
                continue
            if merged.get(key) != value:
                merged[key] = value
        if merged != current:
            merged["generated"] = wanted["generated"]
            manifest.write(folder, merged)
            changes.append("updated manifest.md")
    if regen.write(root, folder):
        changes.append("wrote the generated files")
    if changes:
        logbook.append(folder / "log.md", "Upgrade", "; ".join(changes), schema.plugin_actor())
    return changes


def log(root, operation, text, actor=None) -> None:
    if operation not in logbook.OPERATIONS:
        raise UsageError(f"{operation!r} is not an operation: use {', '.join(logbook.OPERATIONS)}")
    logbook.append(bundle_dir(root) / "log.md", operation, text, actor or schema.plugin_actor())


class _TextTimeLoader(yaml.SafeLoader):
    """A SafeLoader that reads a date or a time as the text that the person gave (STORY-275, as STORY-186).

    No business-case field takes a YAML date: the time fields are strings in the schema, and the
    page read turns each date into text. So a value such as 2026-11-06T22:21:48Z stays
    that text, at each depth of a list or a map.
    """


_TextTimeLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def parse_set(item) -> tuple[str, object]:
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (yaml.load(value, Loader=_TextTimeLoader) if value.strip() else "")


def _apply(frontmatter, pairs, verb) -> None:
    for item in pairs:
        key, value = parse_set(item)
        if key in PROTECTED_KEYS:
            raise UsageError(f"{verb} does not change {key}. Only a person changes protected.")
        frontmatter[key] = value


def write_page(root, path, frontmatter, body, type_name, *, regenerate=True) -> None:
    frontmatter = ordered(frontmatter, schema.types()[type_name]["key_order"])
    problems = schema.validate(type_name, frontmatter)
    if problems:
        raise DataError("the page is not valid, so nothing is written: " + "; ".join(problems))
    write_text(path, dump(frontmatter, body))
    if regenerate:
        regen.write(root)


def _load(root, key):
    bundle = read(root)
    path = resolve(bundle, key)
    page = bundle.pages.get(path) or parse(path)
    if page.error:
        raise DataError(f"{path}: {page.error}")
    return bundle, path, page


def create(root, type_name, title, description, fields=None, body=None, actor=None, *, regenerate=True) -> Path:
    """Make a page with the next ID. `fields` is a dict of frontmatter fields."""
    spec = require_type(type_name)
    folder = bundle_dir(root)
    page_id = next_id(folder, type_name)
    title = " ".join(str(title).split())
    frontmatter = {"type": type_name, "title": title, "description": " ".join(str(description).split()),
                   "status": "draft"}
    frontmatter.update(fields or {})
    frontmatter["generated"] = stamp(actor)
    path = folder / spec["directory"] / f"{page_id}.md"
    text = body if body is not None else f"\n# {page_id}: {title}\n\n{frontmatter['description']}\n"
    write_page(root, path, frontmatter, text, type_name, regenerate=regenerate)
    return path


def new(root, type_name, title, description, pairs=(), actor=None) -> Path:
    fields = {}
    _apply(fields, pairs, "new")
    return create(root, type_name, title, description, fields, None, actor)


def set_fields(root, key, pairs, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    _apply(frontmatter, pairs, "set")
    frontmatter["generated"] = stamp(actor)
    write_page(root, path, frontmatter, page.body, page.type)
    return path


def body(root, key, text, append=False, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    base = regen.strip_generated(page.body)
    new_body = (base + "\n\n" + text.strip("\n") if append else f"\n# {page.id}: {page.title}\n\n" + text.strip("\n")) + "\n"
    frontmatter = dict(page.frontmatter)
    frontmatter["generated"] = stamp(actor)
    write_page(root, path, frontmatter, new_body, page.type)
    return path


def link(root, key, field, target, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    edges = schema.edges()
    if field not in edges:
        raise UsageError(f"{field} is not a link field of business-case: use {', '.join(edges)}")
    if edges[field]["multivalued"]:
        values = list(frontmatter.get(field) or [])
        frontmatter[field] = values + ([target] if target not in values else [])
    else:
        frontmatter[field] = target
    frontmatter["generated"] = stamp(actor)
    write_page(root, path, frontmatter, page.body, page.type)
    return path


def unlink(root, key, field, target, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    value = frontmatter.get(field)
    if isinstance(value, list):
        kept = [v for v in value if v != target]
    else:
        kept = None if value == target else value
    if kept == value:
        raise DataError(f"{key} has no {field} link to {target}")
    if kept in (None, []):
        frontmatter.pop(field)
    else:
        frontmatter[field] = kept
    frontmatter["generated"] = stamp(actor)
    write_page(root, path, frontmatter, page.body, page.type)
    return path


def remove(root, key, actor=None) -> Path:
    bundle, path, page = _load(root, key)
    if page.frontmatter.get("protected") is True:
        raise DataError(f"{key} is protected. Only a person can remove protected: true.")
    page_ref = ref(bundle.dir, path)
    path.unlink()
    manifest.retire(bundle.dir, path.stem)
    logbook.append(bundle.dir / "log.md", "Forget", f"removed {page_ref}", actor or schema.plugin_actor())
    regen.write(root)
    return path


def _need_person(by) -> None:
    if not by or not str(by).startswith("human:") or str(by) == "human:":
        raise UsageError("verify needs --by human:<login>, because only a person confirms a page")


def _confirm(root, bundle, pages, by, what) -> list[Path]:
    """Give each (path, page) `status: stable` and 1 more `verified` entry. Write nothing when 1 page is not valid."""
    entry = {"by": by, "at": logbook.stamp()}
    updated = []
    for other, item in pages:
        frontmatter = dict(item.frontmatter)
        frontmatter["status"] = "stable"
        frontmatter["verified"] = list(frontmatter.get("verified") or []) + [entry]
        frontmatter["generated"] = stamp(by)
        frontmatter = ordered(frontmatter, schema.types()[item.type]["key_order"])
        problems = schema.validate(item.type, frontmatter)
        if problems:
            raise DataError(f"{ref(bundle.dir, other)} is not valid after the change, so nothing is written: "
                            + "; ".join(problems))
        updated.append((other, item, frontmatter))
    for other, item, frontmatter in updated:
        write_text(other, dump(frontmatter, item.body))
    logbook.append(bundle.dir / "log.md", "Learn", f"{by} confirmed {what}", by)
    regen.write(root)
    return [other for other, _item, _frontmatter in updated]


def verify(root, key, by) -> list[Path]:
    """A person confirms 1 page. A second confirmation adds an entry to `verified`, it does not replace the list."""
    _need_person(by)
    bundle, path, page = _load(root, key)
    return _confirm(root, bundle, [(path, page)], by, ref(bundle.dir, path))


def verify_case(root, key, by, run=None) -> list[Path]:
    """A person confirms a case: the Case page and each page of the case get `status: stable` and a `verified` entry.

    With `run`, a Run page of the case, the person confirms that run only: the Case page, the Run page, and each
    `draft` page of the case whose `run` holds that Run page. A `draft` page of an older run stays `draft`,
    because the person did not see it in this run.
    Return the changed paths, the Case page first. A page of another case does not change.
    """
    _need_person(by)
    bundle, path, page = _load(root, key)
    if page.type != "Case":
        raise UsageError(f"verify-case takes a Case page, and {key} is a {page.type} page")
    page_ref = ref(bundle.dir, path)
    others = [(other, item) for other, item in sorted(bundle.pages.items())
              if other != path and page_ref == (item.frontmatter.get("case") or "")]
    if run is None:
        what = f"{page_ref} and the {len(others)} other pages of that case"
    else:
        run_path = resolve(bundle, run)
        run_page = dict(others).get(run_path)  # `others` holds only the pages of this case
        if run_page is None or run_page.type != "Run":
            raise UsageError(f"--run takes a Run page of the case, and {run} is not a Run page of {page_ref}")
        run_ref = ref(bundle.dir, run_path)
        others = [(other, item) for other, item in others
                  if other == run_path or (item.frontmatter.get("status") == "draft"
                                           and run_ref in schema.edge_values(item.frontmatter, "run"))]
        what = f"{page_ref} and the {len(others)} pages of its run {run_ref}"
    return _confirm(root, bundle, [(path, page)] + others, by, what)


def resolve_key(root, key) -> Path:
    return resolve(read(root), key)
