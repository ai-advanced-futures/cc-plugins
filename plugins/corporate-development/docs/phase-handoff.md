# Phase handoff

This file holds the shape of the handoff file that each phase agent writes, and the terms that the phase agents share. The command `/corporate-development:pipeline` reads the handoff files and passes them between the phases. A phase agent reads this file to write its handoff.

## PhaseHandoff schema

```json
{
  "phase_num": 0,
  "phase_name": "Phase 0: Acquisition Readiness",
  "gate": "GO" | "CONDITIONAL" | "NO_GO",
  "score": <float 0-100 or null>,
  "critical_risks": [<up to 5 risk titles as strings>],
  "artifact_paths": {"<artifact name>": "<path>"},
  "next_phase_inputs": {}
}
```

`artifact_paths` lists only a file that exists. When Claude Code refuses a Write of a report file, the phase agent leaves that file out.

The `next_phase_inputs` keys for each phase:

| Phase | `next_phase_inputs` |
|---|---|
| 0 | `readiness_score`, `gate` |
| 1 | `sourcing_complete`, `target_markets`, `candidates_identified` |
| 3 | `operational_health`, `operational_gate`, `operational_critical_count`, `operational_warning_count`, and `phase_3_not_assessed` (only when the inputs have no dimension data) |
| 4 | `financial_health`, `financial_gate`, `financial_critical_count` |

When the inputs of Phase 3 have no dimension data, Phase 3 returns the gate `CONDITIONAL` and adds `phase_3_not_assessed: true` to `next_phase_inputs`. The engine also puts this key at the top level of its output. The command reads it from `next_phase_inputs`.

Phase 1 collects information. It returns GO when its required inputs are valid.

## Engine fields and handoff keys

The engine names the output fields different from the handoff keys. The phase agent maps them when it writes the handoff:

| Engine output field | Phase 3 `next_phase_inputs` key |
|---|---|
| `overall_score` | `operational_health` |
| `gate_decision` | `operational_gate` |
| `critical_count` | `operational_critical_count` |
| `warning_count` | `operational_warning_count` |

| Engine output field | Phase 4 `next_phase_inputs` key |
|---|---|
| `overall_score` | `financial_health` |
| `gate_decision` | `financial_gate` |
| `critical_count` | `financial_critical_count` |

Phase 5 reads the keys of the right column.

## Integration complexity and risk severity

Use the term Integration Complexity when you describe the integration. Use the Risk Severity in risk registers, risk profiles and executive summaries.

| Integration Complexity | Risk Severity | Timeline |
|---|---|---|
| SIMPLE | LOW | 3 months or less |
| MODERATE | MEDIUM | 3 to 6 months |
| COMPLEX | HIGH | 6 to 12 months or more |
