---
name: saving-deferred
description: Saves only the exact group of open architecture findings that the person approved in architecture:explore. Internal helper; returns saved paths, unsaved findings with causes, and check notes without conducting an interview.
user-invocable: false
context: fork
background: false
model: sonnet
allowed-tools: Read, Skill(knowledge:learn), Skill(knowledge:checking), Bash(git rev-parse *), Bash(uv run */scripts/knowledge_graph.py *), Bash(uv run */scripts/knowledge.py brain-check *), Bash(uv run */scripts/knowledge.py check *)
disallowed-tools: Agent, AskUserQuestion, Artifact, ArtifactCheck, ArtifactComments, ArtifactData, CronCreate, CronDelete, CronList, CrossSessionMessage, DesignSync, Edit, EndConversation, EnterPlanMode, EnterWorktree, ExitPlanMode, ExitWorktree, Glob, Grep, ListAgents, ListMcpResourcesTool, Monitor, NotebookEdit, PushNotification, ReadMcpResourceDirTool, ReadMcpResourceTool, RemoteTrigger, ReportFindings, ScheduleWakeup, SendFeedback, SendMessage, SendToProject, SendToProjectContext, TaskCreate, TaskGet, TaskList, TaskStop, TaskUpdate, TodoWrite, ToolSearch, WebFetch, WebSearch, Workflow, Write, mcp__*
---

# Save approved open findings

The input is the exact plain-text group approved by the person in Explorer: **$ARGUMENTS**.
Each finding has a question, context, options, reason it remains open, source, and an
external-ADR identity when present. Approval permits a knowledge save, not acceptance of
the options. If the input lacks the approval or a usable group, return it as unsaved with
the cause. Do not ask interview questions, add findings, choose an option, or expand the
approved group.

Invoke `knowledge:learn` with the approved findings as a learned answer, not as a path or
URL to fetch. Preserve each question as open, its context and options, the reason it
remains open, and its source attribution. An external source is attribution, not a request
to import or verify an external ADR. Save through the knowledge save code that Learn uses.
Expand nested save and check command examples to literal script and repository paths before
calling Bash, because narrow command grants cannot verify shell variables or substitutions.
Leave ADRs and their lifecycle unchanged, because open findings are not accepted choices.
Return a failed save as unsaved, with no fallback file, because only the knowledge graph
is the approved destination. Keep the work to this local save: no agents, interview,
remote write, or issue-reporting flow.

If the plugin, graph, or save support is missing, return the affected findings as unsaved
and name the missing part and setup step. A failed call or failed check is not a successful
save. List any paths written before failure and the findings that still lack a verified
save, because partial writes need repair rather than a success claim. Retain every ERROR,
WARN, and SKIP line from the checks.
A SKIP line names a check that did not run.

Return these four lists to Explorer in the response, not a persistent report file:

- `saved`: each finding and its verified knowledge path, or `none`.
- `unsaved`: each finding without a verified save and its cause, or `none`.
- `written before failure`: each partial path when applicable, clearly not a verified save.
- `check notes`: each ERROR, WARN, and SKIP line, or the reported check result.

Report a saved path only when Learn returns that path and a successful check result.
Explorer keeps unsaved findings open and reports them to the person.
