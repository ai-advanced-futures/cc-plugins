# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
gap_report.py — Gap report assembly and handoff.json emission for grounded-synthesis.

Run it as: uv run ${CLAUDE_PLUGIN_ROOT}/lib/gap_report.py --session <session_dir> ...

Used by: grounded-synthesis-orchestrator (via Bash CLI mode)
Replaces logic that would otherwise live in orchestrator agent prose.

The orchestrator invokes this module via Bash after both Wave 1 (fact extraction)
and Wave 2 (coverage checking) complete. The orchestrator NEVER reads sub-agent
output files (source-*-facts.json, source-*-coverage.json) into its context —
all JSON reading happens here in Python.

session.json shape (written by the orchestrator at session start):
  {
    "session_id": "<uuid4>",
    "draft_path": "<absolute path to the draft file>",
    "source_paths": ["<absolute path>", "..."],
    "session_dir": "<absolute path to the session directory>",
    "started_at": "<ISO 8601 timestamp>",
    "key_facts_per_source": <the clamped value; the handoff shows 12 when it is absent>,
    "sources_skipped": [{"path": "<path>", "reason": "<why>"}]
  }

  (Per-source state is derived at assembly time from the per-source-{i}-facts.json /
  source-{i}-coverage.json files; it is NOT stored in session.json.)

Per-source artifact files (written by Wave 1 + Wave 2 sub-agents):
  source-{i}-facts.json    — fact file (see fact_schema.py)
  source-{i}-coverage.json — coverage file (see coverage_checker agent)

CLI flags:
  --session <session_dir>            (required) absolute path to session directory
  --output <output_path>             (optional) output path for the markdown gap report;
                                     defaults to <draft_dir>/<draft_name>.grounded-synthesis-report.md
  --emit-handoff                     (optional flag) also write handoff.json — to
                                     output_dir_override if set, otherwise to session_dir
  --output-dir-override <OVERRIDE>   (optional) absolute path override for gap-report.md
                                     and handoff.json output (a caller agent)

Output sections in the gap report:
  # grounded-synthesis report
  ## Summary
  ## Per-source
  ## Top-line missing facts
  ## Facts with no verdict  (only when a fact has no verdict)
  ## Sources not analyzed   (only when a source is not analyzed: a skipped source, or a
                            source with no fact file or no coverage file)

doc-contract #4: default_output_path(draft_path) returns
  draft_path.parent / (draft_path.name + OUTPUT_SUFFIX)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve lib package root when run as __main__ (uv run ${CLAUDE_PLUGIN_ROOT}/lib/gap_report.py)
if __name__ == "__main__":
    _plugin_root = Path(__file__).resolve().parent.parent
    if str(_plugin_root) not in sys.path:
        sys.path.insert(0, str(_plugin_root))

from lib.constants import (
    COVERAGE_VERDICTS,
    DEFAULT_FACTS_PER_SOURCE,
    FACTS_PER_SOURCE_BOUNDS,
    OUTPUT_SUFFIX,
    PLUGIN_VERSION,
)

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def default_output_path(draft_path: Path) -> Path:
    """Return the default gap-report output path for *draft_path*.

    Implements doc-contract #4: draft_path.parent / (draft_path.name + OUTPUT_SUFFIX).
    Example: /foo/bar/brief.md → /foo/bar/brief.md.grounded-synthesis-report.md
    """
    return draft_path.parent / (draft_path.name + OUTPUT_SUFFIX)


# ---------------------------------------------------------------------------
# Internal loaders
# ---------------------------------------------------------------------------


def _load_session(session_dir: Path) -> dict:
    """Read and return session.json from *session_dir*."""
    session_path = session_dir / "session.json"
    return json.loads(session_path.read_text(encoding="utf-8"))


def _load_source_data(session_dir: Path, source_index: int) -> tuple[dict | None, dict | None]:
    """Load facts and coverage JSON for source *source_index*.

    Returns (facts_dict, coverage_dict). Either may be None if the file is absent.
    """
    facts_path = session_dir / f"source-{source_index}-facts.json"
    coverage_path = session_dir / f"source-{source_index}-coverage.json"

    try:
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        facts = None

    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        coverage = None

    return facts, coverage


def _discover_source_indices(session_dir: Path, kind: str = "coverage") -> list[int]:
    """Return sorted list of source indices from source-*-<kind>.json files present.

    *kind* is "coverage" (Wave 2 files) or "facts" (Wave 1 files).
    """
    indices: list[int] = []
    for child in session_dir.iterdir():
        m = re.fullmatch(rf"source-(\d+)-{kind}\.json", child.name)
        if m:
            indices.append(int(m.group(1)))
    return sorted(indices)


def _read_fact_source_path(session_dir: Path, source_index: int) -> str | None:
    """Return the normalized source_path of source-{i}-facts.json, or None.

    None when the file is absent, is not valid JSON, is not a JSON object, or has no
    source_path string. A malformed fact file stays in the session folder after the
    orchestrator skips it, so a bad file must not stop the report.
    """
    try:
        data = json.loads(
            (session_dir / f"source-{source_index}-facts.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("source_path"), str):
        return None
    return os.path.normpath(data["source_path"])


def _sources_not_covered(
    session_data: dict, session_dir: Path, coverage_indices: list[int]
) -> list[dict]:
    """Return one {"path", "reason"} entry for each source with no coverage or no facts.

    Compares each path of session.json source_paths with the source_path of the fact
    files (os.path.normpath on both sides). A path is fine when it is in
    sources_skipped (already named), or when a fact file that has a coverage file
    holds it. Any other path is named: "no coverage file" when a fact file holds it,
    else "no fact file".
    """
    skipped = {
        os.path.normpath(str(entry.get("path", "")))
        for entry in session_data.get("sources_skipped") or []
        if isinstance(entry, dict)
    }
    covered: set[str] = set()
    facts_only: set[str] = set()
    for idx in _discover_source_indices(session_dir, "facts"):
        path = _read_fact_source_path(session_dir, idx)
        if path is not None:
            (covered if idx in coverage_indices else facts_only).add(path)

    not_covered: list[dict] = []
    for raw_path in session_data.get("source_paths") or []:
        norm = os.path.normpath(str(raw_path))
        if norm in skipped or norm in covered:
            continue
        reason = "no coverage file" if norm in facts_only else "no fact file"
        not_covered.append({"path": raw_path, "reason": reason})
    return not_covered


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _render_markdown(
    session_data: dict,
    per_source_data: list[dict],
    top_line_missing: list[dict],
    *,
    generated_at: str,
) -> str:
    """Build the full markdown gap report string."""
    session_id = session_data.get("session_id", "unknown")
    draft_path = session_data.get("draft_path", "unknown")
    sources_skipped: list[dict] = session_data.get("sources_skipped") or []

    # Aggregate counts
    total_facts = sum(s["facts_total"] for s in per_source_data)
    total_present = sum(s["facts_present"] for s in per_source_data)
    total_missing = sum(s["facts_missing"] for s in per_source_data)
    n_skipped = len(sources_skipped)
    no_verdict = [item for s in per_source_data for item in s.get("no_verdict", [])]

    lines: list[str] = []

    # Header
    lines.append("# grounded-synthesis report")
    lines.append("")
    lines.append(f"**Session:** {session_id}")
    lines.append(f"**Draft:** {draft_path}")
    lines.append(f"**Generated:** {generated_at}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"{total_facts} facts checked, {total_present} present, "
        f"{total_missing} missing, {n_skipped} sources not analyzed, "
        f"{len(no_verdict)} facts with no verdict"
    )
    lines.append("")

    # Per-source detail
    lines.append("## Per-source")
    lines.append("")
    for src in per_source_data:
        lines.append(f"### Source {src['index']}: {src['source_path']}")
        for verdict_entry in src["verdicts"]:
            fact_id = verdict_entry["fact_id"]
            verdict = verdict_entry["verdict"]
            rationale = verdict_entry.get("rationale", "")
            lines.append(f"- {fact_id}: {verdict} — {rationale}")
        lines.append("")

    # Top-line missing facts
    lines.append("## Top-line missing facts")
    lines.append("")
    if top_line_missing:
        for item in top_line_missing:
            fact_id = item["id"]
            claim = item.get("claim", "")
            prov = item.get("provenance", {})
            locator_type = prov.get("locator_type", "")
            locator = prov.get("locator", "")
            lines.append(f"- {fact_id}: {claim} (provenance: {locator_type} {locator})")
    else:
        lines.append("(none)")
    lines.append("")

    # Facts with no verdict (only when non-empty)
    if no_verdict:
        lines.append("## Facts with no verdict")
        lines.append("")
        for item in no_verdict:
            lines.append(f"- {item['id']}: {item['claim']} (source: {item['source_path']})")
        lines.append("")

    # Sources not analyzed (only when non-empty)
    if sources_skipped:
        lines.append("## Sources not analyzed")
        lines.append("")
        for entry in sources_skipped:
            path = entry.get("path", "unknown")
            reason = entry.get("reason", "unknown")
            lines.append(f"- {path} — {reason}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handoff builder
# ---------------------------------------------------------------------------


def _facts_per_source(session_data: dict) -> tuple[int, str | None]:
    """Return (value, warning) for invocation.key_facts_per_source.

    The orchestrator clamps the value at Step 1 and writes it into session.json.
    No key: the default, no warning. A whole number of 1 or more is kept as it is
    (it is the value the run sent to the fact-extractors), with a warning when it is
    outside FACTS_PER_SOURCE_BOUNDS. Any other value: the default, with a warning.
    The handoff schema needs an integer of 1 or more.
    """
    if "key_facts_per_source" not in session_data:
        return DEFAULT_FACTS_PER_SOURCE, None
    value = session_data["key_facts_per_source"]
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        low, high = FACTS_PER_SOURCE_BOUNDS
        if low <= value <= high:
            return value, None
        return value, f"key_facts_per_source {value} is outside [{low}, {high}]"
    return DEFAULT_FACTS_PER_SOURCE, (
        f"key_facts_per_source {value!r} in session.json is not a whole number of 1 or "
        "more; the handoff shows the default"
    )


def _build_handoff(
    session_data: dict,
    per_source_data: list[dict],
    output_path: Path | None,
    status: str,
    failure_reason: str | None = None,
) -> dict:
    """Build the handoff.json content dict."""
    sources_skipped: list[dict] = session_data.get("sources_skipped") or []
    source_paths: list[str] = session_data.get("source_paths") or []

    total_facts = sum(s["facts_total"] for s in per_source_data)
    total_present = sum(s["facts_present"] for s in per_source_data)
    total_missing = sum(s["facts_missing"] for s in per_source_data)

    # One warning for each source that is not analyzed, then one for each fact with no
    # verdict, then the fact-count warning. The 'warnings' key is ALWAYS present
    # (empty list when none).
    warnings: list[str] = [
        f"Source skipped: {entry.get('path', 'unknown')} — {entry.get('reason', 'unknown')}"
        for entry in sources_skipped
    ]
    for s in per_source_data:
        warnings.extend(
            f"Fact with no verdict: {item['id']} — {item['source_path']}"
            for item in s.get("no_verdict", [])
        )
    key_facts_per_source, facts_warning = _facts_per_source(session_data)
    if facts_warning is not None:
        warnings.append(facts_warning)

    handoff: dict = {
        "session_id": session_data.get("session_id", "unknown"),
        "plugin": "grounded-synthesis",
        "version": PLUGIN_VERSION,
        "schema_version": "1",
        "invocation": {
            "draft_path": session_data.get("draft_path") or "<no draft provided>",
            "source_paths": source_paths,
            "key_facts_per_source": key_facts_per_source,
            "output_path": str(output_path) if output_path is not None else "",
        },
        "outputs": {
            "gap_report_path": str(output_path) if output_path is not None else None,
            "session_dir": session_data.get("session_dir", ""),
        },
        "summary": {
            "facts_checked": total_facts,
            "facts_present": total_present,
            "facts_missing": total_missing,
            "sources_analyzed": len(per_source_data),
            "sources_skipped": len(sources_skipped),
        },
        "status": status,
        "warnings": warnings,
    }

    if failure_reason is not None:
        handoff["failure_reason"] = failure_reason

    return handoff


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _count(n: int, word: str) -> str:
    """'1 source', '2 sources'."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def audit_line(summary: dict, report_path: Path, handoff_path: Path | None) -> str:
    """The last line of an audit. Each count comes from the summary of handoff.json."""
    parts = [
        f"Checked {_count(summary['facts_checked'], 'fact')} across "
        f"{_count(summary['sources_analyzed'], 'source')}",
        f"{summary['facts_missing']} missing",
    ]
    if summary["sources_skipped"]:
        parts.append(f"{_count(summary['sources_skipped'], 'source')} not analyzed")
    parts.append(f"report at {report_path}")
    if handoff_path is not None:
        parts.append(f"handoff at {handoff_path}")
    return "; ".join(parts)


def build_gap_report(
    session_dir: str,
    output_path: str | None = None,
    emit_handoff: bool = False,
    output_dir_override: str | None = None,
) -> str | None:
    """Assemble the gap report from per-source coverage JSON files.

    Reads session.json, all source-*-facts.json and source-*-coverage.json files
    from session_dir. Writes the markdown gap report to output_path (or the
    default computed from draft_path). If emit_handoff=True, also writes
    handoff.json to session_dir.

    Does NOT read draft or source files — operates only on the JSON artifacts
    written by the sub-agents.

    v0.3.0: output_dir_override accepts an absolute path. When set:
    - gap-report.md is written to {override}/gap-report.md (output_path arg is ignored)
    - handoff.json is written to {override}/handoff.json
    Override applies to BOTH the normal path and the catastrophic-failure
    (no-coverage) path — the caller looks ONLY at the override for the handoff.

    The session scratch files (source-*-facts.json, source-*-coverage.json) remain
    at session_dir. Override scope is OUTPUT-only.

    When output_dir_override is None (standalone invocation): preserves v0.1.0
    behavior — gap-report.md goes to output_path (or its default derived from
    draft_path), handoff.json goes to session_dir.

    Status logic:
      - "failed":  no coverage files found at all
      - "partial": a source is not analyzed (skipped, or no fact file, or no coverage
                   file) OR a fact has no verdict
      - "ok":      in all other cases
    """
    session_dir_path = Path(session_dir)
    session_data = _load_session(session_dir_path)

    # v0.3.0 — compute BOTH output paths ONCE, before any branching, so
    # the catastrophic-failure branch and the normal branch use the same paths.
    if output_dir_override is not None:
        override_path = Path(output_dir_override)
        override_path.mkdir(parents=True, exist_ok=True)
        gap_report_path: Path = override_path / "gap-report.md"
        handoff_path: Path = override_path / "handoff.json"
    else:
        # v0.1.0 behavior
        if output_path is not None:
            gap_report_path = Path(output_path)
        else:
            draft_path_str = session_data.get("draft_path", "")
            if draft_path_str:
                gap_report_path = default_output_path(Path(draft_path_str))
            else:
                gap_report_path = session_dir_path / "gap-report.md"
        handoff_path = session_dir_path / "handoff.json"

    # Discover which source indices have coverage files
    coverage_indices = _discover_source_indices(session_dir_path)

    # Sources not analyzed: the skipped ones, then each source with no fact file or no
    # coverage file. The report and the handoff read this list. session.json is not changed.
    not_analyzed: list[dict] = list(session_data.get("sources_skipped") or [])
    not_analyzed += _sources_not_covered(session_data, session_dir_path, coverage_indices)
    report_data = {**session_data, "sources_skipped": not_analyzed}

    generated_at = datetime.now(tz=timezone.utc).isoformat()

    # Handle catastrophic failure: no coverage files at all
    if not coverage_indices:
        if emit_handoff:
            # invocation.output_path must be non-empty per schema even when status=failed;
            # use the would-be gap_report_path as the intended destination.
            handoff = _build_handoff(
                report_data,
                [],
                output_path=None,  # outputs.gap_report_path = null (status=failed)
                status="failed",
                failure_reason="No coverage files found — Wave 2 may have failed entirely.",
            )
            # Override invocation.output_path with the non-empty intended path
            handoff["invocation"]["output_path"] = str(gap_report_path)
            handoff_path.write_text(
                json.dumps(handoff, indent=2), encoding="utf-8"
            )
        return None

    # Load per-source data and build fact lookup
    per_source_data: list[dict] = []
    top_line_missing: list[dict] = []

    for idx in coverage_indices:
        facts_dict, coverage_dict = _load_source_data(session_dir_path, idx)

        # Build id→fact lookup for enriching missing entries
        facts_by_id: dict[str, dict] = {}
        if facts_dict:
            for fact in facts_dict.get("facts", []):
                facts_by_id[fact["id"]] = fact

        source_path = (
            facts_dict.get("source_path", f"source-{idx}")
            if facts_dict
            else f"source-{idx}"
        )

        verdicts: list[dict] = coverage_dict.get("verdicts", []) if coverage_dict else []

        facts_present = 0
        facts_missing = 0
        for _v in verdicts:
            _verdict = _v.get("verdict")
            if _verdict == "PRESENT":
                facts_present += 1
            elif _verdict == "MISSING":
                facts_missing += 1

        # A fact with no verdict: its id has no entry with a verdict of COVERAGE_VERDICTS.
        # With no fact file, each verdict entry with another value counts.
        verdict_ids = {v.get("fact_id") for v in verdicts if v.get("verdict") in COVERAGE_VERDICTS}
        if facts_dict:
            no_verdict = [
                {"id": f["id"], "claim": f.get("claim", ""), "source_path": source_path}
                for f in facts_dict.get("facts", [])
                if f["id"] not in verdict_ids
            ]
        else:
            no_verdict = [
                {"id": v.get("fact_id", "unknown"), "claim": "", "source_path": source_path}
                for v in verdicts
                if v.get("verdict") not in COVERAGE_VERDICTS
            ]
        facts_total = facts_present + facts_missing + len(no_verdict)

        per_source_data.append(
            {
                "index": idx,
                "source_path": source_path,
                "facts_total": facts_total,
                "facts_present": facts_present,
                "facts_missing": facts_missing,
                "verdicts": verdicts,
                "no_verdict": no_verdict,
            }
        )

        # Collect missing facts for top-line section
        for v in verdicts:
            if v.get("verdict") == "MISSING":
                fact_id = v["fact_id"]
                fact_info = facts_by_id.get(fact_id, {"id": fact_id, "claim": "", "provenance": {}})
                top_line_missing.append(fact_info)

    # Determine status
    if not_analyzed or any(s["no_verdict"] for s in per_source_data):
        status = "partial"
    else:
        status = "ok"

    # Render and write the markdown report
    markdown = _render_markdown(
        report_data,
        per_source_data,
        top_line_missing,
        generated_at=generated_at,
    )

    gap_report_path.parent.mkdir(parents=True, exist_ok=True)
    gap_report_path.write_text(markdown, encoding="utf-8")

    # The handoff and the last line of the audit use the same summary dict.
    handoff = _build_handoff(
        report_data,
        per_source_data,
        output_path=gap_report_path,
        status=status,
    )
    if emit_handoff:
        handoff_path.write_text(
            json.dumps(handoff, indent=2), encoding="utf-8"
        )
    return audit_line(handoff["summary"], gap_report_path, handoff_path if emit_handoff else None)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Assemble grounded-synthesis gap report from session directory artifacts. "
            "Reads session.json, source-*-facts.json, source-*-coverage.json. "
            "Writes markdown gap report (and optionally handoff.json)."
        )
    )
    parser.add_argument(
        "--session",
        metavar="SESSION_DIR",
        required=True,
        help="Absolute path to the session directory.",
    )
    parser.add_argument(
        "--output",
        metavar="OUTPUT_PATH",
        default=None,
        help="Output path for the markdown gap report (default: next to draft file).",
    )
    parser.add_argument(
        "--emit-handoff",
        action="store_true",
        default=False,
        help=(
            "Also write handoff.json — to output_dir_override if set, "
            "otherwise to SESSION_DIR."
        ),
    )
    parser.add_argument(
        "--output-dir-override",
        metavar="OVERRIDE_DIR",
        default=None,
        help=(
            "Absolute path override for gap-report.md and handoff.json output "
            "(a caller agent). When set, both files are written to "
            "OVERRIDE_DIR instead of the default session_dir / draft_path locations."
        ),
    )
    args = parser.parse_args()
    line = build_gap_report(
        session_dir=args.session,
        output_path=args.output,
        emit_handoff=args.emit_handoff,
        output_dir_override=args.output_dir_override,
    )
    if line:
        print(line)
    sys.exit(0)
