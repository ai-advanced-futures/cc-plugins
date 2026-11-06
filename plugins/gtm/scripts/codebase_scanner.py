from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.truth_tier_validator import TruthTier


@dataclass
class ProductCapability:
    text: str
    tier: TruthTier
    source_file: str


@dataclass
class ProductCapabilityMap:
    capabilities: list[ProductCapability]
    tech_stack: list[str]

    def to_dict(self) -> dict:
        return {
            "capabilities": [{"text": c.text, "tier": c.tier.value, "source": c.source_file} for c in self.capabilities],
            "tech_stack": self.tech_stack,
        }


FEATURE_HEADER_PATTERN = re.compile(r'^#{1,3}\s*(features?|capabilities|what.+do)', re.IGNORECASE | re.MULTILINE)
LIST_ITEM_PATTERN = re.compile(r'^[\-\*\+]\s+(.+)$', re.MULTILINE)
CHANGELOG_ADDED_PATTERN = re.compile(r'^#{1,4}\s+(added|new features?|features?)\b', re.IGNORECASE | re.MULTILINE)
CHANGELOG_VERSION_PATTERN = re.compile(r'^#{1,3}\s+\[?[\d]+\.[\d]', re.MULTILINE)
OPENAPI_SUMMARY_PATTERN = re.compile(r'^\s+summary:\s*(.+)$', re.MULTILINE)


class CodebaseScanner:
    def __init__(self, repo_root: Path):
        self.root = Path(repo_root)

    def extract_from_readme(self) -> list[ProductCapability]:
        readme = self.root / "README.md"
        if not readme.exists():
            return []
        content = readme.read_text(encoding="utf-8")
        match = FEATURE_HEADER_PATTERN.search(content)
        if not match:
            return []
        section = content[match.start():]
        items = LIST_ITEM_PATTERN.findall(section[:2000])
        return [ProductCapability(text=item.strip(), tier=TruthTier.SHIPPED, source_file="README.md") for item in items[:20]]

    def extract_from_feature_flags(self, flags_path: Path) -> list[ProductCapability]:
        try:
            flags = json.loads(flags_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        caps = []
        for name, enabled in flags.items():
            tier = TruthTier.SHIPPED if enabled else TruthTier.IN_FLIGHT
            try:
                source = str(flags_path.relative_to(self.root))
            except ValueError:
                source = flags_path.name
            caps.append(ProductCapability(text=name.replace("_", " "), tier=tier, source_file=source))
        return caps

    def extract_from_changelog(self) -> list[ProductCapability]:
        for name in ("CHANGELOG.md", "CHANGELOG", "CHANGELOG.rst", "HISTORY.md"):
            path = self.root / name
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            match = CHANGELOG_ADDED_PATTERN.search(content)
            if not match:
                match = CHANGELOG_VERSION_PATTERN.search(content)
            if not match:
                continue
            section = content[match.start():]
            items = LIST_ITEM_PATTERN.findall(section[:2000])
            return [
                ProductCapability(text=item.strip(), tier=TruthTier.SHIPPED, source_file=name)
                for item in items[:20]
            ]
        return []

    def extract_from_openapi(self) -> list[ProductCapability]:
        for name in ("openapi.yaml", "openapi.yml", "openapi.json", "swagger.yaml", "swagger.yml", "swagger.json"):
            path = self.root / name
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix == ".json":
                try:
                    spec = json.loads(content)
                    caps = []
                    for path_key, path_item in spec.get("paths", {}).items():
                        for method, operation in path_item.items():
                            if not isinstance(operation, dict):
                                continue
                            summary = operation.get("summary") or operation.get("description", "")
                            if summary:
                                caps.append(ProductCapability(
                                    text=f"{method.upper()} {path_key}: {summary}",
                                    tier=TruthTier.SHIPPED,
                                    source_file=name,
                                ))
                    if caps:
                        return caps[:20]
                except Exception:
                    pass
            else:
                summaries = OPENAPI_SUMMARY_PATTERN.findall(content)
                if summaries:
                    return [
                        ProductCapability(text=s.strip(), tier=TruthTier.SHIPPED, source_file=name)
                        for s in summaries[:20]
                    ]
        return []

    def infer_tech_stack(self) -> list[str]:
        stack = []
        if (self.root / "requirements.txt").exists() or (self.root / "pyproject.toml").exists():
            stack.append("python")
            req_text = ""
            if (self.root / "requirements.txt").exists():
                req_text = (self.root / "requirements.txt").read_text()
            pyproject_text = ""
            if (self.root / "pyproject.toml").exists():
                pyproject_text = (self.root / "pyproject.toml").read_text()
            combined_text = req_text.lower() + pyproject_text.lower()
            for pkg in ["fastapi", "django", "flask", "sqlalchemy"]:
                if pkg in combined_text:
                    stack.append(pkg)
        if (self.root / "package.json").exists():
            stack.append("node")
            try:
                pkg = json.loads((self.root / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for name in deps:
                    stack.append(name.lstrip("@").split("/")[-1])
            except Exception:
                pass
        return list(set(stack))

    def scan(self) -> ProductCapabilityMap:
        caps = self.extract_from_readme()
        caps.extend(self.extract_from_changelog())
        caps.extend(self.extract_from_openapi())
        flag_files = list(self.root.rglob("feature_flags.json")) + list(self.root.rglob("features.json"))
        for f in flag_files[:3]:
            caps.extend(self.extract_from_feature_flags(f))
        return ProductCapabilityMap(capabilities=caps, tech_stack=self.infer_tech_stack())
