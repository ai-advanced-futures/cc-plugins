from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.truth_tier_validator import TruthTier

# Field intel keyword extraction patterns — canonical source for document_ingester.
# These patterns drive learned_knowledge extraction. See agents/knowledge-agent.md for
# how extracted data is structured and agents/codebase-scanner.md for the division of labor.
# Extend here when adding new field intel signal types.
KEYWORD_PATTERNS = [
    r'win reason[s]?[:\s]+(.+)',
    r'loss reason[s]?[:\s]+(.+)',
    r'objection[s]?[:\s]+(.+)',
    r'response[:\s]+(.+)',
    r'they chose us[^.]+',
    r'competitor[:\s]+(\w+)',
    r'pricing[:\s]+(.+)',
    r'roi[:\s]+(.+)',
]

TIER_BY_EXT = {
    ".vtt":  TruthTier.SHIPPED,
    ".json": TruthTier.SHIPPED,
    ".txt":  TruthTier.IN_FLIGHT,
    ".md":   TruthTier.IN_FLIGHT,
    ".docx": TruthTier.IN_FLIGHT,
    ".csv":  TruthTier.IN_FLIGHT,
    ".pdf":  TruthTier.IN_FLIGHT,
}

TIER_BY_DOC_TYPE = {
    "gong_transcript":    TruthTier.SHIPPED,
    "win_loss_interview": TruthTier.SHIPPED,
    "customer_testimony": TruthTier.SHIPPED,
    "sales_playbook":     TruthTier.IN_FLIGHT,
    "internal_notes":     TruthTier.IN_FLIGHT,
}

SUPPORTED_EXTENSIONS = set(TIER_BY_EXT.keys())

VTT_CONTENT_PATTERN = re.compile(
    r'\d{2}:\d{2}:\d{2}\.\d+ --> .+\n(.+)', re.MULTILINE
)


@dataclass
class IngestedDocument:
    source_path: str
    extracted_text: str
    truth_tier: TruthTier
    file_type: str


@dataclass
class ExtractedKnowledge:
    keywords: list[str]
    raw_text: str
    total_found: int = 0
    truncated: bool = False


class DocumentIngester:
    """Ingests Ring-0 human knowledge files and maps them to Truth Tiers."""

    def ingest(self, path: Path, doc_type: str | None = None) -> IngestedDocument:
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            return IngestedDocument(
                source_path=str(path),
                extracted_text="",
                truth_tier=TruthTier.SPECULATION,
                file_type=ext,
            )

        content = path.read_text(encoding="utf-8", errors="replace")

        if ext == ".vtt":
            lines = VTT_CONTENT_PATTERN.findall(content)
            text = " ".join(lines)
        else:
            text = content

        tier = TIER_BY_DOC_TYPE.get(doc_type) if doc_type else None
        if tier is None:
            tier = TIER_BY_EXT[ext]

        return IngestedDocument(
            source_path=str(path),
            extracted_text=text.strip(),
            truth_tier=tier,
            file_type=ext,
        )


class KnowledgeExtractor:
    """Pulls win/loss signals, objections, and competitive keywords from raw text."""

    _ANCHOR_WORDS = {
        "win", "loss", "objection", "roi", "pricing", "competitor",
        "response", "churn", "renewal", "deal", "close",
    }

    def extract_from_text(self, text: str) -> ExtractedKnowledge:
        keywords: list[str] = []
        text_lower = text.lower()

        for pattern in KEYWORD_PATTERNS:
            matches = re.findall(pattern, text_lower)
            keywords.extend(m.strip() for m in matches if m.strip())

        for word in self._ANCHOR_WORDS:
            if word in text_lower and word not in keywords:
                keywords.append(word)

        total = len(keywords)
        return ExtractedKnowledge(keywords=keywords[:30], raw_text=text, total_found=total, truncated=total > 30)
