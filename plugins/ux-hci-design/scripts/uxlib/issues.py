"""The output contract of every linter (standard section 9)."""
from __future__ import annotations

import sys
from dataclasses import dataclass

ERROR, WARN, SKIP = "ERROR", "WARN", "SKIP"


@dataclass(frozen=True)
class Issue:
    level: str
    rule: str
    message: str
    file: str = ""
    line: int = 1

    def text(self) -> str:
        if self.level == SKIP:
            return f"SKIP: {self.rule} ({self.message})"
        return f"{self.level}: {self.file}:{self.line} [{self.rule}] {self.message}"


def report(issues, strict=False, out=None) -> int:
    out = out or sys.stdout
    for issue in sorted(issues, key=lambda i: (i.level == SKIP, i.file, i.line, i.rule, i.message)):
        print(issue.text(), file=out)
    errors = sum(1 for i in issues if i.level == ERROR)
    warnings = sum(1 for i in issues if i.level == WARN)
    print(f"{errors} errors, {warnings} warnings", file=out)
    return 1 if errors or (strict and warnings) else 0
