#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Rhetorical-question gate (ADR-005).

Three pure functions — scan(), genre_signals(), evaluate() — plus the constants
that are the single source of truth for every consumer. No LLM, no network, no
judgment. The FAIL rule lives in evaluate() and nowhere else.

Fail-closed behaviour (candidates present but unadjudicated -> UNADJUDICATED)
is enforced one layer up, in run_detectors.py: a pure function cannot be
fail-closed about an argument it was never handed.
"""

import hashlib
import re
import unicodedata
from pathlib import Path

from verdicts import GATE_STATUSES  # dependency points question_gate -> verdicts

_PASS, _EXEMPT, _FAIL, _UNADJUDICATED = GATE_STATUSES

GENRES = ("expository", "literary", "verbatim")
EXEMPT_GENRES = ("literary", "verbatim")
GATED_GENRES = ("expository",)

ADJUDICATION_KEYS = ("genre", "genre_evidence", "candidates", "rewrites")

# The three labels the adjudicator may assign a candidate. The LLM adjudicator
# has no schema enforcement, so evaluate() rejects any candidate whose label is
# not one of these — a fail-closed control symmetric with _resolve_genre()'s
# unrecognized-genre -> "expository" fallback.
CANDIDATE_LABELS = ("rhetorical", "genuine", "quoted")

GENRE_SIGNAL_FAMILIES = ("speaker_label_lines", "timestamp_matches",
                         "disfluency_tokens", "transcript_heading")
STRONG_GENRE_SIGNALS = ("timestamp_matches", "transcript_heading")

assert set(GENRES) == set(EXEMPT_GENRES) | set(GATED_GENRES)   # coverage
assert not (set(EXEMPT_GENRES) & set(GATED_GENRES))            # disjointness
assert set(STRONG_GENRE_SIGNALS) < set(GENRE_SIGNAL_FAMILIES)  # proper subset


# A delimiter run is emphasis only if it opens or closes a span. CommonMark
# suppresses intraword `_`, so `run_detectors` keeps its underscore. We strip
# `*`/`~` runs adjacent to non-space, and `_` runs only at a word boundary.
_EMPH_STAR_TILDE = re.compile(r"(?<!\w)([*~]{1,3})(?=\S)|(?<=\S)([*~]{1,3})(?!\w)")
_EMPH_UNDERSCORE = re.compile(r"(?<!\w)(_{1,3})(?=\S)|(?<=\S)(_{1,3})(?!\w)")
_WS = re.compile(r"\s+")


def _normalize(text):
    """NFC -> strip emphasis delimiters -> collapse whitespace -> strip.

    Case is preserved. The emphasized words survive; only the delimiters go.
    """
    out = unicodedata.normalize("NFC", text)
    out = _EMPH_STAR_TILDE.sub("", out)
    out = _EMPH_UNDERSCORE.sub("", out)
    out = _WS.sub(" ", out)
    return out.strip()


ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "cf.", "vs.", "Dr.", "Mr.", "Mrs.",
                 "Ms.", "St.", "Fig.", "No.", "approx.")

_TERMINATOR_RUN = re.compile(r"[.!?]+")


def _is_real_terminator(text, run_start, run_end):
    """A `.` preceded by a digit (decimal) or belonging to an abbreviation is
    not a terminator. `!` and `?` always are."""
    run = text[run_start:run_end]
    if "?" in run or "!" in run:
        return True
    if run_start > 0 and text[run_start - 1].isdigit():
        return False
    # A `.` run mid-token (the internal dot of "e.g.", "v1.2") is not a sentence
    # break — only a period at end-of-text or before whitespace is. A backward
    # `endswith` check catches the closing dot of an abbreviation but never its
    # internal dots, so this forward guard completes the "belongs to an
    # abbreviation" intent (without it, "e.g." splits at its first dot).
    if run_end < len(text) and not text[run_end].isspace():
        return False
    tail = text[max(0, run_start - 12):run_end]
    return not any(tail.endswith(a) for a in ABBREVIATIONS)


def _sentence_spans(text):
    """Spans of sentences ending in a terminator run containing a `?`.

    A maximal run of [.!?] is a single terminator; the span ends at the LAST
    character of the run. NOT heuristics.split_sentences(): its `len > 4` filter
    drops "Why?".
    """
    spans, start = [], 0
    for m in _TERMINATOR_RUN.finditer(text):
        if not _is_real_terminator(text, m.start(), m.end()):
            continue
        end = m.end()
        if "?" in m.group(0):
            spans.append((start, end))
        start = end
        while start < len(text) and text[start].isspace():
            start += 1
    return spans


_FENCE = re.compile(r"^(```|~~~)")
_INLINE_CODE = re.compile(r"`[^`]*`")
_URL = re.compile(r"https?://\S+")
_LINK_TARGET = re.compile(r"\]\([^)]*\)")


def _mask_non_prose(line):
    """Blank out inline code, URLs and markdown link targets so their `?`
    characters cannot seed a candidate. Question marks in link TEXT survive."""
    for pat in (_INLINE_CODE, _URL, _LINK_TARGET):
        line = pat.sub(lambda m: " " * len(m.group(0)), line)
    return line


def _zone_of(line_no, zones):
    for z in zones:
        if z["start_line"] <= line_no <= z["end_line"]:
            return z
    return None


def content_hash(normalized):
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


# A speaker label may carry a leading timestamp: real transcript exports write
# `[00:14:22] SPEAKER_01: ...`. Without the optional prefix a heading-less
# export cites only `timestamp_matches` — one family — so evaluate()'s two-family
# guard would reject `verbatim`, the gate would enforce, and the humanizer would
# rewrite a speaker's words. That makes the record FALSE, not merely flatter.
# The prefix does not weaken the deliberate over-count on memos: `Note:` still
# matches, and neither STRONG family fires there.
SPEAKER_LABEL_RE = re.compile(
    r"^\s*(?:\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*)?"
    r"(?:[A-Z][A-Za-z0-9_ .-]{0,40}|SPEAKER_\d+):\s"
)
TIMESTAMP_RE = re.compile(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?")
TRANSCRIPT_HEADING_RE = re.compile(
    r"(?i)^#{1,6}\s*(transcript|call transcript|interview)\b")
DISFLUENCY_TOKENS = ("uh", "um", "er", "you know", "i mean", "like")

_WORD_BOUNDARY_DISFLUENCY = [
    re.compile(rf"(?i)(?<!\w){re.escape(t)}(?!\w)") for t in DISFLUENCY_TOKENS
]


def genre_signals(doc_path):
    """Deterministic, unit-testable signals the adjudicator cites as evidence.

    Two of the four families over-count on ordinary expository prose by design
    (`Note:` is a speaker label; `like` is a disfluency). evaluate()'s two-family
    guard is the compensating control: a `verbatim` citation must name at least
    one STRONG_GENRE_SIGNALS family, and neither fires on a memo.
    """
    src = Path(doc_path).read_bytes().decode("utf-8")
    lines = src.splitlines()
    return {
        "speaker_label_lines": sum(1 for ln in lines if SPEAKER_LABEL_RE.match(ln)),
        "timestamp_matches": len(TIMESTAMP_RE.findall(src)),
        "disfluency_tokens": sum(len(p.findall(src))
                                 for p in _WORD_BOUNDARY_DISFLUENCY),
        "transcript_heading": any(TRANSCRIPT_HEADING_RE.match(ln) for ln in lines),
    }


def scan(doc_path, zones):
    """Every `?`-terminated interrogative in the whole document, human zones
    included. Skips fenced blocks, inline code spans, URLs and link targets.

    Code surfaces are scanned too; evaluate() exempts them at step 1. A `?` on
    an executable line maps to no zone and carries zone_id/zone_author None.
    """
    src = Path(doc_path).read_bytes().decode("utf-8")
    candidates, in_fence, ordinal = [], False, {}
    for line_no, raw in enumerate(src.splitlines(), start=1):
        if _FENCE.match(raw.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = _mask_non_prose(raw)
        if "?" not in line:
            continue
        for start, end in _sentence_spans(line):
            # Span DISCOVERY runs on the masked `line` (a `?` inside inline
            # code / a URL cannot seed a candidate), but the excerpt and the
            # identity hash must share ONE provenance: both slice the RAW line.
            # Slicing `text` from the masked line erased the subject of the
            # question from the excerpt while the id still hashed the raw text.
            text = raw[start:end]
            if "?" not in text:
                continue
            norm = _normalize(text)
            zone = _zone_of(line_no, zones)
            zone_id = zone["id"] if zone else None
            h = content_hash(norm)
            key = (h, zone_id)
            ordinal[key] = ordinal.get(key, 0) + 1
            n = ordinal[key]
            cid = f"q-{h}" if n == 1 else f"q-{h}-{n}"
            candidates.append({
                "id": cid,
                "candidate_key": f"{cid}:{zone_id}",
                "text": text.strip(),
                "normalized_text": norm,
                "line": line_no,
                "col": start + 1,
                "zone_id": zone_id,
                "zone_author": zone["author"] if zone else None,
                "rewritable": bool(zone) and zone["author"] != "human",
            })
    return candidates


def _families_cited(evidence):
    """Which GENRE_SIGNAL_FAMILIES a citation list names. The check verifies that
    evidence was CITED, never that it is TRUE — a fabricating adjudicator is an
    accepted residual (see Risks)."""
    joined = " ".join(evidence or []).lower()
    return {f for f in GENRE_SIGNAL_FAMILIES if f in joined}


def _resolve_genre(adjudication, genre_override):
    """genre_override -> adjudication["genre"] -> "expository".

    Every EXEMPT_GENRES member must cite evidence or it falls back to expository.
    A `verbatim` citation must additionally name >= 2 families, at least one of
    them STRONG — `Note:` lines make speaker_label_lines fire on a board memo.
    """
    if genre_override in EXEMPT_GENRES:
        return genre_override, "cli_override"
    if not adjudication:
        return "expository", "default"
    claimed = adjudication.get("genre")
    if claimed not in EXEMPT_GENRES:
        return "expository", "default" if claimed != "expository" else "adjudicator"
    evidence = adjudication.get("genre_evidence") or []
    if not evidence:
        return "expository", "default"
    if claimed == "verbatim":
        cited = _families_cited(evidence)
        if len(cited) < 2 or not (cited & set(STRONG_GENRE_SIGNALS)):
            return "expository", "default"
    return claimed, "adjudicator"


def _result(status, genre, genre_source, cands, rhetorical, unrewritable,
            evidence, adjudicator_genre, override_applied, error):
    return {
        "status": status, "genre": genre, "genre_source": genre_source,
        "genre_evidence": evidence, "adjudicator_genre": adjudicator_genre,
        "genre_override_applied": override_applied,
        "candidates": cands, "rhetorical": rhetorical,
        "unrewritable": unrewritable,
        "rewritable_remaining": len(rhetorical) - len(unrewritable),
        "error": error,
    }


def evaluate(candidates, adjudication, genre_override=None,
             source_surface="markdown", gate_error=None):
    """Owns the FAIL rule. Pure: no path, no run_dir, no file I/O."""
    # 1. code surface
    if source_surface == "code":
        return _result(_EXEMPT, None, "code_surface", [], [], [], [], None,
                       False, gate_error)
    # 2. CLI override to an exempting genre — reached with adjudication=None
    if genre_override in EXEMPT_GENRES:
        return _result(_EXEMPT, genre_override, "cli_override", [], [], [], [],
                       (adjudication or {}).get("genre"), True, gate_error)
    # 3. genre resolution (evidence check lives here)
    genre, source = _resolve_genre(adjudication, genre_override)
    # 4. zero candidates
    if not candidates:
        return _result(_PASS, genre, source, [], [], [],
                       (adjudication or {}).get("genre_evidence") or [],
                       (adjudication or {}).get("genre"), False, gate_error)
    # 5. fail-closed: no adjudication, or any candidate unlabelled / mislabelled
    labels = (adjudication or {}).get("candidates") or {}
    if adjudication is None or any(
            c["candidate_key"] not in labels
            or labels[c["candidate_key"]] not in CANDIDATE_LABELS
            for c in candidates):
        return _result(_UNADJUDICATED, genre, source, [], [], [],
                       (adjudication or {}).get("genre_evidence") or [],
                       (adjudication or {}).get("genre"), False, gate_error)

    rewrites = adjudication.get("rewrites") or {}
    out = [dict(c, label=labels[c["candidate_key"]],
                proposed_rewrite=rewrites.get(c["candidate_key"]),
                original_line=None)
           for c in candidates]
    rhetorical = [c["candidate_key"] for c in out if c["label"] == "rhetorical"]
    unrewritable = [c["candidate_key"] for c in out
                    if c["label"] == "rhetorical" and not c["rewritable"]]

    if genre in EXEMPT_GENRES:
        status = _EXEMPT
    elif rhetorical:
        status = _FAIL
    else:
        status = _PASS
    return _result(status, genre, source, out, rhetorical, unrewritable,
                   adjudication.get("genre_evidence") or [],
                   adjudication.get("genre"), False, gate_error)


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path as _Path

    ap = argparse.ArgumentParser(description="Rhetorical-question gate scanner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("doc")
    p_scan.add_argument("--run-dir", required=True)
    p_scan.add_argument("--decisions", help="zone-mapping-decisions.json for code surfaces")
    args = ap.parse_args()

    _doc = _Path(args.doc)
    if _doc.suffix in (".md", ".txt", ""):
        import zone_parser
        _zones = zone_parser.parse_zones(_doc)
    else:
        import extract_prose
        _zones, _ = extract_prose.extract(_doc, decisions_path=args.decisions)

    _cands = scan(_doc, _zones)
    _run_dir = _Path(args.run_dir)
    _run_dir.mkdir(parents=True, exist_ok=True)
    (_run_dir / "candidates.json").write_text(json.dumps({
        "candidate_count": len(_cands),
        "candidates": _cands,
        "genre_signals": genre_signals(_doc),
    }, indent=2))
    print(f"{len(_cands)} candidates")
