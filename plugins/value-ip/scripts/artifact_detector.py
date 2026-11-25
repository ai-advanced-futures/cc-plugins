"""
Auto-detect artifacts in the current context.

Determines whether to run in RETROSPECTIVE mode (artifacts exist)
or GUARDIAN mode (new work in progress, no artifacts).
"""
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class AnalysisMode(Enum):
    RETROSPECTIVE = "retrospective"  # artifacts exist, analyze them
    GUARDIAN = "guardian"            # no artifacts, guard new work


class ArtifactType(Enum):
    PLAN = "plan"
    PRD = "prd"
    CODE = "code"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    MA_DILIGENCE = "ma_diligence"
    PLUGIN_OUTPUT = "plugin_output"


PLAN_KEYWORDS = {"plan", "implementation", "roadmap"}
PRD_KEYWORDS = {"prd", "requirements", "product-requirements"}
MA_KEYWORDS = {"diligence", "acquisition", "merger", "ma-"}
PLUGIN_OUTPUT_KEYS = {"competitors", "type", "jtbd", "forces", "value-analysis"}

SKIP_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', '.mypy_cache'}
# value-ip's own working and result folders, at the top of the search path only
WORK_DIRS = {'debate-context', 'output', '.value-ip'}


def _safe_read_json(file: Path) -> "dict | None":
    """Read and parse a JSON file, returning None on any error."""
    try:
        return json.loads(file.read_text(errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return None


@dataclass
class DetectedArtifact:
    path: Path
    artifact_type: ArtifactType
    content_preview: str


def detect_artifacts(search_path: Path) -> List[DetectedArtifact]:
    return ArtifactDetector(search_path=search_path).detect()


class ArtifactDetector:
    def __init__(self, search_path: Optional[Path] = None):
        self.search_path = search_path or Path.cwd()

    def detect(self) -> List[DetectedArtifact]:
        artifacts = []
        for file in self.search_path.rglob("*"):
            if any(skip in file.parts for skip in SKIP_DIRS):
                continue
            folders = file.relative_to(self.search_path).parts[:-1]
            if folders and folders[0] in WORK_DIRS:
                continue
            if not file.is_file():
                continue
            artifact = self._classify(file)
            if artifact:
                artifacts.append(artifact)
        return artifacts

    def determine_mode(self) -> AnalysisMode:
        return AnalysisMode.RETROSPECTIVE if self.detect() else AnalysisMode.GUARDIAN

    def _classify(self, file: Path) -> Optional[DetectedArtifact]:
        name_lower = file.name.lower()

        if file.suffix == ".json":
            return self._classify_json(file)

        if file.suffix not in {".md", ".txt", ".py", ".ts", ".js"}:
            return None

        content = file.read_text(errors="ignore")
        preview = content[:200] + ("…[truncated]" if len(content) > 200 else "")

        if any(kw in name_lower for kw in MA_KEYWORDS):
            return DetectedArtifact(file, ArtifactType.MA_DILIGENCE, preview)
        if any(kw in name_lower for kw in PRD_KEYWORDS):
            return DetectedArtifact(file, ArtifactType.PRD, preview)
        if any(kw in name_lower for kw in PLAN_KEYWORDS):
            return DetectedArtifact(file, ArtifactType.PLAN, preview)
        if file.suffix in {".py", ".ts", ".js"}:
            return DetectedArtifact(file, ArtifactType.CODE, preview)

        return None

    def _classify_json(self, file: Path) -> Optional[DetectedArtifact]:
        data = _safe_read_json(file)
        if data is not None and isinstance(data, dict) and any(k in data for k in PLUGIN_OUTPUT_KEYS):
            preview = str(list(data.keys()))[:200]
            return DetectedArtifact(file, ArtifactType.PLUGIN_OUTPUT, preview)
        return None
