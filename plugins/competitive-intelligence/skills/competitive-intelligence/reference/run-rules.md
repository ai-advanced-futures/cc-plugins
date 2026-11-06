# Reference: run rules of the full competitive analysis

The skill `competitive-intelligence` points to this file. The skill runs in the main conversation, so it asks the person. An agent cannot ask.

## One phase: ask, dispatch, wait, show

| Part | Rule |
|---|---|
| Ask | The skill asks each question whose answer is not yet known with the `AskUserQuestion` tool [q: none]. It puts up to 4 questions in one call and records where each answer came from. |
| Dispatch | The `Agent` tool, with the full name `competitive-intelligence:<agent>`. The answers go in as dispatch fields. Every agent gets `session_id` and `data_dir`. `data_dir` is `.competitive-intelligence/{session}/` under the git root. |
| Wait | The agent ends with its `DONE:` line. Then the skill reads the summary file of the phase and shows it at the checkpoint. |
| No answer | When `AskUserQuestion` is not available [q: none], or the person gives no answer, the input is left out of the dispatch and the agent uses its own default. At a checkpoint with no answer, the choice is Proceed. |
| Change | When the person picks Adjust, Refine, Add competitors, Reclassify or Gather more, the skill asks what to change in one chat message. It dispatches the same agent again with the dispatch field `adjustments` set to the words of the person. The agent overwrites its output files. |

## Checkpoint options

| Checkpoint | Shown | Options | Follow-up |
|---|---|---|---|
| Lens findings | The 6 lens headlines, the cross-validation agreement in percent, the contradictions | Proceed, Deep dive, Investigate contradictions | Deep dive: ask which lens, read its analysis file, show its key findings, then ask again. Investigate contradictions: read `lens-cross-validation.json`, show each contradiction, then ask again. |
| Synthesis | The top recommendations and the SWOT headline | Proceed, Refine | Refine: the Change row above. |

## Failure of an agent

When an agent returns an error, or writes no output file:

1. The skill logs the failure to `execution-log.md` in `data_dir`, with the time, the phase and a short summary of the error.
2. The skill dispatches the agent again one time with the same fields.
3. When it fails a second time, the skill asks with `AskUserQuestion` [q: none]: "Phase [X] failed twice. Retry, Skip or Cancel?"

| Answer | Effect |
|---|---|
| Retry | Try again. The person can first change the inputs. |
| Skip | Continue without this part. Skip is offered for a lens only. A phase cannot be skipped. |
| Cancel | Stop the analysis. The state is saved in `session.json`, and the person is told how to continue. |

The lens executor handles the failure of one lens by itself. It marks a lens that fails 2 times `skipped` and goes on. Its reason is in `lens_failures` in `session.json`. The skill tells the person which lens was skipped and why. Each phase starts with a failure count of 0.

## Open questions of an agent

When an agent needs an answer that it does not have, it writes `open-questions.json` in `data_dir` and returns `QUESTIONS: <path>` as its last line. It does not return `DONE:`. A `text` question is asked in a chat message.

## session.json

`current_phase` is one of `context`, `ecosystem`, `intelligence`, `lens-analysis`, `synthesis` or `deliverables`. `session.json` replaces the older `state.json` and `session-metadata.json`; those two files are not used.
