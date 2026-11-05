"""Where the two bundles are, below the root directory."""
from pathlib import Path

from . import UsageError

PRODUCT_DIR = "docs/product"
BUNDLES = ("prd", "roadmap")
# The standard reserves index.md, log.md, and manifest.md. closed.md is a
# generated page with `type: ClosedItems`, so the checker reads it like any
# other page.
RESERVED_PAGES = ("index.md", "log.md", "manifest.md")
# The two v3 files that the migration reads. They sit beside the bundles.
V3_PRD = "prd.md"
V3_ROADMAP = "roadmap.md"


def product_dir(root: Path) -> Path:
    return root / PRODUCT_DIR


def bundle_dir(root: Path, bundle: str) -> Path:
    return product_dir(root) / bundle


def require_bundles(root: Path) -> None:
    """Raise UsageError when either bundle directory is absent."""
    missing = [b for b in BUNDLES if not bundle_dir(root, b).is_dir()]
    if missing:
        names = ", ".join(f"{PRODUCT_DIR}/{b}/" for b in missing)
        raise UsageError(
            f"{names} does not exist. Run `prd.py init` for a new repository, "
            f"or `/product:migrate` when {PRODUCT_DIR}/prd.md exists."
        )


def require_no_bundles(root: Path) -> None:
    """The precondition of `migrate --scan`, `--dry-run`, and the main run.

    These three build the bundles, so they refuse to run when one exists.
    This is the opposite of require_bundles, which every other subcommand
    uses. A blanket guard would make each of them unreachable.
    """
    for bundle in BUNDLES:
        if bundle_dir(root, bundle).exists():
            raise UsageError(
                f"{PRODUCT_DIR}/{bundle}/ exists. The migration is done, or "
                f"run `migrate --finish`.")
    if not (product_dir(root) / V3_PRD).is_file():
        raise UsageError(
            f"{PRODUCT_DIR}/{V3_PRD} does not exist. There is nothing to "
            f"migrate. Run `prd.py init` for a new repository.")


def iter_pages(bundle: Path):
    """Each .md file of a bundle that is not a reserved page, sorted by path."""
    for path in sorted(bundle.rglob("*.md")):
        if path.name not in RESERVED_PAGES:
            yield path
