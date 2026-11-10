---
description: Saves knowledge into the generic knowledge graph - a document, a URL, or an answer that the person accepted from an ask - through the save code knowledge_graph.py, then runs both checks and reports. Use for "/knowledge:learn", "ingest this", "add this source to the wiki", and the "Learn this answer?" offer of an ask.
argument-hint: "[path | URL | answer]"
allowed-tools: Read, Write, Edit, Glob, Grep, WebFetch, Skill, AskUserQuestion, Bash(uv run *), Bash(git *), Bash(gh issue create *), Bash(mkdir *), Bash(cp *), Bash(test *), Bash(ls *)
---

# Learn into the knowledge graph

The input is: **$ARGUMENTS**

`ROOT` is `$(git rev-parse --show-toplevel)`.
`G` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge_graph.py --root "$ROOT"`.
`K` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py --root "$ROOT"`.

## Step 0: the guard

Run `$G resolve /index.md`. When it exits 2, stop with: "This project has
no knowledge graph. Run `/knowledge:setup` first."

## Step 1: the input

| Input | What to do |
|---|---|
| empty | List the files in `<container>/raw/` that have no Source page. When there are none, say so and stop. |
| a URL | Fetch it. Save the text to `<container>/raw/<date>-<slug>.<ext>`. |
| a path in `raw/` | Use it. |
| another path | Copy it to `<container>/raw/<date>-<slug>.<ext>`. |
| an answer from an ask | Go to Step 3. |

`<container>` is the parent folder of the bundle. The slug tells what the
file holds. Never edit a raw file, because each Source page cites it as the
record of what the source said.

## Step 2: pages from a source

1. Read the whole raw file.
2. Make the Source page:
   `$G new Source --title "<title>" --description "<one line>" --set resource=raw/<raw file>`.
   The page has the base name of the raw file. When `new` exits 2 because
   the slug is taken, run it again with `--slug <raw base name>-<n>`.
   Write its text with `$G body <slug> --file -`: start with `# <title>`.
3. For each entity, concept, and open question of the source: when a page
   exists (`$G resolve <slug or alias>`), change it with `$G set`, and add a
   section with `$G body <slug> --append --file -`. When not, make it with
   `$G new <Type>`, then write its text with `$G body <slug> --file -`.
   Link each page to its source:
   `$G link <slug> sources /sources/<source file>`, where `<source file>` is
   the file name in the path that `new` printed for the Source page.
4. When 3 or more pages share one story, make a Synthesis page with
   `$G new Synthesis`, then write its text with `$G body <slug> --file -`.
5. Write each refuted claim under `## Refuted or unverified claims`, with
   `$G body <slug> --append --file -`.

## Step 3: a learned answer

1. Make one Synthesis page: `$G new Synthesis --title "<title>" --description "<one line>"`.
   Write the answer with `$G body <slug> --file -`.
2. Link each cited page: `$G link <slug> sources <graph>:/<path>`.
3. For each cited page, add the person to `verified`: run the `set` of the
   save code of that brain (`manifest.md` names it in `save_code`), with the
   full `verified` list plus `{by: human:<login>, at: <now>}`.
4. A cited page in a remote graph changes only through a pull request, after
   a separate yes:
   `$K remote-checkout <graph>`, then the save code with `--root <clone>`,
   then `$K remote-publish <graph> --branch knowledge/learn-<date> --title "<title>" --body-file <file>`.

## Step 4: direct edits

Edit a page directly only for a change that no command of the save code can
make (`body` writes text). Then write one Report entry for each direct edit:
`$G log Report "<operation> failed: <error>. I edited <page> directly: <edit>. Reason: <reason>."`
Write one Report entry for each recommendation to improve this skill or the
save code.

## Step 5: both checks

Call the `knowledge:checking` skill with each graph that changed. When it
returns `CHECKS: FAILED`, correct the cause, and call it again.
Never report success while it returns `CHECKS: FAILED`, because a failed
check means that a page or a link is broken.

## Step 6: report

Tell the person:
- the raw file and its slug;
- the pages that you made and changed, by type;
- each claim that the source contradicts;
- each Report entry of Step 4;
- each ERROR, WARN, and SKIP line of the checks. A SKIP line is a rule that
  did not run.

When Step 4 wrote a Report entry, ask: "Open a GitHub issue with this report
in the plugins repository?" After a yes, show the person the full issue body,
in a fenced block, as the command will send it. Then ask a second question:
"Open the issue with this body? `ai-advanced-futures/cc-plugins` is public, so
remove each path and each value of the project that must stay private." When
the person changes the body, show it again and ask again. Open it only after a
yes to the second question, because the first yes is to the offer and not to
the text:

```bash
gh issue create --repo ai-advanced-futures/cc-plugins --title "knowledge:learn report" --body-file <report file>
```

The report file holds only the body that the person accepted.

Leave the diff uncommitted, so that the person reviews it before the commit.
