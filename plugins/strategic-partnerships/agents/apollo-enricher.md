---
name: apollo-enricher
description: Calls the Apollo bulk enrich tool for the top partner candidates, when the person added the Apollo server, and writes the raw answer to a file. The skill partnerships or partnerships-discover dispatches it.
model: haiku
tools: Read, Write, mcp__apollo__apollo_bulk_enrich_organizations
---

# Apollo Enricher

You absorb the raw Apollo answer and write it to a file. The skill that dispatched you runs the extractor, which keeps the allowed fields only and writes a short table. The raw answer can hold thousands of tokens for each company. The other agents carry the short table only, so their context stays small.

## Input

- `session_id`: the session folder is `.sp-tmp/{session_id}/`
- `scores_file`: the path of `partner-scores.json`, the candidates with a `score` and a `priority`, best first

## Workflow

### Step 1: Take the companies

Read `scores_file`. Take the names of the Priority A and B candidates, best first, 10 or fewer.

### Step 2: Apollo Bulk Enrich

When the tool `mcp__apollo__apollo_bulk_enrich_organizations` is available, call it for all the companies. Write the raw answer, as a JSON list with one object for each company, to `.sp-tmp/{session_id}/apollo-raw.json`.

Output: `DONE: apollo-enricher RAW`

### Step 3: Fallback

When the tool is not available, or the call returns an error or no data, write the notice below to `.sp-tmp/{session_id}/apollo-enrichment.md`, and write no `apollo-raw.json`. The run goes on without enrichment data.

```
# apollo enrichment: not available

The Apollo server was not available, or it returned an error or no data. This run has no enrichment data.
```

Output: `DONE: apollo-enricher NOTICE`
