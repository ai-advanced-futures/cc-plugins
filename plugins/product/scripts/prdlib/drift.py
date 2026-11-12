"""`prd.py drift`: the trace hashes against the pages they name.

Drifted means the hash is different, or the target does not exist, or the
target has `status: deprecated`. Only a person clears the flag, because only a
person can judge whether the change of meaning matters.
"""
import difflib
from pathlib import Path

from . import DataError, UsageError, git
from .graph import CROSS_BUNDLE_PREFIX, relative_target, target_path
from .hashing import GENERATED_BLOCK_RE, body_hash
from .ids import resolve
from .lock import write_lock
from .page import load_page, split_frontmatter, write_page
from .regen import read_tree, require_readable
from .textsafe import escape_controls
from .tree import bundle_dir

HUMAN_PREFIX = "human:"


def _drifted(root: Path, bundle: str, trace: dict, pages: dict) -> bool:
    """`pages` is the read_tree() map. A target inside it is read from there:
    one capability named by twenty traces is parsed one time, not twenty."""
    path = target_path(root, bundle, trace.get("to", ""))
    found = pages.get(path)
    if found is None:
        if not path.is_file():
            return True
        page = load_page(path)
        frontmatter, body = page.frontmatter, page.body
    else:
        _bundle, frontmatter, body = found
    if frontmatter.get("status") == "deprecated":
        return True
    return body_hash(body, path.stem) != trace.get("hash")


def _wanted_targets(root: Path, ids: list[str], pages: dict) -> set[str]:
    """The `prd:` target string of each named page.

    A name that resolves gives the path of its page. A name that no page
    carries can still be the target of a stored trace: `/product:learn` deletes a
    requirement page and then asks about it, and the spec calls a target that
    does not exist drift. Only a name that neither a page nor a trace holds
    is a usage mistake, because exit 1 is the drift verdict and a typo must
    not read as `clean`.
    """
    prd_root = bundle_dir(root, "prd")
    stored = {trace.get("to") for _bundle, frontmatter, _body in pages.values()
              for trace in frontmatter.get("traces") or []
              if isinstance(trace, dict) and trace.get("to")}
    wanted = set()
    for identifier in ids:
        try:
            path = resolve(root, identifier)
        except DataError as error:
            from_trace = {t for t in stored
                          if Path(str(t)).stem == identifier}
            if not from_trace:
                raise UsageError(str(error))
            wanted |= from_trace
            continue
        if prd_root not in path.parents:
            raise UsageError(
                f"{escape_controls(identifier)} is not a PRD page. `--ids` "
                f"names the PRD pages "
                f"that a trace points at.")
        wanted.add(CROSS_BUNDLE_PREFIX
                   + relative_target(path, prd_root))
    return wanted


def scan(root: Path, ids: list[str] | None = None) -> list[tuple[Path, str]]:
    """(work item path, target) for each drifted trace, sorted."""
    # Read every page before resolving --ids, so a page with unparseable
    # frontmatter gives this clear error and not a resolve failure or a
    # traceback out of read_tree(). The pages come next, because a name that
    # no page carries is read against the stored traces.
    pages, broken = read_tree(root)
    require_readable(root, broken)
    wanted = _wanted_targets(root, ids, pages) if ids else None
    found = []
    for path, (bundle, frontmatter, _body) in pages.items():
        for trace in frontmatter.get("traces") or []:
            if not isinstance(trace, dict) or not trace.get("to"):
                # Exit 1 is the `drifted` verdict, so a malformed entry must
                # not reach it as a traceback. Rule E2 names the same fault.
                raise UsageError(
                    f"{escape_controls(path)}: a `traces` entry is a mapping "
                    f"with a `to` key. "
                    f"Run `prd.py check` for rule E2.")
            target = trace.get("to", "")
            if wanted is not None and target not in wanted:
                continue
            if _drifted(root, bundle, trace, pages):
                found.append((path, target))
    return sorted(found)


def write_flags(root: Path, found: list[tuple[Path, str]]) -> list[Path]:
    """Add each drifted target to the `drifted` field of its work item."""
    changed = []
    with write_lock(root):
        by_item = {}
        for path, target in found:
            by_item.setdefault(path, []).append(target)
        for path, targets in by_item.items():
            page = load_page(path)
            current = list(page.frontmatter.get("drifted") or [])
            new = current + [t for t in targets if t not in current]
            if new != current:
                page.frontmatter["drifted"] = new
                write_page(page)
                changed.append(path)
    return sorted(changed)


def accept(root: Path, identifier: str, target: str, actor: str) -> Path:
    """Store the new hash and remove the target from `drifted`."""
    if not actor.startswith(HUMAN_PREFIX):
        raise DataError("only a human: actor can accept a drifted trace")
    with write_lock(root):
        path = resolve(root, identifier)
        page = load_page(path)
        traces = page.frontmatter.get("traces") or []
        match = next((t for t in traces
                      if isinstance(t, dict) and t.get("to") == target), None)
        if match is None:
            raise DataError(f"{escape_controls(path.stem)} has no trace to "
                            f"{escape_controls(target)}")
        source = target_path(root, "roadmap", target)
        if not source.is_file():
            raise DataError(f"{escape_controls(target)} does not exist, so it "
                            "cannot be accepted")
        match["hash"] = body_hash(load_page(source).body, source.stem)
        page.frontmatter["drifted"] = [
            t for t in (page.frontmatter.get("drifted") or []) if t != target]
        if not page.frontmatter["drifted"]:
            del page.frontmatter["drifted"]
        write_page(page)
    return path


def _body_at(root: Path, revision: str, path: Path) -> str | None:
    """The body of one page at one commit. None when the commit does not
    hold the file or holds no frontmatter there."""
    text = git.output(root, "show",
                      f"{revision}:./{path.relative_to(root).as_posix()}")
    if text is None:
        return None
    fm_text, body = split_frontmatter(text + "\n")
    return None if fm_text is None else body


def _readable(body: str) -> list[str]:
    """The body lines a person reads. A generated block is not text of the
    requirement, and the hash leaves it out too."""
    return GENERATED_BLOCK_RE.sub("", body).strip("\n").splitlines()


def show(root: Path, identifier: str, target: str) -> list[str]:
    """What changed in the target since the trace was last accepted.

    The trace stores only a short hash. The text that the hash was made from
    is found in the Git history of the target: the newest commit whose body
    has the stored hash. The lines are for a person, so a missing Git or a
    missing commit is a `NOTE:` line and not an error: the person can still
    read the current text and decide.
    """
    path = resolve(root, identifier)
    trace = next((t for t in load_page(path).frontmatter.get("traces") or []
                  if isinstance(t, dict) and t.get("to") == target), None)
    if trace is None:
        raise DataError(f"{escape_controls(path.stem)} has no trace to "
                            f"{escape_controls(target)}")
    source = target_path(root, "roadmap", target)
    lines = [f"ITEM: {escape_controls(path.stem)}",
             f"TARGET: {escape_controls(target)}"]
    if not source.is_file():
        return lines + ["NOTE: the target does not exist. The requirement "
                        "was deleted or moved."]
    current = load_page(source)
    if current.frontmatter.get("status") == "deprecated":
        lines.append("NOTE: the target has status: deprecated.")
    stored = trace.get("hash")
    if body_hash(current.body, source.stem) == stored:
        lines.append("NOTE: the text did not change since the last accept.")
    revisions = git.output(root, "log", "--format=%H", "--", str(source))
    base = None
    for revision in (revisions or "").split():
        body = _body_at(root, revision, source)
        if body is not None and body_hash(body, source.stem) == stored:
            base = (revision, body)
            break
    if base is None:
        return lines + [
            "NOTE: no commit holds the text of the last accept, so the old "
            "text is not known. The current text follows.", ""
        ] + _readable(current.body)
    revision, old = base
    lines.append("BASE: " + escape_controls(git.output(
        root, "log", "-1", "--format=%h %cs %s", revision)))
    changes = git.output(root, "log", "--format=%h %s",
                         f"{revision}..HEAD", "--", str(source))
    lines += [f"CHANGE: {escape_controls(line)}"
              for line in (changes or "").splitlines()]
    if not git.ok(root, "diff", "--quiet", "HEAD", "--", str(source)):
        lines.append("CHANGE: not committed")
    lines.append("")
    lines += difflib.unified_diff(
        _readable(old), _readable(current.body),
        f"{escape_controls(source.stem)} at {revision[:7]}",
        f"{escape_controls(source.stem)} now", lineterm="")
    return lines
