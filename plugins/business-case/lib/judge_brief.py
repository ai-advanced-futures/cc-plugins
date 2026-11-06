"""The judge brief: fixed text code writes for the fresh-context judge.

Spec §6: the brief holds no text beyond the template. It names the judge's input files (a digest
manifest) and its reply path. Writing a brief counts one judge run against the session budget.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib import case_files, digest, paths

BRIEF_TEMPLATE = """business-case judge brief v1
case_dir: {case_dir}
reply_path: {reply_path}
manifest_digest: {manifest_digest}
inputs:
{input_lines}"""

# The number in a judge file name (brief, reply, report): ASCII digits, at least three, no leading
# zero past three digits.
NNN = r"[0-9]{3}|[1-9][0-9]{3,}"
_BRIEF_NAME = re.compile(rf"^brief-({NNN})\.txt$")
_INPUT_LINE = re.compile(r"^sha256:([0-9a-f]{64}) (\d+) (.+)$")


# A case file changed between finance.json and the manifest (a second writer at the same moment).
CHANGED_WHILE_WRITTEN = "a case file changed while the brief was written ({files}); write the brief again"


class BudgetExhausted(RuntimeError):
    """The current session has used its judge runs."""


class BriefRefused(ValueError):
    """A brief this module will not write, or a file that is not a brief it wrote."""


def brief_name(nnn: int) -> str:
    return f"brief-{nnn:03d}.txt"


def reply_name(nnn: int) -> str:
    return f"reply-{nnn:03d}.json"


def brief_relpath(nnn: int) -> str:
    return f"{paths.JUDGE_DIR}/{brief_name(nnn)}"


def reply_relpath(nnn: int) -> str:
    return f"{paths.JUDGE_DIR}/{reply_name(nnn)}"


def brief_number(brief_path) -> int:
    match = _BRIEF_NAME.match(Path(brief_path).name)
    if not match:
        raise BriefRefused(f"{brief_path} is not a judge brief file name")
    return int(match.group(1))


def _input_lines(manifest: dict) -> str:
    return "\n".join(f"sha256:{m['sha256']} {m['bytes']} {rel}" for rel, m in sorted(manifest.items()))


def manifest_digest(manifest: dict) -> str:
    return digest.sha256_hex(_input_lines(manifest).encode("utf-8"))


def _render(case_dir: str, nnn: int, manifest: dict) -> str:
    return BRIEF_TEMPLATE.format(
        case_dir=case_dir, reply_path=f"{case_dir}/{reply_relpath(nnn)}",
        manifest_digest=manifest_digest(manifest), input_lines=_input_lines(manifest))


def _next_number(judge_dir: Path) -> int:
    numbers = [brief_number(p) for p in judge_dir.glob("brief-*.txt") if _BRIEF_NAME.match(p.name)]
    return max(numbers, default=0) + 1


def _check_manifest(manifest: dict) -> None:
    """Refuse, before a run is counted, a brief that read_brief could not parse back."""
    if not manifest:
        raise BriefRefused("the case has no judge input files")
    for rel in manifest:
        try:
            rel.encode("utf-8")
        except UnicodeEncodeError:
            raise BriefRefused(f"judge input {rel!r} is not a UTF-8 file name") from None
        if "\n" in rel or "\r" in rel:
            raise BriefRefused(f"judge input {rel!r} has a line break in its name")


def check_budget(case_dir) -> None:
    """Refuse when the current session has used `session_budget` runs. Needs a session."""
    session = case_files.current_session(case_dir)
    budget = case_files.read_meta(case_dir)["session_budget"]
    if session["judge_runs"] >= budget:
        raise BudgetExhausted(f"session {session['id']} has used its {budget} judge runs")


def _check_finance(case_dir: Path, manifest: dict) -> None:
    """Refuse when finance.json disagrees with the manifest: an input it records with another digest
    (or present on one side only), or another decisions.jsonl length. finance.json is read as plain
    JSON, so no finance module enters this module's imports (ruling PF-12)."""
    changed = []
    data = None
    try:
        raw = (case_dir / paths.FINANCE).read_bytes()
        if manifest.get(paths.FINANCE) == digest._digest_of(raw):
            data = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError):
        pass
    if not isinstance(data, dict) or not isinstance(data.get("inputs"), dict):
        changed.append(paths.FINANCE)
    else:
        changed += [rel for rel, d in data["inputs"].items() if manifest.get(rel) != d]
        if data.get("decisions_bytes") != manifest.get(paths.DECISIONS, {}).get("bytes"):
            changed.append(paths.DECISIONS)
    if changed:
        raise BriefRefused(CHANGED_WHILE_WRITTEN.format(files=", ".join(sorted(set(changed)))))


def write_brief(case_dir, *, check_finance: bool = False) -> tuple:
    """Count a judge run, then write judge/brief-NNN.txt. Returns (path, manifest).

    Needs a session. Refuses when the session has used `session_budget` runs. With check_finance
    (`bc.py brief`), also refuses when finance.json does not describe the files the manifest lists.
    Every refusal comes before the run is counted. The run counts when the brief is written,
    whether or not a reply is later accepted."""
    case_dir = Path(case_dir).resolve()
    check_budget(case_dir)
    manifest = digest.build_manifest(case_dir)
    _check_manifest(manifest)
    if check_finance:
        _check_finance(case_dir, manifest)
    case_files.bump_judge_runs(case_dir)
    judge_dir = case_dir / paths.JUDGE_DIR
    judge_dir.mkdir(exist_ok=True)
    nnn = _next_number(judge_dir)
    path = judge_dir / brief_name(nnn)
    case_files._atomic_write(path, _render(str(case_dir), nnn, manifest).encode("utf-8"))
    return path, manifest


def read_brief(path) -> tuple:
    """Parse a brief back into (case_dir, manifest, reply_path). Raises BriefRefused when the file
    is not exactly what the template renders for what it says."""
    path = Path(path)
    nnn = brief_number(path)
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BriefRefused(f"{path} is not UTF-8") from exc
    lines = text.split("\n")
    if len(lines) < 6 or not (lines[1].startswith("case_dir: ") and lines[2].startswith("reply_path: ")):
        raise BriefRefused(f"{path} is not a judge brief")
    case_dir = lines[1][len("case_dir: "):]
    reply_path = lines[2][len("reply_path: "):]
    manifest = {}
    for line in lines[5:]:
        match = _INPUT_LINE.match(line)
        if not match:
            raise BriefRefused(f"{path} has a malformed input line: {line!r}")
        manifest[match.group(3)] = {"sha256": match.group(1), "bytes": int(match.group(2))}
    if _render(case_dir, nnn, manifest) != text:
        raise BriefRefused(f"{path} does not match the brief template")
    return case_dir, manifest, reply_path
