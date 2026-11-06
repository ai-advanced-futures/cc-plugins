# ADR-002: JTBD Orchestrator Architecture

**Status:** Accepted
**Date:** 2026-02-27
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Supersedes:** ADR-001 (extends, does not replace)

---

## Context

The original SKILL.md-based workflow accumulated ~143k tokens across 10 phases, causing:
1. Context compaction events mid-session (precision loss)
2. No resume capability
3. No parallelism for independent phases

A new orchestrator pattern was designed to solve all three problems simultaneously.

---

## Decision

**Orchestrator Pattern:** A single lightweight orchestrator agent (consuming ~5-10k tokens) dispatches each phase as a fresh sub-agent via the Task tool. All state is persisted to disk. The orchestrator re-reads state on resume.

---

## Architecture Decisions

### 1. Orchestrator as State Machine (not Thread Pool)

**Decision:** Orchestrator executes phases sequentially (with strategic parallelism), not as a concurrent pool

**Rationale:**
- Phases 1-4 have strict sequential dependencies (each phase reads previous phase output)
- Phase 3 is internally parallel (4 agents for 4 step groups) — maximizes throughput at the most expensive phase
- Phases 7+8 are independent after Phase 6 — parallel dispatch saves ~30 min

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Pure sequential | Simple, predictable | Slow, no parallelism | ❌ Rejected |
| Full parallel (all phases) | Fastest | Violates data dependencies | ❌ Rejected |
| Strategic parallelism | Balances speed + correctness | More complex orchestration | ✅ Selected |

### 2. File-Based State (vs. Context-Carried State)

**Decision:** All inter-phase data passed via `.jtbd/{session}/pN.json` files

**Rationale:**
- Context-carried state accumulates and causes compaction
- File-based state survives context compaction (compact-resilient)
- Orchestrator stays thin (5-10k tokens) by only reading the phase file it needs

**File Schema:**
- `.jtbd/{session}/state.json` — session metadata + current_phase
- `.jtbd/{session}/p1.json` through `.jtbd/{session}/p9.json` — phase outputs
- `.jtbd/{session}/p3-batch-{1..4}.json` — Phase 3 parallel batch outputs
- `.jtbd/{session}/final-output.json` — Phase 10 assembled output

**Atomic Writes:** All file writes via `tmp → rename()` to prevent corruption

### 3. Phase 3 Parallelism Strategy

**Decision:** 4 parallel agents, each handling a group of job steps

**Rationale:**
- Phase 3 (need generation) is the most time-consuming phase (~60-90 min sequential)
- Job steps are independent within step groups (no cross-step dependencies for need generation)
- 4 agents map cleanly to UNDERSTAND + PLAN + EXECUTE/ASSESS + REVISE/CONCLUDE

**Parallel dispatch (single message, 4 Task tool calls):**
- Batch 1: Steps 1-3 (UNDERSTAND phase) → p3-batch-1.json
- Batch 2: Steps 4-6 (PLAN phase) → p3-batch-2.json
- Batch 3: Steps 7-9 (EXECUTE + ASSESS) → p3-batch-3.json
- Batch 4: Steps 10+ (REVISE + CONCLUDE) → p3-batch-4.json

### 4. Phase 5 (Survey) Pause Point

**Decision:** Phase 5 is the only phase where the orchestrator pauses and waits for user confirmation

**Rationale:**
- Survey fielding requires 1-2 weeks of real-world data collection
- Orchestrator cannot proceed until user confirms data is collected
- Phase 5 is marked complete only after user provides survey data confirmation

**Implementation:** Orchestrator asks user "Do you have survey data? (yes/paste CSV | no/I need to field the survey)" and waits. If no → instructions + pause. If yes → proceed to Phase 6.

### 5. Python Helper (jtbd_state.py)

**Decision:** Separate Python helper for all file I/O operations

**Rationale:**
- Centralizes session file operations
- Validates phase numbers (1-10 only) — raises ValueError for invalid phases
- Atomic writes prevent partial state corruption
- 19 unit tests ensure reliability

**Public API:**
```python
create_session(job_statement: str, session_dir: Path) -> dict
load_session(session_dir: Path) -> dict
mark_phase_complete(phase: int, session_dir: Path) -> None
is_phase_complete(phase: int, session_dir: Path) -> bool
write_phase_output(phase: int, data: dict, session_dir: Path) -> None
read_phase_output(phase: int, session_dir: Path) -> dict
get_default_session_dir(base_dir: Path) -> Path
```

---

## Consequences

### Positive
1. **Context efficiency:** 95% reduction (143k → 5-10k per invocation)
2. **Resilience:** Zero data loss across compaction events
3. **Speed:** Phase 3 ×4 parallel
4. **Resume:** Full session resume from any phase

### Negative
1. **Complexity:** More moving parts than single SKILL.md
2. **File dependency:** Requires disk I/O (not pure in-memory)
3. **State schema versioning:** Future changes must handle existing state files

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Disk permissions failure | Orchestrator catches IOError, falls back to in-context mode |
| Partial batch write (Phase 3) | Each batch writes independently; orchestrator validates all 4 batch files before proceeding |
| State schema evolution | session_id timestamp enables future migration logic |

---

## Implementation Notes

### Tests Added

| Test File | Tests | Coverage |
|-----------|-------|---------|
| `test_jtbd_state.py` | 19 | Session CRUD, phase guards, atomic writes, error handling |
| `test_orchestrator_state_integration.py` | 5 | Full lifecycle, resume, parallel batch outputs |

### Total Test Count

- Inherited from v1.1.0: 154 tests
- New in v1.2.0: 19 (jtbd_state) + 5 (integration) = +24 tests
- **Total: 178 tests** (may vary slightly by run configuration)

---

## References

- ADR-001: Original JTBD Plugin Architecture (2026-01-21)
- `agents/orchestrator.md` — Implementation
- `scripts/jtbd_state.py` — Python helper

---

## Amendment (v1.5.1): Phases 7 and 8 run in sequence

The orchestrator runs Phase 8 after Phase 7, because segmentation reads `p7.json` (`agents/orchestrator.md`). The "Phases 7+8 parallel" rationale and consequence above are history. They no longer describe the plugin.

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | Luis F. Amadeo | Initial ADR-002 for orchestrator architecture |
| 1.1 | 2026-11-02 | Luis F. Amadeo | Amendment: Phases 7 and 8 run in sequence |

---

**Document End**
