"""Main entry point for M&A plugin."""

from corporate_development.pipeline.orchestrator import PipelineOrchestrator


def run_pipeline(user_input: dict) -> dict:
    """
    Run complete M&A pipeline from Phase 0 through Phase 6.

    Parallelizes Phase 3 (Operational DD) + Phase 4 (Financial DD) via
    ThreadPoolExecutor. Returns a compact PipelineResult.to_summary() (~2KB)
    instead of accumulating full PhaseOutput data.

    Args:
        user_input: Dictionary with all phase inputs. Each phase reads only
                    its required keys:
            - Phase 0: company_name, ceo_readiness, strategic_targets,
                       organizational_capacity, financial_readiness, governance
            - Phase 1: target_markets, strategic_focus, budget_range
                       (+ optional capability_gaps)
            - Phase 2: company_name, industry, strategic_motivation
            - Phase 3: company_name, team, technology, product, operations,
                       market_position (dicts with 0-100 scores)
            - Phase 4: company_name, income_statement, balance_sheet
            - Phase 5: derived from Phase 3+4 handoffs
            - Phase 6: synthesized from full handoff chain

    Returns:
        PipelineResult.to_summary() — compact dict with:
          final_gate, stopped_at, phases_completed, phase_gates,
          phase_scores, artifact_paths.
    """
    orch = PipelineOrchestrator()
    result = orch.run(user_input)
    return result.to_summary()
