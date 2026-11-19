"""Read Product bundles without running Product commands or hooks."""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import date, datetime
from pathlib import Path

import yaml

from . import PlanError
from .model import TYPES, body_hash, digest, validate


TRACE_TYPES = frozenset({"Problem", "Persona", "Need", "Journey", "Capability", "Experience", "Scope",
                         "Metric", "Business", "GTM", "Risk", "Constraint", "Decision", "Question"})


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise PlanError("frontmatter keys must be text")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise PlanError("frontmatter contains a value that JSON cannot preserve")


def parse_page(text: str, path: str) -> tuple[dict, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?=\r?\n|\Z)", text, re.S)
    if not match:
        raise PlanError(f"{path}: missing or unterminated YAML frontmatter")
    try:
        fields = yaml.safe_load(match[1])
        if not isinstance(fields, dict):
            raise PlanError(f"{path}: frontmatter must be an object")
        fields = _json_value(fields)
        json.dumps(fields, allow_nan=False)
    except (yaml.YAMLError, TypeError, ValueError) as exc:
        raise PlanError(f"{path}: invalid frontmatter: {exc}") from exc
    return fields, text[match.end():]


def _inside(root: Path, path: Path) -> Path:
    result = path.resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise PlanError("source reference must resolve to a file inside its bundle")
    return result


class PRD:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.bundle = self.root / "docs/product/prd"
        self._cache: list[dict] | None = None
        self._indexes: list[dict] = []

    def pages(self) -> list[dict]:
        if self._cache is not None:
            return self._cache
        if not (self.bundle / "index.md").is_file() or not (self.bundle / "product.md").is_file():
            raise PlanError("a Product-format PRD bundle is required; prepare it with product:explore or migrate legacy input with product:migrate")
        result, indexes = [], []
        for path in sorted(self.bundle.rglob("*.md")):
            safe = _inside(self.bundle, path)
            text = safe.read_bytes().decode("utf-8")
            relative = path.relative_to(self.bundle).as_posix()
            frontmatter = text.startswith(("---\n", "---\r\n"))
            fields, body = parse_page(text, relative) if frontmatter else ({}, text)
            if path.name == "index.md":
                heading = re.search(r"(?m)^# ([^\r\n]+)", body)
                title = fields.get("title") or ("Product requirements" if path.parent == self.bundle
                                               else heading[1].strip() if heading else "")
                indexes.append({"id": path.stem, "path": "prd:/" + relative,
                                "fields": {**fields, "type": "Context", "title": title}, "body": body,
                                "hash": body_hash(body, path.stem)})
            if not frontmatter:
                if path.parent == self.bundle and path.name in {"index.md", "lenses.md"}:
                    result.append({"id": path.stem, "path": "prd:/" + path.name,
                                   "fields": {"type": "Context", "title": path.stem}, "body": text,
                                   "hash": body_hash(text, path.stem)})
                continue
            result.append({"id": path.stem, "path": "prd:/" + relative,
                           "fields": fields, "body": body, "hash": body_hash(body, path.stem)})
        self._cache, self._indexes = result, indexes
        return result

    def indexes(self) -> list[dict]:
        """Read existing index pages for publication only."""
        self.pages()
        return self._indexes

    def get(self, value: str) -> dict:
        if ":/" in value and not value.startswith("prd:/"):
            raise PlanError("a requirement reference must name the prd graph")
        pages = self.pages()
        if "/" in value:
            path = value if value.startswith("prd:/") else "prd:/" + value.lstrip("/")
            matches = [page for page in pages if page["path"] == path]
        else:
            identifier = Path(value).stem if value.endswith(".md") else value
            matches = [page for page in pages if page["id"] == identifier
                       or identifier in (page["fields"].get("aliases") or [])]
        if len(matches) != 1:
            raise PlanError(f"requirement {value!r} is missing or ambiguous")
        return matches[0]

    def trace(self, value: str) -> dict:
        page = self.get(value)
        if page["fields"].get("type") not in TRACE_TYPES:
            raise PlanError("a trace must target a typed PRD requirement page, not an index or summary")
        return {"to": page["path"], "hash": page["hash"]}


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise PlanError("cannot read the selected committed source snapshot")
    return result.stdout


def snapshot(source: Path, revision: str | None = None) -> dict:
    """Read one committed snapshot, or an explicitly supplied non-Git folder.

    A Git source defaults to HEAD and never includes concurrent uncommitted
    edits. No checkout, fetch, Product command, or declared check is run.
    """
    source = source.resolve()
    if not source.is_dir():
        raise PlanError("source roadmap directory does not exist")
    probe = subprocess.run(["git", "-C", str(source), "rev-parse", "--show-toplevel"],
                           capture_output=True, timeout=30, check=False,
                           env={**os.environ, "LC_ALL": "C"})
    if probe.returncode:
        outside_git = probe.stderr.startswith(b"fatal: not a git repository (or any")
        marked = any((parent / ".git").exists() or (parent / ".git").is_symlink()
                     for parent in (source, *source.parents))
        if not outside_git or marked:
            raise PlanError("Git could not identify the source repository; no uncommitted files were read")
    texts = {}
    commit = None
    if probe.returncode == 0:
        root = Path(probe.stdout.decode().strip()).resolve()
        relative = source.relative_to(root).as_posix()
        ref = revision or "HEAD"
        commit = _git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
        names = _git(root, "ls-tree", "-rz", "--name-only", commit, "--", relative).split(b"\0")
        for raw in names:
            if not raw:
                continue
            name = raw.decode("utf-8")
            if any(ord(char) < 32 for char in name):
                raise PlanError("source paths cannot contain control characters")
            if name.endswith(".md"):
                local = Path(name).relative_to(relative).as_posix()
                texts[local] = _git(root, "show", f"{commit}:{name}").decode("utf-8")
    else:
        if revision:
            raise PlanError("--revision requires a Git source")
        for path in sorted(source.rglob("*.md")):
            safe = _inside(source, path)
            texts[path.relative_to(source).as_posix()] = safe.read_bytes().decode("utf-8")
    if "manifest.md" not in texts:
        raise PlanError("source must be a Product roadmap bundle with manifest.md")
    manifest, _ = parse_page(texts["manifest.md"], "manifest.md")
    if manifest.get("plugin") != "product" or manifest.get("brain") != "roadmap":
        raise PlanError("source manifest is not a Product roadmap")
    retired = manifest.get("retired_ids") or []
    if not isinstance(retired, list) or any(not isinstance(item, str) for item in retired):
        raise PlanError("retired_ids must be a list of identities")
    records = []
    for path, text in sorted(texts.items()):
        if Path(path).name in {"index.md", "manifest.md", "log.md", "closed.md"}:
            continue
        fields, body = parse_page(text, path)
        if fields.get("type") not in TYPES:
            raise PlanError(f"{path}: unsupported roadmap record type")
        records.append({"id": Path(path).stem, "path": "/" + path,
                        "fields": fields, "body": body, "revision": 1, "events": []})
    errors, warnings = validate(records, retired)
    if errors:
        raise PlanError("source graph is invalid: " + "; ".join(errors))
    if sum(record["fields"]["type"] == "Project" for record in records) != 1:
        raise PlanError("source roadmap must contain exactly one Project")
    data = {"records": records, "retired_ids": retired, "source_revision": commit,
            "source_manifest": manifest, "source_log": texts.get("log.md", "")}
    data["fingerprint"] = digest(data)
    data["warnings"] = warnings
    return data
