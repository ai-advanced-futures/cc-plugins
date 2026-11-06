# ADR-004: Voice Profiles as User-Project Data

**Status:** Accepted

## Context

The command `/prose-authenticity:profile` builds a voice profile from the writing samples of a user. The profile holds the vocabulary, the cadence rules, the banned and favored patterns, and before/after exemplars from those samples. The command `/prose-authenticity:humanize` uses that profile to guide rewrites.

Two questions needed a decision. The first was where profiles live. The second was how the plugin validates them.

## Decision

- **Profiles live in the project of the user**, at `.prose-authenticity/profiles/`. They are not in the plugin package.
  - A voice profile comes from the actual writing samples of one user or team.
  - It is project-specific data. It is not plugin configuration.
  - It belongs with the project that it describes, in the same category as the run state in `.prose-authenticity/run-<id>/`.
- **The plugin ships exactly one bundled profile.** It is a neutral default: `config/default-profile.yaml`. The plugin uses it when no user profile exists. `/prose-authenticity:humanize` then has a sane fallback voice on first use.
- **Validation uses only the standard library.** `lib/profile_store.py` checks the schema by hand. It follows the shape of `config/voice-profile.schema.yaml` and does not add a `jsonschema` dependency.
  - The schema is small and stable.
  - A structural check with the standard library covers it. The check looks for the required keys and the expected types, and it needs no external dependency.
  - This agrees with the preference of the plugin for `lib/` scripts that use only the standard library. That preference holds when the validation work has a clear limit.

## Consequences

- Voice profiles stay in place across plugin upgrades. A plugin version bump never overwrites them, because they are user data. A run of `bump_plugin_version.py` never touches `.prose-authenticity/profiles/`.
- Each project that uses prose-authenticity keeps its own voice profiles. There is no shared or global profile store across projects.
- `lib/profile_store.py` has no `jsonschema` dependency or other non-stdlib dependency. This keeps `requirements-dev.txt` minimal and avoids the CI-environment gap that the PR-Hygiene checklist of the repository describes. The checklist item says that CI does not run `uv sync`. You must name each extra dependency in the file.
- The schema can grow much more complex in a future version. Then the choice of stdlib only may need a new review. The size of the schema limits the tradeoff between hand-rolled validation and a dependency. The choice is not permanent.
