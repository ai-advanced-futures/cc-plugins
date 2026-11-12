"""manifest.md at the bundle root (standard section 6)."""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from knowledgelib import DataError, okf, probe

NAME = "manifest.md"
FIELDS = ("brain", "plugin", "plugin_version", "ask_skill", "install", "save_code",
          "id_pattern", "id_folders", "answers", "required_links", "fixed_pages")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def read(bundle) -> dict | None:
    file = Path(bundle) / NAME
    if not file.is_file():
        return None
    page = okf.read_page(file)
    if page.error:
        raise DataError(f"{file}: {page.error}")
    return page.frontmatter


def problems(data: dict) -> list[str]:
    out = []
    if data.get("type") != "Manifest":
        out.append("type must be Manifest")
    for field in FIELDS:
        if field not in data:
            out.append(f"the field {field} is missing")
    if "plugin_version" in data and not VERSION_RE.match(str(data["plugin_version"])):
        out.append("plugin_version must be X.Y.Z")
    if "plugin" in data and "save_code" in data:
        try:
            probe.check(data["plugin"], data["save_code"])
        except DataError as error:
            out.append(str(error))
    ask = data.get("ask_skill")
    if "ask_skill" in data and not (isinstance(ask, dict) and isinstance(ask.get("plugin"), str)
                                    and isinstance(ask.get("skills"), str)):
        out.append("ask_skill must hold plugin and skills")
    if "id_pattern" in data:
        try:
            re.compile(str(data["id_pattern"]))
        except re.error:
            out.append("id_pattern is not a regular expression")
    for field in ("id_folders", "answers", "fixed_pages"):
        value = data.get(field)
        if field in data and not (isinstance(value, list) and all(isinstance(i, str) for i in value)):
            out.append(f"{field} must be a list of strings")
    links = data.get("required_links")
    if "required_links" in data and not (isinstance(links, dict)
                                         and all(isinstance(v, list) for v in links.values())):
        out.append("required_links must map a page type to a list of fields")
    if "retired_ids" in data and not isinstance(data["retired_ids"], list):
        out.append("retired_ids must be a list")
    cite = data.get("cite_folders")
    if cite is not None and not (isinstance(cite, list) and all(isinstance(i, str) for i in cite)):
        out.append("cite_folders must be a list of strings")
    elif cite:
        known = data.get("id_folders")
        known = known if isinstance(known, list) else []
        out += [f"cite_folders names {folder}, which is not in id_folders" for folder in cite if folder not in known]
    return out


def is_fixed(data: dict, rel: str) -> bool:
    return any(fnmatch.fnmatchcase(rel, pattern) for pattern in data.get("fixed_pages") or [])


def id_matches(data: dict, rel: str) -> bool:
    return re.fullmatch(str(data.get("id_pattern", "")), Path(rel).name) is not None


def write(bundle, fields: dict, body: str) -> Path:
    file = Path(bundle) / NAME
    okf.write_text(file, okf.dump({"type": "Manifest", **{k: v for k, v in fields.items() if k != "type"}}, body))
    return file


def retire(bundle, key: str) -> None:
    file = Path(bundle) / NAME
    page = okf.read_page(file)
    if page.error:
        raise DataError(f"{file}: {page.error}")
    retired = list(page.frontmatter.get("retired_ids") or [])
    if key not in retired:
        retired.append(key)
        page.frontmatter["retired_ids"] = retired
        okf.write_text(file, okf.dump(page.frontmatter, page.body))
