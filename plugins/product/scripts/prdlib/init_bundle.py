"""`prd.py init`: the two empty bundles.

init writes pages only. `regen` owns the content of every index, so this
module makes the two bundle directories and lets the regen pass at the end
write both root indexes.
"""
from datetime import datetime, timezone
from pathlib import Path

from . import UsageError
from .logbook import init_log
from .page import Page, write_page
from .schema import single_line_problems
from .tree import (BUNDLES, PRODUCT_DIR, V3_PRD, V3_ROADMAP, bundle_dir,
                   product_dir)

def _refuse_existing(root: Path) -> None:
    for bundle in BUNDLES:
        if bundle_dir(root, bundle).exists():
            raise UsageError(
                f"{PRODUCT_DIR}/{bundle}/ already exists. init writes nothing.")
    for name in (V3_PRD, V3_ROADMAP):
        if (product_dir(root) / name).exists():
            raise UsageError(
                f"{PRODUCT_DIR}/{name} is a v3 file. Run /product:migrate, "
                f"not init: init would make a second source of truth.")


def _root_index(path: Path) -> None:
    """The directory alone. `regen` at the end of init is the one writer of
    the bundle-root index, so init does not write a header that regen flips."""
    path.parent.mkdir(parents=True, exist_ok=True)


def init(root: Path, title: str | None = None,
         description: str | None = None) -> list[Path]:
    """Write both bundles. Returns the paths written, in write order."""
    _refuse_existing(root)
    # [inferred] The spec gives init no options. --title and --description
    # spare the user one edit; the directory name is the fallback.
    title = title or root.name
    description = description or f"The product of the {root.name} repository."
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # The rule of the single-line fields (issue 1915), before the first write:
    # `init` writes the page with no `new`, and a line break in the title or
    # the description would start a line of its own in the generated index.
    # The Project page holds the same title in its own title and description.
    problems = single_line_problems({"title": title,
                                     "description": description})
    if problems:
        raise UsageError(f"init writes nothing: {'; '.join(problems)}")

    written = []
    _root_index(bundle_dir(root, "prd") / "index.md")
    written.append(bundle_dir(root, "prd") / "index.md")
    init_log(bundle_dir(root, "prd") / "log.md")
    written.append(bundle_dir(root, "prd") / "log.md")

    product = Page(
        path=bundle_dir(root, "prd") / "product.md",
        frontmatter={"type": "Product", "title": title,
                     "description": description, "status": "draft",
                     "created": today, "updated": today},
        body=f"\n# {title}\n\n{description}\n\nRun /product:explore to fill the lenses.\n",
    )
    write_page(product)
    written.append(product.path)

    _root_index(bundle_dir(root, "roadmap") / "index.md")
    written.append(bundle_dir(root, "roadmap") / "index.md")
    init_log(bundle_dir(root, "roadmap") / "log.md")
    written.append(bundle_dir(root, "roadmap") / "log.md")

    project = Page(
        path=bundle_dir(root, "roadmap") / "projects" / "PROJECT-01.md",
        frontmatter={"type": "Project", "title": f"{title} roadmap",
                     "description": f"The one GitHub Project of {title}.",
                     "status": "draft"},
        body=(f"\n# PROJECT-01: {title} roadmap\n\n"
              f"One roadmap bundle is one GitHub Project. Add the `github` "
              f"field when the Project exists.\n"),
    )
    write_page(project)
    written.append(project.path)

    from . import standard  # local import: standard imports regen, which imports page
    from .schema import plugin_actor
    standard.backfill(root, plugin_actor())

    from .regen import write as regen_write  # local import: regen imports page
    # Return each file that init writes, also the files of regen and of the
    # standard, so that the caller can show the full list.
    written += [path for path in regen_write(root) if path not in written]
    for bundle in BUNDLES:
        if standard.write_manifest(root, bundle):
            written.append(bundle_dir(root, bundle) / "manifest.md")
    if standard.registry_add(root):
        written.append(Path(root) / ".claude" / "knowledge.json")
    return written
