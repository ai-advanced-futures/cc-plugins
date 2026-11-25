"""
Pipeline state machine and YOLO configuration for value-ip plugin.

PipelineState: writes .value-ip-state.json at each phase transition.
               Survives context window compaction — state always on disk.

PipelineConfig: reads config/pipeline-defaults.json for YOLO/auto mode.
                Falls back to DEFAULTS when no config file exists.
"""
import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class PipelineState:
    """Durable phase tracker persisted to .value-ip-state.json."""

    PHASES = ["INIT", "FRAMEWORK_ANALYSIS", "DEBATE", "SYNTHESIS", "COMPLETE", "CHALLENGE", "GUARD"]

    DEFAULT_STATE: dict = {
        "version": "1.1.0",
        "phase": "INIT",
        "round": 0,
        "max_rounds": 4,
        "artifact_path": None,
        "artifact_type": None,
        "framework_results": {
            "helmer": "pending",
            "blue_ocean": "pending",
            "christensen": "pending",
            "moore": "pending",
        },
        "unresolved_tensions": [],
        "auto_mode": False,
        "started_at": None,
        "updated_at": None,
    }

    def __init__(self, state_file: Path = Path(".value-ip-state.json")) -> None:
        self.state_file = Path(state_file)

    def load(self) -> dict:
        """Read state from disk. Returns DEFAULT_STATE copy if file absent."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return copy.deepcopy(self.DEFAULT_STATE)

    def save(self, state: dict) -> None:
        """Write state to disk atomically. Always sets updated_at to current UTC time."""
        out = {**state, "updated_at": datetime.now(timezone.utc).isoformat()}
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(out, indent=2))
        os.replace(tmp, self.state_file)

    def update(self, **kwargs) -> dict:
        """Load, merge kwargs, save, and return updated state."""
        if "phase" in kwargs and kwargs["phase"] not in self.PHASES:
            raise ValueError(f"Invalid phase: {kwargs['phase']!r}. Must be one of {self.PHASES}")
        state = self.load()
        state.update(kwargs)
        self.save(state)
        return state

    def reset(self) -> dict:
        """Write DEFAULT_STATE with started_at set. Returns reset state."""
        state = copy.deepcopy(self.DEFAULT_STATE)
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        self.save(state)
        return state


class PipelineConfig:
    """Reads config/pipeline-defaults.json for YOLO/auto mode settings."""

    DEFAULTS: dict = {
        "auto_mode": False,
        "auto_answers": {
            "artifact_selection": "auto-detect",
            "multiple_artifacts_policy": "ask",
            "continue_rounds_policy": "stop_if_no_tensions",
            "framework_failure_policy": "skip_and_continue",
            "commit_output": False,
            "output_format": "both",
        },
        "pipeline": {"max_rounds": 4, "min_rounds": 2},
    }

    def __init__(
        self, config_file: Path = Path("config/pipeline-defaults.json")
    ) -> None:
        config_file = Path(config_file)
        if config_file.exists():
            self._data = json.loads(config_file.read_text())
        else:
            self._data = copy.deepcopy(self.DEFAULTS)

    def get(self, key: str, default=None):
        """Access config by dot-path (e.g. 'auto_answers.commit_output')."""
        parts = key.split(".")
        node = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node
