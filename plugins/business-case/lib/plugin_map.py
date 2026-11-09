"""The plugin map: which producer plugin command serves each business-case item (spec 5.2).

The data lives in `plugin-map/plugin-map-<MAP_VERSION>.json`. This module reads it and answers questions
about it. It holds no map data of its own. The file has these parts:

- `plugins`: each plugin's `min_version`, its `graph` when the plugin writes its results as a knowledge
  graph (`{name, save_script}`: the graph name of `.claude/knowledge.json`, and the save script of the
  plugin, relative to the plugin root; `lib/brain_read.py` reads a run of such a plugin through that
  script, and not from a result file), and its adopting `commands`. A command holds `route` (the
  agent to dispatch, `<plugin>:<route stem>`), `coach_runs`, `reads_from` (map commands whose results it
  reads through `inputs_from`), `kinds` (result kinds it produces), `phases` and `never_set` (inputs the
  coach never sets).
- `ceilings`: `{command, kind, max}` rows where the grade ceiling is lower than the sources give.
- `kinds`: each result kind, with the item ids it serves.
- `items`: each item's `owner`, `contributors`, `after` (the items whose results feed it) and
  `owns_inputs`.

`owns_inputs` has one shape: `{"<plugin:command>": ["<input>"]}`. The key is a map command and the list
holds the inputs of that command that the item owns. In 1.0.0 every item's `owns_inputs` is `{}`.

Python 3.9 syntax only.
"""
from __future__ import annotations

import json
from pathlib import Path

MAP_VERSION = "1.0.0"
SCHEMA = "business-case-plugin-map/1"

_MAP_DIR = Path(__file__).resolve().parent.parent / "plugin-map"


def check_owns_inputs(items) -> list:
    """The problems with the `owns_inputs` of each item, one line each. An empty list means the shape holds."""
    problems = []
    for item_id, spec in items.items():
        owned = spec.get("owns_inputs", {})
        if not isinstance(owned, dict):
            problems.append(f"{item_id}: owns_inputs must be an object of command to input list")
            continue
        for command, inputs in owned.items():
            ok = isinstance(inputs, list) and all(isinstance(i, str) for i in inputs)
            if not (isinstance(command, str) and ok):
                problems.append(f"{item_id}: owns_inputs[{command!r}] must be a list of input names")
    return problems


def load() -> dict:
    m = json.loads((_MAP_DIR / f"plugin-map-{MAP_VERSION}.json").read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA:
        raise ValueError(f"plugin map schema must be {SCHEMA}")
    if m.get("version") != MAP_VERSION:
        raise ValueError(f"plugin map version must be {MAP_VERSION}")
    problems = check_owns_inputs(m.get("items", {}))
    if problems:
        raise ValueError("; ".join(problems))
    return m


def commands(m) -> dict:
    """Every map command, by its canonical name, with its record."""
    return {name: spec for plugin in m.get("plugins", {}).values() for name, spec in plugin["commands"].items()}


def route(m, command) -> str:
    return commands(m)[command]["route"]


def reads_from(m, command) -> list:
    return list(commands(m)[command]["reads_from"])


def coach_runs(m, command) -> bool:
    return bool(commands(m)[command]["coach_runs"])


def never_set(m, command) -> frozenset:
    return frozenset(commands(m)[command]["never_set"])


def min_version(m, plugin) -> str:
    return m["plugins"][plugin]["min_version"]


def graph(m, plugin):
    """The `graph` object of a plugin that writes its results as a knowledge graph (`{name, save_script}`),
    or None for a plugin with no graph and for a name that is not in the map."""
    return m.get("plugins", {}).get(plugin, {}).get("graph")


def owner(m, item_id) -> str:
    return m["items"][item_id]["owner"]


def upstream(m, item_id) -> frozenset:
    """Every item reached through the order of work, directly or through other items."""
    seen = set()
    todo = list(m["items"][item_id]["after"])
    while todo:
        current = todo.pop()
        if current not in seen:
            seen.add(current)
            todo.extend(m["items"][current]["after"])
    return frozenset(seen)


def ceiling(m, command, kind):
    """The highest grade the map allows for this command and kind, or None when the map sets no ceiling."""
    for row in m.get("ceilings", []):
        if row["command"] == command and row["kind"] == kind:
            return row["max"]
    return None


def items_for_kind(m, kind) -> list:
    return list(m["kinds"].get(kind, []))


def analyst_items(m, analyst) -> list:
    return [i for i, spec in m["items"].items() if spec["owner"] == analyst]


def input_owner(m, command, input):
    """The item that owns this input of this command, or None."""
    for item_id, spec in m.get("items", {}).items():
        if input in spec.get("owns_inputs", {}).get(command, []):
            return item_id
    return None
