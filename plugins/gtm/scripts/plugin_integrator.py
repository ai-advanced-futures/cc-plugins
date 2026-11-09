# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Find the input that other plugins give to gtm in a project.

Run it by its path. It puts its own plugin folder on sys.path, never the cwd:
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/plugin_integrator.py" --root <project>

It prints the result of detect_plugin_outputs() and the snapshot paths of the jtbd and
competitive-intelligence graphs (scripts/brain_read.py) as one JSON object, and exits 0.
Each path is a string. A graph that gives no input writes 1 line on stderr that starts with
NO-GRAPH: or GRAPH-READ-FAILED:, and its key is absent.
With --out <file>, it writes the JSON object to that file, prints one summary line
(the file and the plugin keys found), and exits 0. A file that cannot be written gives exit 2 and no file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.brain_read import read_graphs  # noqa: E402
from scripts.truth_tier_validator import TruthTierValidator  # noqa: E402


@dataclass
class ClaimsResult:
    claims: list[dict]
    total_found: int
    truncated: bool


# Plugin output file patterns. detect_plugin_outputs() reads this table.
# Add a pattern here when you add a new plugin integration.
# The orchestrator agent (step 3) writes the found paths into gtm-context.json.
# The value_ip pattern is the scorecard file that value-ip writes, and the glob
# starts at the project root. The other patterns use rglob.
# This table has no key for jtbd-market-discovery or competitive-intelligence:
# gtm reads their graphs through scripts/brain_read.py, never their old files.
PLUGIN_PATTERNS = {
    "value_ip": [".value-ip/*/output/value-ip-scorecard.md"],
    "pricing": ["*right-price*"],
}

SURVIVED_PATTERN = re.compile(r'^[-\*]\s+(.+)$', re.MULTILINE)


class PluginIntegrator:
    def __init__(self, search_root: Path):
        self.root = Path(search_root)

    def detect_plugin_outputs(self) -> dict[str, list[Path]]:
        found: dict[str, list[Path]] = {}
        for plugin, patterns in PLUGIN_PATTERNS.items():
            matches = []
            for pattern in patterns:
                if plugin == "value_ip":
                    matches.extend(self.root.glob(pattern))
                else:
                    matches.extend(self.root.rglob(pattern))
            if matches:
                found[plugin] = matches

        # Customer Support plugin outputs
        # "churn*" starts at the file name: no file of another plugin starts with churn.
        customer_support_patterns = ["churn*", "*customer-support*", "*ticket-summary*"]
        for pattern in customer_support_patterns:
            matches = list(self.root.rglob(pattern))
            if matches:
                found["customer_support"] = str(matches[0])
                break

        # Data plugin outputs
        data_patterns = ["*query-result*", "*cohort-analysis*", "*funnel-data*"]
        for pattern in data_patterns:
            matches = list(self.root.rglob(pattern))
            if matches:
                found["data_plugin"] = str(matches[0])
                break

        return found

    def extract_value_ip_claims(self, scorecard_path: Path) -> ClaimsResult:
        content = scorecard_path.read_text(encoding="utf-8")
        survived_section_match = re.search(r'survived claims', content, re.IGNORECASE)
        if not survived_section_match:
            section = content
        else:
            section = content[survived_section_match.start():]
        items = SURVIVED_PATTERN.findall(section[:3000])
        total_found = len(items)
        # Classify each claim rather than assuming all survived claims are Tier 1 (SHIPPED).
        # Value-ip claims represent positioning assertions that passed a framework filter;
        # without explicit evidence of production deployment, they default to COMMITTED (Tier 3).
        validator = TruthTierValidator()
        claims = []
        for item in items[:20]:
            text = item.strip()
            tier_result = validator.classify({"text": text, "evidence": {"type": "roadmap", "budget": True, "exec_sponsor": True}})
            claims.append({"text": text, "tier": tier_result.tier.value, "source": "value-ip"})
        return ClaimsResult(claims=claims, total_found=total_found, truncated=total_found > 20)


class ContextEnricher:
    def __init__(self, integrator: PluginIntegrator):
        self.integrator = integrator

    def enrich(self, context: dict) -> dict:
        outputs = self.integrator.detect_plugin_outputs()
        if "value_ip" in outputs:
            for path in outputs["value_ip"]:
                result = self.integrator.extract_value_ip_claims(path)
                context["positioning"]["differentiators"].extend(result.claims)
                context.setdefault("_meta", {}).setdefault("sources", {}).setdefault("plugins", []).append("value_ip")
        return context


def _as_json(found: dict) -> dict:
    """Turn each Path of a detect_plugin_outputs() result into a string."""
    return {
        key: [str(p) for p in value] if isinstance(value, list) else str(value)
        for key, value in found.items()
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Find the input that other plugins give to gtm.")
    ap.add_argument("--root", required=True, help="the project folder to search")
    ap.add_argument("--out", help="write the JSON object to this file and print one summary line")
    args = ap.parse_args(argv)
    found = _as_json(PluginIntegrator(Path(args.root)).detect_plugin_outputs())
    graph_inputs, notes = read_graphs(Path(args.root))
    found.update(graph_inputs)
    for note in notes:
        print(note, file=sys.stderr)
    text = json.dumps(found, indent=2)
    if not args.out:
        print(text)
        return 0
    try:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    except OSError as error:
        print(f"plugin_integrator error: cannot write {args.out}: {error}", file=sys.stderr)
        return 2
    print(f"wrote {args.out}: {len(found)} plugin keys ({', '.join(sorted(found)) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
