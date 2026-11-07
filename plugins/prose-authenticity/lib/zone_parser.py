#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Parse ai-check:zone HTML comment markers from a markdown file.

Marker format (unchanged from the ai-text-check toolkit that this plugin ports):
  <!-- ai-check:zone start name="intro" author="human" -->
  ... section text ...
  <!-- ai-check:zone end -->

Port changes vs. source: emits Zone dicts {id, author, start_offset,
end_offset, start_line, end_line, text, source_surface}; fails fast with
line numbers on malformed markers (protects L-027 — never guess zone
boundaries); unmarked docs become a single implicit ai zone.
"""
import re
from pathlib import Path

ZONE_START_RE = re.compile(
    r'<!--\s*ai-check:zone\s+start\s+name="([^"]+)"\s+author="([^"]+)"\s*-->'
)
ZONE_END_RE = re.compile(r"<!--\s*ai-check:zone\s+end\s*-->")
VALID_AUTHORS = {"human", "ai", "mixed"}
# Zone ids become path components (rewrites/iter-N/zone-<id>.md); a strict
# charset blocks path traversal via doc-supplied names.
ZONE_ID_RE = re.compile(r"[A-Za-z0-9_-]+")

# A fence opens on 3+ backticks or 3+ tildes with at most three leading spaces.
# It closes on a run of the SAME character, AT LEAST AS LONG, with nothing after
# it but whitespace. That is CommonMark, and it deliberately differs from
# prose_spans.FENCE_RE on three axes (run length, info string, indent charset).
# Aligning with prose_spans instead would break the four-backtick-outer /
# three-backtick-inner idiom, letting an example marker between the inner fences
# become a real exempt zone — Fault B surviving the fix.
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# A maximal run of backticks of any length. `+` is greedy, so it never splits a
# longer run. Restricting this to 1-2 backticks ("3+ is fence syntax") is wrong:
# CommonMark treats a 3-run in running text as an ordinary code span, and
# restricting it left prose showing marker syntax in triple backticks unmasked,
# so the guard fired on it. Nothing is risked by the wide rule — a fence-opening
# line is already a span bound, and code_mask feeds ONLY the guard.
INLINE_RUN_RE = re.compile(r"`+")


class ZoneParseError(ValueError):
    """Malformed zone markers. Fail fast — never guess boundaries (L-027)."""


def parse_zones(doc_path):
    # read_bytes + decode: no universal-newline translation, so offsets index
    # the on-disk characters exactly (CRLF preserved for faithful reassembly).
    src = Path(doc_path).read_bytes().decode("utf-8")
    lines = src.splitlines(keepends=True)
    line_offsets = []
    off = 0
    for ln in lines:
        line_offsets.append(off)
        off += len(ln)

    fenced = fenced_line_numbers(src)
    masked = code_mask(src, fenced)

    zones = []
    seen_ids = set()
    open_zone = None  # (id, author, start_line_idx)
    for i, line in enumerate(lines, 1):
        # Step 1: a fenced line contributes nothing — no marker, no guard. This
        # makes fenced_line_numbers the single authority on what a fence is, so
        # a later change to code_mask cannot silently alter which markers are
        # suppressed. A marker inside a fence is an example, never a real zone.
        if i in fenced:
            continue
        # Step 2: match the RAW line. Never the mask — spaces can CREATE a
        # match the source never held (the patterns use \s* and \s+), and \s
        # matches a newline, so a whole-source scan matches across a line wrap.
        ms = ZONE_START_RE.search(line)
        me = ZONE_END_RE.search(line)
        # Step 3: the guard's substring test reads the MASKED line, so prose
        # that merely mentions the syntax inside backticks never trips it. The
        # message quotes the RAW line, so an author sees what they wrote.
        if (ms is None and me is None
                and "<!--" in masked[i - 1] and "ai-check:zone" in masked[i - 1]):
            # Fail fast on malformed markers instead of silently ignoring them
            # (L-027 — a typo'd marker must never demote a zone to the implicit
            # whole_doc/ai fallback).
            raise ZoneParseError(
                f"line {i}: unrecognized ai-check:zone marker: {line.strip()!r}"
            )
        if ms:
            if open_zone is not None:
                raise ZoneParseError(
                    f"line {i}: nested zone start (zone '{open_zone[0]}' opened at "
                    f"line {open_zone[2]} is still open)"
                )
            zid = ms.group(1)
            if not ZONE_ID_RE.fullmatch(zid):
                raise ZoneParseError(
                    f"line {i}: invalid zone name {zid!r} "
                    "(allowed: letters, digits, hyphen, underscore)"
                )
            if zid in seen_ids:
                raise ZoneParseError(f"line {i}: duplicate zone name {zid!r}")
            seen_ids.add(zid)
            if ms.group(2) not in VALID_AUTHORS:
                raise ZoneParseError(
                    f"line {i}: invalid author '{ms.group(2)}' (must be human|ai|mixed)"
                )
            open_zone = (zid, ms.group(2), i)
        elif me:
            if open_zone is None:
                raise ZoneParseError(f"line {i}: zone end without a matching start")
            zid, author, start_marker_line = open_zone
            start_line = start_marker_line + 1      # content starts after the marker
            end_line = i - 1                        # content ends before the end marker
            start_offset = line_offsets[start_line - 1] if start_line <= len(lines) else len(src)
            end_offset = line_offsets[i - 1]        # up to the start of the end-marker line
            zones.append({
                "id": zid,
                "author": author,
                "start_line": start_line,
                "end_line": end_line,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "text": src[start_offset:end_offset],
                "source_surface": "markdown",
            })
            open_zone = None

    if open_zone is not None:
        raise ZoneParseError(
            f"line {open_zone[2]}: zone '{open_zone[0]}' never closed before EOF"
        )

    if not zones:
        zones = [{
            "id": "whole_doc",
            "author": "ai",  # implicit surface: rewritable, no calibration zone
            "start_line": 1,
            "end_line": len(lines),
            "start_offset": 0,
            "end_offset": len(src),
            "text": src,
            "source_surface": "markdown",
        }]
    return zones


def fenced_line_numbers(src):
    """1-based line numbers inside a CLOSED fenced block, opening and closing
    lines included. An unclosed opener defines no region, and the scan resumes
    on the line after it — resuming at EOF would let one stray opener hide every
    later fence, so a fenced example below it would stay real, and any real
    marker below it would silently vanish into the whole_doc/ai fallback."""
    lines = src.splitlines(keepends=True)
    fenced = set()
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        run = m.group(1)
        char, need = run[0], len(run)
        for j in range(i + 1, len(lines)):
            cm = FENCE_OPEN_RE.match(lines[j])
            if not cm:
                continue
            crun = cm.group(1)
            if crun[0] != char or len(crun) < need:
                continue
            if lines[j][cm.end():].strip():      # info string: not a closer
                continue
            fenced.update(range(i + 1, j + 2))   # 1-based, inclusive
            i = j + 1
            break
        else:
            i += 1                               # unclosed: resume next line
    return fenced


def code_mask(src, fenced=None):
    """Masked copies of src.splitlines(keepends=True) — one per source line,
    each the same length as its source line — with characters inside a fenced
    region or an inline code span replaced by a space. Line-break characters are
    never replaced, so the masked list can never desynchronise from the source
    list (str.splitlines breaks on \\r, \\x0c, \\x85 and more).

    Used ONLY by the malformed-marker guard. It must never decide whether a
    marker exists: spaces can CREATE a ZONE_START_RE match the raw source never
    held, because the pattern uses \\s* and \\s+."""
    lines = src.splitlines(keepends=True)
    # `fenced` is a pure function of src, so a caller that already has it (like
    # parse_zones) passes it in rather than paying for it twice.
    if fenced is None:
        fenced = fenced_line_numbers(src)
    # Body = the line without its trailing line-break characters, so masking can
    # never touch a break character and every masked line keeps its length.
    # Every character str.splitlines treats as a break, written as ESCAPES.
    # Two of them are U+2028 and U+2029, which are invisible in an editor and
    # in a diff; writing them literally made this line unreviewable.
    bodies = [ln.rstrip("\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")
              for ln in lines]
    tails = [ln[len(b):] for ln, b in zip(lines, bodies)]
    out = [" " * len(b) if (i + 1) in fenced else b for i, b in enumerate(bodies)]

    def bounded(i):
        """True when line i may not be crossed by an open span. Reads the fence
        PATTERN, not the region, so an unclosed opener still bounds a span."""
        return not bodies[i].strip() or FENCE_OPEN_RE.match(lines[i]) is not None

    i, col = 0, 0
    while i < len(lines):
        if (i + 1) in fenced or bounded(i):
            i, col = i + 1, 0
            continue
        m = INLINE_RUN_RE.search(bodies[i], col)
        if not m:
            i, col = i + 1, 0
            continue
        n = len(m.group(0))
        cj, cm = i, INLINE_RUN_RE.search(bodies[i], m.end())
        while True:
            if cm and len(cm.group(0)) == n:
                break
            if cm:
                cm = INLINE_RUN_RE.search(bodies[cj], cm.end())
                continue
            cj += 1
            if cj >= len(lines) or bounded(cj) or (cj + 1) in fenced:
                cj, cm = None, None
                break
            cm = INLINE_RUN_RE.search(bodies[cj])
        if cm is None:
            col = m.end()          # literal run; resume after it on this line
            continue
        if cj == i:
            out[i] = out[i][:m.start()] + " " * (cm.end() - m.start()) + out[i][cm.end():]
        else:
            out[i] = out[i][:m.start()] + " " * (len(bodies[i]) - m.start())
            for k in range(i + 1, cj):
                out[k] = " " * len(bodies[k])
            out[cj] = " " * cm.end() + out[cj][cm.end():]
        i, col = cj, cm.end()
    return [o + t for o, t in zip(out, tails)]


def get_baseline_zone(zones):
    """First zone marked author='human' (calibration ground truth), else None."""
    for z in zones:
        if z["author"] == "human":
            return z
    return None


def latest_rewrite(run_dir, zone_id, iteration):
    """Cascading selection: most recent rewrites/iter-1..N/zone-<id>.md, else None."""
    run_dir = Path(run_dir)
    for n in range(iteration, 0, -1):
        cand = run_dir / "rewrites" / f"iter-{n}" / f"zone-{zone_id}.md"
        if cand.exists():
            return cand
    return None


def reassemble(original_path, run_dir, iteration, suffix=".md"):
    """Rebuild the candidate draft: original frame + latest rewrite per ai/mixed
    zone. Human zones are copied from the original byte-for-byte by construction
    (they are part of the un-spliced frame) — the L-027 structural guarantee.

    The guarantee covers every marker that becomes a zone. A document whose own
    fences are mis-paired can suppress a real marker before it ever becomes one,
    and that text is then rewritable. See ADR-009's accepted residuals.
    Writes run_dir/candidate-iter-<N><suffix> and returns its Path."""
    original_path, run_dir = Path(original_path), Path(run_dir)
    # read_bytes + decode (no universal-newline translation): matches parse_zones's
    # on-disk-character offsets exactly, so CRLF docs reassemble byte-identically.
    src = original_path.read_bytes().decode("utf-8")
    zones = parse_zones(original_path)
    parts, cursor = [], 0
    for z in sorted(zones, key=lambda z: z["start_offset"]):
        parts.append(src[cursor:z["start_offset"]])
        rw = None if z["author"] == "human" else latest_rewrite(run_dir, z["id"], iteration)
        # Rewrite files are read via read_bytes().decode("utf-8") too, for the same
        # reason: consistent no-translation decoding keeps the reassembled output
        # byte-identical regardless of which OS produced the rewrite file.
        parts.append(rw.read_bytes().decode("utf-8") if rw else src[z["start_offset"]:z["end_offset"]])
        cursor = z["end_offset"]
    parts.append(src[cursor:])
    out = run_dir / f"candidate-iter-{iteration}{suffix}"
    out.write_bytes("".join(parts).encode("utf-8"))
    return out


if __name__ == "__main__":
    import argparse
    import json as _json
    import sys

    ap = argparse.ArgumentParser(description="Zone parser / candidate reassembler")
    ap.add_argument("doc")
    ap.add_argument("--reassemble", action="store_true")
    ap.add_argument("--run-dir")
    ap.add_argument("--iter", type=int, default=1)
    ap.add_argument("--out", help="write the zones JSON to this file and print 'zones=<n>'")
    args = ap.parse_args()
    if args.reassemble:
        if not args.run_dir:
            raise SystemExit("--reassemble requires --run-dir")
        print(reassemble(args.doc, args.run_dir, args.iter))
    else:
        zones = parse_zones(args.doc)
        if args.out:
            try:
                _out = Path(args.out)
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_text(_json.dumps(zones, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                print(_json.dumps({"error": "unwritable", "detail": str(exc)}), file=sys.stderr)
                raise SystemExit(3)
            print(f"zones={len(zones)}")
        else:
            print(_json.dumps(zones, indent=2))
