#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Regex-based comment/docstring extraction for py/js/ts (no AST — YAGNI v0.1.0).

Emits the same Zone[] shape as zone_parser (source_surface="code"). Prose
inside code is always author="ai" (rewritable; code files carry no human
calibration zones). Ambiguous cases (triple-quoted strings not in docstring
position) are returned separately for the extraction-agent to resolve via
run-<id>/zone-mapping-decisions.json {zone_id: "include"|"exclude"}.

Also owns deterministic write-back (--reassemble): offset splicing identical
in structure to zone_parser.reassemble, so untouched code is byte-identical.
"""
import json
import re
from pathlib import Path

# Triple-quoted string immediately after a def/class/module start = docstring.
PY_DOCSTRING_RE = re.compile(
    r'(?:(?:^|\n)[ \t]*(?:def|class)[^\n]*:\n[ \t]*|\A)("""|\'\'\')(.*?)\1',
    re.DOTALL,
)
PY_TRIPLE_RE = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)
PY_COMMENT_RE = re.compile(r"(?:^|(?<=\n))[ \t]*#[^\n]*(?:\n[ \t]*#[^\n]*)*")
JS_LINE_RE = re.compile(r"(?:^|(?<=\n))[ \t]*//[^\n]*(?:\n[ \t]*//[^\n]*)*")
JS_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

EXTENSIONS = {".py": "py", ".js": "js", ".ts": "ts", ".jsx": "js", ".tsx": "ts"}


def _overlaps(start, end, claimed):
    """True if [start, end) intersects any (start, end) span in claimed."""
    return any(start < ce and end > cs for cs, ce in claimed)


def _zone(zid, src, m, text=None):
    return {
        "id": zid,
        "author": "ai",
        "start_offset": m.start() if text is None else m.start(2),
        "end_offset": m.end() if text is None else m.end(2),
        "text": text if text is not None else m.group(0),
        "start_line": src.count("\n", 0, m.start()) + 1,
        "end_line": src.count("\n", 0, m.end()) + 1,
        "source_surface": "code",
    }


def extract(path, decisions_path=None):
    """Returns (zones, ambiguities). With a decisions file, ambiguities resolved
    'include' become zones; 'exclude' (or unlisted... none) stay out; remaining
    unresolved ambiguities are returned for the extraction-agent."""
    path = Path(path)
    lang = EXTENSIONS.get(path.suffix)
    if lang is None:
        raise ValueError(f"unsupported code surface: {path.suffix}")
    # read_bytes + decode (no universal-newline translation): matches
    # zone_parser's on-disk-character offsets exactly, so reassembly stays
    # byte-identical regardless of which OS produced the source file.
    src = path.read_bytes().decode("utf-8")
    zones, ambiguities, n = [], [], 0

    if lang == "py":
        # Span masking: every triple-quoted string (docstring or ambiguous)
        # claims its FULL match span (quotes included), and the comment pass
        # skips any # match inside a claimed span. Without this, a `# line`
        # inside a docstring/string body becomes an overlapping zone and
        # reassemble() re-appends already-consumed text, corrupting output.
        doc_spans = set()
        claimed = []
        for m in PY_DOCSTRING_RE.finditer(src):
            n += 1
            doc_spans.add((m.start(2), m.end(2)))
            claimed.append((m.start(), m.end()))
            zones.append(_zone(f"z{n}-docstring", src, m, text=m.group(2)))
        for m in PY_TRIPLE_RE.finditer(src):
            if (m.start(2), m.end(2)) in doc_spans:
                continue
            n += 1
            claimed.append((m.start(), m.end()))
            ambiguities.append(_zone(f"z{n}-string", src, m, text=m.group(2)))
        for m in PY_COMMENT_RE.finditer(src):
            if _overlaps(m.start(), m.end(), claimed):
                continue
            n += 1
            zones.append(_zone(f"z{n}-comment", src, m))
    else:
        # Block comments claim their spans first; a `// line` inside a
        # /* ... */ block must not become a second, overlapping zone.
        claimed = []
        for m in JS_BLOCK_RE.finditer(src):
            n += 1
            claimed.append((m.start(), m.end()))
            zones.append(_zone(f"z{n}-block", src, m))
        for m in JS_LINE_RE.finditer(src):
            if _overlaps(m.start(), m.end(), claimed):
                continue
            n += 1
            zones.append(_zone(f"z{n}-comment", src, m))

    if decisions_path and Path(decisions_path).exists():
        decisions = json.loads(Path(decisions_path).read_text())
        still = []
        for a in ambiguities:
            if decisions.get(a["id"]) == "include":
                zones.append(a)
            elif decisions.get(a["id"]) != "exclude":
                still.append(a)
        ambiguities = still

    zones.sort(key=lambda z: z["start_offset"])
    return zones, ambiguities


def latest_rewrite(run_dir, zone_id, iteration):
    for i in range(iteration, 0, -1):
        cand = Path(run_dir) / "rewrites" / f"iter-{i}" / f"zone-{zone_id}.md"
        if cand.exists():
            return cand
    return None


def reassemble(original_path, run_dir, iteration, decisions_path=None):
    """Offset-splice latest rewrites into the code file. Same cascading rule as
    zone_parser.reassemble; untouched code byte-identical by construction."""
    original_path, run_dir = Path(original_path), Path(run_dir)
    # read_bytes + decode: same no-translation contract as extract() above,
    # so cursor offsets computed by extract() align with this src exactly.
    src = original_path.read_bytes().decode("utf-8")
    zones, _ = extract(original_path, decisions_path=decisions_path)
    parts, cursor = [], 0
    for z in zones:
        # Defense-in-depth: extract()'s span masking guarantees disjoint
        # zones, so this should never fire — but corruption must never be
        # silent if a future extraction path violates that invariant.
        if z["start_offset"] < cursor:
            raise ValueError(
                f"overlapping zones at offset {z['start_offset']} — "
                "refusing to splice (would corrupt output)"
            )
        parts.append(src[cursor:z["start_offset"]])
        rw = latest_rewrite(run_dir, z["id"], iteration)
        # Rewrite files are read via read_bytes().decode("utf-8") too, for the
        # same reason: consistent no-translation decoding keeps the
        # reassembled output byte-identical regardless of which OS produced
        # the rewrite file.
        parts.append(rw.read_bytes().decode("utf-8") if rw else src[z["start_offset"]:z["end_offset"]])
        cursor = z["end_offset"]
    parts.append(src[cursor:])
    out = run_dir / f"candidate-iter-{iteration}{original_path.suffix}"
    # write_bytes: no newline translation on write-back, matching the
    # read-side contract above.
    out.write_bytes("".join(parts).encode("utf-8"))
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Code prose extractor / reassembler")
    ap.add_argument("path")
    ap.add_argument("--reassemble", action="store_true")
    ap.add_argument("--run-dir")
    ap.add_argument("--iter", type=int, default=1)
    ap.add_argument("--decisions")
    ap.add_argument("--out", help="write the JSON to this file and print the "
                    "ambiguity count as the last line")
    args = ap.parse_args()
    if args.reassemble:
        if not args.run_dir:
            raise SystemExit("--reassemble requires --run-dir")
        print(reassemble(args.path, args.run_dir, args.iter, decisions_path=args.decisions))
    else:
        zones, amb = extract(args.path, decisions_path=args.decisions)
        text = json.dumps({"zones": zones, "ambiguities": amb}, indent=2)
        if args.out:
            Path(args.out).write_text(text)
            print(len(amb))
        else:
            print(text)
