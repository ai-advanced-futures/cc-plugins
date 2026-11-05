# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=6.21.4,<7.0.0"]
# ///
"""
source_loader.py — Load and validate source files for grounded-synthesis.

Used by: grounded-synthesis-orchestrator (via Bash CLI mode)
Replaces logic that would otherwise live in orchestrator agent prose.

CLI mode: uv run ${CLAUDE_PLUGIN_ROOT}/lib/source_loader.py --validate <path>
  Returns JSON-serialized SourceLoadResult to stdout.
  Exit 0 on status="ok", exit 1 on any non-ok status.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

# Ensure plugin root is on sys.path for CLI invocation (pytest sets pythonpath=. via pytest.ini;
# CLI invocation via `uv run ${CLAUDE_PLUGIN_ROOT}/lib/source_loader.py` may not have the plugin root on path).
_plugin_root = Path(__file__).resolve().parent.parent
if str(_plugin_root) not in sys.path:
    sys.path.insert(0, str(_plugin_root))

from lib.constants import ALLOWED_EXTENSIONS, MAX_SOURCE_TOKENS  # noqa: E402

# Map raw extensions → normalized source_type
_EXT_TO_TYPE: dict[str, str] = {
    ".md": "md",
    ".markdown": "md",
    ".txt": "txt",
    ".pdf": "pdf",
}


@dataclass(frozen=True)
class SourceLoadResult:
    """Result of loading a single source file.

    status values:
      ok              — file loaded successfully
      unreadable      — file exists but cannot be read (permissions, encoding)
      encrypted_pdf   — PDF is encrypted / password-protected
      empty           — file exists but contains no extractable text
      unsupported_format — extension not in ALLOWED_EXTENSIONS
      too_large       — estimated tokens exceed MAX_SOURCE_TOKENS (145_000; leaves 5K headroom under 150K critical context per pipeline-review)

    source_type is one of ("md", "txt", "pdf") or None on non-ok statuses.
    .markdown files are normalized to source_type="md".

    estimated_tokens is populated for ok and too_large statuses; None otherwise.
    """

    source_path: str
    status: Literal["ok", "unreadable", "encrypted_pdf", "empty", "unsupported_format", "too_large"]
    text: str  # empty string on non-ok statuses
    error_message: str | None = None
    source_type: Literal["md", "txt", "pdf"] | None = None
    estimated_tokens: int | None = None  # populated for ok and too_large statuses


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_tokens(path: str, text: str, source_type: str) -> SourceLoadResult | None:
    """Return a too_large SourceLoadResult if text exceeds MAX_SOURCE_TOKENS, else None.

    Extracted shared helper used by both _load_text and _load_pdf to guarantee
    identical return contracts and eliminate the duplicated token-check logic.
    """
    estimated_tokens = len(text) // 4
    if estimated_tokens > MAX_SOURCE_TOKENS:
        return SourceLoadResult(
            source_path=path,
            status="too_large",
            text="",
            error_message=(
                f"Estimated tokens {estimated_tokens} exceeds MAX_SOURCE_TOKENS {MAX_SOURCE_TOKENS}"
            ),
            source_type=source_type,  # type: ignore[arg-type]
            estimated_tokens=estimated_tokens,
        )
    return None


def load_source(path: str) -> SourceLoadResult:
    """Load and validate a source file at the given path.

    Supports .md, .markdown (normalized to md), .txt, .pdf (via pypdf).
    Returns a frozen SourceLoadResult dataclass.
    """
    ext = Path(path).suffix.lower()

    # --- Unsupported extension check ---
    if ext not in ALLOWED_EXTENSIONS:
        return SourceLoadResult(
            source_path=path,
            status="unsupported_format",
            text="",
            error_message=f"Unsupported file extension {ext!r}; allowed: {ALLOWED_EXTENSIONS}",
            source_type=None,
            estimated_tokens=None,
        )

    source_type = _EXT_TO_TYPE[ext]

    # --- PDF branch ---
    if ext == ".pdf":
        return _load_pdf(path, source_type)

    # --- Text branches (.md, .markdown, .txt) ---
    return _load_text(path, source_type)


def _load_text(path: str, source_type: str) -> SourceLoadResult:
    """Load a plain-text file (.md, .markdown, .txt)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return SourceLoadResult(
            source_path=path,
            status="unreadable",
            text="",
            error_message=str(exc),
            source_type=None,
            estimated_tokens=None,
        )

    if not text.strip():
        return SourceLoadResult(
            source_path=path,
            status="empty",
            text="",
            source_type=None,
            estimated_tokens=None,
        )

    too_large = _check_tokens(path, text, source_type)
    if too_large is not None:
        return too_large

    return SourceLoadResult(
        source_path=path,
        status="ok",
        text=text,
        source_type=source_type,  # type: ignore[arg-type]
        estimated_tokens=len(text) // 4,
    )


def _load_pdf(path: str, source_type: str) -> SourceLoadResult:
    """Load a PDF file via pypdf."""
    try:
        import pypdf  # local import so the rest of the module works without pypdf installed
    except ImportError as exc:
        return SourceLoadResult(
            source_path=path,
            status="unreadable",
            text="",
            error_message=f"pypdf not installed: {exc}",
            source_type=None,
            estimated_tokens=None,
        )

    try:
        reader = pypdf.PdfReader(path)
    except Exception as exc:
        return SourceLoadResult(
            source_path=path,
            status="unreadable",
            text="",
            error_message=str(exc),
            source_type=None,
            estimated_tokens=None,
        )

    # Check encryption BEFORE trying to extract text
    if reader.is_encrypted:
        return SourceLoadResult(
            source_path=path,
            status="encrypted_pdf",
            text="",
            error_message="PDF is encrypted or password-protected",
            source_type=None,
            estimated_tokens=None,
        )

    # Per-page accumulation with early bail — avoids loading all pages into memory
    # when the document already exceeds MAX_SOURCE_TOKENS.
    try:
        parts: list[str] = []
        accumulated_chars = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
            accumulated_chars += len(page_text)
            if accumulated_chars // 4 > MAX_SOURCE_TOKENS:
                # Already over budget — bail early; no need to read remaining pages.
                estimated_tokens = accumulated_chars // 4
                return SourceLoadResult(
                    source_path=path,
                    status="too_large",
                    text="",
                    error_message=(
                        f"Estimated tokens {estimated_tokens} exceeds "
                        f"MAX_SOURCE_TOKENS {MAX_SOURCE_TOKENS}"
                    ),
                    source_type=source_type,  # type: ignore[arg-type]
                    estimated_tokens=estimated_tokens,
                )
        text = "\n".join(parts)
    except Exception as exc:
        return SourceLoadResult(
            source_path=path,
            status="unreadable",
            text="",
            error_message=str(exc),
            source_type=None,
            estimated_tokens=None,
        )

    if not text.strip():
        return SourceLoadResult(
            source_path=path,
            status="empty",
            text="",
            source_type=None,
            estimated_tokens=None,
        )

    return SourceLoadResult(
        source_path=path,
        status="ok",
        text=text,
        source_type=source_type,  # type: ignore[arg-type]
        estimated_tokens=len(text) // 4,
    )


if __name__ == "__main__":
    # CLI mode: python3 lib/source_loader.py --validate <path>
    # Returns JSON-serialized SourceLoadResult to stdout.
    # Exit 0 on status="ok", exit 1 on any non-ok status.
    parser = argparse.ArgumentParser(description="Validate a source file for grounded-synthesis.")
    parser.add_argument("--validate", required=True, metavar="PATH", help="Path to the source file.")
    args = parser.parse_args()

    result = load_source(args.validate)
    print(json.dumps(asdict(result)))
    sys.exit(0 if result.status == "ok" else 1)
