"""Vocabulary linter — see Charter §5.3 / §5.1.1 / §5.2.1."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml


@dataclass
class Violation:
    line: int
    term: str
    audience: str
    severity: str  # "error" | "warning"
    rationale: str


@lru_cache(maxsize=1)
def _load_vocab() -> dict:
    """Parse vocabulary.yaml from the schema folder of this plugin."""
    vocab_path = Path(__file__).resolve().parents[1] / "schemas" / "agentic-pricing" / "vocabulary.yaml"
    return yaml.safe_load(vocab_path.read_text())


def _line_is_in_allowlist(line: str, allowlist_patterns: list[re.Pattern]) -> bool:
    return any(p.search(line) for p in allowlist_patterns)


def _iter_lines_with_fence_state(text: str) -> Iterable[tuple[int, str, bool]]:
    """Yield (1-indexed line number, line text, inside_code_fence)."""
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            yield (i, line, in_fence)
            in_fence = not in_fence
            continue
        yield (i, line, in_fence)


def lint_text(text: str, audience: str) -> list[Violation]:
    """Lint a single text string under the given audience scope."""
    if audience not in ("internal", "customer-facing", "mixed"):
        raise ValueError(f"unknown audience: {audience}")
    if audience == "internal":
        return []
    if audience == "mixed":
        return _lint_mixed(text)
    return _lint_customer_facing(text)


@lru_cache(maxsize=1)
def _compiled_patterns() -> tuple[list[re.Pattern], list[tuple[re.Pattern, dict]]]:
    """Cache the compiled regex patterns derived from vocabulary.yaml.

    Built once per process; subsequent calls return the same lists.
    Pairs with @lru_cache on _load_vocab() to make hot-path linting allocation-free.
    """
    vocab = _load_vocab()
    allowlist = [re.compile(c["pattern"]) for c in vocab["allowlist_contexts"]]
    internal = [(re.compile(e["pattern"], re.IGNORECASE), e) for e in vocab["internal_only"]]
    return allowlist, internal


def _lint_customer_facing(text: str) -> list[Violation]:
    allowlist_patterns, compiled = _compiled_patterns()

    violations: list[Violation] = []
    for lineno, line, inside_fence in _iter_lines_with_fence_state(text):
        if inside_fence:
            continue
        if _line_is_in_allowlist(line, allowlist_patterns):
            continue
        for pattern, entry in compiled:
            if pattern.search(line):
                violations.append(
                    Violation(
                        line=lineno,
                        term=entry["term"],
                        audience="customer-facing",
                        severity=entry["severity"],
                        rationale=entry["rationale"],
                    )
                )
    return violations


_FENCE_OPEN = re.compile(r"<!--\s*audience:([A-Za-z0-9_\-]+)\s*-->")
_VALID_FENCE_AUDIENCES = ("internal", "customer-facing")
_FENCE_CLOSE = re.compile(r"<!--\s*/audience\s*-->")


def _lint_mixed(text: str) -> list[Violation]:
    """Mixed-audience linting — parse fenced sections; each linted under its own audience."""
    violations: list[Violation] = []
    current_audience: str | None = None
    fence_open_line = 0
    found_any_fence = False

    in_code_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        m_open = _FENCE_OPEN.search(line)
        m_close = _FENCE_CLOSE.search(line)

        if m_open:
            audience_value = m_open.group(1)
            # §5.2.1 rule 5 — unknown audience value in fence is ERROR
            if audience_value not in _VALID_FENCE_AUDIENCES:
                violations.append(
                    Violation(
                        line=i,
                        term="<unknown audience value>",
                        audience="mixed",
                        severity="error",
                        rationale=(
                            f"unknown audience value '{audience_value}' in fence marker — "
                            f"must be one of {_VALID_FENCE_AUDIENCES}"
                        ),
                    )
                )
                continue
            if current_audience is not None:
                # Nested fence — §5.2.1 rule 4
                violations.append(
                    Violation(
                        line=i,
                        term="<nested fence>",
                        audience="mixed",
                        severity="error",
                        rationale=(
                            f"nested <!-- audience:{audience_value} --> fence at line {i} "
                            f"while inside fence opened at line {fence_open_line}"
                        ),
                    )
                )
                continue
            current_audience = audience_value
            fence_open_line = i
            found_any_fence = True
            continue
        if m_close:
            if current_audience is None:
                violations.append(
                    Violation(
                        line=i,
                        term="<orphan close>",
                        audience="mixed",
                        severity="error",
                        rationale="unmatched <!-- /audience --> fence close",
                    )
                )
            current_audience = None
            continue
        if current_audience is not None:
            section_violations = _lint_customer_facing(line) if current_audience == "customer-facing" else []
            for v in section_violations:
                v.line = i
                violations.append(v)

    if not found_any_fence:
        # §5.2.1 rule 1 — mixed agent with zero fences is an error
        violations.append(
            Violation(
                line=0,
                term="<no fences>",
                audience="mixed",
                severity="error",
                rationale="audience: mixed file contains no <!-- audience:X --> fenced sections",
            )
        )
    if current_audience is not None:
        # §5.2.1 rule 2 — unclosed fence at EOF
        violations.append(
            Violation(
                line=fence_open_line,
                term="<unclosed fence>",
                audience="mixed",
                severity="error",
                rationale=(
                    f"<!-- audience:{current_audience} --> fence opened at line {fence_open_line} "
                    "but never closed"
                ),
            )
        )
    return violations


_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _read_frontmatter_audience(text: str) -> tuple[str, str, str | None, dict]:
    """Return (audience, body_text, raw_invalid_value, fm_dict).

    fm_dict is the parsed frontmatter (empty dict if no frontmatter or unparseable),
    so callers don't have to re-parse for downstream checks.
    raw_invalid_value is None when audience is missing or valid; it carries the
    raw string when the frontmatter had an audience field with an unrecognized
    value (so callers can emit a violation distinguishing missing from invalid).
    """
    m = _FRONTMATTER.search(text)
    if not m:
        return ("internal", text, None, {})
    fm = yaml.safe_load(m.group(1)) or {}
    raw = fm.get("audience")
    if raw is None:
        return ("internal", text[m.end():], None, fm)
    if raw not in ("internal", "customer-facing", "mixed"):
        return ("internal", text[m.end():], str(raw), fm)
    return (raw, text[m.end():], None, fm)


def lint_agent_file(path: Path) -> list[Violation]:
    text = Path(path).read_text()
    audience, body, invalid_value, fm = _read_frontmatter_audience(text)
    violations = lint_text(body, audience)

    if invalid_value is not None:
        violations.insert(
            0,
            Violation(
                line=1,
                term="<invalid audience value>",
                audience="internal",
                severity="warning",
                rationale=(
                    f"agent file frontmatter has unrecognized `audience: {invalid_value}` "
                    "value; coerced to internal. Valid values: internal, customer-facing, mixed."
                ),
            ),
        )
    elif "audience" not in fm:
        violations.insert(
            0,
            Violation(
                line=1,
                term="<missing audience tag>",
                audience="internal",
                severity="warning",
                rationale=(
                    "agent file has no `audience:` frontmatter; defaulted to "
                    "`audience: internal`. Add an explicit tag."
                ),
            ),
        )
    return violations


def lint_handoff_artifact(path: Path) -> list[Violation]:
    """Lint a JSON handoff artifact."""
    data = json.loads(Path(path).read_text())
    audience = data.get("audience")
    if audience not in ("internal", "customer-facing", "mixed"):
        return [
            Violation(
                line=0,
                term="<missing audience>",
                audience="internal",
                severity="error",
                rationale=(
                    f"handoff artifact at {path} is missing required `audience` field "
                    "or has an invalid value"
                ),
            )
        ]
    text_blob = "\n".join(_iter_text_fields(data))
    return lint_text(text_blob, audience)


def _iter_text_fields(obj):
    """Yield all string values from a JSON object recursively."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_text_fields(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_text_fields(v)
    elif isinstance(obj, str):
        yield obj
