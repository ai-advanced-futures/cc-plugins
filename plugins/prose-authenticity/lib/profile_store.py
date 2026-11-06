#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Load/validate/save voice profiles (ADR-004).

Profiles are USER DATA: they live in the user's project at
.prose-authenticity/profiles/<name>.yaml, never inside the plugin. The only
profile shipped with the plugin is config/default-profile.yaml (fallback).
Validation is stdlib presence/type checking against the shape documented in
config/voice-profile.schema.yaml — no jsonschema dependency."""
import re
from pathlib import Path

import yaml

PROFILE_NAME_RE = re.compile(r"[A-Za-z0-9_-]+")

REQUIRED = {
    "name": str,
    "version": int,
    "description": str,
    "banned_words": list,
    "favored_words": list,
    "cadence_rules": list,
    "exemplars": list,
}


class ProfileValidationError(ValueError):
    pass


def validate_profile(profile):
    for key, typ in REQUIRED.items():
        if key not in profile:
            raise ProfileValidationError(f"missing required key: {key}")
        if not isinstance(profile[key], typ):
            raise ProfileValidationError(
                f"{key}: expected {typ.__name__}, got {type(profile[key]).__name__}"
            )
    if not PROFILE_NAME_RE.fullmatch(profile["name"]):
        raise ProfileValidationError(
            f"invalid profile name {profile['name']!r} (allowed: letters, digits, hyphen, underscore)"
        )
    for i, ex in enumerate(profile["exemplars"]):
        if not isinstance(ex, dict) or "before" not in ex or "after" not in ex:
            raise ProfileValidationError(
                f"exemplars[{i}]: each exemplar needs 'before' and 'after'"
            )
    return profile


def load_profile(path):
    return validate_profile(yaml.safe_load(Path(path).read_text()))


def save_profile(profile, project_dir):
    """Write to <project_dir>/profiles/<name>.yaml (validated first)."""
    validate_profile(profile)
    d = Path(project_dir) / "profiles"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{profile['name']}.yaml"
    p.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True))
    return p


def resolve_profile(name, project_dir, plugin_root):
    """--profile <name> -> user profile path; None -> bundled default."""
    if name is None:
        return Path(plugin_root) / "config" / "default-profile.yaml"
    if not PROFILE_NAME_RE.fullmatch(name):
        raise ProfileValidationError(
            f"invalid profile name {name!r} (allowed: letters, digits, hyphen, underscore)"
        )
    p = Path(project_dir) / "profiles" / f"{name}.yaml"
    if not p.exists():
        raise ProfileValidationError(f"no profile named '{name}' at {p}")
    return p


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Voice profile store")
    ap.add_argument("cmd", choices=["validate", "resolve"])
    ap.add_argument("target", help="profile path (validate) or name|- (resolve)")
    ap.add_argument("--project-dir", default=".prose-authenticity")
    ap.add_argument("--plugin-root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    if args.cmd == "validate":
        load_profile(args.target)
        print("OK")
    else:
        name = None if args.target == "-" else args.target
        print(resolve_profile(name, args.project_dir, args.plugin_root))
