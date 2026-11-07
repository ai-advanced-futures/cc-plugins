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

A new orchestrator pattern was designed to solve all three problems. Since v1.9.0, the `discover` skill is the orchestrator: no agent has `Bash` or `Agent`, and the skill runs the scripts and starts the agents (D-266, FEATURE-26).

---

## Decision

**Orchestrator Pattern:** The `discover` skill (consuming ~5-10k tokens) starts each phase as a fresh sub-agent with the `Agent` tool, one at a time, in the foreground. Between the starts, it runs the scripts of the plugin with `uv run`. All state is persisted to disk. The skill re-reads state on resume.

---

## Architecture Decisions

### 1. The Skill as State Machine (not Thread Pool)

**Decision:** The skill executes phases one at a time, not as a concurrent pool

**Rationale:**
- Phases 1-4 have strict sequential dependencies (each phase reads previous phase output)
- Phase 3 has 4 agents for 4 step groups. The skill starts them one at a time, in the foreground. In Claude Code 2.1.319, agents that start in one message run in the background, and each return starts a new turn that has no tool grant from the skill, so the next `uv run` is refused (D-377)
- Phase 8 runs after Phase 7, because segmentation reads `p7.json`

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Pure sequential, one agent at a time | Simple, predictable, scripts keep their grant | Slower than parallel | ✅ Selected |
| Full parallel (all phases) | Fastest | Violates data dependencies | ❌ Rejected |
| Parallel Phase 3 agents | Faster Phase 3 | A background return loses the tool grant of the skill (D-377) | ❌ Rejected |

### 2. File-Based State (vs. Context-Carried State)

**Decision:** All inter-phase data passed via `.jtbd/{session}/pN.json` files

**Rationale:**
- Context-carried state accumulates and causes compaction
- File-based state survives context compaction (compact-resilient)
- The skill stays thin (5-10k tokens) by only reading the phase file it needs

**File Schema:**
- `.jtbd/{session}/state.json` — session metadata + current_phase
- `.jtbd/{session}/p1.json` through `.jtbd/{session}/p9.json` — phase outputs
- `.jtbd/{session}/p3-batch-{1..4}.json` — Phase 3 batch outputs, merged into `p3.json` by `jtbd_state.py merge-needs`
- `.jtbd/{session}/final-output.json` — Phase 10 assembled output

**Atomic Writes:** All file writes via `tmp → rename()` to prevent corruption

### 3. Phase 3 Batch Strategy

**Decision:** 4 agents, one at a time, each handling a group of job steps

**Rationale:**
- Phase 3 (need generation) is the most time-consuming phase
- Job steps are independent within step groups (no cross-step dependencies for need generation)
- 4 agents map cleanly to UNDERSTAND + PLAN + EXECUTE/ASSESS + REVISE/CONCLUDE

**Dispatch (4 `Agent` calls, one at a time, each in the foreground):**
- Batch 1: Steps 1-3 (UNDERSTAND phase) → p3-batch-1.json
- Batch 2: Steps 4-6 (PLAN phase) → p3-batch-2.json
- Batch 3: Steps 7-9 (EXECUTE + ASSESS) → p3-batch-3.json
- Batch 4: Steps 10+ (REVISE + CONCLUDE) → p3-batch-4.json

### 4. Phase 5 (Survey) Pause Point

**Decision:** Phase 5 is the only phase where the skill pauses and waits for user confirmation

**Rationale:**
- Survey fielding requires 1-2 weeks of real-world data collection
- The skill cannot proceed until user confirms data is collected
- Phase 5 is marked complete only after user provides survey data confirmation

**Implementation:** The skill asks user "Do you have survey data? (yes/paste CSV | no/I need to field the survey)" and waits. If no → instructions + pause. If yes → proceed to Phase 6.

### 5. Python Helper (jtbd_state.py)

**Decision:** Separate Python helper for all file I/O operations

**Rationale:**
- Centralizes session file operations
- Validates phase numbers (1-10 only) — raises ValueError for invalid phases
- Atomic writes prevent partial state corruption
- 19 unit tests ensure reliability

**Subcommands (v1.9.0):** `jtbd_state.py` also runs from the command line, for the skill: `select`, `now`, `finished`, `wtp-folder`, `merge-needs` and `place-result`.

### 6. No Agent Has `Bash`

**Decision:** The skill runs each script. Each agent has `Read, Write` (`Glob` for `output-assembler` and `wtp-validator`) and reads the result file of its script.

**Rationale:**
- An agent that writes and runs its own helper file runs code that the model wrote, and no one checks that code
- A fixed script gives the same number in each run, and the agent cannot change it

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
3. **Safety:** no agent runs code that the model writes
4. **Resume:** Full session resume from any phase

### Negative
1. **Complexity:** More moving parts than single SKILL.md
2. **File dependency:** Requires disk I/O (not pure in-memory)
3. **State schema versioning:** Future changes must handle existing state files

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Disk permissions failure | The skill catches the error, writes the halt draft and stops |
| Partial batch write (Phase 3) | Each batch writes independently; `merge-needs` validates all 4 batch files before proceeding |
| State schema evolution | session_id timestamp enables future migration logic |

---

## Implementation Notes

### Tests Added

| Test File | Tests | Coverage |
|-----------|-------|---------|
| `test_jtbd_state.py` | 19 | Session CRUD, phase guards, atomic writes, error handling |
| `test_orchestrator_state_integration.py` | 5 | Full lifecycle, resume, batch outputs |

### Total Test Count

- Inherited from v1.1.0: 154 tests
- New in v1.2.0: 19 (jtbd_state) + 5 (integration) = +24 tests
- **Total: 178 tests** (may vary slightly by run configuration)

---

## References

- ADR-001: Original JTBD Plugin Architecture (2026-01-21)
- `skills/discover/SKILL.md` — Implementation
- `scripts/jtbd_state.py` — Python helper

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | Luis F. Amadeo | Initial ADR-002 for orchestrator architecture |
| 1.1 | 2026-11-02 | Luis F. Amadeo | Phases 7 and 8 run in sequence |
| 1.2 | 2026-11-06 | STORY-121 | The skill is the orchestrator; no agent has `Bash`; Phase 3 agents start one at a time |

---

**Document End**
