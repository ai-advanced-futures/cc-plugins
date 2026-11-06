# C4 Container Diagram — prose-authenticity Plugin

## Container View

This view expands the system boundary from
`docs/diagrams/prose-authenticity-context.md`. It shows six agents, a tool-belt
of deterministic Python scripts, a config, and a store of per-run state.

Agents supply judgment only. Every number, parse, verdict, and loop decision is
in a unit-tested `lib/*.py` script, and an agent calls the script over Bash. This
is the architecture principle of the plugin. Each script carries a PEP 723
header and runs with `uv run`.

The commands start the agents. The command `check` dispatches the
detection-analyst. The command `profile` dispatches the voice-profiler. The
command `humanize` dispatches the orchestrator. Each command uses the Agent tool.
The command `setup` has no agent.

The orchestrator does not ask the person a question. The commands `profile` and
`setup` ask the questions.

The diagram also shows the ASD-STE100 conformance checker (`ste_checker.py`,
`config/ste.yaml`) and the `simplified-technical-english` drafting skill. Since
v0.5.0, the detection-analyst runs this checker as part of every report. The
checker stays apart from the scoring. STE conformance and AI-likelihood are
different measurements. So the checker keeps its own verdict and never joins the
detector composite (ADR-006).

The diagram also shows the prose correctness checker (`correctness_checker.py`,
`config/correctness.yaml`) and the `prose-correctness` skill. They have the same
status as the STE checker, for the same reason. Correctness is a third
measurement with its own verdict. It joins neither the detector composite nor
the STE report (ADR-010).

The detection-analyst runs both checkers. It reports their verdicts beside the
tell score. On a humanize run, it also reports the delta against the original. So
a reader sees what the rewrite introduced (ADR-012).

`fault_delta.py` computes that difference. The difference is arithmetic, and this
plugin keeps arithmetic out of agent prose. Neither check gates the loop. Both
checkers read one prose seam, `prose_spans.py`. We extracted it from
`ste_checker.py`. That file now re-exports `checked_spans`, so no existing caller
changed.

```mermaid
%%{init: {'theme': 'neutral'}}%%
C4Container
    title Container — prose-authenticity Plugin

    Person(user, "Author")

    Container_Boundary(pa, "prose-authenticity Plugin") {
        Container(orchestrator, "orchestrator", "Agent / sonnet", "Drives the humanize loop, manages run dir + handoff, emits DONE")
        Container(voiceprofiler, "voice-profiler", "Agent / opus", "Distills a voice profile YAML from 3+ writing samples")
        Container(humanizer, "humanizer", "Agent / opus", "Rewrites flagged ai-zones per tell report + voice profile")
        Container(detectionanalyst, "detection-analyst", "Agent / sonnet", "Runs detector tiers for /check; turns scores into a verdict report")
        Container(extractionagent, "extraction-agent", "Agent / haiku", "Resolves ambiguous code-surface zone-mapping calls")
        Container(questionadjudicator, "question-adjudicator", "Agent / sonnet", "Classifies genre + labels interrogatives rhetorical|genuine|quoted")

        Container(heuristics, "heuristics.py", "Python Script (uv run, PEP 723)", "Stylometric composite: burstiness, TTR, tell detection")
        Container(zoneparser, "zone_parser.py", "Python Script (uv run, PEP 723)", "Zone parsing, fail-fast validation, --reassemble splicing")
        Container(extractprose, "extract_prose.py", "Python Script (uv run, PEP 723)", "Code-surface comment/docstring extraction + ambiguity flags")
        Container(verdicts, "verdicts.py", "Python Script (uv run, PEP 723)", "PASS/WARN/FAIL decision table, tier precedence. Invoked only as a run_detectors-internal import, never called directly by an agent")
        Container(loopcontroller, "loop_controller.py", "Python Script (uv run, PEP 723)", "Deterministic humanize-loop state machine: cap/plateau/fact-retry")
        Container(factgate, "fact_gate.py", "Python Script (uv run, PEP 723)", "Parses grounded-synthesis coverage output via --from-handoff")
        Container(profilestore, "profile_store.py", "Python Script (uv run, PEP 723)", "Voice-profile schema validation and storage (stdlib only)")
        Container(apidetectors, "api_detectors.py", "Python Script (uv run, PEP 723)", "GPTZero/Originality/Sapling adapters (urllib)")
        Container(hfdetectors, "hf_detectors.py", "Python Script (uv run, PEP 723)", "Local HF model inference, import-guarded")
        Container(rundetectors, "run_detectors.py", "Python Script (uv run, PEP 723)", "Tier runner + consent pre-flight, fixed api > hf > heuristics precedence")
        Container(questiongate, "question_gate.py", "Python Script (uv run, PEP 723)", "scan/genre_signals/evaluate: the rhetorical-question gate")

        Container(config, "config/detectors.yaml", "YAML", "Detector roster + verdict thresholds (ADR-003)")
        ContainerDb(runstate, ".prose-authenticity/run-<id>/", "Filesystem State", "Per-run zones, scores, rewrites, handoff.json")

        %% ASD-STE100 conformance checker. A standalone CLI that is not part
        %% of the humanize pipeline. Rule conformance and AI-likelihood are
        %% different measurements; they never share a scale (ADR-006).
        Container(stechecker, "ste_checker.py", "Python Script / CLI (uv run, PEP 723)", "Seven-rule ASD-STE100 conformance check; reads the shared prose_spans seam; own verdict, own config (ADR-006, ADR-007)")
        Container(steconfig, "config/ste.yaml", "YAML", "STE rule thresholds and word lists (ADR-007)")
        Container(steskill, "simplified-technical-english", "Skill", "Drafting-time STE discipline; loaded before writing, independent of the /prose-authenticity:* commands (ADR-008)")

        %% Prose correctness checker. Standalone in the same way, and it shares
        %% the prose seam with the STE checker. Correctness, STE conformance
        %% and AI-likelihood never share a scale (ADR-010).
        Container(prosespans, "prose_spans.py", "Python Script (uv run, PEP 723)", "SHARED prose seam: code fences, inline code, block quotes, frontmatter and human zones removed, line numbers true to the raw file (ADR-010)")
        Container(correctnesschecker, "correctness_checker.py", "Python Script / CLI (uv run, PEP 723)", "Three-rule correctness check: C1 misspellings, C2 doubled words, C3 article agreement; own verdict, own config (ADR-010)")
        Container(faultdelta, "fault_delta.py", "Python Script / CLI (uv run, PEP 723)", "Multiset difference over both checkers' findings; buckets introduced / pre-existing / resolved. Identity ignores line numbers, because a rewrite moves text (ADR-012)")
        Container(correctnessconfig, "config/correctness.yaml", "YAML", "C1-C3 word lists, thresholds and per-rule severities (ADR-010)")
        Container(correctnessskill, "prose-correctness", "Skill", "Drafting-time correctness discipline and the rule for adding a list entry; independent of the /prose-authenticity:* commands (ADR-010)")
    }

    System_Ext(groundedsynth, "grounded-synthesis-orchestrator", "Fact-coverage audit over source files")

    %% The commands start the agents. The command setup has no agent.
    Rel(user, detectionanalyst, "Starts /prose-authenticity:check (Agent tool)")
    Rel(user, voiceprofiler, "Starts /prose-authenticity:profile (Agent tool)")
    Rel(user, orchestrator, "Starts /prose-authenticity:humanize (Agent tool)")

    Rel(orchestrator, zoneparser, "Parse/reassemble zones (Bash)")
    Rel(orchestrator, extractprose, "Extract/reassemble code-surface prose (Bash)")
    Rel(orchestrator, loopcontroller, "Next-action decision each iteration (Bash)")
    Rel(orchestrator, factgate, "Resolve fact-coverage verdict (Bash)")
    Rel(orchestrator, profilestore, "Load/validate voice profile (Bash)")

    Rel(orchestrator, humanizer, "Dispatch per iteration (Agent tool)")
    Rel(orchestrator, extractionagent, "Dispatch on ambiguous zone mapping (Agent tool)")
    Rel(orchestrator, questionadjudicator, "Dispatch to adjudicate the question gate (Agent tool)")
    Rel(orchestrator, groundedsynth, "Dispatch fact-coverage audit (Agent tool)")

    Rel(detectionanalyst, rundetectors, "Run detector tiers (Bash)")
    Rel(detectionanalyst, questionadjudicator, "Dispatch to adjudicate the question gate (Agent tool)")
    Rel(rundetectors, questiongate, "Scan + evaluate the rhetorical-question gate (internal import)")
    Rel(rundetectors, heuristics, "Always-on tier")
    Rel(rundetectors, hfdetectors, "Opt-in tier")
    Rel(rundetectors, apidetectors, "Opt-in, consent-gated tier")
    Rel(rundetectors, config, "Read roster + thresholds")
    Rel(rundetectors, verdicts, "Decide PASS/WARN/FAIL (internal import, not a Bash dispatch)")

    Rel(orchestrator, runstate, "Read/write run state, write handoff before DONE")

    %% STE checker + skill. A standalone CLI and a drafting skill. The
    %% orchestrator does not dispatch them, and they are not part of the
    %% humanize chain above.
    Rel(user, stechecker, "Invokes directly as a CLI (Bash)")
    Rel(detectionanalyst, stechecker, "Run for the report; delta vs the original on a humanize run (Bash) — never a composite input (ADR-006, ADR-012)")
    Rel(stechecker, prosespans, "Extract checked prose spans (import; re-exports checked_spans)")
    Rel(stechecker, zoneparser, "Catches ZoneParseError raised through the seam (import)")
    Rel(stechecker, steconfig, "Reads rule thresholds + word lists")
    Rel(user, steskill, "Loads while drafting, independent of /prose-authenticity:* commands")

    %% Correctness checker. The second consumer of the shared seam.
    Rel(user, correctnesschecker, "Invokes directly as a CLI (Bash)")
    Rel(detectionanalyst, correctnesschecker, "Run for the report; delta vs the original on a humanize run (Bash) — never a composite input (ADR-006, ADR-012)")
    Rel(detectionanalyst, faultdelta, "Run on a humanize run to bucket what the rewrite introduced (Bash)")
    Rel(faultdelta, correctnesschecker, "Collect findings for both documents (import)")
    Rel(faultdelta, stechecker, "Collect findings for both documents (import)")
    Rel(correctnesschecker, prosespans, "Extract checked prose spans (import)")
    Rel(correctnesschecker, zoneparser, "Catches ZoneParseError raised through the seam (import)")
    Rel(correctnesschecker, correctnessconfig, "Reads word lists, thresholds + severities")
    Rel(prosespans, zoneparser, "Parse zones before extraction (import)")
    Rel(user, correctnessskill, "Loads while drafting, independent of /prose-authenticity:* commands")

    classDef agent fill:#1a3a5c,stroke:#0d2137,color:#ffffff
    classDef script fill:#1e4d2b,stroke:#0f2e19,color:#ffffff
    classDef state fill:#7a4a00,stroke:#4d2e00,color:#ffffff
    classDef skill fill:#5c2d5c,stroke:#33193a,color:#ffffff
    class orchestrator,voiceprofiler,humanizer,detectionanalyst,extractionagent,questionadjudicator agent
    class heuristics,zoneparser,extractprose,verdicts,loopcontroller,factgate,profilestore,apidetectors,hfdetectors,rundetectors,questiongate,stechecker,prosespans,correctnesschecker script
    class runstate state
    class steskill,correctnessskill skill
```

## Model Tier Rationale

| Agent | Model | Reason |
|---|---|---|
| voice-profiler | opus | The agent distills a coherent voice profile from samples. This needs nuanced pattern synthesis, not structured extraction |
| humanizer | opus | The agent rewrites text to defeat detectors, keeps the meaning, and matches a voice profile. This is the highest-stakes generative task in the plugin |
| orchestrator | sonnet | Thin coordination: run-dir management and loop dispatch. No open-ended judgment |
| detection-analyst | sonnet | The agent makes a structured report from scores that the scripts already computed |
| extraction-agent | haiku | Narrow, bounded include/exclude calls on flagged zones. No open-ended reasoning |
| question-adjudicator | sonnet | The agent classifies the genre and judges each interrogative as rhetorical, genuine, or quoted, from deterministic signals. This is bounded judgment, not open-ended synthesis |
