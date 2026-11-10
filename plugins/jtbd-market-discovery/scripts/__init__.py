"""
JTBD Market Discovery - Analysis Scripts

Author: Luis F. Amadeo (Chief Agentic Officer)
Framework: Outcome-Driven Innovation (ODI) - Tony Ulwick
Version: 1.11.1
Last Updated: 2026-01-21

This package provides Python scripts for quantitative analysis in the
Jobs To Be Done (JTBD) market discovery methodology.

Core Modules:
    - opportunity_scorer: Calculate ODI opportunity scores from survey data
    - evc_calculator: Economic Value to Customer analysis
    - segmentation_engine: Multi-dimensional customer segmentation (k-means)
    - wtp_validator: 6-layer willingness-to-pay validation
    - forces_analyzer: Christensen's Forces analysis integration

Usage:
    from scripts import opportunity_scorer

    # Load survey data
    results = opportunity_scorer.calculate_opportunities('survey-results.csv')

    # Get top opportunities
    top_10 = results.head(10)

Platform Support:
    - Claude Code (full Python execution)
    - Claude.ai web (AI-powered analysis as fallback)

Dependencies:
    - pandas: Data manipulation
    - numpy: Numerical operations
    - scikit-learn: Clustering algorithms
    - scipy: Statistical functions

For detailed documentation, see scripts/README.md
"""

__version__ = "1.11.1"
__author__ = "Luis F. Amadeo (Chief Agentic Officer)"
__license__ = "MIT"

# Version info
VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "license": __license__,
    "framework": "Outcome-Driven Innovation (ODI)",
    "source": "Tony Ulwick - Jobs To Be Done Theory",
}

# Package-level imports (will be added in Phase 2)
# from .opportunity_scorer import calculate_opportunities
# from .evc_calculator import calculate_evc
# from .segmentation_engine import segment_customers
# from .wtp_validator import validate_wtp
# from .forces_analyzer import analyze_forces

__all__ = [
    # Will be populated in Phase 2 as modules are created
]
