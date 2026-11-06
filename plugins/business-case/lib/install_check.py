"""The install check (spec 5.3): which map plugins this session can use, and where they are installed.

It reads the files Claude Code writes, as Claude Code 2.1.316 writes them:

- `<config>/plugins/installed_plugins.json`: `{"version": 2, "plugins": {"<name>@<marketplace>":
  [{"scope": "user" | "project" | "local", "projectPath" (project and local only), "installPath",
  "version", ...}]}}`;
- each scope's settings file, `"enabledPlugins": {"<name>@<marketplace>": true | false}`: managed (the
  `managed` path), local (`.claude/settings.local.json` at the main checkout's root only; a worktree's own
  file is not read), project (`.claude/settings.json` in the session's working directory) and user
  (`<config>/settings.json`). The first of these that holds a key decides it;
- for a key no settings file holds, `defaultEnabled`: the marketplace entry's (through
  `<config>/plugins/known_marketplaces.json`), else the installed `plugin.json`'s, else true.

Which entries count. A user entry always. A project entry whose `projectPath` equals the working
directory. A local entry whose `projectPath` equals the main checkout's root or the current worktree's
root: Task 2 measured (LOCAL_PROJECT_PATH_RULE) that a local install run from a linked worktree records
the worktree's own root, while Claude Code writes its enabling line to the main checkout's
settings.local.json. Each match is exact; a parent folder never counts. When one key has entries at
several scopes that count, the entry of the scope that wins (local, then project, then user) is used.

Each map plugin gets one of STATES. `too_old` also covers a coach-run map command with no questions list
in the install; a `coach_runs: false` command needs none, since no card ever sets its inputs. When the
managed settings are not a file this can read, the result also holds MANAGED_SCOPE as `not_checked`.
Two enabled keys of one name are `ambiguous` even when only one is new enough: both copies load, so the
dispatch name does not settle which one runs. Anything this cannot read gives `not_checked`, never
`not_installed`: a file that exists and cannot be read, an `installed_plugins.json` of another version
(the whole file) or a key whose value is not a list of objects (that plugin), and a git that fails (git
reporting "not a git repository" is the no-repository case, not a failure).

Python 3.9 syntax only.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from lib import paths, plugin_map, plugin_result

STATES = ("available", "too_old", "ambiguous", "disabled", "not_installed", "not_checked")
MANAGED_SCOPE = "managed scope"
INSTALLED_PLUGINS_VERSION = 2  # the installed_plugins.json shape this reads; any other is not_checked
SCOPE_ORDER = ("local", "project", "user")  # the scope that wins comes first


class _Unreadable(Exception):
    """A file that exists, or must exist, and cannot be read as JSON."""


class GitFailed(_Unreadable):
    """git ran and failed, or could not run: not the same as "outside a git repository"."""


def _git(cwd: Path, *args) -> Optional[Path]:
    """`git rev-parse --path-format=absolute <args>` as a path; None outside a git repository; GitFailed
    when git cannot run, times out, or fails another way (`--path-format` needs git 2.31). git runs with
    LC_ALL=C, so its "not a git repository" message is the English text matched below. The program is
    always `git` from PATH: nothing in the environment names another program."""
    env = {**os.environ, "LC_ALL": "C"}
    try:
        proc = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--path-format=absolute", *args],
                              capture_output=True, text=True, timeout=10, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitFailed(f"git could not run: {exc}") from None
    out = proc.stdout.strip()
    if proc.returncode == 0 and out:
        return Path(out)
    if proc.returncode == 128 and "not a git repository" in proc.stderr:
        return None
    raise GitFailed(f"git rev-parse {' '.join(args)} failed: exit {proc.returncode}: {proc.stderr.strip()[:200]}")


def _git_common_dir(cwd: Path) -> Optional[Path]:
    """`git rev-parse --git-common-dir`, absolute, or None outside a git repository; GitFailed otherwise."""
    return _git(cwd, "--git-common-dir")


def _git_toplevel(cwd: Path) -> Optional[Path]:
    """`git rev-parse --show-toplevel`: the current worktree's root, or None outside a git repository."""
    return _git(cwd, "--show-toplevel")


def config_dir() -> Path:
    """The Claude config folder: `$CLAUDE_CONFIG_DIR` when set, else `~/.claude`."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env) if env else Path.home() / ".claude"


def main_checkout_root(cwd: Path) -> Path:
    """The parent of the git common folder, or `cwd` outside a git repository."""
    common = _git_common_dir(Path(cwd))
    return common.parent if common is not None else Path(cwd)


def questions_path(install_path, command: str) -> Path:
    """`<install>/questions/<command part>.json`; `gtm:marketing:launch` gives `marketing-launch.json`."""
    return Path(install_path) / "questions" / f"{plugin_result.command_part(command)}.json"


def default_managed_path() -> Path:
    """Where Claude Code reads file-based managed settings on this platform. No environment variable moves
    it: a project's environment must not hide the admin's file."""
    if sys.platform == "darwin":
        return Path("/Library/Application Support/ClaudeCode/managed-settings.json")
    if sys.platform.startswith("win"):
        return Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "ClaudeCode" / "managed-settings.json"
    return Path("/etc/claude-code/managed-settings.json")


def _same(a, b) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except (OSError, RuntimeError, TypeError):
        return False


def _read_json(path: Path, *, required: bool) -> Optional[dict]:
    """The JSON object in `path`; None when it is absent and not required; _Unreadable otherwise. The
    read itself is the existence test: a folder that cannot be read, a symlink loop or a directory in the
    file's place raises OSError, which is _Unreadable, never "absent"."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        if not required:
            return None
        raise _Unreadable(f"{path}: {exc}") from None
    except (OSError, ValueError) as exc:
        raise _Unreadable(f"{path}: {exc}") from None
    if not isinstance(data, dict):
        raise _Unreadable(f"{path}: not a JSON object")
    return data


def _enabled_maps(paths) -> list:
    """The `enabledPlugins` object of each settings file that exists, in the order given."""
    maps = []
    for path in paths:
        data = _read_json(path, required=False)
        if data is not None:
            enabled = data.get("enabledPlugins", {})
            maps.append(enabled if isinstance(enabled, dict) else {})
    return maps


def _local_settings_path(cwd: Path, main: Path) -> Path:
    """The main checkout's file only (spec 5.3: "In a worktree, it uses the file at the main checkout's
    root"). A repository whose root is the home folder keeps it beside the project file."""
    if _same(main, Path.home()):
        return cwd / ".claude" / "settings.local.json"
    return main / ".claude" / "settings.local.json"


def _counts(entry: dict, cwd: Path, local_roots: list) -> bool:
    scope, project = entry.get("scope"), entry.get("projectPath")
    if scope == "user":
        return True
    if scope == "project":
        return project is not None and _same(project, cwd)
    if scope == "local":
        return project is not None and any(_same(project, root) for root in local_roots)
    return False


def _winning_entry(entries, cwd: Path, local_roots: list) -> Optional[dict]:
    counting = [e for e in entries if isinstance(e, dict) and _counts(e, cwd, local_roots)]
    for scope in SCOPE_ORDER:
        for entry in counting:
            if entry.get("scope") == scope:
                return entry
    return None


def _default_enabled(key: str, install_path, config: Path) -> bool:
    name, _, marketplace = key.partition("@")
    known = _read_json(config / "plugins" / "known_marketplaces.json", required=False) or {}
    location = (known.get(marketplace) or {}).get("installLocation") if isinstance(known.get(marketplace), dict) else None
    if location:
        listing = _read_json(Path(location) / ".claude-plugin" / "marketplace.json", required=False) or {}
        for plugin in listing.get("plugins", []) if isinstance(listing.get("plugins"), list) else []:
            if isinstance(plugin, dict) and plugin.get("name") == name and "defaultEnabled" in plugin:
                return plugin["defaultEnabled"] is not False
    if install_path:
        manifest = _read_json(Path(install_path) / ".claude-plugin" / "plugin.json", required=False) or {}
        if "defaultEnabled" in manifest:
            return manifest["defaultEnabled"] is not False
    return True


def _enabled(key: str, install_path, maps: list, config: Path) -> bool:
    for enabled in maps:
        if key in enabled:
            return enabled[key] is True
    return _default_enabled(key, install_path, config)


def _version(text) -> Optional[tuple]:
    try:
        return tuple(int(part) for part in str(text).split("."))
    except ValueError:
        return None


def _padded(a: tuple, b: tuple):
    """Both tuples at one length, so `1.10` compares equal to `1.10.0`."""
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)), b + (0,) * (n - len(b))


def _is_file(path: Path) -> bool:
    try:
        return paths.stat_is_file(path)
    except OSError as exc:
        raise _Unreadable(f"{path}: {exc}") from None


def _new_enough(m, name: str, entry: dict) -> bool:
    have, need = _version(entry.get("version")), _version(plugin_map.min_version(m, name))
    if have is None or need is None:
        return False
    have, need = _padded(have, need)
    if have < need:
        return False
    install = entry.get("installPath")
    return bool(install) and all(_is_file(questions_path(install, command))
                                 for command, spec in m["plugins"][name]["commands"].items() if spec["coach_runs"])


def _state(state: str, install_path=None, key=None) -> dict:
    return {"state": state, "install_path": install_path, "key": key}


def _plugin_state(m, name: str, installed: dict, maps: list, config: Path, cwd: Path, local_roots: list) -> dict:
    keys = sorted(k for k in installed if isinstance(k, str) and k.partition("@")[0] == name)
    counted = {}
    for key in keys:
        entries = installed[key]
        if not (isinstance(entries, list) and all(isinstance(e, dict) for e in entries)):
            raise _Unreadable(f"installed_plugins.json: {key} is not a list of objects")
        entry = _winning_entry(entries, cwd, local_roots)
        if entry is not None:
            counted[key] = entry
    if not counted:
        return _state("not_installed")
    enabled = {key: entry for key, entry in counted.items() if _enabled(key, entry.get("installPath"), maps, config)}
    if len(enabled) > 1:
        return _state("ambiguous")
    if not enabled:
        return _state("disabled", key=sorted(counted)[0])
    (key, entry), = enabled.items()
    state = "available" if _new_enough(m, name, entry) else "too_old"
    return _state(state, entry.get("installPath"), key)


def check(m, *, config_dir: Path, cwd: Path, managed: Optional[Path] = None) -> dict:
    """{plugin name: {"state", "install_path", "key"}} for each map plugin, plus MANAGED_SCOPE as
    `not_checked` when the managed settings are not a file this can read."""
    config, cwd = Path(config_dir), Path(cwd)
    result = {}
    maps = []
    managed_ok = False
    if managed is not None:
        try:
            data = _read_json(Path(managed), required=True)
            enabled = data.get("enabledPlugins", {})
            maps = [enabled if isinstance(enabled, dict) else {}]
            managed_ok = True
        except _Unreadable:
            maps = []
    try:
        data = _read_json(config / "plugins" / "installed_plugins.json", required=True)
        if data.get("version") != INSTALLED_PLUGINS_VERSION:
            raise _Unreadable(f"installed_plugins.json version {data.get('version')!r} is not {INSTALLED_PLUGINS_VERSION}")
        installed = data.get("plugins")
        if not isinstance(installed, dict):
            raise _Unreadable("installed_plugins.json holds no plugins object")
        main, toplevel = main_checkout_root(cwd), _git_toplevel(cwd)
        local_roots = [main] if toplevel is None else [main, toplevel]
        maps += _enabled_maps([_local_settings_path(cwd, main), cwd / ".claude" / "settings.json",
                               config / "settings.json"])
        for name in m["plugins"]:
            try:
                result[name] = _plugin_state(m, name, installed, maps, config, cwd, local_roots)
            except _Unreadable:
                result[name] = _state("not_checked")
    except _Unreadable:
        result = {name: _state("not_checked") for name in m["plugins"]}
    if not managed_ok:
        result[MANAGED_SCOPE] = _state("not_checked")
    return result
