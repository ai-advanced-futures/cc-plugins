"""The save operations of the generic graph (standard section 8)."""
from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath

import yaml

from knowledgelib import DataError, FileError, UsageError, changes, graph_regen, links, logbook, manifest, okf, registry
from knowledgelib.graph import (DEFAULT_DIR, GRAPH, LINK_FIELDS, MANIFEST_BODY, OPERATIONS, SLUG_RE, TYPES,
                                bundle_dir, manifest_fields, plugin_actor, stamp, validate)

PROTECTED_KEYS = ("type", "generated", "protected")


def parse_set(item) -> tuple[str, object]:
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (yaml.safe_load(value) if value.strip() else "")


def slugify(title) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        raise UsageError(f"the title {title!r} gives no slug")
    return slug


def _log(bundle, operation, text, actor) -> None:
    when = stamp()
    logbook.append(bundle / "log.md", logbook.entry(operation, text, actor, when), when[:10])


def init(root, directory=DEFAULT_DIR, actor=None) -> Path:
    directory = registry.check_path(directory, GRAPH)
    bundle = Path(root) / directory
    if (bundle / manifest.NAME).exists():
        raise UsageError(f"{directory} already has a manifest.md. Run upgrade, not init.")
    if bundle.is_dir() and any(bundle.iterdir()):
        raise UsageError(f"{directory} is not empty. Run upgrade on an existing bundle.")
    for folder in TYPES.values():
        (bundle / folder).mkdir(parents=True, exist_ok=True)
    registry.add(root, GRAPH, directory)
    _log(bundle, "Setup", f"made the bundle {directory}", actor or plugin_actor())
    graph_regen.write(root, bundle)
    manifest.write(bundle, manifest_fields(), MANIFEST_BODY)
    return bundle


def _load(file):
    page = okf.read_page(file)
    if page.error:
        raise DataError(f"{file}: {page.error}")
    return page


def regen(root, done=None) -> list[Path]:
    """Run regen. When a file cannot be read or written, name the step and the file, say what is done
    (for example "the page <path> is saved"), and give the command to run."""
    try:
        return graph_regen.write(root)
    except FileError as error:
        head = f"{done}, but " if done else ""
        raise DataError(f"{head}regen of {okf.shown(root, error.path)} failed: {error.reason}. "
                        f'Run: knowledge_graph.py --root "{root}" regen') from error


def _write_page(root, file, frontmatter, body) -> None:
    problems = validate(frontmatter.get("type"), frontmatter)
    if problems:
        raise DataError("the page is not valid, so nothing is written: " + "; ".join(problems))
    try:
        okf.write_text(file, okf.dump(frontmatter, body))
    except FileError as error:
        raise DataError(f"the page {okf.shown(root, file)} was not saved: {error.reason}. "
                        "Run the command again.") from error
    regen(root, done=f"the page {okf.shown(root, file)} is saved")


def _edit(root, key, change, actor, new_body=None) -> Path:
    """Load the page, apply change to a copy of its frontmatter, stamp it, and write it.
    A change that returns False leaves the page as it is. new_body, when given, maps the
    current body to the new body."""
    file = resolve(root, key)
    page = _load(file)
    frontmatter = dict(page.frontmatter)
    if change(frontmatter) is False:
        return file
    frontmatter["generated"] = {"by": actor or plugin_actor(), "at": stamp()}
    _write_page(root, file, frontmatter, new_body(page.body) if new_body else page.body)
    return file


def _apply_sets(frontmatter, sets, verb) -> None:
    for item in sets:
        key, value = parse_set(item)
        if key in PROTECTED_KEYS:
            raise UsageError(f"{verb} does not change {key}. Only a person changes protected.")
        frontmatter[key] = value


def _new_slug(type_name, title, frontmatter, slug) -> str:
    """The slug of a new page: --slug, else the base name of the raw file of a Source, else the title."""
    if slug is not None:
        if not SLUG_RE.fullmatch(slug):
            raise UsageError(f"the slug {slug!r} is not valid: use lowercase letters, digits, and single hyphens")
        return slug
    resource = frontmatter.get("resource")
    if type_name == "Source" and isinstance(resource, str) and resource.startswith("raw/"):
        return slugify(PurePosixPath(resource).stem)
    return slugify(title)


def new(root, type_name, title, description, sets=(), actor=None, slug=None) -> Path:
    bundle = bundle_dir(root)
    if type_name not in TYPES:
        raise UsageError(f"{type_name!r} is not a type: use {', '.join(TYPES)}")
    frontmatter = {"type": type_name, "title": title, "description": description, "status": "draft"}
    _apply_sets(frontmatter, sets, "new")
    slug = _new_slug(type_name, title, frontmatter, slug)
    file = bundle / TYPES[type_name] / f"{slug}.md"
    if slug in ((manifest.read(bundle) or {}).get("retired_ids") or []) or os.path.lexists(file):
        raise UsageError(f"the slug {slug} is taken or retired. Give --slug or another title.")
    if file.parent.is_symlink():
        raise UsageError(f"{file.parent} is a symbolic link, so new writes nothing there.")
    frontmatter["generated"] = {"by": actor or plugin_actor(), "at": stamp()}
    _write_page(root, file, frontmatter, f"\n# {title}\n\n{description}\n")
    return file


def resolve(root, key) -> Path:
    bundle = bundle_dir(root)
    if key.startswith("/"):
        file = bundle / key.lstrip("/")
        if links.inside(bundle, file):
            return file
        raise DataError(f"no page is at {key}")
    for folder in TYPES.values():
        if links.inside(bundle, bundle / folder / f"{key}.md"):
            return bundle / folder / f"{key}.md"
    folded = okf.oneline(key).casefold()
    hits = [file for file in okf.bundle_pages(bundle)
            if links.inside(bundle, file)
            and folded in {okf.oneline(a).casefold()
                           for a in (okf.read_page(file).frontmatter or {}).get("aliases") or []}]
    if len(hits) == 1:
        return hits[0]
    if hits:
        raise DataError(f"the alias {key!r} names more than one page")
    raise DataError(f"no page has the slug or the alias {key!r}")


def set_fields(root, key, sets, actor=None) -> Path:
    return _edit(root, key, lambda frontmatter: _apply_sets(frontmatter, sets, "set"), actor)


def body(root, key, text, append=False, actor=None) -> Path:
    """Write the text above the LINKS block: replace it, or add the text after it. regen owns the block."""
    if not text.strip():
        raise UsageError("the text is empty, so body writes nothing")
    if okf.LINKS_START in text or okf.LINKS_END in text:
        raise UsageError("the text holds a LINKS marker. regen writes the LINKS block, so leave it out.")
    text = text.strip("\n")

    def new_body(current):
        if append:
            return okf.strip_links_block(current).rstrip("\n") + "\n\n" + text + "\n"
        return "\n" + text + "\n"

    return _edit(root, key, lambda frontmatter: None, actor, new_body)


def _link_check(field, target) -> None:
    if field not in LINK_FIELDS:
        raise UsageError(f"{field} is not a link field: use {', '.join(LINK_FIELDS)}")
    if not okf.is_link(target):
        raise UsageError(f"{target!r} is not a link: use /<path> or <graph>:/<path>")


def _source_entry(root, target) -> dict:
    """The full sources entry for target: id, resource, title, last_modified (the keys of SourceRef)."""
    found = links.resolve(root, registry.read(root), GRAPH, target, cache_only=True)
    if found.file is None:
        raise DataError(f"cannot link {target}: {found.state}")
    data = _load(found.file).frontmatter
    title = data.get("title")
    generated = data.get("generated")
    at = generated.get("at") if isinstance(generated, dict) else None
    if not title or not at:
        raise DataError(f"cannot link {target}: the page has no title or no generated.at")
    return {"id": found.file.stem, "resource": target, "title": title, "last_modified": str(at)[:10]}


def link(root, key, field, target, actor=None) -> Path:
    _link_check(field, target)

    def change(frontmatter):
        entries = list(frontmatter.get(field) or [])
        if any(isinstance(e, dict) and e.get("resource") == target for e in entries):
            return False
        frontmatter[field] = entries + [_source_entry(root, target)]

    return _edit(root, key, change, actor)


def unlink(root, key, field, target, actor=None) -> Path:
    _link_check(field, target)

    def change(frontmatter):
        entries = list(frontmatter.get(field) or [])
        kept = [e for e in entries if not (isinstance(e, dict) and e.get("resource") == target) and e != target]
        if len(kept) == len(entries):
            raise DataError(f"{key} has no {field} link to {target}")
        if kept:
            frontmatter[field] = kept
        else:
            frontmatter.pop(field)

    return _edit(root, key, change, actor)


def remove(root, key, actor=None) -> Path:
    file = resolve(root, key)
    if _load(file).frontmatter.get("protected") is True:
        raise DataError(f"{key} is protected. Only a person can remove protected: true.")
    bundle = bundle_dir(root)
    path = okf.bundle_path(bundle, file)
    file.unlink()
    changes.note(file)
    manifest.retire(bundle, file.stem)
    _log(bundle, "Forget", f"removed {path}", actor or plugin_actor())
    regen(root, done=f"the page {okf.shown(root, file)} is removed")
    return file


MOVE_ITEMS = ("AGENTS.md", "raw", "bundle")


def _move_target(root, container) -> tuple[str, str]:
    """Check the move and return the old container and the new container."""
    from scaffold import ScaffoldError, normalize_container

    entry = registry.read(root).get(GRAPH)
    if entry is None:
        raise UsageError("the knowledge graph is not in .claude/knowledge.json. Run /knowledge:setup first.")
    if entry.remote:
        raise UsageError("the knowledge graph is a remote graph. Move it in its own repository.")
    old_bundle = bundle_dir(root)
    if old_bundle.name != "bundle" or old_bundle.parent == Path(root):
        raise UsageError(f"{entry.path} is not <container>/bundle, so the layout is not known.")
    try:
        new = normalize_container(container)
    except ScaffoldError as error:
        raise UsageError(str(error)) from error
    registry.check_path(new, GRAPH)
    old = entry.path[:-len("bundle")]
    target = Path(root) / new
    if new == old:
        raise DataError(f"{new} is the folder of the graph already.")
    if (Path(root) / old / "raw") in (target, *target.parents) or old_bundle in (target, *target.parents):
        raise DataError(f"{new} is inside the graph. Give a folder outside it.")
    for item in MOVE_ITEMS:
        if os.path.lexists(target / item):
            raise DataError(f"{new}{item} exists. Nothing is moved.")
    root = Path(root)
    checked = [root / old / item for item in MOVE_ITEMS] + [target, *target.parents]
    for path in checked:
        if root in path.parents and path.is_symlink():
            raise DataError(f"{path.relative_to(root)} is a symbolic link. Nothing is moved.")
    return old, new


def _new_container_text(text, old, new) -> str:
    """Replace the old container path where it starts a path, not inside a longer path or a URL."""
    return re.sub(rf"(?<![\w/.-])(\./)?{re.escape(old)}", lambda m: (m.group(1) or "") + new, text)


def move(root, container, actor=None) -> Path:
    """Move AGENTS.md, raw/, and bundle/ of the graph to another container (spec STORY-14, row 4)."""
    old, new = _move_target(root, container)
    root, source, target = Path(root), Path(root) / old, Path(root) / new
    moved, created, agents_text, registered = [], [], None, False
    try:
        for folder in reversed([target, *target.parents]):
            if not folder.exists():
                created.append(folder)
        target.mkdir(parents=True, exist_ok=True)
        for item in MOVE_ITEMS:
            if (source / item).exists():
                (source / item).rename(target / item)
                moved.append(item)
        agents = target / "AGENTS.md"
        if agents.is_file():
            agents_text = agents.read_text("utf-8")
            okf.write_text(agents, _new_container_text(agents_text, old, new))
        registry.add(root, GRAPH, f"{new}bundle")
        registered = True
    except Exception as error:
        left = _undo_move(root, old, new, moved, created, agents_text, registered)
        if left:
            raise DataError(f"the move failed ({error}) and the undo failed: {'; '.join(left)}. "
                            f"Look at {old} and {new}, then move each item back by hand.") from error
        raise DataError(f"the move failed, so the graph is at {old}: {error}") from error
    bundle = target / "bundle"
    try:
        if not any(source.iterdir()):
            source.rmdir()
    except OSError as error:
        raise DataError(f"the graph is at {new}, but the old folder {old} was not removed: {error}") from error
    try:
        _log(bundle, "Upgrade", f"moved {old} to {new}", actor or plugin_actor())
        graph_regen.write(root)
    except Exception as error:
        raise DataError(f"the graph is at {new}, but the log entry or regen failed: {error}") from error
    return bundle


def _undo_move(root, old, new, moved, created, agents_text, registered) -> list[str]:
    """Put everything back. Each step runs, also after an error. Return one line for each step that failed."""
    source, target = root / old, root / new
    left = []

    def step(what, action) -> None:
        try:
            action()
        except Exception as error:
            left.append(f"{what}: {error}")

    if registered:
        step(f"the registry still names {new}bundle", lambda: registry.add(root, GRAPH, f"{old}bundle"))
    if agents_text is not None:
        step(f"{new}AGENTS.md has the new paths", lambda: okf.write_text(target / "AGENTS.md", agents_text))
    for item in reversed(moved):
        step(f"{item} is still in {new}", lambda item=item: (target / item).rename(source / item))
    for folder in reversed(created):
        try:
            folder.rmdir()
        except OSError:
            pass
    return left


def log(root, operation, text, actor=None) -> None:
    if operation not in OPERATIONS:
        raise UsageError(f"{operation!r} is not an operation: use {', '.join(OPERATIONS)}")
    _log(bundle_dir(root), operation, text, actor or plugin_actor())
