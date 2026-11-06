# ADR-004 — The decision-record library lives in the plugin for v1

**Status:** Accepted · **Date:** 2026-10-27

## Context

The decision record is project 4 of the product lifecycle system map. Other
plugins will record decisions too, so the library will be shared one day. In
v0.1.0, only this plugin writes decisions. A shared package outside this plugin
needs a workspace entry, its own tests and a `requirements-dev.txt` path for
every plugin that uses it. That cost buys nothing while there is one user.

## Decision

The library lives at `lib/decision_record.py` inside this plugin for v1. It
is the only writer of `decisions.jsonl`. It refuses a record with no reason,
no role or no name, and it fixes what each decision kind cites (ADR-005).

It moves to a shared package when system map project 4 needs it outside this plugin
(spec §10).

## Consequences

- No new workspace package and no change to the root `pyproject.toml`.
- `lib/` stays stdlib-only, so the plugin's tests run in a bare venv.
- The move is a later refactor. When it comes, the decision record's file
  format must not change, so existing cases stay readable.
