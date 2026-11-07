# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""ASD-STE100 conformance checker.

A separate check from the AI-detection tiers in run_detectors.py. Those tiers
score the probability that a machine wrote the text. This module scores
conformance to a rule set. The two measure different things, so they never
share a scale. See ADR-006.

Exit codes: 0 pass / 1 warn / 2 fail / 3 usage-or-operational error.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import zone_parser
from prose_spans import (  # noqa: F401 - re-exported for existing callers
    BLOCKQUOTE_RE,
    BULLET_RE,
    FENCE_RE,
    HEADING_RE,
    HTML_COMMENT_RE,
    INLINE_CODE_RE,
    ORDERED_RE,
    ProseLine,
    checked_spans,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "ste_checker needs PyYAML. Start it with:\n"
        "    uv run ${CLAUDE_PLUGIN_ROOT}/lib/ste_checker.py <document>\n"
        "or install PyYAML with:\n"
        "    pip install -r requirements-dev.txt"
    ) from exc

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "ste.yaml"


class ConfigError(Exception):
    """The config file is missing, cannot be parsed, or lacks a required key."""


# Every scalar a rule reads with `cfg[...]`. A config without one of these
# raised KeyError out of the rule, which no handler caught, so an operational
# error reported itself as exit 1 — indistinguishable from a WARN verdict.
# The word lists are read with `cfg.get(...)` and stay optional.
REQUIRED_CONFIG_KEYS = (
    "r1_warn_words", "r1_fail_words", "r2_max_sentences", "r7_stdev_floor",
)

# Keys a rule compares against a number. Presence was validated; type was not,
# so `r7_stdev_floor: "4.0"` reached `spread >= "4.0"` and raised TypeError
# mid-rule, which no handler caught — the process exited 1, and a caller reading
# "1 = warn and continue" treats a crashed run as passing with warnings.
INT_CONFIG_KEYS = ("r1_warn_words", "r1_fail_words", "r2_max_sentences")
NUMBER_CONFIG_KEYS = ("r7_stdev_floor",)

# Keys a rule iterates as a list of words or phrases. PyYAML's SafeLoader
# resolves a bare yes/no/y/n/true/false/on/off to a Python bool under YAML 1.1,
# so an unquoted entry reached `w.lower()` and raised AttributeError — the same
# fail-open. config/ste.yaml documents the hazard in its own comment.
LIST_CONFIG_KEYS = (
    "banned_part_a", "banned_part_b", "exempt_terms",
    "sentence_abbreviations", "sentence_abbreviations_ambiguous",
    "r4_be_forms", "r5_determiners", "r6_function_words",
)


def _validate_types(cfg, cfg_path):
    """Every declared key holds a value of the type its rule assumes.

    Validating at load time fails with one clear message naming the key, instead
    of surfacing as a TypeError or AttributeError from inside a rule. `bool` is
    excluded explicitly from the numeric checks: it is an `int` subclass in
    Python, so `r2_max_sentences: yes` would otherwise pass as 1.
    """
    for key in INT_CONFIG_KEYS:
        value = cfg.get(key)
        if key in cfg and (isinstance(value, bool) or not isinstance(value, int)):
            raise ConfigError(
                f"{key} must be a whole number, got {type(value).__name__}: {cfg_path}")
    for key in NUMBER_CONFIG_KEYS:
        value = cfg.get(key)
        if key in cfg and (isinstance(value, bool)
                           or not isinstance(value, (int, float))):
            raise ConfigError(
                f"{key} must be a number, got {type(value).__name__}: {cfg_path}")
    for key in LIST_CONFIG_KEYS:
        if key not in cfg:
            continue
        value = cfg[key]
        if not isinstance(value, list):
            raise ConfigError(
                f"{key} must be a list, got {type(value).__name__}: {cfg_path}")
        for item in value:
            if not isinstance(item, str):
                raise ConfigError(
                    f"{key} holds a non-string entry ({item!r}, "
                    f"{type(item).__name__}). Quote it: {cfg_path}")


def load_config(path=None):
    """Read ste.yaml. `path` defaults to a module-relative location, so the
    default works from any current directory. An explicit path is used as
    given."""
    cfg_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        raw = cfg_path.read_text()
    except OSError as exc:
        raise ConfigError(f"cannot read config: {cfg_path}") from exc
    try:
        cfg = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigError(f"cannot parse config: {cfg_path}") from exc
    if not isinstance(cfg, dict):
        raise ConfigError(f"config is not a mapping: {cfg_path}")
    missing = [k for k in REQUIRED_CONFIG_KEYS if k not in cfg]
    if missing:
        raise ConfigError(
            f"config is missing {', '.join(missing)}: {cfg_path}")
    _validate_types(cfg, cfg_path)
    return cfg


def paragraphs(prose_lines):
    """Group (lineno, text) into paragraph units.

    A unit ends at a blank line, at the start of the next list item, and at a
    heading — a heading is its own unit and never merges with the body text
    below it, whether or not a blank line separates them. A list item is its
    own unit, because a vertical list is the practice the STE skill mandates
    for complex information, and merging the items turned that practice into a
    false R2 paragraph-length failure.
    """
    para, out = [], []
    for lineno, text in prose_lines:
        if not text.strip():
            if para:
                out.append(para)
                para = []
            continue
        if getattr(text, "starts_block", False) and para:
            out.append(para)
            para = []
        para.append((lineno, text))
        if getattr(text, "is_heading", False):
            out.append(para)
            para = []
    if para:
        out.append(para)
    return out


def _join_paragraph(para):
    """One paragraph joined into a single string, plus the offset table that
    maps a position in that string back to the line it came from.

    Returns (text, [(offset, lineno, line_text)]).
    """
    buf, starts = "", []
    for lineno, text in para:
        piece = text.strip()
        if buf:
            buf += " "
        starts.append((len(buf), lineno, text))
        buf += piece
    return buf, starts


def _locate(starts, offset):
    """(lineno, line_text) for the line that holds `offset` in the joined text."""
    lineno, text = starts[0][1], starts[0][2]
    for start_off, ln, tx in starts:
        if start_off <= offset:
            lineno, text = ln, tx
        else:
            break
    return lineno, text


INITIAL_RE = re.compile(r"(?:^|[\s(\[])[A-Za-z]\.$")

_ABBREVIATIONS_CACHE = None

NEVER_FINAL = "never"
AMBIGUOUS = "ambiguous"


def _abbreviations(cfg):
    """(never_final, ambiguous) — the two abbreviation lists.

    `sentence_abbreviations` holds abbreviations that can never close a
    sentence, so the period after one is never a boundary.
    `sentence_abbreviations_ambiguous` holds abbreviations that routinely DO
    close a sentence, so the period after one needs a look at what follows.

    Read from `cfg` when the caller has one, otherwise from the default config,
    cached — both lists are linguistic data and live in config/ste.yaml like
    every other word list here.
    """
    global _ABBREVIATIONS_CACHE
    source = cfg
    if source is None:
        if _ABBREVIATIONS_CACHE is None:
            _ABBREVIATIONS_CACHE = load_config()
        source = _ABBREVIATIONS_CACHE
    return (source.get("sentence_abbreviations", []),
            source.get("sentence_abbreviations_ambiguous", []))


def _matches_abbreviation(text, abbreviations):
    """True when `text` ends in one of `abbreviations` on a token boundary.

    An entry that contains an uppercase letter (`Ms.`, `Dr.`, `Inc.`) matches
    case-sensitively; an entry that is entirely lowercase (`e.g.`, `etc.`)
    keeps matching case-insensitively. Comparing everything lowercased made
    the honorific `Ms.` match the SI unit `ms.` unconditionally, with no
    lookahead — and moving `Ms.` to the ambiguous list cannot fix that,
    because the lookahead only sees the case of what follows the period,
    which is uppercase in both `20 ms. The p99...` and `Ms. Smith...`. The
    case of the abbreviation itself is what tells them apart.
    """
    for abbr in abbreviations:
        if abbr == abbr.lower():
            candidate, needle = text.lower(), abbr.lower()
        else:
            candidate, needle = text, abbr
        if candidate.endswith(needle):
            before = candidate[:len(candidate) - len(needle)]
            if not before or not (before[-1].isalnum() or before[-1] in "-'"):
                return True
    return False


def _terminal_abbreviation(text, never_final, ambiguous):
    """Classify the period that closes `text`.

    Returns `NEVER_FINAL` when the period closes an abbreviation that cannot end
    a sentence, `AMBIGUOUS` when it closes one that often does, and None when
    `text` does not end in an abbreviation at all.

    A single-letter initial is ambiguous in general ("We prefer option A." ends
    a sentence; "J. Smith" does not), so it resolves by position: an initial
    that opens the text, or that follows another abbreviation or initial, is
    part of a name chain and never final. An initial that follows ordinary words
    is ambiguous and the caller must look at what comes next.
    """
    stripped = text.rstrip()
    if _matches_abbreviation(stripped, never_final):
        return NEVER_FINAL
    if _matches_abbreviation(stripped, ambiguous):
        return AMBIGUOUS
    m = INITIAL_RE.search(stripped)
    if m is None:
        return None
    before = stripped[:m.start()].rstrip()
    if not before or _terminal_abbreviation(before, never_final, ambiguous):
        return NEVER_FINAL
    return AMBIGUOUS


def _opens_a_new_sentence(following):
    """True when `following` — the text after a whitespace separator — reads as
    the start of a new sentence: it is empty, or its first character is neither
    lowercase nor a digit."""
    first = following[:1]
    if not first:
        return True
    return not (first.islower() or first.isdigit())


def _split_on_terminators(buf, never_final, ambiguous=()):
    """`buf` cut after every `.`, `!` or `?` that ends a sentence. Each piece is
    a verbatim substring of `buf`, so the caller can still locate its offset.

    A never-final abbreviation absorbs the separator unconditionally. An
    ambiguous one absorbs it only when what follows does not open a new
    sentence: merging unconditionally swallowed every real boundary after
    `etc.`, `No.`, `Inc.`, `Ltd.` and a trailing initial, which joined two
    sentences into one — a false R1 FAIL, an undercounted R2 paragraph, and an
    inflated R7 spread that stopped R7 from firing.
    """
    parts = re.split(r"((?<=[.!?])\s+)", buf)
    pieces, current = [], ""
    for i in range(0, len(parts), 2):
        current += parts[i]
        separator = parts[i + 1] if i + 1 < len(parts) else ""
        if separator:
            kind = _terminal_abbreviation(current, never_final, ambiguous)
            following = parts[i + 2] if i + 2 < len(parts) else ""
            if kind == NEVER_FINAL or (
                    kind == AMBIGUOUS and not _opens_a_new_sentence(following)):
                current += separator
                continue
        pieces.append(current)
        current = ""
    if current:
        pieces.append(current)
    return pieces


def split_sentences_with_lines(prose_lines, cfg=None):
    """[(starting_lineno, sentence_text)] across every paragraph.

    heuristics.split_sentences is not reused: it collapses the document to a
    single line, which destroys the line numbers the finding schema needs, and
    it drops fragments under five characters.

    A fragment counts as a sentence only when it ends in `.`, `!`, or `?`.
    [inferred] A heading survives prose extraction as bare text with its `#`
    stripped, and it carries no terminal punctuation, so this keeps a heading
    from being treated as a one-word sentence that skews R1, R2, and R7's
    statistics. R3 still scans headings directly, because it reads
    prose_lines rather than this function's output.
    """
    never_final, ambiguous = _abbreviations(cfg)
    results = []
    for para in paragraphs(prose_lines):
        buf, starts = _join_paragraph(para)
        pos = 0
        for sentence in _split_on_terminators(buf, never_final, ambiguous):
            sentence = sentence.strip()
            if not sentence:
                continue
            off = buf.find(sentence, pos)
            pos = off + len(sentence)
            if sentence[-1] not in ".!?":
                continue
            results.append((_locate(starts, off)[0], sentence))
    return results


# Counting. STE counts a numeral as a word, so a numeric-dense sentence used to
# run over the cap unreported ("Deploy 3 clusters in 2 regions" counted 4).
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")

# Grammatical position. R4, R5 and R6 match tokens against word lists that hold
# no numerals, and they read adjacency rather than length: "was 2019 revised" is
# still passive, and "the 3 states" is still a noun position. They keep the
# letter-only stream instead of inheriting the counting one.
GRAMMAR_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def word_count(text):
    return len(WORD_RE.findall(text))


def finding(rule, severity, line, excerpt, message):
    return {
        "rule": rule,
        "severity": severity,
        "line": line,
        "excerpt": excerpt[:120],
        "message": message,
    }


def rule_r1(sentences, cfg):
    """Sentence length. WARN above the warn cap, FAIL above the fail cap."""
    warn_cap = cfg["r1_warn_words"]
    fail_cap = cfg["r1_fail_words"]
    out = []
    for lineno, sentence in sentences:
        count = word_count(sentence)
        if count > fail_cap:
            out.append(finding(
                "R1", "FAIL", lineno, sentence,
                f"Sentence is {count} words. The cap is {fail_cap}."))
        elif count > warn_cap:
            out.append(finding(
                "R1", "WARN", lineno, sentence,
                f"Sentence is {count} words. The cap for instructions is {warn_cap}."))
    return out


def rule_r2(prose_lines, cfg):
    """Paragraph length in sentences."""
    limit = cfg["r2_max_sentences"]
    out = []
    for para in paragraphs(prose_lines):
        sentences = split_sentences_with_lines(para, cfg)
        if len(sentences) > limit:
            lineno = para[0][0]
            out.append(finding(
                "R2", "FAIL", lineno, para[0][1],
                f"Paragraph has {len(sentences)} sentences. The limit is {limit}."))
    return out


def _phrase_pattern(term):
    """Whole-token, case-insensitive. Hyphens are literal; the space between
    two words of a phrase matches any run of whitespace, so a phrase that the
    author hard-wrapped across two lines still matches."""
    body = r"\s+".join(re.escape(part) for part in term.split())
    return re.compile(r"(?<![\w-])" + body + r"(?![\w-])", re.IGNORECASE)


def _exempt_ranges(text, cfg):
    spans = []
    for term in cfg.get("exempt_terms", []):
        for m in _phrase_pattern(term).finditer(text):
            spans.append((m.start(), m.end()))
    return spans


def _r3_findings(term, severity, message, text, starts, exempt):
    """Every non-exempt occurrence of `term` in one joined paragraph, each
    located to the line the phrase starts on."""
    out = []
    for m in _phrase_pattern(term).finditer(text):
        if any(s <= m.start() and m.end() <= e for s, e in exempt):
            continue
        lineno, line_text = _locate(starts, m.start())
        out.append(finding("R3", severity, lineno, line_text, message))
    return out


def rule_r3(prose_lines, cfg):
    """Banned vocabulary. Part A is single-token and exact, so it FAILs.
    Part B is multi-word and contextual, so it WARNs. A term in exempt_terms
    is never flagged, at either severity, even when it is also listed.

    Matching runs over the joined paragraph rather than one line at a time, so
    a hard-wrapped multi-word phrase — and a hard-wrapped exempt term — is
    still seen. The finding reports the line the phrase starts on.
    """
    out = []
    for para in paragraphs(prose_lines):
        text, starts = _join_paragraph(para)
        if not text.strip():
            continue
        exempt = _exempt_ranges(text, cfg)
        for term in cfg.get("banned_part_a", []):
            out += _r3_findings(
                term, "FAIL",
                f'"{term}" is banned corporate vocabulary. Use a plain word.',
                text, starts, exempt)
        for term in cfg.get("banned_part_b", []):
            out += _r3_findings(
                term, "WARN",
                f'"{term}" reads as jargon here. Check whether a plain phrase works.',
                text, starts, exempt)
    return out


IRREGULAR_PARTICIPLES = {
    "written", "given", "taken", "seen", "done", "made", "held", "kept",
    "sent", "built", "found", "told", "shown", "known", "run", "set", "put",
    "read", "left", "meant", "brought", "bought", "caught", "taught", "chosen",
}


def _looks_like_participle(word):
    lower = word.lower()
    if lower in IRREGULAR_PARTICIPLES:
        return True
    return lower.endswith("ed") and len(lower) > 3


def rule_r4(sentences, cfg):
    """Passive voice: a form of "be" followed by a past participle.
    Approximate without a tagger, so it WARNs."""
    be_forms = {w.lower() for w in cfg.get("r4_be_forms", [])}
    out = []
    for lineno, sentence in sentences:
        tokens = GRAMMAR_WORD_RE.findall(sentence)
        for i in range(len(tokens) - 1):
            if tokens[i].lower() in be_forms and _looks_like_participle(tokens[i + 1]):
                out.append(finding(
                    "R4", "WARN", lineno, sentence,
                    f'"{tokens[i]} {tokens[i + 1]}" reads as passive. Use an active verb.'))
                break
    return out


def rule_r5(sentences, cfg):
    """One word, one meaning. A word in both a noun position and a verb
    position in the same sentence is reported.

    Positional and approximate, because locating a subject needs the
    part-of-speech tagging this checker does not use. It WARNs.
    """
    determiners = {w.lower() for w in cfg.get("r5_determiners", [])}
    out = []
    for lineno, sentence in sentences:
        tokens = GRAMMAR_WORD_RE.findall(sentence)
        nouns, verbs = set(), set()
        for i, token in enumerate(tokens):
            lower = token.lower()
            if i > 0 and tokens[i - 1].lower() in determiners:
                nouns.add(lower)
            if i > 0 and tokens[i - 1].lower() == "to" and lower not in determiners:
                verbs.add(lower)
            if i == 0 and lower.endswith("s"):
                verbs.add(lower)
        for word in sorted(nouns & verbs):
            out.append(finding(
                "R5", "WARN", lineno, sentence,
                f'"{word}" is used as both a noun and a verb in one sentence. '
                f"Give it one meaning."))
    return out


CLUSTER_BREAK_RE = re.compile(r"[,;:()\[\].!?]|—|–|--|\s-\s")


def rule_r6(sentences, cfg):
    """A run of 4 or more consecutive non-function words is a noun cluster
    above the 3-word limit. Approximate without a tagger, so it WARNs.

    A cluster is contiguous by definition, so punctuation ends a run as surely
    as a function word does. Without that, a comma-separated list of four
    products read as one four-word cluster.

    Terminal punctuation is in the break set as defence in depth: a cluster can
    never span a sentence boundary, so if the splitter ever swallows one again,
    R6 still cannot report a cluster nobody wrote.
    """
    function_words = {w.lower() for w in cfg.get("r6_function_words", [])}
    out = []
    for lineno, sentence in sentences:
        for chunk in CLUSTER_BREAK_RE.split(sentence):
            run = []
            for token in GRAMMAR_WORD_RE.findall(chunk):
                if token.lower() in function_words:
                    run = []
                    continue
                run.append(token)
                if len(run) == 4:
                    out.append(finding(
                        "R6", "WARN", lineno, sentence,
                        f'"{" ".join(run)}" is a noun cluster of 4 words. '
                        f"The limit is 3."))
                    run = []
    return out


def _sentence_lengths(sentences):
    return [word_count(s) for _, s in sentences]


def rule_r7(sentences, cfg):
    """Uniform cadence. Fires when the spread is below the floor.

    Evaluated only when the mean sentence length is at or below the R1 fail
    cap. That is a single gate on the document mean. Individual R1 findings
    never suppress R7.
    """
    lengths = _sentence_lengths(sentences)
    if len(lengths) < 2:
        return []
    if statistics.mean(lengths) > cfg["r1_fail_words"]:
        return []
    spread = statistics.stdev(lengths)
    if spread >= cfg["r7_stdev_floor"]:
        return []
    lineno = sentences[0][0]
    return [finding(
        "R7", "WARN", lineno, sentences[0][1],
        f"Sentence length is uniform: standard deviation {spread:.1f}, "
        f"floor {cfg['r7_stdev_floor']}. Vary the length.")]


def metrics(sentences, prose_lines, exempt_zones, cfg, truncated_scan=False):
    """Reported statistics. The spread is the real standard deviation whenever
    there are two sentences to compute it from. R7's firing gate is a separate
    decision: reusing it here reported 0 for a document whose mean exceeds the
    R1 fail cap, which reads the same as "cannot compute" and the same as a
    genuinely uniform document.

    `truncated_scan` defaults to False so every existing caller keeps its
    current PASS/WARN/FAIL meaning; it is True only when `check()` detects an
    unterminated code fence, which blanks the rest of the document."""
    lengths = _sentence_lengths(sentences)
    mean = round(statistics.mean(lengths), 1) if lengths else 0
    spread = round(statistics.stdev(lengths), 1) if len(lengths) >= 2 else 0
    return {
        "sentences": len(lengths),
        "mean_sentence_words": mean,
        "stdev_sentence_words": spread,
        "paragraphs": len(paragraphs(prose_lines)),
        "exempt_zones": exempt_zones,
        "truncated_scan": truncated_scan,
    }


def check(doc_path, cfg=None):
    """Run every rule over a document and return the result object."""
    cfg = cfg if cfg is not None else load_config()
    scan_meta = {}
    prose_lines, exempt_zones = checked_spans(doc_path, scan_meta)
    sentences = split_sentences_with_lines(prose_lines, cfg)

    findings = []
    findings += rule_r1(sentences, cfg)
    findings += rule_r2(prose_lines, cfg)
    findings += rule_r3(prose_lines, cfg)
    findings += rule_r4(sentences, cfg)
    findings += rule_r5(sentences, cfg)
    findings += rule_r6(sentences, cfg)
    findings += rule_r7(sentences, cfg)
    findings.sort(key=lambda f: (f["line"], f["rule"]))

    severities = {f["severity"] for f in findings}
    verdict = "FAIL" if "FAIL" in severities else "WARN" if "WARN" in severities else "PASS"
    return {
        "document": str(doc_path),
        "verdict": verdict,
        "metrics": metrics(sentences, prose_lines, exempt_zones, cfg,
                            truncated_scan=scan_meta.get("truncated_scan", False)),
        "findings": findings,
    }


EXIT_BY_VERDICT = {"PASS": 0, "WARN": 1, "FAIL": 2}


def _render(result):
    lines = []
    for f in result["findings"]:
        lines.append(f'{f["rule"]}  {f["severity"]:<4}  line {f["line"]}  {f["message"]}')
    m = result["metrics"]
    lines.append(
        f'{result["verdict"]}: {len(result["findings"])} findings, '
        f'{m["sentences"]} sentences, mean {m["mean_sentence_words"]} words, '
        f'stdev {m["stdev_sentence_words"]}, {m["exempt_zones"]} exempt zones')
    if m.get("truncated_scan"):
        # The flag exists to make an unscanned document distinguishable from a
        # clean one, and this is the path where the result is read. Printing it
        # only into the --json payload left the default path reporting
        # "PASS: 0 findings" for a document that was never checked.
        lines.append(
            "WARNING: scan truncated — a code fence opened and never closed, "
            "so every line from it to the end of the file was skipped.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check a document for ASD-STE100 conformance.")
    parser.add_argument("doc", help="path to the document")
    parser.add_argument("--config", default=None,
                        help="path to ste.yaml (default: module-relative)")
    parser.add_argument("--json", action="store_true",
                        help="print the result object instead of one line per finding")
    parser.add_argument("--out", default=None,
                        help="write the result object to this file and print 'verdict=<V>'")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        result = check(args.doc, cfg)
    except ConfigError as exc:
        print(json.dumps({"error": "config", "detail": str(exc)}), file=sys.stderr)
        return 3
    except zone_parser.ZoneParseError as exc:
        # ZoneParseError and UnicodeDecodeError are sibling ValueError
        # subclasses — neither catches the other — so the order of these two
        # handlers is free. Both are here because ValueError is not an OSError,
        # so the OSError handler below never saw either one.
        print(json.dumps({"error": "zone-parse", "detail": str(exc)}), file=sys.stderr)
        return 3
    except UnicodeDecodeError as exc:
        print(json.dumps({"error": "decode", "detail": str(exc)}), file=sys.stderr)
        return 3
    except OSError as exc:
        print(json.dumps({"error": "unreadable", "detail": str(exc)}), file=sys.stderr)
        return 3

    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": "unwritable", "detail": str(exc)}), file=sys.stderr)
            return 3
        print(f'verdict={result["verdict"]}')
    else:
        print(json.dumps(result, indent=2) if args.json else _render(result))
    return EXIT_BY_VERDICT[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
