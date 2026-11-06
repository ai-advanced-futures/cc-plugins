"""
Web Research Integration Module.

Orchestrates WebFetch and WebSearch tools for competitive intelligence
gathering, with source credibility assessment and data extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class SourceType(Enum):
    """Types of web sources for competitive intelligence."""

    OFFICIAL = "official"  # Company websites, press releases
    NEWS = "news"  # News articles, industry publications
    REVIEW = "review"  # G2, Capterra, TrustRadius
    SOCIAL = "social"  # LinkedIn, Twitter, forums
    ANALYST = "analyst"  # Gartner, Forrester reports
    COMMUNITY = "community"  # Reddit, HN, Stack Overflow
    JOB_POSTING = "job_posting"  # LinkedIn jobs, careers pages


class CredibilityLevel(Enum):
    """Source credibility levels."""

    HIGH = "high"  # Official sources, established analysts
    MEDIUM = "medium"  # News, reviews from known platforms
    LOW = "low"  # Social media, anonymous forums
    UNKNOWN = "unknown"  # Unclassified sources


@dataclass
class WebSource:
    """Represents a web source with metadata."""

    url: str
    source_type: SourceType
    credibility: CredibilityLevel = CredibilityLevel.UNKNOWN
    domain: str = ""
    fetch_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Extract domain from URL if not provided."""
        if not self.domain and self.url:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            self.domain = parsed.netloc


@dataclass
class ExtractedData:
    """Data extracted from a web source."""

    source: WebSource
    raw_content: str
    extracted_facts: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    extraction_method: str = "default"


@dataclass
class ResearchResult:
    """Result of a web research operation."""

    query: str
    sources: List[WebSource] = field(default_factory=list)
    extracted_data: List[ExtractedData] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SourceCredibilityAssessor:
    """Assess credibility of web sources."""

    # Domain credibility mappings
    HIGH_CREDIBILITY_DOMAINS = {
        "gartner.com", "forrester.com", "mckinsey.com",
        "hbr.org", "techcrunch.com", "wsj.com",
        "bloomberg.com", "reuters.com", "forbes.com",
    }

    MEDIUM_CREDIBILITY_DOMAINS = {
        "g2.com", "capterra.com", "trustradius.com",
        "linkedin.com", "crunchbase.com", "glassdoor.com",
        "medium.com", "substack.com",
    }

    LOW_CREDIBILITY_DOMAINS = {
        "reddit.com", "twitter.com", "x.com",
        "quora.com", "facebook.com",
    }

    def __init__(self):
        """Initialize the assessor."""
        self.custom_high: Set[str] = set()
        self.custom_medium: Set[str] = set()
        self.custom_low: Set[str] = set()

    def assess(self, source: WebSource) -> CredibilityLevel:
        """Assess the credibility of a source."""
        domain = source.domain.lower()

        # Remove www. prefix for matching
        if domain.startswith("www."):
            domain = domain[4:]

        # Check custom overrides first
        if domain in self.custom_high:
            return CredibilityLevel.HIGH
        if domain in self.custom_medium:
            return CredibilityLevel.MEDIUM
        if domain in self.custom_low:
            return CredibilityLevel.LOW

        # Check built-in mappings
        if domain in self.HIGH_CREDIBILITY_DOMAINS:
            return CredibilityLevel.HIGH
        if domain in self.MEDIUM_CREDIBILITY_DOMAINS:
            return CredibilityLevel.MEDIUM
        if domain in self.LOW_CREDIBILITY_DOMAINS:
            return CredibilityLevel.LOW

        # Check source type
        if source.source_type == SourceType.OFFICIAL:
            return CredibilityLevel.HIGH
        if source.source_type == SourceType.ANALYST:
            return CredibilityLevel.HIGH
        if source.source_type in (SourceType.NEWS, SourceType.REVIEW):
            return CredibilityLevel.MEDIUM
        if source.source_type in (SourceType.SOCIAL, SourceType.COMMUNITY):
            return CredibilityLevel.LOW

        return CredibilityLevel.UNKNOWN

    def add_custom_credibility(
        self,
        domain: str,
        level: CredibilityLevel
    ) -> None:
        """Add custom credibility rating for a domain."""
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Remove from other sets first
        self.custom_high.discard(domain)
        self.custom_medium.discard(domain)
        self.custom_low.discard(domain)

        if level == CredibilityLevel.HIGH:
            self.custom_high.add(domain)
        elif level == CredibilityLevel.MEDIUM:
            self.custom_medium.add(domain)
        elif level == CredibilityLevel.LOW:
            self.custom_low.add(domain)


class DataExtractor:
    """Extract structured data from web content."""

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Extraction patterns for different data types
    COMPETITOR_PATTERNS = {
        "pricing": [
            r"\$[\d,]+(?:\.\d{2})?(?:\s*\/\s*(?:month|mo|year|yr|user))?",
            r"(?:starting at|from)\s*\$[\d,]+",
            r"(?:free|freemium|enterprise)",
        ],
        "features": [
            r"(?:features?|capabilities?|includes?)[:.]?\s*(.+?)(?:\.|$)",
        ],
        "customers": [
            r"(?:trusted by|used by|customers include)\s*(.+?)(?:\.|$)",
        ],
    }

    def __init__(self):
        """Initialize the extractor."""
        self.custom_patterns: Dict[str, List[str]] = {}

    def extract(
        self,
        content: str,
        source: WebSource,
        extract_types: Optional[List[str]] = None
    ) -> ExtractedData:
        """Extract structured data from content."""
        import re

        facts: List[Dict[str, Any]] = []
        types_to_extract = extract_types or list(self.COMPETITOR_PATTERNS.keys())

        for data_type in types_to_extract:
            patterns = self.COMPETITOR_PATTERNS.get(
                data_type,
                self.custom_patterns.get(data_type, [])
            )

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    facts.append({
                        "type": data_type,
                        "value": match.strip() if isinstance(match, str) else match,
                        "pattern": pattern,
                    })

        # Calculate extraction confidence based on matches and source
        base_confidence = 0.3 if facts else 0.1
        if source.credibility == CredibilityLevel.HIGH:
            base_confidence += 0.4
        elif source.credibility == CredibilityLevel.MEDIUM:
            base_confidence += 0.2

        return ExtractedData(
            source=source,
            raw_content=content[:5000],  # Truncate for storage
            extracted_facts=facts,
            confidence=min(base_confidence, 1.0),
            extraction_method="regex_patterns",
        )

    def add_custom_pattern(self, data_type: str, pattern: str) -> None:
        """Add a custom extraction pattern."""
        if data_type not in self.custom_patterns:
            self.custom_patterns[data_type] = []
        self.custom_patterns[data_type].append(pattern)


class WebResearcher:
    """Orchestrate web research for competitive intelligence."""

    # Search query templates for different research goals
    QUERY_TEMPLATES = {
        "competitor_overview": "{competitor} company overview product features",
        "competitor_pricing": "{competitor} pricing plans cost",
        "competitor_reviews": "{competitor} reviews g2 capterra trustradius",
        "competitor_news": "{competitor} news announcements funding",
        "competitor_jobs": "{competitor} careers jobs hiring",
        "market_analysis": "{market} market size trends analysis",
        "technology_trends": "{technology} trends 2024 2025",
    }

    def __init__(
        self,
        web_fetch_fn: Optional[Callable[[str, str], str]] = None,
        web_search_fn: Optional[Callable[[str], List[dict]]] = None,
    ):
        """Initialize the researcher.

        Args:
            web_fetch_fn: Function to fetch URL content. Signature: (url, prompt) -> content
            web_search_fn: Function to search web. Signature: (query) -> list of results
        """
        self.web_fetch = web_fetch_fn
        self.web_search = web_search_fn
        self.credibility_assessor = SourceCredibilityAssessor()
        self.data_extractor = DataExtractor()

    def build_query(
        self,
        template_name: str,
        **kwargs: str
    ) -> str:
        """Build a search query from a template."""
        template = self.QUERY_TEMPLATES.get(template_name, "{query}")
        return template.format(**kwargs)

    def classify_source_type(self, url: str) -> SourceType:
        """Classify the type of a source based on URL."""
        url_lower = url.lower()

        # Review sites
        if any(site in url_lower for site in ["g2.com", "capterra.com", "trustradius.com"]):
            return SourceType.REVIEW

        # News sites
        if any(site in url_lower for site in [
            "techcrunch", "news", "reuters", "bloomberg",
            "wsj.com", "forbes.com", "venturebeat"
        ]):
            return SourceType.NEWS

        # Analyst sites
        if any(site in url_lower for site in [
            "gartner.com", "forrester.com", "idc.com"
        ]):
            return SourceType.ANALYST

        # Social/community
        if any(site in url_lower for site in [
            "reddit.com", "twitter.com", "x.com",
            "linkedin.com", "facebook.com"
        ]):
            return SourceType.SOCIAL

        # Job postings
        if any(term in url_lower for term in [
            "careers", "jobs", "greenhouse", "lever.co"
        ]):
            return SourceType.JOB_POSTING

        # Default to official (company websites)
        return SourceType.OFFICIAL

    def research_competitor(
        self,
        competitor_name: str,
        research_types: Optional[List[str]] = None
    ) -> ResearchResult:
        """Research a specific competitor.

        Args:
            competitor_name: Name of competitor to research
            research_types: Types of research to perform (overview, pricing, reviews, etc.)
        """
        if research_types is None:
            research_types = ["competitor_overview", "competitor_pricing", "competitor_reviews"]

        result = ResearchResult(query=competitor_name)

        for research_type in research_types:
            query = self.build_query(research_type, competitor=competitor_name)

            # Search for sources
            if self.web_search:
                try:
                    search_results = self.web_search(query)
                    for sr in search_results[:5]:  # Limit to top 5
                        url = sr.get("url", "")
                        if url:
                            source = WebSource(
                                url=url,
                                source_type=self.classify_source_type(url),
                            )
                            source.credibility = self.credibility_assessor.assess(source)
                            result.sources.append(source)
                except Exception as e:
                    result.errors.append(f"Search error for {research_type}: {str(e)}")

        # Fetch and extract from high-value sources
        high_value_sources = [
            s for s in result.sources
            if s.credibility in (CredibilityLevel.HIGH, CredibilityLevel.MEDIUM)
        ][:3]  # Limit fetches

        if self.web_fetch:
            for source in high_value_sources:
                try:
                    content = self.web_fetch(
                        source.url,
                        f"Extract competitive intelligence about {competitor_name}"
                    )
                    extracted = self.data_extractor.extract(content, source)
                    result.extracted_data.append(extracted)
                except Exception as e:
                    result.errors.append(f"Fetch error for {source.url}: {str(e)}")

        return result

    def research_market(
        self,
        market_name: str,
        include_trends: bool = True
    ) -> ResearchResult:
        """Research a market segment."""
        result = ResearchResult(query=f"market:{market_name}")

        queries = [self.build_query("market_analysis", market=market_name)]
        if include_trends:
            queries.append(self.build_query("technology_trends", technology=market_name))

        if self.web_search:
            for query in queries:
                try:
                    search_results = self.web_search(query)
                    for sr in search_results[:5]:
                        url = sr.get("url", "")
                        if url:
                            source = WebSource(
                                url=url,
                                source_type=self.classify_source_type(url),
                            )
                            source.credibility = self.credibility_assessor.assess(source)
                            result.sources.append(source)
                except Exception as e:
                    result.errors.append(f"Search error: {str(e)}")

        return result

    def aggregate_findings(
        self,
        results: List[ResearchResult]
    ) -> Dict[str, Any]:
        """Aggregate findings from multiple research results."""
        all_facts: List[Dict[str, Any]] = []
        sources_by_credibility: Dict[str, int] = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }

        for result in results:
            for extracted in result.extracted_data:
                for fact in extracted.extracted_facts:
                    all_facts.append({
                        **fact,
                        "source_url": extracted.source.url,
                        "source_credibility": extracted.source.credibility.value,
                        "extraction_confidence": extracted.confidence,
                    })
                sources_by_credibility[extracted.source.credibility.value] += 1

        # Group facts by type
        facts_by_type: Dict[str, List[dict]] = {}
        for fact in all_facts:
            fact_type = fact.get("type", "unknown")
            if fact_type not in facts_by_type:
                facts_by_type[fact_type] = []
            facts_by_type[fact_type].append(fact)

        return {
            "total_sources": sum(sources_by_credibility.values()),
            "sources_by_credibility": sources_by_credibility,
            "facts_by_type": facts_by_type,
            "total_facts": len(all_facts),
        }


def create_web_researcher(
    web_fetch_fn: Optional[Callable[[str, str], str]] = None,
    web_search_fn: Optional[Callable[[str], List[dict]]] = None,
) -> WebResearcher:
    """Factory function to create a WebResearcher.

    Args:
        web_fetch_fn: Function to fetch URL content
        web_search_fn: Function to search web

    Returns:
        Configured WebResearcher instance
    """
    return WebResearcher(
        web_fetch_fn=web_fetch_fn,
        web_search_fn=web_search_fn,
    )
