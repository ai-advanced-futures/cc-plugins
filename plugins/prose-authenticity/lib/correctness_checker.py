# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Deterministic prose correctness check.

A separate check from the AI-detection tiers and from the STE checker. Those
measure how prose reads; this measures whether it is correct. The three never
share a scale. See ADR-010, which cites ADR-006 as its precedent.

Exit codes: 0 pass / 1 warn / 2 fail / 3 usage-or-operational error. 1 is
defined but unreachable in v0.4.0 — no rule emits WARN.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "correctness_checker needs PyYAML. Start it with:\n"
        "    uv run ${CLAUDE_PLUGIN_ROOT}/lib/correctness_checker.py <document>\n"
        "or install PyYAML with:\n"
        "    pip install -r requirements-dev.txt"
    ) from exc

import prose_spans
import zone_parser

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "correctness.yaml")


class ConfigError(Exception):
    """Raised when the config file is unreadable, unparsable or malformed."""


INT_CONFIG_KEYS = ("c2_min_token_length", "c3_gap_width")
LIST_CONFIG_KEYS = ("c2_allow_list", "c3_sounded_h", "c3_long_u")
MAP_CONFIG_KEYS = ("misspellings", "c3_initialisms", "severities")
# Every required key is typed by exactly one tuple above, so the presence check
# reads its schema from them. A separate literal list could drift: a key typed
# but not required (or the reverse) would let the two checks disagree.
REQUIRED_CONFIG_KEYS = INT_CONFIG_KEYS + LIST_CONFIG_KEYS + MAP_CONFIG_KEYS


def _validate_types(cfg, cfg_path):
    """Every declared key holds a value of the type its rule assumes.

    `bool` is excluded explicitly from the numeric checks: it is an `int`
    subclass in Python, so `c2_min_token_length: yes` would otherwise pass
    as 1. That exact defect shipped in the STE checker.
    """
    for key in INT_CONFIG_KEYS:
        value = cfg.get(key)
        if key in cfg and (isinstance(value, bool) or not isinstance(value, int)):
            raise ConfigError(
                f"{key} must be a whole number, got {type(value).__name__}: {cfg_path}")
    for key in LIST_CONFIG_KEYS:
        if key not in cfg:
            continue
        if not isinstance(cfg[key], list):
            raise ConfigError(
                f"{key} must be a list, got {type(cfg[key]).__name__}: {cfg_path}")
        for item in cfg[key]:
            if not isinstance(item, str):
                raise ConfigError(
                    f"{key} holds a non-string entry ({item!r}, "
                    f"{type(item).__name__}). Quote it: {cfg_path}")
    for key in MAP_CONFIG_KEYS:
        if key not in cfg:
            continue
        if not isinstance(cfg[key], dict):
            raise ConfigError(
                f"{key} must be a mapping, got {type(cfg[key]).__name__}: {cfg_path}")
        for k, v in cfg[key].items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ConfigError(
                    f"{key} holds a non-string entry ({k!r}: {v!r}). "
                    f"Quote it: {cfg_path}")
    _validate_severities(cfg, cfg_path)


VALID_SEVERITIES = ("PASS", "WARN", "FAIL")
SHIPPED_RULES = ("C1", "C2", "C3")


def _validate_severities(cfg, cfg_path):
    """`severities` names every shipped rule, and every value is a real verdict.

    Type validation alone fails open twice, and both paths were measured. A
    value typo (`FAILL`) keeps the mapping a `dict[str, str]`, so a document
    with two real faults prints PASS and exits 0 — the finding severity never
    matches any verdict level. An empty mapping satisfies the required-keys
    check and then raises `KeyError` from inside a rule, which exits 1: the
    code a caller reads as "warn and continue".
    """
    severities = cfg.get("severities", {})
    missing = [r for r in SHIPPED_RULES if r not in severities]
    if missing:
        raise ConfigError(
            f"severities is missing {', '.join(missing)}: {cfg_path}")
    for rule, value in severities.items():
        if value not in VALID_SEVERITIES:
            raise ConfigError(
                f"severities[{rule}] must be one of "
                f"{', '.join(VALID_SEVERITIES)}, got {value!r}: {cfg_path}")


def load_config(path=None):
    """Read correctness.yaml. `path` defaults to a module-relative location, so
    the default works from any current directory."""
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
        raise ConfigError(f"config is missing {', '.join(missing)}: {cfg_path}")
    _validate_types(cfg, cfg_path)
    return cfg


TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z'’\-]*(?![A-Za-z0-9])")


def tokenise(text):
    """Whole tokens only.

    The lookarounds are what make the rule safe. Without them `re.findall`
    harvests the letter runs inside digit-bearing tokens — `v0.3.1` yields
    `v`, `19th` yields `th` — and those fragments are then checked against
    the misspelling list as if they were words.

    A compound of letters stays whole; a hyphen adjacent to a digit or another
    hyphen still opens a token, so `ASD-STE100` yields `ASD`. Every fragment is
    itself a whole word, and the curation invariant keeps whole words off the
    list, so the direction is conservative: missed, never mis-flagged.
    """
    return TOKEN_RE.findall(text)


def finding(rule, severity, line, excerpt, message):
    return {"rule": rule, "severity": severity, "line": line,
            "excerpt": excerpt, "message": message}


C2_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
NONSPACE_RE = re.compile(r"\S+")


def _adjacent_tokens(text):
    """(previous, current, lineoffset) for runs separated by exactly one space.

    A run is a token only when it is wholly alphanumeric, so `harness;` is not
    one — that is the whitespace-only requirement, and it is what removes two
    of the residuals and every boundary-straddling pair. A gap wider than one
    space means the seam blanked something between the two runs, so they were
    never adjacent in the source.
    """
    out = []
    prev = None
    prev_end = None
    for m in NONSPACE_RE.finditer(text):
        token = m.group() if C2_TOKEN_RE.fullmatch(m.group()) else None
        if (token is not None and prev is not None
                and m.start() - prev_end == 1):
            out.append((prev, token, m.start()))
        prev, prev_end = token, m.end()
    return out


def rule_c2(prose_lines, cfg):
    """The same word twice in a row, within one line."""
    allow = {p.lower() for p in cfg["c2_allow_list"]}
    min_len = cfg["c2_min_token_length"]
    severity = cfg["severities"]["C2"]
    out = []
    for lineno, text in prose_lines:
        if not text:
            continue
        for prev, token, _ in _adjacent_tokens(text):
            if len(token) < min_len or len(prev) < min_len:
                continue
            if prev.lower() != token.lower():
                continue
            if f"{prev.lower()} {token.lower()}" in allow:
                continue
            excerpt = f"{prev} {token}"
            out.append(finding(
                "C2", severity, lineno, excerpt,
                f"{excerpt!r} repeats a word"))
    return out


C3_RE = re.compile(r"(?<![A-Za-z0-9])([Aa]n?)(\s+)([A-Za-z][A-Za-z'’\-]*)")
VOWELS = "aeiou"

# The letters whose NAMES open on a vowel sound: ay, ee, ef, aitch, eye, el,
# em, en, oh, ar, ess, ex. A reader says the name, so `R` takes `an` while its
# spelling says otherwise. Applied ONLY to one-character tokens — see
# `_expected_article`.
#
# A set, not the string `"AEFHILMNORSX"`. Membership on a string is SUBSTRING
# containment, so `"MN" in "AEFHILMNORSX"` is True. The one-character guard
# below makes the two equivalent today, which is exactly the problem: the
# string form hides a wrong answer behind a guard in another function, and it
# returns it silently on the day that guard moves. No test can separate the two
# while the guard holds.
VOWEL_SOUNDED_LETTERS = frozenset("AEFHILMNORSX")

# A match ending in one of these is two unrelated tokens the regex adjoined,
# not an article and a noun — `A and B converge`, where `A` is a label.
#
# TWO conjunctions, not all seven, and the cut is not stylistic. Suppression
# is only ever needed where the fallback would otherwise be WRONG, and the
# fallback reads the first letter: `and` and `or` open on a vowel, so `A and
# B` is asked to become `an and`. `nor` and `but` open on a consonant, so they
# never produced a finding to suppress — listing them changed exactly two
# strings, `An nor …` and `An but …`, and both are REAL article faults. Two
# members that could only ever swallow a true positive.
#
# `for`, `so` and `yet` stay out for a second reason: each also reads as
# something that legitimately follows an article — `a for loop`, `a so-called
# fix`, `a yet-unnamed rule`. Widening this set to all seven coordinating
# conjunctions would be the same mistake as reading every all-caps token as an
# initialism: a rule applied past the point where it can still be right.
NEVER_AFTER_AN_ARTICLE = frozenset({"and", "or"})

# Ordinary English words that happen to SPELL a `c3_initialisms` row. Folding
# the lookup let the pronoun `us` reach the `US` row, so `an us-versus-them
# framing` asked for `a`; the noun `sot` reaches `SoT` the same way. Written
# in lower case, these are the word and not the row, so the table is skipped
# and the ordinary rules decide.
#
# This is the all-caps wall seen from the other side. There, capitals cannot
# prove a token IS an initialism. Here, lower case cannot prove it is NOT.
# Neither is decidable, so both are closed lists. The uppercase spelling still
# reaches the table, because that casing is the row.
#
# ACCEPTED RESIDUAL: title case goes to the table, so a sentence-initial
# `An Us-versus-them framing …` is still reported. Relaxing the test to
# "anything not all-caps" would fix that one phrase and break `an SoT`, whose
# key is mixed case and would then be shadowed by the noun `sot`. A rare
# capitalised pronoun is the cheaper of the two errors.
WORDS_THAT_SPELL_A_TABLE_ROW = frozenset({"us", "sot"})


def _sentence_initial(text, pos):
    """True when the match at `pos` opens the line or follows a terminator."""
    before = text[:pos].rstrip()
    return not before or before[-1] in ".!?:"


def _expected_article(word, initialisms, sounded_h, long_u):
    """`a` or `an` for the token that follows the article.

    The three lookup structures are built once per document by the caller, not
    here: this runs once per article match, so rebuilding the two lowercased
    sets on every call recomputed them hundreds of times over a document.

    A hyphenated compound falls back to its head before the vowel test. Without
    that, `one` and `user` sit in `c3_long_u` while `one-line` and
    `user-facing` are different tokens that miss the lookup, and the vowel test
    then demands `an` for every one of them. Measured over the repository, that
    class alone accounts for a large share of C3's output, and every instance
    is correct English.

    Every candidate is tried against all three structures, `initialisms`
    included. Consulting the table for the whole token only left each
    hyphenated initialism to drop through to the vowel test, which FAILed
    `an STE-plus-tells` in this plugin's own ADR-008 and `a UUID-scoped` in
    architecture ADR-003 — both correct English, and both with the head already
    sitting in the table.

    All three structures are keyed LOWERCASE and the candidate is folded to
    match, so `an mc`, `an sdlc` and `an mcp-server` reach the table the way
    `an MC` does. All three are correct English written by authors who typed
    the initialism in lower case, and the exact-case lookup missed every one.

    `HEAD` is absent from the table under every casing, so `a HEAD start` is
    untouched. What keeps it safe is that the table is CLOSED, not that the
    lookup is case-sensitive. ADR-011 records why the opposite was believed.

    A ONE-CHARACTER candidate is read as the letter's name, so `an R` and `an
    f-string` are correct and the vowel test FAILed both. The rule stops at one
    character on purpose. `HEAD` is `head` in capitals and `MOAT` is `moat`,
    yet H is `aitch` and M is `em`, so the same rule over all-caps tokens
    demands `an HEAD` and `an MOAT`. Nothing mechanical separates an initialism
    from a word in capitals, which is why the table above it is closed. At one
    character that ambiguity cannot arise: a single letter has no word reading.
    """
    for candidate in _article_candidates(word):
        lowered = candidate.lower()
        if lowered in initialisms and not (
                candidate == lowered and lowered in WORDS_THAT_SPELL_A_TABLE_ROW):
            return initialisms[lowered]
        if lowered in sounded_h:
            return "an"
        if lowered in long_u:
            return "a"
        if len(candidate) == 1:
            return "an" if candidate.upper() in VOWEL_SOUNDED_LETTERS else "a"
    return "an" if word[0].lower() in VOWELS else "a"


def _article_candidates(word):
    """The token, then its hyphen head, then its possessive stem.

    Exactly three, and deliberately not four: adding the stem's own hyphen head
    would make `one` reachable twice for `one-line`, and deleting the hyphen
    head — the mutation that proves it load-bearing — would then change nothing.
    """
    return (word,
            word.split("-")[0],
            word.split("'")[0].split("’")[0])


def rule_c3(prose_lines, cfg):
    """`a` or `an` disagreeing with the word that follows it."""
    severity = cfg["severities"]["C3"]
    gap_width = cfg["c3_gap_width"]
    initialisms = {k.lower(): v for k, v in cfg["c3_initialisms"].items()}
    sounded_h = {w.lower() for w in cfg["c3_sounded_h"]}
    long_u = {w.lower() for w in cfg["c3_long_u"]}
    out = []
    for lineno, text in prose_lines:
        if not text:
            continue
        for m in C3_RE.finditer(text):
            article, gap, word = m.group(1), m.group(2), m.group(3)
            if len(gap) > gap_width:
                # The seam blanked the noun, so the article has nothing to
                # agree with. Whitespace width is the only signal available:
                # prose_lines carries no record of what was removed.
                continue
            if article[0].isupper() and not _sentence_initial(text, m.start()):
                # An uppercase label such as `PR-A is ...` is not an article.
                continue
            if word.lower() in NEVER_AFTER_AN_ARTICLE:
                # `A and B converge` — a label, not an article. The guard above
                # cannot catch it, because that capital opens the line.
                continue
            expected = _expected_article(word, initialisms, sounded_h, long_u)
            if article.lower() != expected:
                excerpt = f"{article} {word}"
                out.append(finding(
                    "C3", severity, lineno, excerpt,
                    f"{excerpt!r} should be {expected!r} {word!r}"))
    return out


def rule_c1(prose_lines, cfg):
    """A token that appears on the curated misspelling list.

    The rule never asks whether a word is in a dictionary. A general
    dictionary measured 413 findings and 0 genuine over this repository's
    prose, because it cannot tell project vocabulary from a typo and because
    it is US-only against British-English prose. See ADR-010.
    """
    listed = {k.lower(): v for k, v in cfg["misspellings"].items()}
    severity = cfg["severities"]["C1"]
    out = []
    for lineno, text in prose_lines:
        if not text:
            continue
        for token in tokenise(text):
            correction = listed.get(token.lower())
            if correction is not None:
                out.append(finding(
                    "C1", severity, lineno, token,
                    f"{token!r} is a misspelling of {correction!r}"))
    return out


EXIT_BY_VERDICT = {"PASS": 0, "WARN": 1, "FAIL": 2}


def check(doc_path, cfg=None):
    """Run every rule over a document and return the result object.

    The top-level keys match `ste_checker.check` — `document`, `verdict`,
    `metrics`, `findings` — so a consumer that switches on the verdict or walks
    the findings needs no special case. `metrics` is rule-specific and does not
    match: this checker reports checked lines, exempt zones and truncated_scan,
    the STE checker reports sentence counts and length statistics. Each module
    renders its own; there is no shared renderer, and one would break on either
    input.
    """
    cfg = cfg if cfg is not None else load_config()
    scan_meta = {}
    prose_lines, exempt_zones = prose_spans.checked_spans(doc_path, scan_meta)

    findings = []
    findings += rule_c1(prose_lines, cfg)
    findings += rule_c2(prose_lines, cfg)
    findings += rule_c3(prose_lines, cfg)
    findings.sort(key=lambda f: (f["line"], f["rule"]))

    severities = {f["severity"] for f in findings}
    verdict = ("FAIL" if "FAIL" in severities
               else "WARN" if "WARN" in severities else "PASS")
    return {
        "document": str(doc_path),
        "verdict": verdict,
        "metrics": {
            "checked_lines": sum(1 for _, t in prose_lines if t.strip()),
            "exempt_zones": exempt_zones,
            "truncated_scan": scan_meta.get("truncated_scan", False),
        },
        "findings": findings,
    }


def _render(result):
    lines = []
    for f in result["findings"]:
        lines.append(
            f'{f["rule"]}  {f["severity"]:<4}  line {f["line"]}  {f["message"]}')
    m = result["metrics"]
    lines.append(
        f'{result["verdict"]}: {len(result["findings"])} findings, '
        f'{m["checked_lines"]} checked lines, {m["exempt_zones"]} exempt zones')
    if m.get("truncated_scan"):
        lines.append(
            "WARNING: scan truncated — a code fence opened and never closed, "
            "so every line from it to the end of the file was skipped.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check a document for spelling and mechanical grammar faults.")
    parser.add_argument("doc", help="path to the document")
    parser.add_argument("--config", default=None,
                        help="path to correctness.yaml (default: module-relative)")
    parser.add_argument("--json", action="store_true",
                        help="print the result object instead of one line per finding")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        result = check(args.doc, cfg)
    except ConfigError as exc:
        print(json.dumps({"error": "config", "detail": str(exc)}), file=sys.stderr)
        return 3
    except zone_parser.ZoneParseError as exc:
        print(json.dumps({"error": "zone-parse", "detail": str(exc)}), file=sys.stderr)
        return 3
    except UnicodeDecodeError as exc:
        print(json.dumps({"error": "decode", "detail": str(exc)}), file=sys.stderr)
        return 3
    except OSError as exc:
        print(json.dumps({"error": "unreadable", "detail": str(exc)}), file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2) if args.json else _render(result))
    return EXIT_BY_VERDICT[result["verdict"]]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
