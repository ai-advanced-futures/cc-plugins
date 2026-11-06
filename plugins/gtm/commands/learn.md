---
description: Ingest human knowledge files (call transcripts, win/loss notes, playbooks) and extract GTM intelligence
allowed-tools: ["Read(*)", "Write(*)", "Glob(*)", "Grep(*)", "AskUserQuestion", "mcp__notion__notion-search", "mcp__notion__notion-retrieve-page"]
---

# /gtm:learn

## Purpose

Ingest human knowledge artifacts — Gong call transcripts, win/loss notes, sales playbooks, competitive battle cards, customer interview recordings, and support tickets — and extract structured GTM intelligence from them. The team knowledge your team has already learned from real customers becomes signal that populates `gtm-context.json`. This is the highest-trust data input in the GTM system because it comes from direct customer contact, not inference.

Intelligence from Tier 1 sources (recorded calls) overrides framework defaults when the two conflict.

## Usage

```
/gtm:learn path/to/transcript.vtt
/gtm:learn path/to/win-loss-notes/
/gtm:learn "interviews/*.md"
/gtm:learn --notion                          # pull documents directly from Notion
/gtm:learn path/to/file.vtt --tier 1        # override auto-detected Truth Tier
```

Accepts single files, directories, or glob patterns.

## Process

1. **Accept path argument** — accept a file path, folder path, or glob pattern from the user. If no argument is provided, ask via `AskUserQuestion` where the knowledge files are located. Also accept `--notion` flag to pull from Notion instead of local files.

2. **Detect file types** — identify the type of each file in the input set and select the appropriate ingestion strategy:
   - `.vtt` — Gong or Zoom call transcript (WebVTT format)
   - `.json` — structured call data or CRM export (including a Gong JSON export)
   - `.md` / `.txt` — written notes, battle cards, playbooks, email threads, customer emails
   - `.csv` — win/loss analysis exports, survey data
   - `.pdf` — research reports, analyst briefs, customer case studies
   - `.docx` — sales decks in document form, formal playbooks

3. **Read each file by the rule of `${CLAUDE_PLUGIN_ROOT}/definitions/learned-knowledge-schema.md`** — read that file first. It gives the fields of `learned_knowledge`, the Truth Tier of each source type, and the rule that merges sources. Read each input file with the `Read` tool. For a transcript, note who speaks each line. For a structured document, note each section. If a file cannot be read, put it in the list of failed files with the reason.

4. **Assign Truth Tier by source type** — the Truth Tier of extracted intelligence is the Truth Tier of its source. The table of `learned-knowledge-schema.md` decides:
   - Call recording (`.vtt`, verbatim) → **Tier 1** (primary source, customer's own words)
   - CRM export (`.json`) → **Tier 1** (system-of-record data)
   - Win/loss write-ups (`.md`) → **Tier 2** (observed, filtered through rep interpretation)
   - Strategy decks (`.pdf`) → **Tier 3** (intended direction, not actuals)
   - CRM notes that a rep wrote after a call, customer emails and messages → **Tier 2**
   - Team-written playbooks, battle cards, best-practice documents → **Tier 3** (COMMITTED: a plan that the team wrote down, not validated by customers)
   - Blog posts, competitor websites, third-party analysis → **Tier 3** (external inference)
   - AI prompt instructions → context only, not a marketing claim
   - The user can override with `--tier` for any file

5. **Extract GTM intelligence** — run structured extraction on each document to surface:
   - **Winning phrases** — exact customer language that resonates ("we were drowning in manual work", "it just worked")
   - **Objections** — every objection raised with the context in which it arose
   - **Objection responses** — what the rep said and whether it worked (based on deal outcome)
   - **Customer language** — the words customers use to describe their problem (not your marketing language)
   - **Loss patterns** — recurring reasons deals were lost (price, competitor, timing, champion left, no champion)
   - **Win patterns** — recurring conditions present in closed-won deals
   - **Competitor intelligence** — competitor names mentioned, strengths cited by customers, competitor weaknesses
   - **Feature requests** — product gaps mentioned as blockers or deal risks
   - **Proof points** — specific outcomes customers have achieved, with source attribution

6. **Pull documents from Notion** (if connected and `--notion` flag used) — run `notion-search` to find relevant pages in the GTM workspace, then `notion-retrieve-page` to read each page. Apply the same extraction to each page. If the Notion tools are not in the session, tell the person to run `/gtm:setup` and stop this step.

7. **Write extracted intelligence to `gtm-context.json.learned_knowledge`** — structure the output as:
   ```json
   {
     "learned_knowledge": {
       "winning_phrases": [...],
       "objections": [{ "objection": "...", "context": "...", "effective_response": "...", "tier": 1 }],
       "customer_language": [...],
       "loss_patterns": [...],
       "win_patterns": [...],
       "competitor_intel": [{ "competitor": "...", "strength": "...", "weakness": "...", "source": "...", "tier": 2 }],
       "feature_requests": [...],
       "sources_ingested": [{ "file": "...", "type": "...", "tier": 1, "ingested_at": "..." }]
     }
   }
   ```
   When 3 or more independent sources show the same signal, mark it `high_confidence: true`, as `learned-knowledge-schema.md` says.

8. **Tag the result for the later agents:**
   - Winning phrases and customer language are the preferred vocabulary for all future artifacts.
   - Objections go to the objection bank of `pipeline-playbook.json`.
   - Loss patterns go to the orchestrator for ICP refinement.

9. **Summarize extraction results** — report to the user:
   - Number of files ingested
   - Number of intelligence items extracted per category
   - Top 3 most frequently cited objections
   - Top 3 most frequently cited competitor names
   - Any files that failed to parse with the reason

## Output Artifacts

- Updates `gtm-context.json.learned_knowledge` with all extracted intelligence
- `ingestion-report.md` — summary of what was ingested and what was learned

## Why Learn First

Everything built downstream — brand narrative, pitch deck, objection handling, ICP — should be grounded in what real customers have already said. In `/gtm:run`, the knowledge agent runs before all other agents when you give it files. Without this step, the GTM system reasons from first principles. With this step, it reasons from evidence.
