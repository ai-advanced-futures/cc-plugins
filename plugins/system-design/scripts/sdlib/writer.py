"""The save operations of system-design (standard section 8)."""
from __future__ import annotations

from pathlib import Path

import yaml

from sdlib import DataError, UsageError, logbook, manifest, regen, schema
from sdlib.bundle import AREA_TITLES, DEFAULT_DIR, GRAPH, bundle_dir, read, ref, registry_add
from sdlib.ids import next_id, resolve
from sdlib.page import dump, ordered, parse, write_text

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


def init(root, directory=DEFAULT_DIR, title="System design", actor=None) -> Path:
    directory = check_dir(directory)
    folder = Path(root) / directory
    if (folder / manifest.NAME).exists():
        raise UsageError(f"{directory} already has a manifest.md. Run upgrade, not init.")
    if folder.is_dir() and any(folder.iterdir()):
        raise UsageError(f"{directory} is not empty. Run upgrade on an existing bundle.")
    for spec in schema.types().values():
        if spec["directory"]:
            (folder / spec["directory"]).mkdir(parents=True, exist_ok=True)
    when = stamp(actor)
    write_text(folder / "system.md", dump(
        {"type": "System", "title": title, "description": "The system in scope and the root of the design.",
         "status": "draft", "design_state": "draft", "version": 1, "generated": when},
        f"\n# {title}\n\n## Summary\n\nNo summary yet.\n"))
    for slug in schema.areas():
        name = AREA_TITLES[slug]
        write_text(folder / "areas" / f"{slug}.md", dump(
            {"type": "Area", "title": name, "description": f"The {name.lower()} area of the design.",
             "status": "draft", "area": slug, "area_state": "open", "anchor": schema.anchors()[slug],
             "generated": when}, f"\n# {name}\n"))
    registry_add(root, GRAPH, directory)
    logbook.append(folder / "log.md", "Setup", f"made the bundle {directory}", actor or schema.plugin_actor())
    regen.write(root, folder)
    manifest.write(folder, manifest.fields())
    return folder


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


def _write(root, path, frontmatter, body, type_name) -> None:
    frontmatter = ordered(frontmatter, schema.types()[type_name]["key_order"])
    problems = schema.validate(type_name, frontmatter)
    if problems:
        raise DataError("the page is not valid, so nothing is written: " + "; ".join(problems))
    write_text(path, dump(frontmatter, body))
    regen.write(root)


def _load(root, key):
    bundle = read(root)
    path = resolve(bundle, key)
    page = bundle.pages.get(path) or parse(path)
    if page.error:
        raise DataError(f"{path}: {page.error}")
    return bundle, path, page


def new(root, type_name, title, description, pairs=(), actor=None) -> Path:
    folder = bundle_dir(root)
    spec = schema.types().get(type_name)
    if spec is None or spec["prefix"] is None:
        names = ", ".join(n for n, s in schema.types().items() if s["prefix"])
        raise UsageError(f"{type_name!r} is not a page type with an ID: use {names}")
    page_id = next_id(folder, type_name)
    frontmatter = {"type": type_name, "title": title, "description": description, "status": "draft"}
    _apply(frontmatter, pairs, "new")
    frontmatter["generated"] = stamp(actor)
    path = folder / spec["directory"] / f"{page_id}.md"
    _write(root, path, frontmatter, f"\n# {page_id}: {title}\n\n{description}\n", type_name)
    return path


def set_fields(root, key, pairs, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    _apply(frontmatter, pairs, "set")
    frontmatter["generated"] = stamp(actor)
    _write(root, path, frontmatter, page.body, page.type)
    return path


def _mapping_key(field) -> str | None:
    names = [name for name in schema.edges() if name.startswith(f"{field}.")]
    return names[0].split(".", 1)[1] if names else None


def link(root, key, field, target, pairs=(), actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    edges = schema.edges()
    if field in edges:
        if edges[field]["multivalued"]:
            values = list(frontmatter.get(field) or [])
            frontmatter[field] = values + ([target] if target not in values else [])
        else:
            frontmatter[field] = target
    elif _mapping_key(field):
        item = {_mapping_key(field): target}
        for pair in pairs:
            name, value = parse_set(pair)
            item[name] = value
        frontmatter[field] = list(frontmatter.get(field) or []) + [item]
    else:
        raise UsageError(f"{field} is not a link field of system-design")
    frontmatter["generated"] = stamp(actor)
    _write(root, path, frontmatter, page.body, page.type)
    return path


def unlink(root, key, field, target, actor=None) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    value = frontmatter.get(field)
    if isinstance(value, list):
        kept = [v for v in value if v != target and not (isinstance(v, dict) and target in v.values())]
    else:
        kept = None if value == target else value
    if kept == value:
        raise DataError(f"{key} has no {field} link to {target}")
    if kept in (None, []):
        frontmatter.pop(field)
    else:
        frontmatter[field] = kept
    frontmatter["generated"] = stamp(actor)
    _write(root, path, frontmatter, page.body, page.type)
    return path


def remove(root, key, actor=None) -> Path:
    bundle, path, page = _load(root, key)
    if page.type in ("System", "Area"):
        raise UsageError(f"{key} has a fixed name. The design needs it: change it, do not remove it.")
    if page.frontmatter.get("protected") is True:
        raise DataError(f"{key} is protected. Only a person can remove protected: true.")
    page_ref = ref(bundle.dir, path)
    path.unlink()
    manifest.retire(bundle.dir, path.stem)
    logbook.append(bundle.dir / "log.md", "Forget", f"removed {page_ref}", actor or schema.plugin_actor())
    regen.write(root)
    return path


def resolve_key(root, key) -> Path:
    return resolve(read(root), key)
