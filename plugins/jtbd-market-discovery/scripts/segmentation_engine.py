# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1", "numpy==2.4.6", "scikit-learn==1.9.1"]
# ///
"""
Segmentation Engine - K-means Clustering for Customer Segmentation

Segments customers based on their needs importance and satisfaction ratings
using K-means clustering with optimal k detection.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage:
    from scripts.segmentation_engine import SegmentationEngine

    engine = SegmentationEngine(survey_data)
    optimal = engine.find_optimal_k(k_range=(2, 6))
    segments = engine.cluster(k=optimal['optimal_k'])
    profiles = engine.generate_segment_profiles()
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


class SegmentationEngine:
    """
    Customer segmentation using K-means clustering.

    Features:
        - Optimal k detection using elbow method + silhouette score
        - Multi-dimensional needs-based clustering
        - Segment profile generation
        - Segment naming suggestions based on characteristics

    Usage:
        engine = SegmentationEngine(survey_data)
        engine.find_optimal_k(k_range=(2, 6))
        segments = engine.cluster(k=3)
        profiles = engine.generate_segment_profiles()
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize segmentation engine with survey data.

        Args:
            data: DataFrame where each row is a respondent and columns are
                  needs importance/satisfaction ratings. Can include respondent
                  metadata columns that will be preserved.

        Example:
            >>> data = pd.DataFrame({
            ...     'respondent_id': [1, 2, 3],
            ...     'need_1_importance': [9, 5, 8],
            ...     'need_1_satisfaction': [3, 8, 4],
            ...     'need_2_importance': [8, 4, 7],
            ...     'need_2_satisfaction': [2, 9, 3]
            ... })
            >>> engine = SegmentationEngine(data)
        """
        if data.empty:
            raise ValueError("Data cannot be empty")

        self.original_data = data.copy()
        self.data = data.copy()
        self.scaler = StandardScaler()
        self.kmeans = None
        self.optimal_k = None

        # Identify numeric columns for clustering (exclude IDs, names, etc.)
        self.feature_columns = data.select_dtypes(include=[np.number]).columns.tolist()

        if not self.feature_columns:
            raise ValueError("Data must contain numeric columns for clustering")

        # Scale features for clustering
        self.scaled_data = self.scaler.fit_transform(data[self.feature_columns])

    def find_optimal_k(
        self,
        k_range: Tuple[int, int] = (2, 6),
        random_state: int = 42
    ) -> Dict:
        """
        Find optimal number of clusters using elbow method and silhouette score.

        Args:
            k_range: (min_k, max_k) range of k values to test
            random_state: Random seed for reproducibility

        Returns:
            Dictionary containing:
                - optimal_k: Recommended number of clusters
                - elbow_scores: Inertia scores for each k (lower is better)
                - silhouette_scores: Silhouette scores for each k (higher is better, -1 to 1)
                - recommendation: Human-readable recommendation

        Example:
            >>> engine = SegmentationEngine(data)
            >>> result = engine.find_optimal_k(k_range=(2, 5))
            >>> print(f"Optimal k: {result['optimal_k']}")
        """
        min_k, max_k = k_range

        if min_k < 2:
            raise ValueError("min_k must be at least 2")
        if max_k < min_k:
            raise ValueError("max_k must be >= min_k")
        if len(self.data) < max_k:
            raise ValueError(f"Data has {len(self.data)} samples but max_k is {max_k}")

        inertias = []
        silhouette_scores_list = []
        k_values = list(range(min_k, max_k + 1))

        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            kmeans.fit(self.scaled_data)

            inertias.append(kmeans.inertia_)

            # Calculate silhouette score (requires at least 2 clusters)
            if k >= 2:
                silhouette = silhouette_score(self.scaled_data, kmeans.labels_)
                silhouette_scores_list.append(silhouette)
            else:  # pragma: no cover — min_k validation (line 108) ensures k >= 2 always
                silhouette_scores_list.append(0)

        # Find optimal k using combined approach
        # Higher silhouette score is better
        optimal_k = k_values[np.argmax(silhouette_scores_list)]

        # Generate recommendation
        max_silhouette = max(silhouette_scores_list)
        if max_silhouette > 0.5:
            quality = "strong"
        elif max_silhouette > 0.3:
            quality = "moderate"
        else:
            quality = "weak"

        recommendation = (
            f"Recommended k={optimal_k} with {quality} cluster separation "
            f"(silhouette score: {max_silhouette:.3f})"
        )

        self.optimal_k = optimal_k

        return {
            'optimal_k': optimal_k,
            'elbow_scores': inertias,
            'silhouette_scores': silhouette_scores_list,
            'k_values': k_values,
            'recommendation': recommendation
        }

    def cluster(
        self,
        k: int,
        random_state: int = 42
    ) -> pd.DataFrame:
        """
        Perform K-means clustering with k clusters.

        Args:
            k: Number of clusters
            random_state: Random seed for reproducibility

        Returns:
            Original DataFrame with added 'segment' column containing cluster assignments (0 to k-1)

        Example:
            >>> engine = SegmentationEngine(data)
            >>> clustered = engine.cluster(k=3)
            >>> print(clustered['segment'].value_counts())
        """
        if k < 2:
            raise ValueError("k must be at least 2")
        if k > len(self.data):
            raise ValueError(f"k ({k}) cannot exceed number of samples ({len(self.data)})")

        # Perform K-means clustering
        self.kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        clusters = self.kmeans.fit_predict(self.scaled_data)

        # Add segment column to data
        self.data['segment'] = clusters

        return self.data.copy()

    def generate_segment_profiles(self) -> List[Dict]:
        """
        Generate profiles for each segment based on cluster characteristics.

        Must call cluster() before calling this method.

        Returns:
            List of dictionaries, one per segment:
            {
                'segment_id': int,
                'size': int,
                'percentage': float,
                'top_needs': list,  # Top 5 needs by importance
                'avg_importance': float,
                'avg_satisfaction': float,
                'gap': float,  # avg_importance - avg_satisfaction
                'characteristics': str
            }

        Example:
            >>> engine = SegmentationEngine(data)
            >>> engine.cluster(k=3)
            >>> profiles = engine.generate_segment_profiles()
            >>> for profile in profiles:
            ...     print(f"{profile['segment_id']}: {profile['size']} customers")
        """
        if self.kmeans is None:
            raise RuntimeError("Must call cluster() before generating profiles")

        if 'segment' not in self.data.columns:
            raise RuntimeError("segment column not found. Call cluster() first.")

        profiles = []
        n_segments = len(self.data['segment'].unique())

        for segment_id in range(n_segments):
            segment_data = self.data[self.data['segment'] == segment_id]
            size = len(segment_data)
            percentage = size / len(self.data)

            # Calculate average importance and satisfaction
            importance_cols = [col for col in self.feature_columns
                             if isinstance(col, str) and 'importance' in col.lower()]
            satisfaction_cols = [col for col in self.feature_columns
                               if isinstance(col, str) and 'satisfaction' in col.lower()]

            if importance_cols:
                avg_importance = segment_data[importance_cols].mean().mean()
            else:
                avg_importance = 0.0

            if satisfaction_cols:
                avg_satisfaction = segment_data[satisfaction_cols].mean().mean()
            else:
                avg_satisfaction = 0.0

            gap = avg_importance - avg_satisfaction

            # Find top needs (highest average importance in this segment)
            if importance_cols:
                need_importances = segment_data[importance_cols].mean().sort_values(ascending=False)
                top_needs = need_importances.head(5).index.tolist()
                # Clean up column names (remove '_importance')
                top_needs = [need.replace('_importance', '').replace('_', ' ').title()
                           for need in top_needs]
            else:
                top_needs = []

            # Generate characteristics description
            if gap > 5:
                gap_desc = "severely underserved"
            elif gap > 2:
                gap_desc = "moderately underserved"
            elif gap > -2:
                gap_desc = "appropriately served"
            else:
                gap_desc = "overserved"

            if avg_importance > 8:
                importance_desc = "very high"
            elif avg_importance > 6:
                importance_desc = "high"
            elif avg_importance > 4:
                importance_desc = "moderate"
            else:
                importance_desc = "low"

            characteristics = f"{importance_desc} importance needs that are {gap_desc}"

            profiles.append({
                'segment_id': segment_id,
                'size': size,
                'percentage': percentage,
                'top_needs': top_needs,
                'avg_importance': avg_importance,
                'avg_satisfaction': avg_satisfaction,
                'gap': gap,
                'characteristics': characteristics
            })

        return profiles

    def suggest_segment_names(self, profiles: List[Dict]) -> List[str]:
        """
        Suggest descriptive names for segments based on their profiles.

        Args:
            profiles: Output from generate_segment_profiles()

        Returns:
            List of suggested segment names (e.g., ["Crisis Avoiders", "Efficiency-Driven"])

        Example:
            >>> engine = SegmentationEngine(data)
            >>> engine.cluster(k=3)
            >>> profiles = engine.generate_segment_profiles()
            >>> names = engine.suggest_segment_names(profiles)
            >>> print(names)
            ['High-Need Seekers', 'Satisfied Maintainers', 'Opportunity Seekers']
        """
        names = []

        for profile in profiles:
            gap = profile['gap']
            avg_importance = profile['avg_importance']
            avg_satisfaction = profile['avg_satisfaction']

            # Generate name based on characteristics
            if gap > 5 and avg_importance > 8:
                # High importance, very underserved
                names.append("Crisis Avoiders")
            elif gap > 5:
                # Moderately underserved with high gap
                names.append("Opportunity Seekers")
            elif avg_importance > 8 and abs(gap) <= 2:
                # High importance, well served
                names.append("Satisfied Performers")
            elif avg_satisfaction > 8:
                # Very high satisfaction
                names.append("Happy Customers")
            elif gap > 2:
                # Moderate underservement
                names.append("Efficiency-Driven")
            elif gap < -2:
                # Overserved
                names.append("Feature-Rich Users")
            else:
                # Balanced
                names.append("Balanced Users")

        # Ensure unique names by adding segment ID if duplicates
        unique_names = []
        for i, name in enumerate(names):
            if names.count(name) > 1:
                unique_names.append(f"{name} {i+1}")
            else:
                unique_names.append(name)

        return unique_names


if __name__ == "__main__":  # pragma: no cover
    print("Segmentation Engine - Example Usage")
    print("=" * 60)

    # Example: Customer segments for navigation app
    np.random.seed(42)

    # Create synthetic customer data with 3 clear segments
    print("\nGenerating synthetic customer survey data...")
    print("Segment 1: High importance, low satisfaction (Crisis Avoiders)")
    print("Segment 2: Low importance, high satisfaction (Satisfied)")
    print("Segment 3: Medium importance, medium satisfaction (Balanced)")

    # Segment 1: Crisis Avoiders (30 customers)
    segment1 = pd.DataFrame({
        f'need_{i}_importance': np.random.normal(9, 0.5, 30).clip(1, 10)
        for i in range(1, 6)
    })
    for i in range(1, 6):
        segment1[f'need_{i}_satisfaction'] = np.random.normal(3, 0.5, 30).clip(1, 10)

    # Segment 2: Satisfied (30 customers)
    segment2 = pd.DataFrame({
        f'need_{i}_importance': np.random.normal(5, 0.5, 30).clip(1, 10)
        for i in range(1, 6)
    })
    for i in range(1, 6):
        segment2[f'need_{i}_satisfaction'] = np.random.normal(8, 0.5, 30).clip(1, 10)

    # Segment 3: Balanced (30 customers)
    segment3 = pd.DataFrame({
        f'need_{i}_importance': np.random.normal(7, 0.5, 30).clip(1, 10)
        for i in range(1, 6)
    })
    for i in range(1, 6):
        segment3[f'need_{i}_satisfaction'] = np.random.normal(6, 0.5, 30).clip(1, 10)

    # Combine all segments
    survey_data = pd.concat([segment1, segment2, segment3], ignore_index=True)
    survey_data['respondent_id'] = range(1, len(survey_data) + 1)

    print(f"\nTotal respondents: {len(survey_data)}")

    # Initialize engine
    print("\n1. Initialize Segmentation Engine")
    print("-" * 60)
    engine = SegmentationEngine(survey_data)
    print(f"Loaded {len(engine.data)} respondents")
    print(f"Feature columns: {len(engine.feature_columns)}")

    # Find optimal k
    print("\n2. Find Optimal Number of Segments")
    print("-" * 60)
    optimal = engine.find_optimal_k(k_range=(2, 6))
    print(f"Optimal k: {optimal['optimal_k']}")
    print(f"Recommendation: {optimal['recommendation']}")
    print("\nSilhouette scores by k:")
    for k, score in zip(optimal['k_values'], optimal['silhouette_scores']):
        print(f"  k={k}: {score:.3f}")

    # Perform clustering
    print("\n3. Perform K-means Clustering")
    print("-" * 60)
    segmented = engine.cluster(k=optimal['optimal_k'])
    print(f"Segmented {len(segmented)} customers into {optimal['optimal_k']} segments")
    print("\nSegment sizes:")
    print(segmented['segment'].value_counts().sort_index())

    # Generate profiles
    print("\n4. Generate Segment Profiles")
    print("-" * 60)
    profiles = engine.generate_segment_profiles()
    names = engine.suggest_segment_names(profiles)

    for i, profile in enumerate(profiles):
        print(f"\nSegment {profile['segment_id']}: {names[i]}")
        print(f"  Size: {profile['size']} customers ({profile['percentage']:.1%})")
        print(f"  Avg Importance: {profile['avg_importance']:.1f}/10")
        print(f"  Avg Satisfaction: {profile['avg_satisfaction']:.1f}/10")
        print(f"  Gap: {profile['gap']:.1f}")
        print(f"  Characteristics: {profile['characteristics']}")
        print("  Top Needs:")
        for need in profile['top_needs'][:3]:
            print(f"    - {need}")

    # Example 2: Real-world workflow
    print("\n\n5. Complete Workflow Example")
    print("=" * 60)
    print("Navigation App - Real Customer Segmentation")

    # Smaller realistic example
    real_data = pd.DataFrame({
        'respondent_id': range(1, 13),
        'estimate_departure_importance': [9, 9, 5, 5, 7, 7, 9, 9, 5, 5, 7, 7],
        'estimate_departure_satisfaction': [3, 3, 8, 8, 6, 6, 4, 4, 7, 7, 5, 5],
        'traffic_alerts_importance': [10, 9, 4, 3, 8, 7, 10, 9, 4, 3, 8, 7],
        'traffic_alerts_satisfaction': [4, 4, 9, 9, 5, 5, 5, 5, 8, 8, 6, 6]
    })

    engine2 = SegmentationEngine(real_data)
    optimal2 = engine2.find_optimal_k(k_range=(2, 4))
    segmented2 = engine2.cluster(k=optimal2['optimal_k'])
    profiles2 = engine2.generate_segment_profiles()
    names2 = engine2.suggest_segment_names(profiles2)

    print(f"\nIdentified {optimal2['optimal_k']} customer segments:")
    for i, (profile, name) in enumerate(zip(profiles2, names2)):
        print(f"\n{name}:")
        print(f"  {profile['size']} customers ({profile['percentage']:.0%})")
        print(f"  Gap: {profile['gap']:.1f} ({profile['characteristics']})")

    print("\n" + "=" * 60)
    print("Examples complete!")
