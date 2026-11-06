"""Charter §17 Publication Gate — anti-multiplicative-formula scanner.

Pure-function module. No agent state. No global I/O until scan_plugin/scan_repo.

This scanner enforces Charter v1.2.0 §17 — no output of a plugin that follows the Charter
may resolve to a single multiplicative pricing-power score. An earlier formula of this
kind was rejected in review and is prohibited.

See:
- docs/adr/ADR-008-publication-gate.md (the design and the reasons)
- tests/unit/test_charter_publication_gate.py (the tests and the CI gate)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    "multiplicative score",         # check42-allow: scanner pattern definition
    "pricing power index",          # check42-allow: scanner pattern definition
    "pricing risk index",           # check42-allow: scanner pattern definition
    "single numeric pricing risk",  # check42-allow: scanner pattern definition
)

SCAN_FILE_GLOBS: tuple[str, ...] = ("agents/**/*.md", "skills/**/*.md", "**/*.py")
EXCLUDED_DIR_NAMES: frozenset[str] = frozenset({"tests"})


@dataclass(frozen=True)
class Violation:
    """Immutable violation record emitted by scan_text / scan_plugin / scan_repo."""
    plugin: str            # plugin name (e.g., "pricing")
    path: Path             # absolute path of the file
    line_no: int           # 1-indexed
    pattern: str           # which forbidden pattern matched (empty string = empty-reason directive)
    line_text: str         # the offending line (trimmed)


_DIRECTIVE_TOKEN = "check42-allow:"


def _parse_reason(line: str) -> str | None:
    """Extract the post-token reason from a line, or return None if no directive.

    4-step deterministic pipeline (spec §4.2):
      1. Locate `check42-allow:` literal (case-sensitive).
      2. Capture chars after token to EOL.
      3. Right-strip trailing comment-close markers (one each, in any order):
         `-->`, `*/`, `\"\"\"`. Do NOT strip `#` or `)`.
      4. Strip leading AND trailing whitespace. If empty after stripping, return ""
         (caller treats empty string as an empty-reason violation).

    Returns:
      None if no `check42-allow:` token on this line.
      str (possibly empty) of the parsed reason otherwise.
    """
    idx = line.find(_DIRECTIVE_TOKEN)
    if idx < 0:
        return None
    body = line[idx + len(_DIRECTIVE_TOKEN):]
    # Step 3: strip each trailing marker AT MOST ONCE, in any order
    stripped: set[str] = set()
    while True:
        progress = False
        for marker in ("-->", "*/", '"""'):
            if marker in stripped:
                continue
            if body.endswith(marker):
                body = body[:-len(marker)]
                stripped.add(marker)
                progress = True
                break
        if not progress:
            break
    return body.strip()


def scan_text(text: str, path: Path, plugin: str) -> list[Violation]:
    """Pure text scan honoring `check42-allow:` directives.

    Behavior:
      - Forbidden patterns matched case-insensitively against the line.
      - Suppression: a non-empty reason on the SAME line OR the IMMEDIATELY
        PRECEDING line suppresses violations on the current line.
      - Empty-reason directives (`check42-allow:` followed by only whitespace)
        produce their own Violation with pattern="" and do NOT suppress.
      - Multi-line constructs require SAME-LINE directive on each occurrence
        (the lookback spans exactly one line).
    """
    violations: list[Violation] = []
    lines = text.splitlines()
    # Carry the previous line's parsed reason so we don't re-parse each line twice
    # (once as reason_same for line N, again as reason_prev for line N+1). Hot path.
    prev_reason: str | None = None
    for i, line in enumerate(lines):
        # Step A: emit empty-reason violations (the directive itself failed CI).
        reason_same = _parse_reason(line)
        if reason_same == "":
            violations.append(
                Violation(
                    plugin=plugin,
                    path=path,
                    line_no=i + 1,
                    pattern="",
                    line_text=line.strip(),
                )
            )
            # Skip Step C for this line. If the line ALSO contains a forbidden
            # pattern (e.g., `multiplicative score # check42-allow:`), emitting a
            # second Violation is redundant CI noise — the contributor sees "your
            # directive is empty" once and fixes both at once. [M2 from
            # /feature-dev:code-reviewer]
            prev_reason = reason_same  # carry "" for next iteration's lookback
            continue

        # Step B: determine suppression — non-empty reason same-line OR preceding-line.
        suppressed = (reason_same is not None and reason_same != "") or \
                     (prev_reason is not None and prev_reason != "")
        prev_reason = reason_same  # carry for the next iteration

        if suppressed:
            continue

        # Step C: scan for forbidden patterns. Emit at most ONE Violation per line
        # (the first FORBIDDEN_PATTERN match) — design choice for clean CI output;
        # the contributor fixes the line once regardless of how many patterns it
        # contains. [L2 from /feature-dev:code-reviewer]
        line_lower = line.lower()
        for pat in FORBIDDEN_PATTERNS:
            if pat in line_lower:
                violations.append(
                    Violation(
                        plugin=plugin,
                        path=path,
                        line_no=i + 1,
                        pattern=pat,
                        line_text=line.strip(),
                    )
                )
                break
    return violations


def _scannable_files(plugin_dir: Path) -> list[Path]:
    """Yield absolute paths of files inside plugin_dir to scan.

    Walks the tree with os.walk so we can prune subdirectories BEFORE descending.
    A directory is pruned if its name starts with `.` (so .venv, .claude-plugin,
    .git, etc. never enter the walk) OR its name is in EXCLUDED_DIR_NAMES.

    Files are kept if their relative path matches at least one of these patterns:
      - agents/**/*.md
      - skills/**/*.md
      - **/*.py (anywhere under plugin_dir)
    """
    keep: list[Path] = []
    plugin_dir = plugin_dir.resolve()
    for dirpath, dirnames, filenames in os.walk(plugin_dir):
        # Prune subdirectories in-place — os.walk reads `dirnames` for descent.
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in EXCLUDED_DIR_NAMES
        ]
        dirpath_p = Path(dirpath)
        rel_dir = dirpath_p.relative_to(plugin_dir)
        for fname in filenames:
            rel_file = rel_dir / fname
            if _matches_scan_globs(rel_file):
                keep.append(dirpath_p / fname)
    return keep


def _matches_scan_globs(rel_path: Path) -> bool:
    """True iff rel_path matches one of SCAN_FILE_GLOBS.

    Implementation notes:
      - `agents/**/*.md` requires the path to start with `agents/` and end in `.md`.
      - `skills/**/*.md` requires the path to start with `skills/` and end in `.md`.
      - `**/*.py` matches any `.py` anywhere under the plugin.
    """
    parts = rel_path.parts
    suffix = rel_path.suffix
    if suffix == ".py":
        return True
    if suffix == ".md":
        if parts and parts[0] in ("agents", "skills"):
            return True
    return False


def scan_plugin(plugin_dir: Path) -> list[Violation]:
    """Walk plugin_dir, scanning matched files. Returns all violations.

    The plugin label on each Violation is plugin_dir.name (the basename).
    """
    plugin_name = Path(plugin_dir).name
    violations: list[Violation] = []
    for fpath in _scannable_files(Path(plugin_dir)):
        try:
            text = fpath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # UnicodeDecodeError: binary file slipped through; skip.
            # OSError covers FileNotFoundError (dangling symlink), PermissionError
            # (read-protected), IsADirectoryError, etc. Crafted adversarial files
            # must NOT crash the CI gate — they must fail cleanly. [H1 from
            # /feature-dev:code-reviewer]
            continue
        violations.extend(scan_text(text, fpath, plugin=plugin_name))
    return violations


