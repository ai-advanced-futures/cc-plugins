---
description: Answers a question from the knowledge graphs of the project, one step at a time - the generic graph and each brain in .claude/knowledge.json, also a graph in another GitHub repository. The ask skill of each brain uses this procedure for the steps after its shortcuts, and this skill is the fallback when no brain ask fits. Use for "/knowledge:ask", "what do we know about X", "ask the wiki", and a question that crosses two brains.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(mktemp *)
---

# Ask the knowledge graphs

The question is: **$ARGUMENTS**

Answer from the graphs only. When no page answers the question, say so.
Never write a page (D23), because an ask only reads: `knowledge:learn` writes,
after the person says yes.

`K` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py --root "$(git rev-parse --show-toplevel)"`.

## Step 1: start

1. When the question is empty, stop with:
   "Give me a question. Run `/knowledge:ask <your question>`."
2. Run `$K registry list`. When it exits 2 or prints nothing, stop with:
   "This project has no knowledge graph. Run `/knowledge:setup`, or the setup of a brain."
3. For each graph, get the path of its manifest with
   `$K resolve <graph>:/manifest.md`, then read that file with the Read tool.
   Read `answers` and `ask_skill`.
4. Select the start nodes:
   - When the ask skill of a brain called this procedure, use its start nodes.
   - When not, select each graph whose `answers` match the question, and use
     its root index, `<graph>:/index.md`.
5. Make the walk state. Use `$KNOWLEDGE_WALK_STATE` when it is set. When not,
   use the output of `mktemp -u /tmp/knowledge-walk-XXXXXX.json`:

   ```bash
   $K walk start --state "$STATE" --question "<the question>" <start node> ...
   ```

## Step 2: the loop

Do these steps again and again:

1. Run `$K walk next --state "$STATE"`. Exit 1 means that no node is waiting:
   go to Step 4.
2. Get the path of the node with `$K resolve <node>`, then read that one file
   with the Read tool, not with `cat`, `grep` or another shell command.
3. Run `$K walk candidates --state "$STATE" <node>`. Each row is one neighbor
   that is not done and not waiting.
4. Dispatch one `knowledge:neighbor-judge` subagent. Give it the question, the
   facts (`$K walk show --state "$STATE"`), the node with its text, and the
   rows. Never judge the rows yourself (D24), because the judge sees only the
   inputs of this step, so what you read before cannot bias it.
5. Record each FACTS line: `$K walk fact --state "$STATE" <node> "<fact>"`.
   Add each KEEP node: `$K walk keep --state "$STATE" <node> ...`.
6. Do the facts answer the question? When yes, go to Step 4. When no, do the
   loop again.

## Step 3: enter another graph

When a kept node is in another graph, get the path of its manifest with
`$K resolve <graph>:/manifest.md`, and read that file with the Read tool. When
the skill of its `ask_skill.plugin` is in your skill list, load it with the
Skill tool for its shortcuts, and give it the state file. When not, continue
with this procedure (D25). A node in a remote graph resolves through the cache
(`$K fetch <graph>` updates it).

## Step 4: answer

- Cite each page that you used, with its graph and its path:
  `(<graph>:/<path>)`.
- Write `(draft)` after each page with `status: draft`.
- When the facts give no answer to the question, write:
  "The graphs hold no page that answers this question." Then list the gaps.
- Give the count of pages that you read: the length of `done` in
  `$K walk show --state "$STATE"`.

## Step 5: offer to learn

After the person accepts the answer, ask one question: "Learn this answer?"

- On yes, call `knowledge:learn` with the answer, the type `Synthesis`, each
  cited `<graph>:/<path>` as a source, and `verified` with the person as the
  actor on each source page (A5).
- When the answer fits a page type of the brain that answered (for example a
  new decision), name the `learn` skill of that brain too.
- A change to a remote graph goes through a pull request (standard section 12).
- On no, stop. Write nothing.

## No subagents

When the Agent tool or the `knowledge:neighbor-judge` agent type is missing
(a skills install has no subagents), stop with: "knowledge:ask needs
subagents and the knowledge plugin. Install the plugin: claude plugin install
knowledge@cc-plugins." (A8)

An answer that does not come from the walk, for example from a grep of the files, starts
with this exact first line: `not a graph walk: grep fallback`.
