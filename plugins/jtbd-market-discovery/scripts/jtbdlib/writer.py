"""The save operations of the jtbd graph (standard section 8)."""
from __future__ import annotations

from pathlib import Path

import yaml

from jtbdlib import DataError, UsageError, logbook, manifest, regen, schema
from jtbdlib.bundle import DEFAULT_DIR, GRAPH, bundle_dir, read, ref, registry_add
from jtbdlib.ids import next_id, require_type, resolve
from jtbdlib.page import dump, ordered, parse, write_text

PROTECTED_KEYS = ("type", "generated", "protected")


def stamp(actor=None) -> dict:
    return {"by": actor or schema.plugin_actor(), "at": logbook.stamp()}


def check_dir(directory) -> str:
    value = str(directory).strip()
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
    if directory:
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


def parse_set(item) -> tuple[str, object]:
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (yaml.safe_load(value) if value.strip() else "")


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
        raise UsageError(f"{field} is not a link field of the jtbd graph: use {', '.join(edges)}")
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


def remove(root, key, actor=None) -> list[Path]:
    """Remove a page. A Run page takes the pages of its run with it, so no page keeps a link to a page that is gone.

    Return the removed paths, the page of the key first. The code removes nothing when one of the pages is protected.
    """
    bundle, path, page = _load(root, key)
    page_ref = ref(bundle.dir, path)
    doomed = [(path, page)]
    if page.type == "Run":
        doomed += [(other, item) for other, item in sorted(bundle.pages.items())
                   if other != path and page_ref in schema.edge_values(item.frontmatter, "run")]
    for other, item in doomed:
        if item.frontmatter.get("protected") is True:
            raise DataError(f"{ref(bundle.dir, other)} is protected. Only a person can remove protected: true.")
    for other, _item in doomed:
        other.unlink()
        manifest.retire(bundle.dir, other.stem)
    detail = f"removed {page_ref}" + (f" and the {len(doomed) - 1} other pages of that run" if len(doomed) > 1 else "")
    logbook.append(bundle.dir / "log.md", "Forget", detail, actor or schema.plugin_actor())
    regen.write(root)
    return [other for other, _item in doomed]


def resolve_key(root, key) -> Path:
    return resolve(read(root), key)
