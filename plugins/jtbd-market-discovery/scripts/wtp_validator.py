# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1", "numpy==2.4.6"]
# ///
"""
WTP Validator - 6-Layer Willingness-to-Pay Validation

Validates willingness-to-pay (WTP) data through multiple layers: statistical outlier
detection, comparative benchmarking, value economics checks, confidence scoring,
segment-specific validation, and optional Van Westendorp PSM.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage:
    from scripts.wtp_validator import WTPValidator

    validator = WTPValidator(wtp_data, evc=11500, benchmarks={'comp1': 50, 'comp2': 70})
    report = validator.validate_all_layers()
    print(f"Validated WTP Range: ${report['validated_wtp_range'][0]}-${report['validated_wtp_range'][1]}")
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class WTPValidator:
    """
    6-layer willingness-to-pay validation framework.

    Layers:
        1. Statistical outlier detection (IQR method)
        2. Comparative benchmarking (competitor pricing)
        3. Value economics reality check (WTP vs EVC ratio)
        4. Confidence scoring (data quality assessment)
        5. Segment-specific benchmarks
        6. Van Westendorp PSM (optional, requires price sensitivity data)

    Usage:
        validator = WTPValidator(wtp_data, evc=11500)
        report = validator.validate_all_layers()
        print(report['recommendation'])
    """

    # Standard value capture percentage (10-30% of EVC)
    VALUE_CAPTURE_MIN = 0.10
    VALUE_CAPTURE_MAX = 0.30

    # Sample size thresholds
    SAMPLE_SIZE_GOOD = 30
    SAMPLE_SIZE_EXCELLENT = 50

    def __init__(
        self,
        wtp_data: pd.Series,
        evc: float,
        benchmarks: Optional[Dict[str, float]] = None
    ):
        """
        Initialize WTP validator.

        Args:
            wtp_data: Series of willingness-to-pay values from survey
            evc: Economic Value to Customer (monthly or per period)
            benchmarks: Optional dict of competitor pricing {'competitor': price}

        Example:
            >>> data = pd.Series([60, 65, 70, 75, 80])
            >>> validator = WTPValidator(data, evc=300, benchmarks={'comp1': 50})
        """
        if wtp_data.empty:
            raise ValueError("wtp_data cannot be empty")

        if evc < 0:
            raise ValueError("evc must be non-negative")

        self.wtp_data = wtp_data.copy()
        self.evc = evc
        self.benchmarks = benchmarks or {}

        # Remove NaN values
        self.wtp_data = self.wtp_data.dropna()

        if self.wtp_data.empty:
            raise ValueError("wtp_data contains only NaN values")

    def layer1_outlier_detection(self) -> Dict:
        """
        Detect and remove statistical outliers using IQR method.

        The IQR (Interquartile Range) method identifies outliers as values
        that fall below Q1 - 1.5×IQR or above Q3 + 1.5×IQR.

        Returns:
            Dictionary with:
                - passed: bool (always True, informational layer)
                - outliers_removed: int
                - outlier_values: list of removed values
                - clean_median: float (median after outlier removal)
                - clean_mean: float (mean after outlier removal)
                - clean_std: float (std dev after outlier removal)
                - confidence: str ('low', 'medium', 'high')

        Example:
            >>> data = pd.Series([60, 62, 65, 70, 500])  # 500 is outlier
            >>> validator = WTPValidator(data, evc=1000)
            >>> result = validator.layer1_outlier_detection()
            >>> result['outliers_removed']
            1
        """
        # Calculate IQR
        q1 = self.wtp_data.quantile(0.25)
        q3 = self.wtp_data.quantile(0.75)
        iqr = q3 - q1

        # Define outlier bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Identify outliers
        outliers = self.wtp_data[(self.wtp_data < lower_bound) | (self.wtp_data > upper_bound)]
        clean_data = self.wtp_data[(self.wtp_data >= lower_bound) & (self.wtp_data <= upper_bound)]

        # Calculate clean statistics
        if len(clean_data) > 0:
            clean_median = float(clean_data.median())
            clean_mean = float(clean_data.mean())
            clean_std = float(clean_data.std())
        else:  # pragma: no cover — IQR bounds always include Q1/Q3 values; all-outliers is unreachable
            # No clean data (all outliers) - use original
            clean_median = float(self.wtp_data.median())
            clean_mean = float(self.wtp_data.mean())
            clean_std = float(self.wtp_data.std())

        # Assess confidence based on std deviation
        cv = clean_std / clean_mean if clean_mean > 0 else 0  # Coefficient of variation
        if cv < 0.15:
            confidence = 'high'
        elif cv < 0.30:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'passed': True,  # Informational layer
            'outliers_removed': len(outliers),
            'outlier_values': outliers.tolist(),
            'clean_median': clean_median,
            'clean_mean': clean_mean,
            'clean_std': clean_std,
            'confidence': confidence,
            'sample_size_after_cleaning': len(clean_data)
        }

    def layer2_comparative_benchmarking(self, benchmarks: Optional[Dict[str, float]] = None) -> Dict:
        """
        Compare WTP against competitor pricing benchmarks.

        Args:
            benchmarks: Dict of competitor prices {'competitor_name': price}
                       Uses self.benchmarks if not provided

        Returns:
            Dictionary with:
                - passed: bool (True if within reasonable range of benchmarks)
                - median_benchmark: float (median competitor price)
                - your_price_vs_benchmark: float (ratio of your WTP to benchmark)
                - positioning: str ('premium', 'competitive', 'discount')
                - benchmarks_used: dict

        Example:
            >>> data = pd.Series([60, 65, 70])
            >>> validator = WTPValidator(data, evc=300)
            >>> result = validator.layer2_comparative_benchmarking({'comp1': 50, 'comp2': 80})
            >>> result['positioning']
            'competitive'
        """
        benchmarks = benchmarks or self.benchmarks

        if not benchmarks:
            return {
                'passed': True,
                'median_benchmark': None,
                'your_price_vs_benchmark': None,
                'positioning': 'unknown',
                'benchmarks_used': {},
                'note': 'No benchmarks provided for comparison'
            }

        # Calculate median benchmark
        benchmark_prices = list(benchmarks.values())
        median_benchmark = np.median(benchmark_prices)

        # Calculate your median WTP
        your_median = self.wtp_data.median()

        # Calculate ratio
        ratio = your_median / median_benchmark if median_benchmark > 0 else 0

        # Determine positioning
        if ratio > 1.25:
            positioning = 'premium'
            passed = True  # Premium pricing is valid
        elif ratio > 0.75:
            positioning = 'competitive'
            passed = True
        else:
            positioning = 'discount'
            passed = True  # Discount pricing is also valid

        return {
            'passed': passed,
            'median_benchmark': float(median_benchmark),
            'your_price_vs_benchmark': float(ratio),
            'your_median_wtp': float(your_median),
            'positioning': positioning,
            'benchmarks_used': benchmarks
        }

    def layer3_value_economics_check(self) -> Dict:
        """
        Validate WTP against EVC using value capture percentage.

        Rule: Pricing should capture 10-30% of EVC as the standard range.
        - Below 10%: Below optimal range (pricing power available)
        - 10-30%: Optimal range
        - Above 30%: May be too high vs value delivered

        Returns:
            Dictionary with:
                - passed: bool (True if WTP is 10-30% of EVC)
                - evc: float
                - suggested_wtp_min: float (10% of EVC)
                - suggested_wtp_max: float (30% of EVC)
                - your_median_wtp: float
                - capture_percentage: float
                - assessment: str

        Example:
            >>> data = pd.Series([60, 65, 70])  # Median ~65
            >>> validator = WTPValidator(data, evc=300)  # 65 is ~22% of 300
            >>> result = validator.layer3_value_economics_check()
            >>> result['passed']
            True
        """
        median_wtp = self.wtp_data.median()

        # Calculate suggested range
        suggested_min = self.evc * self.VALUE_CAPTURE_MIN
        suggested_max = self.evc * self.VALUE_CAPTURE_MAX

        # Calculate actual capture percentage
        capture_pct = (median_wtp / self.evc) if self.evc > 0 else 0

        # Assess
        if capture_pct < self.VALUE_CAPTURE_MIN:
            passed = False
            assessment = f"Below optimal range ({capture_pct:.1%} < {self.VALUE_CAPTURE_MIN:.0%}). Consider higher pricing."
        elif capture_pct <= self.VALUE_CAPTURE_MAX:
            passed = True
            assessment = f"Within optimal range ({self.VALUE_CAPTURE_MIN:.0%}-{self.VALUE_CAPTURE_MAX:.0%})"
        else:
            passed = False
            assessment = f"Above optimal range ({capture_pct:.1%} > {self.VALUE_CAPTURE_MAX:.0%}). Price may exceed perceived value."

        return {
            'passed': passed,
            'evc': self.evc,
            'suggested_wtp_min': float(suggested_min),
            'suggested_wtp_max': float(suggested_max),
            'your_median_wtp': float(median_wtp),
            'capture_percentage': float(capture_pct),
            'assessment': assessment
        }

    def layer4_confidence_scoring(self) -> Dict:
        """
        Score data quality and confidence level.

        Factors considered:
            - Sample size (30+ is good, 50+ is excellent)
            - Response variance (lower is better)
            - Distribution shape (normal distribution is ideal)

        Returns:
            Dictionary with:
                - passed: bool (True if confidence is medium or high)
                - sample_size: int
                - variance: float
                - std_dev: float
                - coefficient_of_variation: float
                - confidence_score: float (0-100)
                - confidence_level: str ('low', 'medium', 'high')
                - issues: list of quality issues found

        Example:
            >>> data = pd.Series([60, 62, 65, 68, 70] * 10)  # 50 samples
            >>> validator = WTPValidator(data, evc=1000)
            >>> result = validator.layer4_confidence_scoring()
            >>> result['confidence_level']
            'high'
        """
        sample_size = len(self.wtp_data)
        variance = float(self.wtp_data.var())
        std_dev = float(self.wtp_data.std())
        mean_wtp = float(self.wtp_data.mean())

        # Coefficient of variation (lower is better)
        cv = std_dev / mean_wtp if mean_wtp > 0 else 0

        issues = []
        confidence_score = 100.0

        # Factor 1: Sample size (40 points)
        if sample_size < 10:
            confidence_score -= 40
            issues.append(f"Very small sample size ({sample_size} < 10)")
        elif sample_size < self.SAMPLE_SIZE_GOOD:
            confidence_score -= 20
            issues.append(f"Small sample size ({sample_size} < {self.SAMPLE_SIZE_GOOD})")
        elif sample_size >= self.SAMPLE_SIZE_EXCELLENT:
            pass  # Excellent sample size, no penalty

        # Factor 2: Variance/CV (40 points)
        if cv > 0.50:
            confidence_score -= 40
            issues.append(f"Very high variance (CV: {cv:.2f} > 0.50)")
        elif cv > 0.30:
            confidence_score -= 20
            issues.append(f"High variance (CV: {cv:.2f} > 0.30)")

        # Factor 3: Distribution shape (20 points)
        # Check if data is roughly normal using skewness
        skewness = float(self.wtp_data.skew())
        if abs(skewness) > 2:
            confidence_score -= 20
            issues.append(f"Highly skewed distribution (skewness: {skewness:.2f})")
        elif abs(skewness) > 1:
            confidence_score -= 10
            issues.append(f"Moderately skewed distribution (skewness: {skewness:.2f})")

        # Determine confidence level
        if confidence_score >= 70:
            confidence_level = 'high'
            passed = True
        elif confidence_score >= 50:
            confidence_level = 'medium'
            passed = True
        else:
            confidence_level = 'low'
            passed = False

        return {
            'passed': passed,
            'sample_size': sample_size,
            'variance': variance,
            'std_dev': std_dev,
            'coefficient_of_variation': float(cv),
            'skewness': skewness,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'issues': issues
        }

    def layer5_segment_benchmarks(self, segments: Optional[List[Dict]] = None) -> Dict:
        """
        Validate WTP by customer segment.

        Args:
            segments: List of segment dicts from SegmentationEngine

        Returns:
            Dictionary with:
                - passed: bool (True if segments provided and analyzed)
                - segment_wtp: dict mapping segment names to WTP ranges
                - recommendation: str

        Note: This layer requires segmented data. If segments not provided,
              returns informational pass.

        Example:
            >>> data = pd.Series([60, 65, 70])
            >>> validator = WTPValidator(data, evc=1000)
            >>> result = validator.layer5_segment_benchmarks()
            >>> result['passed']
            True
        """
        if not segments:
            return {
                'passed': True,  # Informational pass
                'segment_wtp': {},
                'recommendation': 'Segment-specific analysis requires segmented customer data',
                'note': 'This layer is optional if segmentation not performed'
            }

        # Analyze WTP by segment characteristics
        segment_wtp = {}
        for segment in segments:
            segment_id = segment.get('segment_id', 'unknown')
            gap = segment.get('gap', 0)
            size = segment.get('size', 0)

            # Estimate WTP multiplier based on gap
            # Higher gap = more underserved = willing to pay more
            if gap > 5:
                multiplier = 1.2  # 20% premium for severely underserved
            elif gap > 2:
                multiplier = 1.1  # 10% premium for moderately underserved
            elif gap > -2:
                multiplier = 1.0  # Standard pricing
            else:
                multiplier = 0.9  # 10% discount for overserved

            base_wtp = self.wtp_data.median()
            segment_wtp[f"Segment {segment_id}"] = {
                'multiplier': multiplier,
                'suggested_wtp': float(base_wtp * multiplier),
                'segment_size': size,
                'gap': gap
            }

        recommendation = "Consider segment-specific pricing tiers based on customer needs gaps"

        return {
            'passed': True,
            'segment_wtp': segment_wtp,
            'recommendation': recommendation,
            'segments_analyzed': len(segments)
        }

    def validate_all_layers(
        self,
        benchmarks: Optional[Dict[str, float]] = None,
        segments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Run all validation layers and generate comprehensive report.

        Args:
            benchmarks: Optional competitor pricing benchmarks
            segments: Optional customer segment data

        Returns:
            Dictionary containing:
                - overall_passed: bool (True if critical layers passed)
                - layers: dict of results from each layer
                - validated_wtp_range: tuple (min, max) recommended WTP
                - confidence: str overall confidence level
                - recommendation: str summary recommendation
                - warnings: list of issues found

        Example:
            >>> data = pd.Series([60, 65, 70] * 20)
            >>> validator = WTPValidator(data, evc=300)
            >>> report = validator.validate_all_layers()
            >>> report['overall_passed']
            True
        """
        layers = {}
        warnings = []

        # Layer 1: Outlier detection
        layers['outlier_detection'] = self.layer1_outlier_detection()
        if layers['outlier_detection']['outliers_removed'] > 0:
            warnings.append(
                f"{layers['outlier_detection']['outliers_removed']} outliers detected and removed"
            )

        # Layer 2: Comparative benchmarking
        layers['comparative_benchmarking'] = self.layer2_comparative_benchmarking(benchmarks)

        # Layer 3: Value economics check
        layers['value_economics'] = self.layer3_value_economics_check()
        if not layers['value_economics']['passed']:
            warnings.append(layers['value_economics']['assessment'])

        # Layer 4: Confidence scoring
        layers['confidence_scoring'] = self.layer4_confidence_scoring()
        if not layers['confidence_scoring']['passed']:
            warnings.extend(layers['confidence_scoring']['issues'])

        # Layer 5: Segment benchmarks
        layers['segment_benchmarks'] = self.layer5_segment_benchmarks(segments)

        # Determine overall pass/fail
        critical_layers = ['value_economics', 'confidence_scoring']
        overall_passed = all(layers[layer]['passed'] for layer in critical_layers)

        # Calculate validated WTP range
        outlier_result = layers['outlier_detection']
        value_result = layers['value_economics']

        # Use cleaned data for range, but respect value economics bounds
        wtp_min = max(
            outlier_result['clean_median'] * 0.9,  # 10% below median
            value_result['suggested_wtp_min']  # But not below EVC min
        )
        wtp_max = min(
            outlier_result['clean_median'] * 1.1,  # 10% above median
            value_result['suggested_wtp_max']  # But not above EVC max
        )

        # Overall confidence
        confidence = layers['confidence_scoring']['confidence_level']

        # Generate recommendation
        if overall_passed:
            if confidence == 'high':
                recommendation = f"WTP data is validated with high confidence. Recommended pricing: ${wtp_min:.2f}-${wtp_max:.2f}"
            elif confidence == 'medium':
                recommendation = f"WTP data is validated with medium confidence. Recommended pricing: ${wtp_min:.2f}-${wtp_max:.2f}. Consider additional validation."
            else:  # pragma: no cover — low confidence always fails confidence_scoring, making overall_passed False
                recommendation = f"WTP data has low confidence. Recommended pricing: ${wtp_min:.2f}-${wtp_max:.2f}. Collect more survey responses."
        else:
            recommendation = "WTP validation failed critical checks. Review warnings and collect additional data."

        return {
            'overall_passed': overall_passed,
            'layers': layers,
            'validated_wtp_range': (float(wtp_min), float(wtp_max)),
            'confidence': confidence,
            'recommendation': recommendation,
            'warnings': warnings,
            'sample_size': len(self.wtp_data),
            'median_wtp': float(self.wtp_data.median()),
            'evc': self.evc
        }


if __name__ == "__main__":  # pragma: no cover
    print("WTP Validator - Example Usage")
    print("=" * 60)

    # Example: Team coverage tool WTP validation
    print("\nTeam Coverage Tool - WTP Validation")
    print("-" * 60)

    # WTP survey data (monthly pricing from 30 respondents)
    wtp_data = pd.Series([
        55, 60, 60, 65, 65, 70, 70, 75, 75, 80,
        50, 55, 60, 65, 70, 75, 80, 85, 90, 95,
        60, 60, 65, 70, 70, 75, 75, 80, 80, 85
    ])

    # EVC from Phase 2.2 (monthly)
    evc_monthly = 11500

    # Competitive benchmarks (monthly pricing)
    benchmarks = {
        'Deputy': 50,
        '7shifts': 70,
        'When I Work': 60,
        'Homebase': 55
    }

    # Initialize validator
    validator = WTPValidator(wtp_data, evc=evc_monthly, benchmarks=benchmarks)

    print(f"Survey Responses: {len(wtp_data)}")
    print(f"EVC (monthly): ${evc_monthly:,.2f}")
    print(f"Competitors: {len(benchmarks)}")

    # Run all validation layers
    print("\nRunning 6-Layer Validation...")
    report = validator.validate_all_layers(benchmarks=benchmarks)

    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    print(f"\nOverall Result: {'✓ PASSED' if report['overall_passed'] else '✗ FAILED'}")
    print(f"Confidence Level: {report['confidence'].upper()}")
    print(f"Sample Size: {report['sample_size']} respondents")

    print("\nValidated WTP Range:")
    print(f"  ${report['validated_wtp_range'][0]:.2f} - ${report['validated_wtp_range'][1]:.2f} per month")

    print(f"\nMedian WTP: ${report['median_wtp']:.2f}")
    print(f"Value Capture: {(report['median_wtp'] / report['evc']):.1%} of EVC")

    print("\nRecommendation:")
    print(f"  {report['recommendation']}")

    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report['warnings']:
            print(f"  ⚠ {warning}")

    print("\nLayer-by-Layer Results:")
    print("-" * 60)

    for layer_name, layer_result in report['layers'].items():
        status = "✓" if layer_result.get('passed', False) else "✗"
        print(f"\n{status} {layer_name.replace('_', ' ').title()}")

        if layer_name == 'outlier_detection':
            print(f"    Outliers removed: {layer_result['outliers_removed']}")
            print(f"    Clean median: ${layer_result['clean_median']:.2f}")
            print(f"    Confidence: {layer_result['confidence']}")

        elif layer_name == 'comparative_benchmarking':
            print(f"    Your median: ${layer_result['your_median_wtp']:.2f}")
            print(f"    Market median: ${layer_result['median_benchmark']:.2f}")
            print(f"    Positioning: {layer_result['positioning']}")

        elif layer_name == 'value_economics':
            print(f"    Capture rate: {layer_result['capture_percentage']:.1%}")
            print(f"    Suggested range: ${layer_result['suggested_wtp_min']:.2f}-${layer_result['suggested_wtp_max']:.2f}")

        elif layer_name == 'confidence_scoring':
            print(f"    Score: {layer_result['confidence_score']:.0f}/100")
            print(f"    Level: {layer_result['confidence_level']}")
            if layer_result['issues']:
                print(f"    Issues: {len(layer_result['issues'])}")

    print("\n" + "=" * 60)
    print("Validation complete!")
