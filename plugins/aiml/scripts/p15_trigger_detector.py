"""Pure-function P15 trigger detector (cost-rate + quality-floor).

Per Charter sub-spec 4b §6 + §3.10 D10. NO I/O — all reads in loader, all
writes in emitter. Reimplemented per Charter §6.3 mandate (zero
plugins/pricing/ imports). Returns (events, detection_notes) tuple.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from datetime import datetime, timedelta

from p15_trigger_input_loader import ResolvedThresholds


def derive_severity(miss_band_pct: float) -> str:
    if miss_band_pct < 0:
        raise ValueError(f"miss_band_pct must be non-negative, got {miss_band_pct}")
    if miss_band_pct < 15:
        return "minor"
    if miss_band_pct < 50:
        return "major"
    return "critical"  # [50, ∞) per spec §3.8 + T1A-3 reconciliation


def _canonical_json_bytes(obj) -> bytes:
    """Per spec §3.13 D13: sort_keys, no whitespace, UTF-8.
    Special case: None AND empty list both hash to b"" (R1-fixer D13 invariant)."""
    if obj is None or obj == []:
        return b""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_inputs_hash(current: dict, history: list[dict] | None) -> str:
    """Per spec §3.13 D13: sha256 of canonical-JSON-serialized current + FULL history."""
    h = hashlib.sha256()
    h.update(_canonical_json_bytes(current))
    h.update(_canonical_json_bytes(history))
    return h.hexdigest()


def _parse_iso(s: str) -> datetime:
    # Compat shim — Z is native in Python 3.11 but explicit replace is harmless
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _vendor_actor(current: dict) -> dict:
    # actor.vendor_name REQUIRED per spec §5.1. v0.3.0 defaults to "unspecified"
    # if input doesn't carry an explicit vendor_name field. Operator can extend
    # the input shape in future sub-specs to populate this from telemetry.
    return {"vendor_name": current.get("vendor_name", "unspecified")}


def detect(
    current: dict,
    history: list[dict] | None,
    resolved: ResolvedThresholds,
    rolling_window_days: int = 365,  # default 365 days = 12mo (config default; NOT a Charter invariant — see spec §16 M1)
) -> tuple[list[dict], list[str]]:
    """Pure function. Returns (events, detection_notes).

    Pseudocode shorthand `emit X event with: ...` desugars to events.append({...})
    on the function-local list. detection_notes.append(...) appears verbatim.
    """
    events: list[dict] = []
    detection_notes: list[str] = []

    inputs_hash = canonical_inputs_hash(current, history)
    actor = _vendor_actor(current)
    trigger_ts = current["produced_at"]

    # ----- Cost-rate breach -----
    amps = current.get("amplifiers") or {}
    if amps:
        if history is None or len(history) == 0:
            detection_notes.append("cost_rate detection skipped: no history file supplied")
        else:
            cutoff = _parse_iso(current["produced_at"]) - timedelta(days=rolling_window_days)
            window_samples = []
            for s in history:
                mw_end = s.get("measurement_window", {}).get("end")
                if mw_end and _parse_iso(mw_end) >= cutoff:
                    window_samples.append(s)
            for amp_id, cur in amps.items():
                if not cur.get("present", True):
                    continue
                hist_p75 = [s["amplifiers"][amp_id]["measured_p75"]
                            for s in window_samples
                            if amp_id in s.get("amplifiers", {}) and s["amplifiers"][amp_id].get("present", True)]
                hist_p95 = [s["amplifiers"][amp_id]["measured_p95"]
                            for s in window_samples
                            if amp_id in s.get("amplifiers", {}) and s["amplifiers"][amp_id].get("present", True)]
                if not hist_p75:
                    continue
                baseline_p75 = statistics.median(hist_p75)
                baseline_p95 = statistics.median(hist_p95)
                # Dual-tail zero-baseline guard per spec T2C-5 + T2C-R2-2:
                # P75=0 → ZeroDivisionError; P95=0 → schema exclusiveMinimum:0 violation on emit.
                if baseline_p75 == 0 or baseline_p95 == 0:
                    continue
                cur_p75 = cur["measured_p75"]
                cur_p95 = cur["measured_p95"]
                rate_pct = (cur_p75 - baseline_p75) / baseline_p75 * 100
                if resolved.threshold_pct is None:
                    continue  # short-circuit no-threshold case
                if rate_pct > resolved.threshold_pct:
                    # Round to 9 decimals to neutralize IEEE-754 noise at band edges
                    # (e.g., (2.8 - 2.0)/2.0 * 100 = 39.9999... → miss_band would
                    # land 14.9999... and trigger "minor" instead of spec-canonical "major")
                    miss_band = round(rate_pct - resolved.threshold_pct, 9)
                    contracted = {"threshold_pct": resolved.threshold_pct}
                    if resolved.cap_pct is not None:
                        contracted["cap_pct"] = resolved.cap_pct
                    # severity derived from miss_band_pct per spec §6.3 + §6.1
                    events.append({
                        "trigger_kind": "cost_rate_breach",
                        "pattern_id": "P15",
                        "severity": derive_severity(miss_band),
                        "trigger_timestamp": trigger_ts,
                        "actor": actor,
                        "miss_band_pct": miss_band,
                        "detection_signal": f"computed/amplifier_id_{amp_id}/p75_vs_baseline_median",
                        "inputs_hash": inputs_hash,
                        "breach_basis": "detector_derived",
                        "computed": {
                            "amplifier_id": amp_id,
                            "measured_p75": cur_p75,
                            "measured_p95": cur_p95,
                            "baseline_p75": baseline_p75,
                            "baseline_p95": baseline_p95,
                            "rate_pct_over_window": rate_pct,
                            "rolling_window_days": rolling_window_days,
                        },
                        "contracted": contracted,
                    })

    # ----- Quality-floor breach -----
    qms = current.get("quality_metrics") or []
    floor_target_idx = {t["metric_id"]: t for t in (resolved.quality_floor_targets or [])}
    for entry in qms:
        mid = entry["metric_id"]
        # Floor resolution per spec §6.2 (dispatch CLI > input top-level > per-entry inline > skip):
        contracted_floor = None
        floor_unit = None
        if mid in floor_target_idx:
            contracted_floor = floor_target_idx[mid]["target_value"]
            floor_unit = floor_target_idx[mid].get("target_unit")
        elif "contracted_floor" in entry:
            contracted_floor = entry["contracted_floor"]
        if contracted_floor is None:
            detection_notes.append(f"quality_floor detection skipped for metric_id={mid}: no contracted_floor resolved")
            continue
        measured = entry["measured_value"]
        if entry.get("breach_observed") is True:
            # Operator-declared — clamp negative miss_band to 0 per spec §6.2 + T1B-1
            miss_band = max(0.0, (contracted_floor - measured) / contracted_floor * 100)
            basis = "operator_declared"
            breach = True
        elif measured < contracted_floor:
            miss_band = (contracted_floor - measured) / contracted_floor * 100
            basis = "detector_derived"
            breach = True
        else:
            breach = False
        if breach:
            # Per spec §5.1 R1 I8: computed block does NOT carry breach_observed
            # (superseded by envelope-level breach_basis enum). Only metric_id + measured_value.
            ev = {
                "trigger_kind": "quality_floor_breach",
                "pattern_id": "P15",
                "severity": derive_severity(miss_band),
                "trigger_timestamp": trigger_ts,
                "actor": actor,
                "miss_band_pct": miss_band,
                "detection_signal": f"computed/quality_metric_{mid}/measured_vs_contracted_floor",
                "inputs_hash": inputs_hash,
                "breach_basis": basis,
                "computed": {
                    "metric_id": mid,
                    "measured_value": measured,
                },
                "contracted": {"floor_value": contracted_floor},
            }
            if floor_unit is not None:
                ev["contracted"]["floor_unit"] = floor_unit
            events.append(ev)

    return events, detection_notes
