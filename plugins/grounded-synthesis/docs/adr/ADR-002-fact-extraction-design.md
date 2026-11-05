# ADR-002 — Fact extraction design

**Status:** Accepted

## Context

Fact extraction needs judgment: Python cannot decide what an atomic, falsifiable fact is. But the next stage needs machine-readable output.

## Decision

The `fact-extractor` agent extracts the facts. It writes JSON to `{session_dir}/source-{i}-facts.json`. The agent text has a calibration table with examples that are a fact, examples to split, and examples that are no fact. `lib/fact_schema.py` checks each fact file with `jsonschema`. The orchestrator runs this check before Wave 2, and the tests run it too.

## Consequences

The JSON contract is explicit and testable. The calibration table fixes the meaning of "atomic and falsifiable" for all runs. The check at run time finds a bad fact file before it reaches the coverage stage. `validate_fact_file()` is the only definition of a valid fact file.
