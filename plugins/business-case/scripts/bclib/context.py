"""The check context: the parsed bundle and helpers that every rule uses."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bclib.bundle import read, read_registry, shown
from bclib.issues import Issue


@dataclass
class Ctx:
    root: Path
    dir: Path
    pages: dict
    registry: dict

    def shown(self, path) -> str:
        return shown(self.root, path)

    def ok(self) -> dict:
        return {p: pg for p, pg in self.pages.items() if not pg.error and pg.type}

    def live(self) -> dict:
        return {p: pg for p, pg in self.ok().items() if pg.live}

    def of_type(self, name) -> dict:
        return {p: pg for p, pg in self.live().items() if pg.type == name}

    def at(self, link):
        return self.pages.get(self.dir / link.lstrip("/"))

    def issue(self, level, rule, path, message, key=None) -> Issue:
        line = 1
        page = self.pages.get(path)
        if page is not None and key:
            for number, text in enumerate(page.head.splitlines(), 1):
                if text.startswith(f"{key}:"):
                    line = number
                    break
        return Issue(level, rule, message, self.shown(path), line)


def make(root, directory=None) -> Ctx:
    bundle = read(root, directory)
    return Ctx(Path(root), bundle.dir, bundle.pages, read_registry(root))
