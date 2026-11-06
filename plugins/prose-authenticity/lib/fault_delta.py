#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""What a rewrite INTRODUCED, measured against the original (ADR-012).

The humanize report discloses the correctness and STE faults the rewrite added,
not the ones the document already carried. That is a multiset difference over
two findings lists. This plugin keeps arithmetic in `lib/*.py` rather than in
agent prose, so it lives here and not in the detection-analyst's prompt.

Identity is `(checker, rule, excerpt)` — deliberately NOT the line number. A
rewrite moves text, so nearly every surviving fault lands on a new line, and a
line-keyed identity would report the whole pre-existing set as newly
introduced. The excerpt is the fault itself: the misspelled token, the doubled
pair, the article-and-noun pair.

R7 is the one exception. It is document-scoped and emits at most one finding,
anchored to the document's first sentence. Keying it on that excerpt would call
it newly introduced whenever the opening sentence changed, which a rewrite does
routinely. It keys on the rule alone.

Counts matter, so the difference is over a multiset. An original with one
doubled word and a candidate with two means the rewriter added one.

Exit codes: 0 nothing introduced, 2 something introduced, 3 an operational
error. 2 and 3 stay apart — a missing file must never read as a bad rewrite.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import correctness_checker  # noqa: E402
import ste_checker  # noqa: E402
import zone_parser  # noqa: E402

CHECKERS = (("correctness", correctness_checker), ("ste", ste_checker))

# Document-scoped rules: one finding for the whole document, anchored to text
# the rewrite is expected to change. Keyed on the rule alone.
DOC_SCOPED_RULES = frozenset({"R7"})

EXIT_OK = 0
EXIT_INTRODUCED = 2
EXIT_ERROR = 3


def identity(finding):
    """The key two findings must share to count as the same fault."""
    if finding["rule"] in DOC_SCOPED_RULES:
        return (finding["checker"], finding["rule"], None)
    return (finding["checker"], finding["rule"], finding["excerpt"])


def _tagged(result, checker_name):
    out = []
    for f in result["findings"]:
        tagged = dict(f)
        tagged["checker"] = checker_name
        out.append(tagged)
    return out


def _load_configs():
    """Each config parsed once, then reused across both documents.

    `check()` reloads from disk when handed no config, so letting it default
    would parse both YAML files four times for one comparison.
    """
    return {name: module.load_config() for name, module in CHECKERS}


def _run(doc_path, configs=None):
    """Every finding for one document, tagged with the checker that found it."""
    configs = configs if configs is not None else _load_configs()
    findings = []
    verdicts = {}
    for name, module in CHECKERS:
        result = module.check(doc_path, configs[name])
        verdicts[name] = result["verdict"]
        findings += _tagged(result, name)
    return findings, verdicts


def _surplus_indices(left, right):
    """Positions in `left` whose identity `right` does not account for.

    A multiset difference: three copies on the left and one on the right
    leaves two, not zero.

    Returns positions rather than the findings themselves so the caller can
    split `left` into two complementary buckets. Splitting on object identity
    instead would work only while nothing in the chain copies a finding dict,
    which is not a property worth depending on.
    """
    budget = collections.Counter(identity(f) for f in right)
    out = []
    for i, f in enumerate(left):
        key = identity(f)
        if budget[key]:
            budget[key] -= 1
        else:
            out.append(i)
    return out


def delta(original_path, candidate_path):
    """Compare two documents and bucket every finding.

    `introduced` is the rewrite's own damage. `resolved` is what it cleaned up.
    `pre_existing` is the author's to fix, and the report lists it separately
    so the two are never confused.

    The two verdicts are named apart. Both checkers emit a top-level `verdict`,
    and ADR-006 requires renaming before a combined report can carry both.
    """
    configs = _load_configs()
    original, _ = _run(original_path, configs)
    candidate, candidate_verdicts = _run(candidate_path, configs)

    introduced_at = set(_surplus_indices(candidate, original))
    introduced = [f for i, f in enumerate(candidate) if i in introduced_at]
    pre_existing = [f for i, f in enumerate(candidate) if i not in introduced_at]
    resolved = [original[i] for i in _surplus_indices(original, candidate)]

    return {
        "original": str(original_path),
        "candidate": str(candidate_path),
        "correctness_verdict": candidate_verdicts["correctness"],
        "ste_verdict": candidate_verdicts["ste"],
        "introduced": introduced,
        "pre_existing": pre_existing,
        "resolved": resolved,
    }


def _render(result):
    lines = []
    for f in result["introduced"]:
        lines.append(f'INTRODUCED  {f["checker"]}/{f["rule"]}  '
                     f'line {f["line"]}  {f["message"]}')
    lines.append(
        f'{len(result["introduced"])} introduced, '
        f'{len(result["pre_existing"])} pre-existing, '
        f'{len(result["resolved"])} resolved '
        f'(correctness_verdict {result["correctness_verdict"]}, '
        f'ste_verdict {result["ste_verdict"]})')
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report the correctness and STE faults a rewrite introduced.")
    parser.add_argument("--original", required=True, help="the document as authored")
    parser.add_argument("--candidate", required=True, help="the rewritten document")
    parser.add_argument("--json", action="store_true",
                        help="print the result object instead of one line per finding")
    args = parser.parse_args(argv)

    try:
        result = delta(args.original, args.candidate)
    except (correctness_checker.ConfigError, ste_checker.ConfigError) as exc:
        print(json.dumps({"error": "config", "detail": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    except zone_parser.ZoneParseError as exc:
        print(json.dumps({"error": "zone-parse", "detail": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    except UnicodeDecodeError as exc:
        print(json.dumps({"error": "decode", "detail": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(json.dumps({"error": "unreadable", "detail": str(exc)}), file=sys.stderr)
        return EXIT_ERROR

    print(json.dumps(result, indent=2) if args.json else _render(result))
    return EXIT_INTRODUCED if result["introduced"] else EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
