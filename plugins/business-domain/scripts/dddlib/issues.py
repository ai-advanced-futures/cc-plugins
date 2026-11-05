"""One finding of `ddd.py check`."""
from dataclasses import dataclass
from pathlib import Path

ERROR = "ERROR"
WARN = "WARN"


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    path: Path
    line: int
    message: str

    def text(self, root: Path) -> str:
        try:
            shown = self.path.relative_to(root).as_posix()
        except ValueError:
            shown = str(self.path)
        return f"{self.level}: {shown}:{self.line} [{self.code}] {self.message}"
