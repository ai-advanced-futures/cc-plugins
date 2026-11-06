# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Market Sizing Calculator for Discovery Stage Financial Analysis.

This module provides comprehensive market sizing calculations including:
- TAM/SAM/SOM calculations (top-down, bottom-up, value theory)
- Revenue opportunity by customer segment
- CAC calculations for 6 channels (Inbound, Outbound, PLG, Partnerships, Enterprise, Community)
- Blended metrics (weighted CAC, payback, LTV:CAC)
- Validation and health checks
- JTBD integration for WTP and segment data

Based on industry-standard frameworks:
- TAM/SAM/SOM methodology from VC/startup ecosystem
- CAC benchmarks from SaaS capital surveys
- Unit economics from David Skok, Brad Feld, Tomasz Tunguz

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import argparse
import dataclasses
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.input_check import build, check, limits  # noqa: E402
from scripts.utils.calculators import calculate_channel_economics  # noqa: E402
from scripts.utils.enums import MetricHealth  # noqa: E402


class TAMMethod(str, Enum):
    """TAM calculation methodology."""

    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"
    VALUE_THEORY = "value_theory"
    STATED = "stated"


class AcquisitionChannel(str, Enum):
    """Customer acquisition channels."""

    INBOUND_MARKETING = "inbound_marketing"
    OUTBOUND_SALES = "outbound_sales"
    PRODUCT_LED_GROWTH = "product_led_growth"
    PARTNERSHIPS = "partnerships"
    FIELD_SALES = "field_sales"
    COMMUNITY = "community"


# ============================================================================
# Input Models
# ============================================================================


@dataclass
class TAMInput:
    """Input for TAM calculation."""

    method: TAMMethod
    # Top-down inputs
    total_market_size: Optional[float] = limits(gt=0, default=None)
    icp_filter_percent: Optional[float] = limits(gt=0, le=100, default=None)
    # Bottom-up inputs
    potential_customers: Optional[int] = limits(gt=0, default=None)
    target_acv: Optional[float] = limits(gt=0, default=None)
    # Value theory inputs
    economic_value_per_customer: Optional[float] = limits(gt=0, default=None)
    value_capture_percent: Optional[float] = limits(gt=0, le=100, default=None)


@dataclass
class SAMInput:
    """Input for SAM calculation."""

    tam: float = limits(gt=0)
    geographic_filter: float = limits(gt=0, le=100)  # % of TAM geographically accessible
    customer_size_filter: float = limits(gt=0, le=100)  # % of TAM by customer size
    channel_filter: float = limits(gt=0, le=100)  # % of TAM by channel capability


@dataclass
class SOMInput:
    """Input for SOM calculation."""

    sam: float = limits(gt=0)
    timeframe_years: int = limits(gt=0, le=10)
    market_share_percent: float = limits(gt=0, le=100)


@dataclass
class CustomerSegment:
    """Customer segment definition."""

    segment_name: str
    potential_customers: int = limits(gt=0)
    target_acv: float = limits(gt=0)
    conversion_rate_pct: float = limits(gt=0, le=100)
    acquisition_difficulty: str = limits(one_of=("low", "medium", "high"))
    willingness_to_pay: Optional[float] = limits(gt=0, default=None)
    wtp_source: Optional[str] = None


@dataclass
class InboundMarketingInput:
    """Inbound marketing channel inputs."""

    monthly_spend: float = limits(gt=0)
    mqls_per_month: int = limits(gt=0)
    mql_to_customer_pct: float = limits(gt=0, le=100)


@dataclass
class OutboundSalesInput:
    """Outbound sales channel inputs."""

    sdrs: int = limits(gt=0)
    sdr_cost_annual: float = limits(gt=0)
    opps_per_sdr_monthly: int = limits(gt=0)
    aes: int = limits(gt=0)
    ae_cost_annual: float = limits(gt=0)
    opp_to_close_pct: float = limits(gt=0, le=100)


@dataclass
class PLGInput:
    """Product-Led Growth channel inputs."""

    free_users_monthly: int = limits(gt=0)
    free_to_paid_pct: float = limits(gt=0, le=100)
    cost_per_signup: float = limits(gt=0)


@dataclass
class PartnershipsInput:
    """Partnerships channel inputs."""

    active_partners: int = limits(gt=0)
    commission_pct: float = limits(gt=0, le=100)
    average_acv: float = limits(gt=0)
    customers_per_partner_quarterly: int = limits(gt=0)


@dataclass
class FieldSalesInput:
    """Field sales (Enterprise) channel inputs."""

    enterprise_aes: int = limits(gt=0)
    ae_cost_annual: float = limits(gt=0)
    deals_per_ae_annual: int = limits(gt=0)


@dataclass
class CommunityInput:
    """Community-led growth channel inputs."""

    monthly_investment: float = limits(gt=0)
    conversions_monthly: int = limits(gt=0)


@dataclass
class AssumptionsInput:
    """Complete assumptions input model."""

    # Market sizing
    tam: TAMInput
    sam_filters: Dict[str, float]
    som_timeframe_years: int = limits(gt=0, le=10)
    som_market_share_pct: float = limits(gt=0, le=100)

    # Customer segments
    segments: List[CustomerSegment]

    # Unit economics for LTV calculation
    average_acv: float = limits(gt=0)
    gross_margin_pct: float = limits(gt=0, le=100)
    monthly_churn_pct: float = limits(gt=0, le=100)

    # Channel inputs (all optional)
    inbound_marketing: Optional[InboundMarketingInput] = None
    outbound_sales: Optional[OutboundSalesInput] = None
    plg: Optional[PLGInput] = None
    partnerships: Optional[PartnershipsInput] = None
    field_sales: Optional[FieldSalesInput] = None
    community: Optional[CommunityInput] = None


# The input classes, in definition order.
INPUT_CLASSES = (
    TAMInput,
    SAMInput,
    SOMInput,
    CustomerSegment,
    InboundMarketingInput,
    OutboundSalesInput,
    PLGInput,
    PartnershipsInput,
    FieldSalesInput,
    CommunityInput,
    AssumptionsInput,
)


# ============================================================================
# Loading the assumptions file
# ============================================================================

EXIT_INPUTS = 3

# The inputs each TAM method needs; calculate_tam keeps its own checks too.
TAM_METHOD_INPUTS: Dict[str, tuple[str, ...]] = {
    "top_down": ("total_market_size", "icp_filter_percent"),
    "bottom_up": ("potential_customers", "target_acv"),
    "value_theory": ("economic_value_per_customer", "value_capture_percent", "potential_customers"),  # noqa: E501
    "stated": ("total_market_size",),
}

# Segment fields read from setup's market.target_segments by the same name.
_SEGMENT_SAME_NAME_FIELDS = (
    "segment_name", "acquisition_difficulty", "willingness_to_pay", "wtp_source",
    "target_acv", "conversion_rate_pct",
)


class AssumptionsProblem(Exception):
    """One or more inputs are missing or invalid. Each problem is one line."""

    def __init__(self, problems: List[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def _drop_none(value: Any) -> Any:
    """Remove every null key, at any depth: a null is not given.

    A null list item stays, so a segment keeps its index in the file; the segment
    readers skip it.
    """
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _given(items: List[Any]) -> List[Any]:
    return [item for item in items if item is not None]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _positive(value: Any) -> bool:
    return _is_number(value) and value > 0


def _show(value: Any) -> str:
    """The value as the person wrote it in JSON: 120, -1234567, 100.00004, true, "500M"."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return json.dumps(value)


# The setup values each mapped input is computed from, in market (spec §2 decision 2).
_RATIO_INPUTS = {
    "sam_filters": ("sam", "tam"),
    "som_market_share_pct": ("som", "sam"),
}


def _why_missing(name: str, market: Dict[str, Any], tam_named: bool, shares: bool) -> List[str]:
    """At most one line for a missing mapped input.

    The first present-but-unusable setup value is named with its source and reason. A
    bad market.tam already reported as tam.total_market_size is not reported again.
    A plain `<name>: missing` stays when a value is absent or none is unusable, and
    when setup's shares are not used (`shares` is False).
    """
    if name == "segments" and "target_segments" in market:
        return [f"segments = {_show(market['target_segments'])} (market.target_segments): not a list"]  # noqa: E501
    if name not in _RATIO_INPUTS or not shares:
        return [f"{name}: missing"]
    keys = _RATIO_INPUTS[name]
    bad = [k for k in keys if k in market and not _positive(market[k])]
    shown = [k for k in bad if not (k == "tam" and tam_named)]
    if shown:
        reason = "not above 0" if _is_number(market[shown[0]]) else "not a number"
        return [f"{name} = {_show(market[shown[0]])} (market.{shown[0]}): {reason}"]
    absent = any(k not in market for k in keys)
    return [f"{name}: missing"] if absent or not bad else []


def _segment_key(entry: Any) -> Optional[str]:
    if isinstance(entry, dict) and isinstance(entry.get("segment_name"), str):
        return entry["segment_name"].strip().casefold()
    return None


# Segment fields that hold numbers; a setup value there is used only when it is one.
_SEGMENT_NUMBER_FIELDS = ("potential_customers", "willingness_to_pay", "target_acv", "conversion_rate_pct")  # noqa: E501

# Setup values that feed a ratio, and the inputs each one feeds.
_RATIO_FEEDS = {
    "tam": ("sam_filters",),
    "sam": ("sam_filters", "som_market_share_pct"),
    "som": ("som_market_share_pct",),
}


def _uses_setups_shares(data: Dict[str, Any], market: Dict[str, Any]) -> bool:
    """False when the file gives a tam of its own: setup's sam/tam and som/sam are
    shares of setup's TAM, not of that one."""
    return "tam" not in data or data["tam"] == {
        "method": TAMMethod.STATED.value, "total_market_size": market.get("tam")}


def _map_nested(
    data: Dict[str, Any], sources: Dict[tuple, str], rejected: Dict[tuple, tuple]
) -> Dict[str, Any]:
    """Map setup's nested shape onto AssumptionsInput fields (spec §2 decision 2).

    A setup number is used only when it is a JSON number; any other value is left
    out and kept in `rejected` (location -> (value, source)) to be named.
    """
    mapped: Dict[str, Any] = {}
    market = data.get("market") if isinstance(data.get("market"), dict) else {}
    tam, sam, som = market.get("tam"), market.get("sam"), market.get("som")

    def take(loc: tuple, value: Any, source: str) -> bool:
        if _is_number(value):
            sources[loc] = source
            return True
        rejected[loc] = (value, source)
        return False

    if "tam" in market and take(("tam", "total_market_size"), tam, "market.tam"):
        mapped["tam"] = {"method": TAMMethod.STATED.value, "total_market_size": tam}
    shares = _uses_setups_shares(data, market)
    if shares and _positive(sam) and _positive(tam):
        mapped["sam_filters"] = {"geographic": sam / tam * 100}
        sources[("sam_filters", "geographic")] = "market.sam / market.tam"
    landscape = market.get("competitive_landscape")
    if shares and _positive(som) and _positive(sam):
        mapped["som_market_share_pct"] = som / sam * 100
        sources[("som_market_share_pct",)] = "market.som / market.sam"
    elif isinstance(landscape, dict) and "market_share_target_pct" in landscape:
        share = landscape["market_share_target_pct"]
        if take(("som_market_share_pct",), share, "market.competitive_landscape.market_share_target_pct"):  # noqa: E501
            mapped["som_market_share_pct"] = share
    retention = data.get("retention")
    if isinstance(retention, dict) and "monthly_churn_rate_pct" in retention:
        churn = retention["monthly_churn_rate_pct"]
        if take(("monthly_churn_pct",), churn, "retention.monthly_churn_rate_pct"):
            mapped["monthly_churn_pct"] = churn

    nested_segments = market.get("target_segments")
    if isinstance(nested_segments, list):
        segments = []
        for i, entry in enumerate(nested_segments):
            if entry is None:
                continue
            if not isinstance(entry, dict):
                segments.append(entry)
                continue
            segment: Dict[str, Any] = {}
            at = len(segments)  # its place in the merged list; i is its place in the file
            for field, nested_field in [(f, f) for f in _SEGMENT_SAME_NAME_FIELDS] + [("potential_customers", "size")]:  # noqa: E501
                if nested_field not in entry:
                    continue
                source = f"market.target_segments[{i}].{nested_field}"
                if field not in _SEGMENT_NUMBER_FIELDS:
                    segment[field] = entry[nested_field]
                    sources[("segments", at, field)] = source
                elif take(("segments", at, field), entry[nested_field], source):
                    segment[field] = entry[nested_field]
            segments.append(segment)
        mapped["segments"] = segments
    return mapped


def _merge_segments(
    nested: List[Any], top: List[Any], sources: Dict[tuple, str], rejected: Dict[tuple, tuple]
) -> List[Any]:
    """Top-level segments win field by field over a nested one of the same name."""
    merged = [dict(e) if isinstance(e, dict) else e for e in nested]
    by_key = {}
    for i, entry in enumerate(merged):
        key = _segment_key(entry)
        if key is not None and key not in by_key:
            by_key[key] = i
    for entry in top:
        key = _segment_key(entry)
        if key is not None and key in by_key:
            i = by_key[key]
            merged[i].update(entry)
            for field in entry:
                sources.pop(("segments", i, field), None)
                rejected.pop(("segments", i, field), None)
        else:
            merged.append(entry)
    return merged


def _problem_name(loc: tuple, merged: Dict[str, Any]) -> str:
    if len(loc) >= 2 and loc[0] == "segments" and isinstance(loc[1], int):
        segments = merged.get("segments")
        entry = segments[loc[1]] if isinstance(segments, list) and loc[1] < len(segments) else None  # noqa: E501
        name = entry.get("segment_name") if isinstance(entry, dict) else None
        label = name if isinstance(name, str) and name.strip() else str(loc[1])
        return ".".join([f"segments[{label}]", *(str(part) for part in loc[2:])])
    return ".".join(str(part) for part in loc)


def load_assumptions(data: Dict[str, Any]) -> AssumptionsInput:
    """Load setup's nested shape, the flat shape, or both (spec §2 decisions 1-4).

    A top-level key named like an AssumptionsInput field wins over its mapped value.
    Raises AssumptionsProblem naming every missing or invalid input at once.
    """
    data = _drop_none(data if isinstance(data, dict) else {})
    sources: Dict[tuple, str] = {}
    rejected: Dict[tuple, tuple] = {}
    merged = _map_nested(data, sources, rejected)
    for field in (f.name for f in dataclasses.fields(AssumptionsInput)):
        if field not in data:
            continue
        if field == "segments" and isinstance(data[field], list) and isinstance(merged.get(field), list):  # noqa: E501
            merged[field] = _merge_segments(merged[field], _given(data[field]), sources, rejected)  # noqa: E501
            continue
        merged[field] = _given(data[field]) if isinstance(data[field], list) else data[field]
        for found in (sources, rejected):
            for key in [k for k in found if k[0] == field]:
                del found[key]

    market = data.get("market") if isinstance(data.get("market"), dict) else {}
    shares = _uses_setups_shares(data, market)
    problems: List[str] = []
    # A setup value that is not a JSON number is named once, by the first input it
    # feeds that the file does not give itself; the inputs it leaves missing are not
    # listed again.
    explained = set()
    for loc, (value, source) in rejected.items():
        name = _problem_name(loc, merged)
        problems.append(f"{name} = {_show(value)} ({source}): not a number")
        explained.add(name)
        if loc == ("tam", "total_market_size"):
            explained.update(("tam", *_RATIO_FEEDS["tam"]))
    for key, feeds in _RATIO_FEEDS.items() if shares else ():
        open_feeds = [f for f in feeds if f not in data]
        if key not in market or _is_number(market[key]) or not open_feeds:
            continue
        if not (key == "tam" and ("tam", "total_market_size") in rejected):
            problems.append(f"{open_feeds[0]} = {_show(market[key])} (market.{key}): not a number")  # noqa: E501
        explained.update(open_feeds)
    tam = merged.get("tam")
    method = tam.get("method") if isinstance(tam, dict) else None
    if isinstance(method, str) and method in TAM_METHOD_INPUTS:
        problems.extend(
            f"tam.{name}: missing" for name in TAM_METHOD_INPUTS[method] if name not in tam
        )
    sam_filters = merged.get("sam_filters")
    if isinstance(sam_filters, dict):
        for key, value in sam_filters.items():
            if _is_number(value) and 0 < value <= 100:
                continue
            source = sources.get(("sam_filters", key))
            where = f" ({source})" if source else ""
            if not _is_number(value):
                reason = "not a number"
                explained.add(f"sam_filters.{key}")
            else:
                reason = "above 100" if value > 100 else "not above 0"
            problems.append(f"sam_filters.{key} = {_show(value)}{where}: {reason}")

    missing: List[str] = []
    assumptions, found = check(AssumptionsInput, merged)
    for p in found:
        name = _problem_name(p.loc, merged)
        if p.kind == "missing":
            missing.append(name)
            continue
        if name in explained and name.startswith("sam_filters."):
            continue
        source = sources.get(p.loc)
        where = f" ({source})" if source else ""
        problems.append(f"{name} = {_show(p.value)}{where}: {p.reason}")
    # Only after every invalid line is known: a mapped input missing because of a bad
    # setup value names that value, unless its line is already there.
    tam_named = any(p.startswith("tam.total_market_size = ") and " (market.tam): " in p for p in problems)  # noqa: E501
    for name in [m for m in missing if m not in explained]:
        problems.extend(_why_missing(name, market, tam_named, shares) if name not in data else [f"{name}: missing"])  # noqa: E501

    if problems or not isinstance(assumptions, AssumptionsInput):
        raise AssumptionsProblem(list(dict.fromkeys(problems)) or ["assumptions: not valid"])
    return assumptions


# ============================================================================
# Output Models
# ============================================================================


@dataclass
class TAMResult:
    """TAM calculation result."""

    value: float
    calculation_method: str
    assumptions: Dict[str, Any]


@dataclass
class SAMResult:
    """SAM calculation result."""

    value: float
    filters: Dict[str, float]
    sam_to_tam_ratio: float


@dataclass
class SOMResult:
    """SOM calculation result."""

    value: float
    timeframe_years: int
    market_share_pct: float
    som_to_sam_ratio: float


@dataclass
class SegmentOpportunity:
    """Revenue opportunity for a customer segment."""

    segment_name: str
    potential_customers: int
    target_acv: float
    conversion_rate_pct: float
    acquisition_difficulty: str
    revenue_opportunity: float
    willingness_to_pay: Optional[float] = None
    wtp_source: Optional[str] = None


@dataclass
class ChannelCAC:
    """CAC analysis for an acquisition channel."""

    channel: str
    cac: float
    customers_per_month: float
    monthly_cost: float
    cac_payback_months: Optional[float]
    ltv_cac_ratio: Optional[float]
    efficiency_rank: int
    notes: Optional[str] = None


@dataclass
class BlendedMetrics:
    """Blended metrics across all channels."""

    blended_cac: float
    total_customers_per_month: float
    total_monthly_cost: float
    weighted_cac_payback_months: float
    weighted_ltv_cac_ratio: float


@dataclass
class DiscoveryReport:
    """Complete discovery stage financial analysis report."""

    market_sizing: Dict[str, Any]
    customer_segments: List[SegmentOpportunity]
    revenue_opportunity: Dict[str, Any]
    cac_by_channel: List[ChannelCAC]
    blended_metrics: BlendedMetrics
    jtbd_integration: Dict[str, Any]
    health_assessment: Dict[str, str]
    recommendations: Dict[str, Any]
    metadata: Dict[str, str]


# ============================================================================
# Calculation Functions
# ============================================================================


def calculate_tam(tam_input: TAMInput) -> TAMResult:
    """Calculate Total Addressable Market.

    Args:
        tam_input: TAM calculation inputs

    Returns:
        TAMResult with calculated value and assumptions

    Raises:
        ValueError: If required inputs for method are missing
    """
    if tam_input.method == TAMMethod.TOP_DOWN:
        if tam_input.total_market_size is None or tam_input.icp_filter_percent is None:
            raise ValueError("Top-down method requires total_market_size and icp_filter_percent")
        tam = tam_input.total_market_size * (tam_input.icp_filter_percent / 100)
        assumptions = {
            "total_market_size": tam_input.total_market_size,
            "icp_filter_percent": tam_input.icp_filter_percent,
        }

    elif tam_input.method == TAMMethod.BOTTOM_UP:
        if tam_input.potential_customers is None or tam_input.target_acv is None:
            raise ValueError("Bottom-up method requires potential_customers and target_acv")
        tam = tam_input.potential_customers * tam_input.target_acv
        assumptions = {
            "potential_customers": tam_input.potential_customers,
            "target_acv": tam_input.target_acv,
        }

    elif tam_input.method == TAMMethod.VALUE_THEORY:
        if (
            tam_input.economic_value_per_customer is None
            or tam_input.value_capture_percent is None
            or tam_input.potential_customers is None
        ):
            raise ValueError(
                "Value theory requires economic_value_per_customer, value_capture_percent, and potential_customers"  # noqa: E501
            )
        price = tam_input.economic_value_per_customer * (tam_input.value_capture_percent / 100)
        tam = tam_input.potential_customers * price
        assumptions = {
            "economic_value_per_customer": tam_input.economic_value_per_customer,
            "value_capture_percent": tam_input.value_capture_percent,
            "potential_customers": tam_input.potential_customers,
            "calculated_price": price,
        }

    elif tam_input.method == TAMMethod.STATED:
        if tam_input.total_market_size is None:
            raise ValueError("Stated method requires total_market_size")
        tam = tam_input.total_market_size
        assumptions = {"total_market_size": tam_input.total_market_size}

    else:
        raise ValueError(f"Unknown TAM method: {tam_input.method}")

    return TAMResult(value=tam, calculation_method=tam_input.method.value, assumptions=assumptions)


def calculate_sam(sam_input: SAMInput) -> SAMResult:
    """Calculate Serviceable Addressable Market.

    Args:
        sam_input: SAM calculation inputs

    Returns:
        SAMResult with calculated value and filters applied
    """
    sam = sam_input.tam * (
        (sam_input.geographic_filter / 100)
        * (sam_input.customer_size_filter / 100)
        * (sam_input.channel_filter / 100)
    )

    filters = {
        "geographic": sam_input.geographic_filter,
        "customer_size": sam_input.customer_size_filter,
        "channel": sam_input.channel_filter,
    }

    return SAMResult(value=sam, filters=filters, sam_to_tam_ratio=sam / sam_input.tam)


def calculate_som(som_input: SOMInput) -> SOMResult:
    """Calculate Serviceable Obtainable Market.

    Args:
        som_input: SOM calculation inputs

    Returns:
        SOMResult with calculated value and market share
    """
    som = som_input.sam * (som_input.market_share_percent / 100)

    return SOMResult(
        value=som,
        timeframe_years=som_input.timeframe_years,
        market_share_pct=som_input.market_share_percent,
        som_to_sam_ratio=som / som_input.sam,
    )


def calculate_ltv(average_acv: float, gross_margin_pct: float, monthly_churn_pct: float) -> float:
    """Calculate Customer Lifetime Value.

    Formula: LTV = (ACV / 12) × (1 / monthly_churn_rate) × gross_margin
    Or equivalently: LTV = ACV × (1 / annual_churn_rate) × gross_margin

    Args:
        average_acv: Annual Contract Value in dollars
        gross_margin_pct: Gross margin percentage (0-100)
        monthly_churn_pct: Monthly churn rate percentage (0-100)

    Returns:
        LTV in dollars

    Example:
        >>> calculate_ltv(12000, 75, 3.0)
        24750.0
        # Explanation: $12,000/year ACV, 3% monthly churn = 33.33 month lifetime (2.78 years)
        # LTV = ($12,000 / 12) × (1 / 0.03) × 0.75 = $1,000 × 33.33 × 0.75 = $24,750
    """
    monthly_revenue = average_acv / 12
    customer_lifetime_months = 1 / (monthly_churn_pct / 100)
    gross_margin_decimal = gross_margin_pct / 100

    ltv = monthly_revenue * customer_lifetime_months * gross_margin_decimal
    return ltv


def calculate_segment_opportunity(segment: CustomerSegment) -> SegmentOpportunity:
    """Calculate revenue opportunity for a customer segment.

    Args:
        segment: Customer segment definition

    Returns:
        SegmentOpportunity with calculated revenue potential
    """
    revenue_opportunity = (
        segment.potential_customers * segment.target_acv * (segment.conversion_rate_pct / 100)
    )

    return SegmentOpportunity(
        segment_name=segment.segment_name,
        potential_customers=segment.potential_customers,
        target_acv=segment.target_acv,
        conversion_rate_pct=segment.conversion_rate_pct,
        acquisition_difficulty=segment.acquisition_difficulty,
        revenue_opportunity=revenue_opportunity,
        willingness_to_pay=segment.willingness_to_pay,
        wtp_source=segment.wtp_source,
    )


def calculate_inbound_cac(
    input_data: InboundMarketingInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float  # noqa: E501
) -> ChannelCAC:
    """Calculate CAC for inbound marketing channel."""
    customers_per_month = input_data.mqls_per_month * (input_data.mql_to_customer_pct / 100)
    cac = input_data.monthly_spend / customers_per_month

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="inbound_marketing",
        cac=cac,
        customers_per_month=customers_per_month,
        monthly_cost=input_data.monthly_spend,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,  # Will be set later
    )


def calculate_outbound_cac(
    input_data: OutboundSalesInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float  # noqa: E501
) -> ChannelCAC:
    """Calculate CAC for outbound sales channel."""
    opps_per_month = input_data.sdrs * input_data.opps_per_sdr_monthly
    customers_per_month = opps_per_month * (input_data.opp_to_close_pct / 100)
    monthly_cost = (input_data.sdrs * input_data.sdr_cost_annual + input_data.aes * input_data.ae_cost_annual) / 12  # noqa: E501
    cac = monthly_cost / customers_per_month

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="outbound_sales",
        cac=cac,
        customers_per_month=customers_per_month,
        monthly_cost=monthly_cost,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,
    )


def calculate_plg_cac(
    input_data: PLGInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float
) -> ChannelCAC:
    """Calculate CAC for product-led growth channel."""
    customers_per_month = input_data.free_users_monthly * (input_data.free_to_paid_pct / 100)
    cac = input_data.cost_per_signup / (input_data.free_to_paid_pct / 100)
    monthly_cost = input_data.free_users_monthly * input_data.cost_per_signup

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="product_led_growth",
        cac=cac,
        customers_per_month=customers_per_month,
        monthly_cost=monthly_cost,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,
    )


def calculate_partnerships_cac(
    input_data: PartnershipsInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float  # noqa: E501
) -> ChannelCAC:
    """Calculate CAC for partnerships channel."""
    customers_per_month = (input_data.active_partners * input_data.customers_per_partner_quarterly) / 3  # noqa: E501
    cac = input_data.average_acv * (input_data.commission_pct / 100)
    monthly_cost = customers_per_month * cac

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="partnerships",
        cac=cac,
        customers_per_month=customers_per_month,
        monthly_cost=monthly_cost,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,
    )


def calculate_field_sales_cac(
    input_data: FieldSalesInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float  # noqa: E501
) -> ChannelCAC:
    """Calculate CAC for field sales (enterprise) channel."""
    customers_per_month = (input_data.enterprise_aes * input_data.deals_per_ae_annual) / 12
    monthly_cost = (input_data.enterprise_aes * input_data.ae_cost_annual) / 12
    cac = monthly_cost / customers_per_month

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="field_sales",
        cac=cac,
        customers_per_month=customers_per_month,
        monthly_cost=monthly_cost,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,
        notes="High CAC justified by high-ACV enterprise deals" if cac > 50000 else None,
    )


def calculate_community_cac(
    input_data: CommunityInput, average_acv: float, gross_margin_pct: float, monthly_churn_pct: float  # noqa: E501
) -> ChannelCAC:
    """Calculate CAC for community-led growth channel."""
    cac = input_data.monthly_investment / input_data.conversions_monthly

    economics = calculate_channel_economics(
        cac=cac,
        arpu=average_acv / 12,
        gross_margin=gross_margin_pct / 100,
        monthly_churn_rate=monthly_churn_pct / 100,
    )

    return ChannelCAC(
        channel="community",
        cac=cac,
        customers_per_month=input_data.conversions_monthly,
        monthly_cost=input_data.monthly_investment,
        cac_payback_months=economics["payback_months"],
        ltv_cac_ratio=economics["ltv_cac_ratio"],
        efficiency_rank=0,
    )


def calculate_blended_metrics(channels: List[ChannelCAC]) -> BlendedMetrics:
    """Calculate blended metrics across all channels.

    Args:
        channels: List of channel CAC results

    Returns:
        BlendedMetrics with weighted averages
    """
    total_cost = sum(ch.monthly_cost for ch in channels)
    total_customers = sum(ch.customers_per_month for ch in channels)
    blended_cac = total_cost / total_customers if total_customers > 0 else 0

    # Weighted payback and LTV:CAC (skip channels where the value is None)
    weighted_payback = (
        sum((ch.cac_payback_months or 0.0) * ch.customers_per_month for ch in channels) / total_customers  # noqa: E501
        if total_customers > 0 else 0.0
    )
    weighted_ltv_cac = (
        sum((ch.ltv_cac_ratio or 0.0) * ch.customers_per_month for ch in channels) / total_customers
        if total_customers > 0 else 0.0
    )

    return BlendedMetrics(
        blended_cac=blended_cac,
        total_customers_per_month=total_customers,
        total_monthly_cost=total_cost,
        weighted_cac_payback_months=weighted_payback,
        weighted_ltv_cac_ratio=weighted_ltv_cac,
    )


def assess_market_opportunity_health(som: float, som_to_sam_ratio: float) -> MetricHealth:
    """Assess health of market opportunity.

    Args:
        som: Serviceable Obtainable Market value
        som_to_sam_ratio: SOM as percentage of SAM

    Returns:
        MetricHealth assessment
    """
    if som > 50_000_000 and som_to_sam_ratio < 0.1:
        return MetricHealth.EXCELLENT
    elif som >= 10_000_000 and som_to_sam_ratio < 0.15:
        return MetricHealth.GOOD
    elif som < 10_000_000 or som_to_sam_ratio > 0.2:
        return MetricHealth.WARNING
    else:
        return MetricHealth.CRITICAL


def assess_cac_efficiency_health(blended_payback: float, blended_ltv_cac: float) -> MetricHealth:
    """Assess health of CAC efficiency.

    Args:
        blended_payback: Blended CAC payback in months
        blended_ltv_cac: Blended LTV:CAC ratio

    Returns:
        MetricHealth assessment
    """
    if blended_payback < 6 and blended_ltv_cac > 5:
        return MetricHealth.EXCELLENT
    elif blended_payback <= 12 and blended_ltv_cac >= 3:
        return MetricHealth.GOOD
    elif blended_payback <= 18 or blended_ltv_cac >= 1.5:
        return MetricHealth.WARNING
    else:
        return MetricHealth.CRITICAL


def load_jtbd_data(jtbd_file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JTBD market analysis data if available.

    Args:
        jtbd_file_path: Path to a jtbd-market-discovery result file
            (`.jtbd-market-discovery/results/*.json`)

    Returns:
        JTBD data dictionary or None if file doesn't exist or is malformed
    """
    if not jtbd_file_path.exists():
        return None

    try:
        with open(jtbd_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load JTBD data from {jtbd_file_path}: {e}", file=sys.stderr)
        return None


def integrate_jtbd_data(
    assumptions: AssumptionsInput,
    jtbd_data: Optional[Dict[str, Any]],
    source_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Integrate JTBD data into discovery analysis.

    Args:
        assumptions: Financial assumptions
        jtbd_data: JTBD analysis data (or None)
        source_file: The JTBD file the data was read from, as given on the command line

    Returns:
        Integration metadata
    """
    if jtbd_data is None:
        return {
            "data_imported": False,
            "source_file": None,
            "segments_imported": 0,
            "wtp_data_available": False,
        }

    # Count segments with WTP data
    segments_with_wtp = sum(1 for seg in assumptions.segments if seg.willingness_to_pay is not None)

    return {
        "data_imported": True,
        "source_file": source_file,
        "segments_imported": len(assumptions.segments),
        "wtp_data_available": segments_with_wtp > 0,
    }


def generate_recommendations(
    market_health: MetricHealth,
    cac_health: MetricHealth,
    channels: List[ChannelCAC],
    segments: List[SegmentOpportunity],
) -> Dict[str, Any]:
    """Generate actionable recommendations based on analysis.

    Args:
        market_health: Market opportunity health status
        cac_health: CAC efficiency health status
        channels: List of channel results
        segments: List of segment opportunities

    Returns:
        Recommendations dictionary
    """
    # Sort channels by CAC efficiency
    sorted_channels = sorted(channels, key=lambda ch: ch.cac)

    # Primary channel (most efficient with reasonable volume)
    primary_channel = sorted_channels[0].channel if sorted_channels else None

    # Secondary channels (next 2 most efficient)
    secondary_channels = [ch.channel for ch in sorted_channels[1:3]]

    # Channels to avoid/delay (those with payback > 12 months; skip channels where payback is None)
    avoid_channels = [ch.channel for ch in channels if ch.cac_payback_months is not None and ch.cac_payback_months > 12]  # noqa: E501

    # Segment priority (by revenue opportunity)
    sorted_segments = sorted(segments, key=lambda s: s.revenue_opportunity, reverse=True)
    segment_priority = [seg.segment_name for seg in sorted_segments]

    # Risk flags
    risk_flags = []
    if market_health in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        risk_flags.append("Market opportunity may be too small or market share target too aggressive")  # noqa: E501
    if cac_health in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        risk_flags.append("CAC estimates based on assumptions - validate with pilot campaigns")

    # Check for very high LTV:CAC ratios (may indicate underestimated CAC; skip channels where ratio is None)  # noqa: E501
    high_ltv_cac = [ch for ch in channels if ch.ltv_cac_ratio is not None and ch.ltv_cac_ratio > 100]  # noqa: E501
    if high_ltv_cac:
        risk_flags.append(
            f"Very high LTV:CAC ratios ({', '.join(ch.channel for ch in high_ltv_cac)}) "
            "may indicate underestimated CAC - validate with real data"
        )

    return {
        "primary_channel": primary_channel,
        "primary_rationale": f"Lowest CAC (${sorted_channels[0].cac:,.2f}), efficient acquisition"
        if primary_channel
        else None,
        "secondary_channels": secondary_channels,
        "avoid_channels": avoid_channels,
        "target_segment_priority": segment_priority,
        "pricing_validation": "Validated by market analysis" if any(s.wtp_source for s in segments) else "Requires validation",  # noqa: E501
        "risk_flags": risk_flags,
    }


def _worst_health(healths: list[MetricHealth]) -> MetricHealth:
    """Return the most conservative (worst) of the given healths.

    Inputs are constrained to EXCELLENT/GOOD/WARNING/CRITICAL (the assess_* helpers
    never return UNKNOWN), so the highest MetricHealth index is the worst.
    """
    return max(healths, key=lambda h: list(MetricHealth).index(h))


def calculate_discovery_report(
    assumptions: AssumptionsInput,
    jtbd_data: Optional[Dict[str, Any]],
    jtbd_source: Optional[str] = None,
) -> DiscoveryReport:
    """Perform complete discovery stage financial analysis.

    Args:
        assumptions: Financial assumptions input
        jtbd_data: Optional JTBD market analysis data

    Returns:
        Complete DiscoveryReport with all calculations and recommendations
    """
    # Market sizing
    tam_result = calculate_tam(assumptions.tam)

    sam_input = build(
        SAMInput,
        tam=tam_result.value,
        geographic_filter=assumptions.sam_filters.get("geographic", 100),
        customer_size_filter=assumptions.sam_filters.get("customer_size", 100),
        channel_filter=assumptions.sam_filters.get("channel", 100),
    )
    sam_result = calculate_sam(sam_input)

    som_input = build(
        SOMInput,
        sam=sam_result.value,
        timeframe_years=assumptions.som_timeframe_years,
        market_share_percent=assumptions.som_market_share_pct,
    )
    som_result = calculate_som(som_input)

    # Customer segments and revenue opportunity
    segment_opportunities = [calculate_segment_opportunity(seg) for seg in assumptions.segments]
    total_revenue_opportunity = sum(seg.revenue_opportunity for seg in segment_opportunities)
    penetration_required = (som_result.value / total_revenue_opportunity * 100) if total_revenue_opportunity > 0 else 0  # noqa: E501

    # CAC by channel
    channels = []
    if assumptions.inbound_marketing:
        channels.append(
            calculate_inbound_cac(
                assumptions.inbound_marketing,
                assumptions.average_acv,
                assumptions.gross_margin_pct,
                assumptions.monthly_churn_pct,
            )
        )
    if assumptions.outbound_sales:
        channels.append(
            calculate_outbound_cac(
                assumptions.outbound_sales,
                assumptions.average_acv,
                assumptions.gross_margin_pct,
                assumptions.monthly_churn_pct,
            )
        )
    if assumptions.plg:
        channels.append(
            calculate_plg_cac(
                assumptions.plg, assumptions.average_acv, assumptions.gross_margin_pct, assumptions.monthly_churn_pct  # noqa: E501
            )
        )
    if assumptions.partnerships:
        channels.append(
            calculate_partnerships_cac(
                assumptions.partnerships,
                assumptions.average_acv,
                assumptions.gross_margin_pct,
                assumptions.monthly_churn_pct,
            )
        )
    if assumptions.field_sales:
        channels.append(
            calculate_field_sales_cac(
                assumptions.field_sales,
                assumptions.average_acv,
                assumptions.gross_margin_pct,
                assumptions.monthly_churn_pct,
            )
        )
    if assumptions.community:
        channels.append(
            calculate_community_cac(
                assumptions.community, assumptions.average_acv, assumptions.gross_margin_pct, assumptions.monthly_churn_pct  # noqa: E501
            )
        )

    # Rank channels by efficiency (lowest CAC = rank 1)
    sorted_channels = sorted(channels, key=lambda ch: ch.cac)
    for rank, channel in enumerate(sorted_channels, 1):
        channel.efficiency_rank = rank

    # Blended metrics
    blended = calculate_blended_metrics(channels) if channels else None

    # Health assessments
    market_health = assess_market_opportunity_health(som_result.value, som_result.som_to_sam_ratio)
    cac_health = (
        assess_cac_efficiency_health(blended.weighted_cac_payback_months, blended.weighted_ltv_cac_ratio)  # noqa: E501
        if blended
        else MetricHealth.CRITICAL
    )

    # Overall health = the most conservative (worst) of the component healths.
    overall_health = _worst_health([market_health, cac_health])

    # JTBD integration
    jtbd_integration = integrate_jtbd_data(assumptions, jtbd_data, jtbd_source)

    # Recommendations
    recommendations = generate_recommendations(market_health, cac_health, channels, segment_opportunities)  # noqa: E501

    # Build report
    return DiscoveryReport(
        market_sizing={
            "tam": {
                "value": tam_result.value,
                "calculation_method": tam_result.calculation_method,
                "assumptions": tam_result.assumptions,
            },
            "sam": {"value": sam_result.value, "filters": sam_result.filters, "sam_to_tam_ratio": sam_result.sam_to_tam_ratio},  # noqa: E501
            "som": {
                "value": som_result.value,
                "timeframe_years": som_result.timeframe_years,
                "market_share_pct": som_result.market_share_pct,
                "som_to_sam_ratio": som_result.som_to_sam_ratio,
            },
        },
        customer_segments=segment_opportunities,
        revenue_opportunity={
            "total": total_revenue_opportunity,
            "penetration_required_for_som": penetration_required,
            "by_segment": [
                {
                    "segment": seg.segment_name,
                    "opportunity": seg.revenue_opportunity,
                    "percentage": (seg.revenue_opportunity / total_revenue_opportunity * 100)
                    if total_revenue_opportunity > 0
                    else 0,
                }
                for seg in segment_opportunities
            ],
        },
        cac_by_channel=channels,
        blended_metrics=blended,
        jtbd_integration=jtbd_integration,
        health_assessment={
            "market_opportunity": market_health.value,
            "cac_efficiency": cac_health.value,
            "ltv_cac_health": cac_health.value,
            "overall": overall_health.value,
        },
        recommendations=recommendations,
        metadata={
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            "analysis_stage": "discovery",
            "confidence_level": "medium",
            "data_sources": ["user_provided", "industry_benchmarks"]
            + (["jtbd_analysis"] if jtbd_integration["data_imported"] else []),
        },
    )


def format_report_as_json(report: DiscoveryReport) -> str:
    """Format discovery report as JSON.

    Args:
        report: Discovery report

    Returns:
        JSON string
    """

    def to_dict(obj: Any) -> Any:
        """Convert dataclass to dict recursively."""
        if isinstance(obj, (SegmentOpportunity, ChannelCAC, BlendedMetrics)):
            return {k: to_dict(v) for k, v in obj.__dict__.items() if v is not None}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        else:
            return obj

    report_dict = {
        "market_sizing": report.market_sizing,
        "customer_segments": [to_dict(seg) for seg in report.customer_segments],
        "revenue_opportunity": report.revenue_opportunity,
        "cac_by_channel": [to_dict(ch) for ch in report.cac_by_channel],
        "blended_metrics": to_dict(report.blended_metrics) if report.blended_metrics else None,
        "jtbd_integration": report.jtbd_integration,
        "health_assessment": report.health_assessment,
        "recommendations": report.recommendations,
        "metadata": report.metadata,
    }

    return json.dumps(report_dict, indent=2)


def format_report_as_markdown(report: DiscoveryReport) -> str:
    """Format discovery report as Markdown.

    Args:
        report: Discovery report

    Returns:
        Markdown string
    """
    lines = [
        "# Discovery Stage Financial Analysis",
        "",
        f"**Analysis Date:** {report.metadata['created_at'][:10]}",
        f"**Market Opportunity:** {report.health_assessment['market_opportunity'].upper()}",
        f"**CAC Efficiency:** {report.health_assessment['cac_efficiency'].upper()}",
        f"**Overall Health:** {report.health_assessment['overall'].upper()}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "**Market Opportunity:**",
        f"- TAM: ${report.market_sizing['tam']['value']:,.0f}",
        f"- SAM: ${report.market_sizing['sam']['value']:,.0f} "
        f"({report.market_sizing['sam']['sam_to_tam_ratio']:.1%} of TAM)",
        f"- SOM: ${report.market_sizing['som']['value']:,.0f} "
        f"({report.market_sizing['som']['som_to_sam_ratio']:.1%} of SAM - "
        f"{report.market_sizing['som']['timeframe_years']}-year target)",
        "",
        "**Revenue Opportunity:**",
        f"- Total addressable: ${report.revenue_opportunity['total']:,.0f} "
        f"across {len(report.customer_segments)} segments",
        f"- SOM requires {report.revenue_opportunity['penetration_required_for_som']:.1f}% penetration",  # noqa: E501
        "",
    ]

    if report.blended_metrics:
        lines.extend([
            "**Customer Acquisition:**",
            f"- Blended CAC: ${report.blended_metrics.blended_cac:,.2f}",
            f"- CAC Payback: {report.blended_metrics.weighted_cac_payback_months:.1f} months",
            f"- LTV:CAC Ratio: {report.blended_metrics.weighted_ltv_cac_ratio:.1f}:1",
            "",
        ])

    lines.extend([
        f"**Recommendation:** {report.health_assessment['overall'].upper()} - "
        f"{'Proceed with confidence' if report.health_assessment['overall'] in ['excellent', 'good'] else 'Address concerns before proceeding'}",  # noqa: E501
        "",
        "---",
        "",
        "## Market Sizing Analysis",
        "",
        "### TAM: Total Addressable Market",
        f"**Value:** ${report.market_sizing['tam']['value']:,.0f}",
        "",
        f"**Calculation Method:** {report.market_sizing['tam']['calculation_method']}",
    ])

    # Add TAM assumptions
    for key, value in report.market_sizing["tam"]["assumptions"].items():
        if isinstance(value, (int, float)):
            lines.append(f"- {key.replace('_', ' ').title()}: {value:,.0f}")
        else:
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    lines.extend([
        "",
        "### SAM: Serviceable Addressable Market",
        f"**Value:** ${report.market_sizing['sam']['value']:,.0f} "
        f"({report.market_sizing['sam']['sam_to_tam_ratio']:.1%} of TAM)",
        "",
        "**Filters Applied:**",
    ])

    for filter_name, filter_value in report.market_sizing["sam"]["filters"].items():
        lines.append(f"- {filter_name.replace('_', ' ').title()}: {filter_value:.1f}%")

    lines.extend([
        "",
        "### SOM: Serviceable Obtainable Market",
        f"**Value:** ${report.market_sizing['som']['value']:,.0f} "
        f"({report.market_sizing['som']['som_to_sam_ratio']:.1%} of SAM)",
        "",
        f"**Timeframe:** {report.market_sizing['som']['timeframe_years']} years",
        f"**Market Share Target:** {report.market_sizing['som']['market_share_pct']:.1f}%",
        "",
        "---",
        "",
        "## Customer Segments & Revenue Opportunity",
        "",
    ])

    for i, seg in enumerate(report.customer_segments, 1):
        lines.extend([
            f"### Segment {i}: {seg.segment_name}",
            f"**Opportunity:** ${seg.revenue_opportunity:,.0f} "
            f"({seg.revenue_opportunity / report.revenue_opportunity['total'] * 100:.1f}% of total)",  # noqa: E501
            "",
            "**Profile:**",
            f"- Potential customers: {seg.potential_customers:,}",
            f"- Target ACV: ${seg.target_acv:,.0f}/year",
            f"- Conversion rate: {seg.conversion_rate_pct:.1f}%",
            f"- Acquisition difficulty: {seg.acquisition_difficulty.title()}",
        ])

        if seg.willingness_to_pay:
            source = f" (from {seg.wtp_source})" if seg.wtp_source else ""
            lines.append(f"- Willingness-to-Pay: ${seg.willingness_to_pay:,.0f}{source}")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Customer Acquisition Cost (CAC) by Channel",
        "",
        "### Channel Efficiency Ranking",
        "",
        "| Rank | Channel | CAC | Customers/Mo | Payback | LTV:CAC | Status |",
        "|------|---------|-----|--------------|---------|---------|--------|",
    ])

    # Sort channels by efficiency rank
    sorted_channels = sorted(report.cac_by_channel, key=lambda ch: ch.efficiency_rank)
    for ch in sorted_channels:
        if ch.cac_payback_months is None:
            status = "N/A"
        elif ch.cac_payback_months < 6:
            status = "✅ EXCELLENT"
        elif ch.cac_payback_months <= 12:
            status = "✅ GOOD"
        else:
            status = "⚠️ WARNING"
        payback_str = f"{ch.cac_payback_months:.1f} mo" if ch.cac_payback_months is not None else "—"  # noqa: E501
        ltv_cac_str = f"{ch.ltv_cac_ratio:.1f}:1" if ch.ltv_cac_ratio is not None else "—"
        lines.append(
            f"| {ch.efficiency_rank} | {ch.channel.replace('_', ' ').title()} | "
            f"${ch.cac:,.0f} | {ch.customers_per_month:.1f} | "
            f"{payback_str} | {ltv_cac_str} | {status} |"
        )

    if report.blended_metrics:
        lines.extend([
            "",
            "### Blended Metrics",
            f"- **Blended CAC:** ${report.blended_metrics.blended_cac:,.2f}",
            f"- **Total Customers/Month:** {report.blended_metrics.total_customers_per_month:.0f}",
            f"- **Weighted Payback:** {report.blended_metrics.weighted_cac_payback_months:.1f} months",  # noqa: E501
            f"- **Weighted LTV:CAC:** {report.blended_metrics.weighted_ltv_cac_ratio:.1f}:1",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Go-to-Market Strategy Recommendations",
        "",
    ])

    if report.recommendations["primary_channel"]:
        lines.extend([
            f"**Primary Channel:** {report.recommendations['primary_channel'].replace('_', ' ').title()}",  # noqa: E501
            f"- {report.recommendations['primary_rationale']}",
            "",
        ])

    if report.recommendations["secondary_channels"]:
        lines.append("**Secondary Channels:**")
        for ch in report.recommendations["secondary_channels"]:
            lines.append(f"- {ch.replace('_', ' ').title()}")
        lines.append("")

    if report.recommendations["target_segment_priority"]:
        lines.append("**Segment Priority:**")
        for i, seg in enumerate(report.recommendations["target_segment_priority"], 1):
            lines.append(f"{i}. {seg}")
        lines.append("")

    if report.recommendations["risk_flags"]:
        lines.extend([
            "## Risk Assessment",
            "",
        ])
        for risk in report.recommendations["risk_flags"]:
            lines.append(f"- ⚠️ {risk}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "**Analysis prepared by:** Product Finance Plugin",
        f"**Confidence Level:** {report.metadata['confidence_level'].upper()}",
    ])

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for market sizing calculator."""
    parser = argparse.ArgumentParser(
        description="Market Sizing Calculator for Discovery Stage Financial Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--assumptions", type=str, required=True, help="Path to assumptions JSON file")  # noqa: E501
    parser.add_argument("--jtbd-data", type=str, help="Path to a jtbd-market-discovery result file (`.jtbd-market-discovery/results/*.json`) (optional)")  # noqa: E501
    parser.add_argument("--output", type=str, required=True, help="Path to output discovery-report.json file")  # noqa: E501
    parser.add_argument("--output-md", type=str, help="Path to output discovery-report.md file (optional)")  # noqa: E501

    args = parser.parse_args()

    # Load assumptions
    try:
        with open(args.assumptions, "r", encoding="utf-8") as f:
            assumptions_data = json.load(f)
        assumptions = load_assumptions(assumptions_data)
    except AssumptionsProblem as problem:
        print(f"Missing or invalid inputs in {args.assumptions}:", file=sys.stderr)
        for line in problem.problems:
            print(f"- {line}", file=sys.stderr)
        sys.exit(EXIT_INPUTS)
    except FileNotFoundError:
        print(f"Error: Assumptions file not found: {args.assumptions}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in assumptions file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading assumptions: {e}", file=sys.stderr)
        sys.exit(1)

    # Load JTBD data if provided
    jtbd_data = None
    if args.jtbd_data:
        jtbd_data = load_jtbd_data(Path(args.jtbd_data))

    # Calculate discovery report
    try:
        report = calculate_discovery_report(assumptions, jtbd_data, args.jtbd_data)
    except Exception as e:
        print(f"Error calculating discovery report: {e}", file=sys.stderr)
        sys.exit(1)

    # Write JSON output
    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(format_report_as_json(report))
        print(f"✓ Discovery report written to {args.output}")
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Write Markdown output if requested
    if args.output_md:
        try:
            md_path = Path(args.output_md)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(format_report_as_markdown(report))
            print(f"✓ Discovery report (Markdown) written to {args.output_md}")
        except IOError as e:
            print(f"Error writing markdown file: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
