"""Build child settings without changing the parent process."""
from __future__ import annotations

import os
from collections.abc import Mapping

MODEL_ENV = ("ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
             "ANTHROPIC_DEFAULT_OPUS_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL")


def child_environment(claude_defaults: bool = False, source: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if source is None else source)
    env.pop("CLAUDECODE", None)
    if claude_defaults:
        env = {key: value for key, value in env.items()
               if not key.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_"))
               and key != "CLAUDE_CODE_SUBAGENT_MODEL"}
    return env


def claude_command(executable: str, claude_defaults: bool = False) -> list[str]:
    return [executable, "--setting-sources", ""] if claude_defaults else [executable]


def settings_record(claude_defaults: bool = False) -> dict:
    """Record the selected mode and model names, not credentials or URLs."""
    env = child_environment(claude_defaults)
    return {"claude_defaults": claude_defaults,
            "model_environment": {key: env[key] for key in MODEL_ENV if key in env}}
