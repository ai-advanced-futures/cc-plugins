"""Four-component AE comp-model reference calculator (framework Chapter 5).

STANDALONE — NOT wired into the producer path (see ADR-003). The gate-agent
invokes these functions ad hoc to inform precondition #1 and to surface comp
numbers in comms; the emitter never imports this module, and comp dollars never
enter the gate file.
"""
from __future__ import annotations

from dataclasses import dataclass

_LAND_MIN, _LAND_MAX = 0.60, 0.70
_EXPAND_MIN, _EXPAND_MAX = 0.30, 0.40
_QB_MIN, _QB_MAX = 0.05, 0.15
_CLAWBACK_OF_LAND = 0.50
_SUM_TOL = 0.001
_OVERLAY_CAP_MULT = 1.30
_RETENTION_LOW, _RETENTION_HIGH = 0.15, 0.25
_COMP_LOSS_LIMIT = 0.15


@dataclass(frozen=True)
class CompSplit:
    land_dollars: float
    expand_dollars: float
    qb_dollars: float
    clawback_exposure: float


def component_split(ote: float, land_share: float, expand_share: float, qb_share: float) -> CompSplit:
    if not (_LAND_MIN <= land_share <= _LAND_MAX):
        raise ValueError(f"land_share {land_share} outside [{_LAND_MIN},{_LAND_MAX}]")
    if not (_EXPAND_MIN <= expand_share <= _EXPAND_MAX):
        raise ValueError(f"expand_share {expand_share} outside [{_EXPAND_MIN},{_EXPAND_MAX}]")
    if not (_QB_MIN <= qb_share <= _QB_MAX):
        raise ValueError(f"qb_share {qb_share} outside [{_QB_MIN},{_QB_MAX}]")
    if abs(land_share + expand_share - 1.0) > _SUM_TOL:
        raise ValueError(f"land_share+expand_share must be ~1.0 (got {land_share + expand_share})")
    land_dollars = land_share * ote
    return CompSplit(
        land_dollars=land_dollars,
        expand_dollars=expand_share * ote,
        qb_dollars=qb_share * land_dollars,
        clawback_exposure=_CLAWBACK_OF_LAND * land_dollars,
    )


def overlay_cap(steady_state_ote: float) -> float:
    return _OVERLAY_CAP_MULT * steady_state_ote


def retention_bonus_band(ote: float) -> tuple[float, float]:
    return (_RETENTION_LOW * ote, _RETENTION_HIGH * ote)


def comp_impact_ok(modeled_cash_comp: float, prior_cash_comp: float) -> bool:
    if prior_cash_comp <= 0:
        raise ValueError("prior_cash_comp must be > 0")
    return (prior_cash_comp - modeled_cash_comp) / prior_cash_comp <= _COMP_LOSS_LIMIT
