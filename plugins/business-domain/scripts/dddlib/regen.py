"""`ddd.py regen`: write each generated part from the frontmatter only.

regen never fails on page content. It skips a page that does not parse, and
it writes an edge to a missing page as plain text. Only `check` reports
these. regen writes a file only when its new bytes differ from the bytes on
disk, so a run with no drift touches no file.
"""
from .bundle import Bundle, read
from .indexes import directory_index, links_tsv, root_index
from .links import incoming, page_text
from .page import read_text, write_text
from .schema import types


def expected(bundle: Bundle) -> dict:
    """Path -> the text regen gives the file, or None when the file must
    not exist."""
    out = {}
    edges_in = incoming(bundle)
    for path in bundle.pages:
        out[path] = page_text(bundle, path, edges_in)
    for type_name, spec in types().items():
        out[bundle.dir / spec["directory"] / "index.md"] = \
            directory_index(bundle, type_name)
    out[bundle.dir / "index.md"] = root_index(bundle)
    out[bundle.dir / "links.tsv"] = links_tsv(bundle)
    return out


def _current(bundle: Bundle, path):
    """The text on disk. A page was read one time by `read`, so use it."""
    if path in bundle.pages:
        return bundle.pages[path].text
    return read_text(path) if path.is_file() else None


def differences(bundle: Bundle) -> list:
    """Each generated part that does not agree with what regen writes now."""
    return sorted(path for path, text in expected(bundle).items()
                  if _current(bundle, path) != text)


def write(root) -> list:
    """Write each stale part. Returns the paths written or removed. The
    caller holds the write lock."""
    bundle = read(root)
    changed = []
    for path, text in expected(bundle).items():
        if _current(bundle, path) == text:
            continue
        if text is None:
            path.unlink()
            if path.parent != bundle.dir and not any(path.parent.iterdir()):
                path.parent.rmdir()
        else:
            write_text(path, text)
        changed.append(path)
    return sorted(changed)
