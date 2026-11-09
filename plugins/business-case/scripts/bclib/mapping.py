"""Constants that `publish` and the brain check share: the sections of the template, their parts, and the aliases."""
from __future__ import annotations

import re

# The 15 sections of templates/business-case.md, in the order of the template, and the part of each (spec, "Parts").
SECTION_PART = {
    "offering": "strategy", "problem": "job", "customers": "job", "journeys": "job", "market": "market",
    "competition": "competition", "pricing": "price", "go-to-market": "gtm", "forecast": "finance",
    "assumptions": "finance", "financials": "finance", "baseline": "baseline", "success": "baseline",
    "execution": "baseline", "funding": "strategy",
}
SECTIONS = tuple(SECTION_PART)

# The alias of a page after the slug: a fixed pattern for each page type, except Run and Part.
ALIAS_TAIL = {
    "Evidence": re.compile(r"EV-\d{2,}"), "Decision": re.compile(r"D-\d{2,}"),
    "StrategyEntry": re.compile(r"SD-\d{2,}"), "Condition": re.compile(r"C-\d{2,}"),
    "Note": re.compile(r"N-\d{2,}"), "Figure": re.compile(r"FIG-\d{2,}"),
    "Review": re.compile(r"report-\d{2,}"), "Finance": re.compile(r"finance"),
    # The item pages (D-583): 1 page for each open item, item verdict and finding.
    "OpenItem": re.compile(r"open/BC-[A-Z0-9-]+"), "ItemVerdict": re.compile(r"report-\d{2,}/BC-[A-Z0-9-]+"),
    "Finding": re.compile(r"report-\d{2,}/F-[0-9A-Za-z]+"),
}

# The snapshot folder of the case that `result_ref.path` of an Evidence page names (spec, row 14).
SNAPSHOT_DIR = "team/upstream/"
SOURCE_RESULT_RE = re.compile(r"^(jtbd|competitive-intelligence):/results/RESULT-\d{2,}\.md$")

# The words that a page body stays under (spec, row 5).
MAX_LINES = 100
MAX_WORDS = 600
