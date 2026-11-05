"""
build_test_pdf.py — Render tests/fixtures/sample_transcript.md to
tests/fixtures/sample_transcript.pdf using pypdf.

Usage (from repo root or plugin directory):
    uv run python3 plugins/grounded-synthesis/scripts/build_test_pdf.py

The PDF uses Helvetica (a standard Type1 font available in all PDF viewers).
Text is split into lines and paginated at PAGE_HEIGHT - 2*MARGIN.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

# Layout constants
PAGE_WIDTH = 612   # US Letter pts
PAGE_HEIGHT = 792
MARGIN = 50
FONT_SIZE = 10
LINE_HEIGHT = 14   # pts between baselines
CHARS_PER_LINE = 90  # rough wrap width for Helvetica 10pt


def _escape_pdf_string(text: str) -> bytes:
    """Escape a string for use in a PDF literal string object."""
    result = []
    for ch in text:
        code = ord(ch)
        if code > 127 or code < 32:
            # Replace non-ASCII / control chars with space
            result.append(b" ")
        elif ch in ("\\", "(", ")"):
            result.append(b"\\" + ch.encode("latin-1"))
        else:
            result.append(ch.encode("latin-1"))
    return b"".join(result)


def _wrap_line(line: str, width: int) -> list[str]:
    """Word-wrap a single line to at most `width` characters."""
    if len(line) <= width:
        return [line]
    words = line.split()
    wrapped: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).lstrip() if current else word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                wrapped.append(current)
            current = word
    if current:
        wrapped.append(current)
    return wrapped if wrapped else [line[:width]]


def _build_font_resource() -> DictionaryObject:
    """Return a /Resources dict with an embedded Helvetica Type1 font as /F1."""
    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_dict[NameObject("/Encoding")] = NameObject("/WinAnsiEncoding")

    resources = DictionaryObject()
    resources[NameObject("/Font")] = DictionaryObject(
        {NameObject("/F1"): font_dict}
    )
    return resources


def _render_lines_to_pages_absolute(lines: list[str]) -> list[bytes]:
    """
    Paginate using Tm (absolute text matrix) for each line — safer than
    chained Td offsets.
    """
    usable_height = PAGE_HEIGHT - 2 * MARGIN
    lines_per_page = int(usable_height // LINE_HEIGHT)

    pages: list[bytes] = []
    idx = 0
    while idx < len(lines):
        chunk = lines[idx : idx + lines_per_page]
        idx += lines_per_page

        ops: list[bytes] = [b"BT", f"/F1 {FONT_SIZE} Tf".encode()]
        y = PAGE_HEIGHT - MARGIN - LINE_HEIGHT
        for text_line in chunk:
            escaped = _escape_pdf_string(text_line)
            # Tm: [a b c d e f] — identity matrix with translation
            ops.append(f"1 0 0 1 {MARGIN} {y:.1f} Tm".encode())
            ops.append(b"(" + escaped + b") Tj")
            y -= LINE_HEIGHT
        ops.append(b"ET")
        pages.append(b"\n".join(ops))

    return pages if pages else [b"BT\nET"]


def build_pdf(source_md: Path, output_pdf: Path) -> None:
    """Read `source_md`, render to `output_pdf`."""
    raw_text = source_md.read_text(encoding="utf-8")

    # Expand each raw line with word-wrap
    wrapped_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        wrapped_lines.extend(_wrap_line(raw_line, CHARS_PER_LINE))

    content_streams = _render_lines_to_pages_absolute(wrapped_lines)
    resources = _build_font_resource()

    writer = PdfWriter()
    for stream_bytes in content_streams:
        page = writer.add_blank_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        cs = DecodedStreamObject()
        cs.set_data(stream_bytes)
        page.replace_contents(cs)
        page[NameObject("/Resources")] = resources

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf, "wb") as fh:
        writer.write(fh)

    # Verify the output is readable
    reader = PdfReader(str(output_pdf))
    total_chars = sum(len(p.extract_text() or "") for p in reader.pages)
    print(
        f"Wrote {output_pdf} — "
        f"{len(reader.pages)} page(s), {total_chars} chars extracted"
    )


def main() -> None:
    # Resolve paths relative to this script's location
    script_dir = Path(__file__).resolve().parent
    plugin_dir = script_dir.parent  # plugins/grounded-synthesis/
    source_md = plugin_dir / "tests" / "fixtures" / "sample_transcript.md"
    output_pdf = plugin_dir / "tests" / "fixtures" / "sample_transcript.pdf"

    if not source_md.exists():
        print(f"ERROR: source not found: {source_md}", file=sys.stderr)
        sys.exit(1)

    build_pdf(source_md, output_pdf)


if __name__ == "__main__":
    main()
