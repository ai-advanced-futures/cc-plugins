# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=1.3.0"]
# ///
"""
Opportunity Scorer - ODI Algorithm Implementation

Calculates opportunity scores for customer needs using Outcome-Driven Innovation (ODI)
methodology. Supports both additive and multiplicative algorithms.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage:
    from scripts.opportunity_scorer import calculate_opportunity_score, score_needs_dataframe

    # Single score
    score = calculate_opportunity_score(importance=9, satisfaction=3, algorithm='additive')

    # Batch scoring
    df = pd.DataFrame({'importance': [9, 8, 5], 'satisfaction': [3, 7, 8]})
    scored_df = score_needs_dataframe(df, algorithm='additive')
"""

from typing import Literal

import pandas as pd


def calculate_opportunity_score(
    importance: float,
    satisfaction: float,
    algorithm: Literal['additive', 'multiplicative'] = 'additive'
) -> float:
    """
    Calculate opportunity score using ODI algorithm.

    The opportunity score quantifies the gap between importance and satisfaction,
    indicating market opportunity potential.

    Args:
        importance: How important is this need? (1-10 scale)
        satisfaction: How satisfied are customers currently? (1-10 scale)
        algorithm: Algorithm variant to use:
            - 'additive': Importance + max(Importance - Satisfaction, 0)
            - 'multiplicative': Importance × (Importance - Satisfaction)

    Returns:
        Opportunity score (higher = better opportunity)

    Raises:
        ValueError: If algorithm is not 'additive' or 'multiplicative'

    Examples:
        >>> calculate_opportunity_score(9, 3, 'additive')
        15.0
        >>> calculate_opportunity_score(9, 3, 'multiplicative')
        54.0
        >>> calculate_opportunity_score(10, 10, 'additive')
        10.0
        >>> calculate_opportunity_score(5, 8, 'additive')
        5.0
    """
    if algorithm not in ['additive', 'multiplicative']:
        raise ValueError(f"Invalid algorithm '{algorithm}'. Must be 'additive' or 'multiplicative'.")

    if algorithm == 'additive':
        # Additive: Importance + max(Importance - Satisfaction, 0)
        return importance + max(importance - satisfaction, 0)
    else:
        # Multiplicative: Importance × (Importance - Satisfaction)
        return importance * (importance - satisfaction)


def score_needs_dataframe(
    df: pd.DataFrame,
    importance_col: str = 'importance',
    satisfaction_col: str = 'satisfaction',
    algorithm: Literal['additive', 'multiplicative'] = 'additive'
) -> pd.DataFrame:
    """
    Score all needs in a DataFrame and sort by opportunity score.

    Args:
        df: DataFrame containing importance and satisfaction columns
        importance_col: Name of importance column (default: 'importance')
        satisfaction_col: Name of satisfaction column (default: 'satisfaction')
        algorithm: 'additive' or 'multiplicative'

    Returns:
        DataFrame with added 'opportunity_score' column, sorted by score (descending)

    Raises:
        KeyError: If importance or satisfaction columns not found
        ValueError: If DataFrame is empty

    Examples:
        >>> df = pd.DataFrame({
        ...     'need': ['Need A', 'Need B', 'Need C'],
        ...     'importance': [9, 8, 5],
        ...     'satisfaction': [3, 7, 8]
        ... })
        >>> result = score_needs_dataframe(df)
        >>> result.iloc[0]['need']
        'Need A'
        >>> result.iloc[0]['opportunity_score']
        15.0
    """
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot score empty dataset.")

    if importance_col not in df.columns:
        raise KeyError(f"Column '{importance_col}' not found in DataFrame.")

    if satisfaction_col not in df.columns:
        raise KeyError(f"Column '{satisfaction_col}' not found in DataFrame.")

    df = df.copy()
    df['opportunity_score'] = df.apply(
        lambda row: calculate_opportunity_score(
            row[importance_col],
            row[satisfaction_col],
            algorithm
        ),
        axis=1
    )

    df = df.sort_values('opportunity_score', ascending=False).reset_index(drop=True)

    return df


def categorize_opportunities(
    df: pd.DataFrame,
    importance_col: str = 'importance',
    satisfaction_col: str = 'satisfaction',
    opportunity_col: str = 'opportunity_score'
) -> pd.DataFrame:
    """
    Categorize opportunities into strategic tiers based on ODI opportunity score.

    Uses Ulwick's published score-based thresholds. Also adds a 'gap' diagnostic
    column (importance - satisfaction) for reference without driving categorization.

    Categories (per Ulwick ODI methodology):
        - Severely Underserved: score >= 15 (extremely high opportunity)
        - Underserved: 12 <= score < 15 (high opportunity)
        - Appropriately Served: 10 <= score < 12 (moderate opportunity)
        - Overserved: score < 10 (low opportunity)

    Args:
        df: DataFrame with importance, satisfaction, and opportunity_score columns
        importance_col: Name of importance column (used for gap diagnostic only)
        satisfaction_col: Name of satisfaction column (used for gap diagnostic only)
        opportunity_col: Name of opportunity score column (drives categorization)

    Returns:
        DataFrame with added 'category' (score-based) and 'gap' (diagnostic) columns

    Raises:
        ValueError: If DataFrame is empty
        KeyError: If required columns are not found

    Examples:
        >>> df = pd.DataFrame({
        ...     'importance': [9, 8, 7, 5],
        ...     'satisfaction': [3, 5, 7, 9],
        ...     'opportunity_score': [15, 11, 7, 5]
        ... })
        >>> result = categorize_opportunities(df)
        >>> result.iloc[0]['category']
        'Severely Underserved'
        >>> result.iloc[2]['category']
        'Overserved'
    """
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot categorize empty dataset.")

    if importance_col not in df.columns:
        raise KeyError(f"Column '{importance_col}' not found in DataFrame.")

    if satisfaction_col not in df.columns:
        raise KeyError(f"Column '{satisfaction_col}' not found in DataFrame.")

    if opportunity_col not in df.columns:
        raise KeyError(f"Column '{opportunity_col}' not found in DataFrame. "
                       "Run score_needs_dataframe() first, or pass the correct column name.")

    df = df.copy()

    # Add gap as a diagnostic column (does not drive categorization)
    df['gap'] = df[importance_col] - df[satisfaction_col]

    df['category'] = pd.cut(
        df[opportunity_col],
        bins=[-float("inf"), 10.0, 12.0, 15.0, float("inf")],
        labels=["Overserved", "Appropriately Served", "Underserved", "Severely Underserved"],
        right=False,
    ).astype(str)

    return df


def get_top_opportunities(
    df: pd.DataFrame,
    n: int = 10,
    category_filter: str = None
) -> pd.DataFrame:
    """
    Get top N opportunities, optionally filtered by category.

    Args:
        df: Scored and categorized DataFrame
        n: Number of top opportunities to return
        category_filter: Optional category to filter by
            ('Severely Underserved', 'Underserved', etc.)

    Returns:
        Top N opportunities as DataFrame

    Examples:
        >>> df = pd.DataFrame({
        ...     'need': ['A', 'B', 'C'],
        ...     'opportunity_score': [15, 12, 8],
        ...     'category': ['Severely Underserved', 'Underserved', 'Appropriately Served']
        ... })
        >>> top = get_top_opportunities(df, n=2)
        >>> len(top)
        2
        >>> top = get_top_opportunities(df, n=5, category_filter='Severely Underserved')
        >>> len(top)
        1
    """
    if df.empty:
        return df

    if category_filter:
        if 'category' not in df.columns:
            raise KeyError("Column 'category' not found. Run categorize_opportunities() first.")
        df = df[df['category'] == category_filter]

    return df.head(n)


def validate_formula_invariant(algorithm: Literal['additive', 'multiplicative'] = 'additive') -> dict:
    """
    Assert the ODI formula invariant: best-case inputs must produce the highest score.

    Invariant: f(importance=10, satisfaction=1) > f(importance=1, satisfaction=10)

    For additive:     f(10,1) = 10+9 = 19  >  f(1,10) = 1+0 = 1  ✓
    For multiplicative: f(10,1) = 10×9 = 90  >  f(1,10) = 1×(−9) = −9  ✓

    Args:
        algorithm: 'additive' (default, Ulwick canonical) or 'multiplicative'

    Returns:
        {"passed": True, "algorithm": str, "best_case": float, "worst_case": float}

    Raises:
        AssertionError: If the formula does not rank best-case above worst-case.
            This should never happen for the canonical ODI formulas — if it fires,
            the formula has been modified incorrectly.
    """
    best_case = calculate_opportunity_score(10.0, 1.0, algorithm)
    worst_case = calculate_opportunity_score(1.0, 10.0, algorithm)

    if not best_case > worst_case:
        raise AssertionError(
            f"ODI formula invariant FAILED for '{algorithm}': "
            f"f(importance=10, satisfaction=1) = {best_case} "
            f"should be > f(importance=1, satisfaction=10) = {worst_case}. "
            "The formula does not correctly rank the highest-opportunity input above the lowest."
        )

    return {
        "passed": True,
        "algorithm": algorithm,
        "best_case": best_case,
        "worst_case": worst_case,
    }


if __name__ == "__main__":  # pragma: no cover
    print("ODI Opportunity Scorer - Example Usage")
    print("=" * 60)

    # Example: Navigation needs
    needs = pd.DataFrame({
        'need_id': ['N001', 'N002', 'N003', 'N004', 'N005', 'N006'],
        'need_statement': [
            'Minimize time to estimate departure time',
            'Reduce likelihood of arriving late',
            'Minimize effort to identify alternate routes',
            'Minimize fuel consumption',
            'Reduce stress from traffic uncertainty',
            'Maximize ability to predict arrival time'
        ],
        'job_step': [
            'Estimate departure time',
            'Travel to destination',
            'Reset route as needed',
            'Travel to destination',
            'Travel to destination',
            'Assess when destination will be reached'
        ],
        'importance': [9, 10, 8, 5, 9, 10],
        'satisfaction': [3, 4, 6, 7, 4, 5]
    })

    print("\n1. Calculate Individual Scores (Additive Algorithm)")
    print("-" * 60)
    for i, row in needs.iterrows():
        score = calculate_opportunity_score(
            row['importance'],
            row['satisfaction'],
            algorithm='additive'
        )
        print(f"{row['need_id']}: Importance={row['importance']}, "
              f"Satisfaction={row['satisfaction']}, Score={score:.1f}")

    print("\n2. Batch Score with DataFrame (Additive)")
    print("-" * 60)
    scored = score_needs_dataframe(needs, algorithm='additive')
    scored = categorize_opportunities(scored)

    print("\nTop Opportunities:")
    for i, row in scored.head(5).iterrows():
        print(f"\n{i+1}. {row['need_statement']}")
        print(f"   Need ID: {row['need_id']}")
        print(f"   Importance: {row['importance']}, Satisfaction: {row['satisfaction']}")
        print(f"   Opportunity Score: {row['opportunity_score']:.1f}")
        print(f"   Category: {row['category']}")

    print("\n3. Compare Algorithms")
    print("-" * 60)
    # NOTE: The multiplicative algorithm (Importance × (Importance - Satisfaction)) can
    # produce negative scores when Satisfaction > Importance, which breaks ODI categories.
    # The additive algorithm is Ulwick's canonical formula and the recommended default.
    # Use multiplicative only for research/comparison purposes with careful interpretation.
    additive_scores = score_needs_dataframe(needs, algorithm='additive')
    multiplicative_scores = score_needs_dataframe(needs, algorithm='multiplicative')

    comparison = pd.DataFrame({
        'need_id': needs['need_id'],
        'importance': needs['importance'],
        'satisfaction': needs['satisfaction'],
        'additive_score': additive_scores['opportunity_score'],
        'multiplicative_score': multiplicative_scores['opportunity_score']
    })

    print("\nAlgorithm Comparison:")
    print(comparison.to_string(index=False))

    print("\n4. Category Distribution")
    print("-" * 60)
    category_counts = scored['category'].value_counts()
    for category, count in category_counts.items():
        percentage = (count / len(scored)) * 100
        print(f"{category}: {count} needs ({percentage:.1f}%)")

    print("\n5. Get Severely Underserved Opportunities Only")
    print("-" * 60)
    severe = get_top_opportunities(scored, n=10, category_filter='Severely Underserved')
    if not severe.empty:
        print(f"\nFound {len(severe)} severely underserved needs:")
        for i, row in severe.iterrows():
            print(f"  - {row['need_statement']} (Score: {row['opportunity_score']:.1f})")
    else:
        print("No severely underserved needs found.")

    print("\n" + "=" * 60)
    print("Example complete!")
