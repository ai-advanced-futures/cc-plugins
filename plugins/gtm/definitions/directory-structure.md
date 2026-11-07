# GTM Directory Structure — Canonical Reference

## Runtime Directories

| Path | Purpose | Creator | Owner |
|------|---------|---------|-------|
| `.gtm/working/{agent}/` | Draft artifacts before integrity review | `gtm_init.create_directories()` | Content agents write here |
| `.gtm/audit/` | Per-agent integrity audit files (`{agent}-truth-tier-audit.json`) | `gtm_init.create_directories()` | integrity-agent |
| `gtm-output/` | Final integrity-cleaned artifacts | `gtm_init.create_directories()` | integrity-agent (sole writer) |

## Run Files

| Path | Purpose | Writer | Reader |
|------|---------|--------|--------|
| `.gtm/open-questions.json` | A question that an agent cannot ask the person. The agent writes it, then ends with the line `OPEN: .gtm/open-questions.json`. | orchestrator, or an agent that a command dispatches | The command that dispatched the agent. It asks the person, then dispatches again. |

## Artifact Path Patterns

### Draft Artifacts (`.gtm/working/{agent}/`)

| Agent | Draft Files |
|-------|-------------|
| brand | `brand-identity.draft.json`, `messaging-architecture.draft.json`, `voice-guide.draft.md`, `purpose-statement.draft.md`, `storybrand-script.draft.md` |
| marketing | `campaign-plan.draft.json`, `launch-plan.draft.json`, `content-calendar.draft.md` |
| sales | `pitch-deck.draft.json`, `pitch-narrative.draft.md`, `prospecting-plan.draft.json`, `pipeline-playbook.draft.json`, `discovery-questions.draft.md`, `meddpicc-scorecard.draft.md` |
| funnel | `funnel-metrics.draft.json`, `funnel-health.draft.md`, `handoff-sla.draft.md`, `revenue-math.draft.md` |

### Final Artifacts (`gtm-output/`)

The integrity-agent promotes draft files to `gtm-output/` using the exact paths defined in
`scripts/integrity_manifest.py::AGENT_MANIFESTS[target_agent]` — this is the single source of truth
for final file names. See that file for the complete list.

### Audit Artifacts (`.gtm/audit/`)

| File | Written by | Contents |
|------|-----------|----------|
| `{agent}-integrity.json` | integrity-agent (the claims and the issues) and `truth_tier_validator.py` (the score keys) | Claims, issues, integrity score, band, blocked count |
| `{agent}-integrity-BREACH.json` | integrity-agent | Created on floor breach; overwritten with `{"status": "resolved"}` on override or re-pass |

## Key Invariants

1. **Only integrity-agent writes to `gtm-output/`** — content agents never write final paths directly
2. **Draft artifacts always use `.draft.` suffix** — `campaign-plan.draft.json` not `campaign-plan.json`
3. **Audit files live in `.gtm/audit/`** — never in `.gtm/working/` or `gtm-output/`
4. **All directories are created by `gtm_init.create_directories()`** — agents never mkdir themselves

## Python Reference

- Directory creation: `scripts/gtm_init.create_directories()`
- Artifact manifests: `scripts/integrity_manifest.py::AGENT_MANIFESTS`
- Output schemas: `scripts/integrity_manifest.py::OUTPUT_SCHEMAS`
- Output check: `scripts/output_check.py`
- Agent name constants: `scripts/gtm_constants.py::CONTENT_AGENTS`
