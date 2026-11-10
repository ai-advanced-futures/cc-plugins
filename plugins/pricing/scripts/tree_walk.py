# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0", "pyyaml>=6.0"]
# ///
"""Walk the value-metric tree for the answers of the input file and write the agentic-pricing-diagnosis file.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tree_walk.py" --input .pricing/tree-walk-input.json --out .pricing/agentic-pricing-diagnosis.json

The input file holds `success_mode`, `branch_diagnostic` (true or false), `bounded_vs_unbounded` and
`portco_arr_band`, and it can hold `value_metric_rationale` and `engagement_id`. The script calls `walk_tree` of
`pricing.lib.value_metric_tree`, checks the result against `agentic-pricing-diagnosis.schema.json`, and writes it.
Prints `terminal_node=<t> archetype=<a> layer=<l> confidence=<c> patterns=<ids>`, then the `engagement_id` and
its source, then `wrote <file>`.
Each file is a `.json` file in the `.pricing` folder of the project.
Exit 1: an input error (1 line on stderr, no file). Exit 2: usage.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib import handoff_file  # noqa: E402
from pricing.lib.value_metric_tree import TreeAnswers, walk_tree  # noqa: E402

SCHEMA = "agentic-pricing-diagnosis.schema.json"


def build(data):
    branch = data.get("branch_diagnostic")
    if not isinstance(branch, bool):
        raise ValueError("branch_diagnostic must be true or false")
    answers = TreeAnswers(success_mode=handoff_file.text(data, "success_mode"), branch_diagnostic=branch,
                          bounded_vs_unbounded=handoff_file.text(data, "bounded_vs_unbounded"),
                          portco_arr_band=handoff_file.text(data, "portco_arr_band"))
    node = walk_tree(answers)  # ValueError for a success_mode that is not known
    rationale = handoff_file.text(data, "value_metric_rationale", "success_mode %s, branch answer %s: terminal node %s"
                                  % (answers.success_mode, "yes" if branch else "no", node.terminal_node))
    result = {**handoff_file.envelope(data), "portco_arr_band": answers.portco_arr_band,
              "layer_classification": node.layer_classification, "archetype": node.archetype,
              "bounded_vs_unbounded": answers.bounded_vs_unbounded, "terminal_node": node.terminal_node,
              "value_metric_rationale": rationale, "recommended_pattern_ids": node.recommended_pattern_ids,
              "confidence": node.confidence, "audience": "mixed"}
    handoff_file.check(result, SCHEMA)
    line = "terminal_node=%s archetype=%s layer=%s confidence=%s patterns=%s" % (
        node.terminal_node, node.archetype, node.layer_classification, node.confidence,
        ",".join(node.recommended_pattern_ids))
    return result, line


if __name__ == "__main__":
    sys.exit(handoff_file.run("tree_walk.py", sys.argv[1:], build))
