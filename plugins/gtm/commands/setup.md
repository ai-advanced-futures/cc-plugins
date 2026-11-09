---
description: Show how to add the optional MCP servers — HubSpot, Apollo.io, Ahrefs, Canva, GA4, Notion, Slack — and check which ones are connected
allowed-tools: ["Read(*)", "Write(*)", "Bash(docker info)", "Bash(claude mcp list)", "AskUserQuestion"]
---

# /gtm:setup

## Purpose

Show how to connect the optional MCP servers of the GTM plugin. Each connected server gives live data: pipeline stages from HubSpot, keyword research from Ahrefs, prospect lists from Apollo.io, funnel analytics from GA4, design generation from Canva, and publishing to Notion and Slack. Every GTM agent works without these servers. This command is safe to run again: it skips servers that are already connected.

This command asks for no token and does not run `setup_mcp.sh`. You type your own credentials, in your own terminal.

## Usage

```
/gtm:setup
/gtm:setup --server hubspot
/gtm:setup --skip-optional
```

## Process

1. **Run `claude mcp list`** — read which MCP servers are already configured. Compare the names with the server names below.

2. **Show the status table** — one line for each of the 7 servers. This is an example:

   ```
   Server              Name         Status             Unlocks
   ─────────────────────────────────────────────────────────────────────────
   Google Analytics 4  ga4          connected          Funnel analytics, acquisition data
   Notion              notion       connected          Document publishing, knowledge base
   Slack               slack        not configured     Team announcements, channel posting
   Apollo.io           apollo       not configured     Prospect search, contact enrichment
   HubSpot             hubspot      not configured     Pipeline stages, CRM sync
   Ahrefs              ahrefs       not configured     Keyword research, SEO data
   Canva               canva        not configured     Design generation, asset creation
   ```

   Read `${CLAUDE_PLUGIN_ROOT}/definitions/mcp-commands.json`. It maps each GTM command to the servers it can use. For each server that is not configured, list the commands that use it.

3. **Check for Docker** — run `docker info`. If Docker Desktop is installed, show Path A. If it is not installed, show Path B only.

4. **Ask which servers to set up** — use `AskUserQuestion`, in this order: GA4, Notion, Slack, Apollo.io, HubSpot, Ahrefs, Canva. Skip a server that is connected. With `--skip-optional`, ask only about GA4 and Notion. With `--server <name>`, ask about that server only.

5. **Show the steps for each server that the person picks** — say what the server unlocks in the GTM workflow and which credential it needs (see the table below). Then show Path A or Path B. The person types the credential and runs the install line in a terminal. A credential typed here stays in the conversation log.

6. **Run `claude mcp list` again** — tell the person to run the lines in a terminal, then run this command again. Show the new status. A server that shows as connected is ready. For a server that does not, show the Graceful Degradation line for it.

7. **Write `.gtm-mcp-status.json`** — record the status that `claude mcp list` shows, for all 7 servers:

   ```json
   {
     "last_checked": "<ISO timestamp>",
     "servers": {
       "google-analytics": { "connected": true, "verified_at": "<timestamp>" },
       "hubspot": { "connected": false, "error": "not in claude mcp list" }
     }
   }
   ```

8. **Update `gtm-context.json`** — if the file exists, write `_meta.sources.mcp_connections[]` with the list of connected servers. If it does not exist, leave it absent, because this command only reports the MCP status there.

## Two Paths

### Path A — Docker MCP Toolkit (preferred)

If Docker Desktop is installed, the person runs:

```
/plugin install docker-mcp-toolkit@docker
```

Then the person runs `/gtm:setup` again. HubSpot, Notion, Slack and Apollo.io are in the Docker MCP Catalog. Add them from the catalog.

### Path B — Terminal (when Docker is not installed)

The person runs this line in a terminal. The script asks for the token there and keeps it out of this conversation:

```
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup_mcp.sh" <name>
```

`<name>` is `all`, `hubspot`, `apollo`, `ahrefs`, `ga4`, `notion` or `canva`. Do not put `--server` in front of the name. For Slack, show the sentence below the table.

Or the person runs the `claude mcp add` line of the server. Replace each value in `<angle brackets>` with your own value.

| Name | Line to run |
|------|-------------|
| `hubspot` | `claude mcp add-json hubspot '{"command":"npx","args":["-y","@hubspot/mcp-server@0.4.0"],"env":{"PRIVATE_APP_ACCESS_TOKEN":"<token>"}}'` |
| `apollo` | `claude mcp add-json apollo '{"command":"npx","args":["-y","@thevgergroup/apollo-io-mcp@3.0.0"],"env":{"APOLLO_API_KEY":"<key>"}}'` |
| `ahrefs` | `claude mcp add --transport sse ahrefs https://api.ahrefs.com/mcp/mcp` |
| `ga4` | `claude mcp add-json google-analytics '{"command":"uvx","args":["--from","analytics-mcp==0.8.0","analytics-mcp"],"env":{"GOOGLE_APPLICATION_CREDENTIALS":"<path-to-credentials-json>","GOOGLE_CLOUD_PROJECT":"<project-id>"}}'` |
| `notion` | `claude mcp add-json notion '{"command":"npx","args":["-y","@notionhq/notion-mcp-server@2.6.1"],"env":{"NOTION_TOKEN":"<token>"}}'` |
| `canva` | `claude mcp add-json canva '{"command":"npx","args":["-y","@canva/cli@2.17.0","mcp"]}'` |

Slack has no line: the old package is deprecated, and the hosted Slack server needs your own Slack app. The section "MCP servers" of the README says what to do. Until a server named `slack` gives the tool `slack_post_message`, `/gtm:marketing:launch` writes no Slack post.

The server names must be exactly `hubspot`, `apollo`, `ahrefs`, `google-analytics`, `notion`, `slack` and `canva`. A server that has another name does not match the tool names that the GTM agents use (`mcp__<server>__<tool>`).

## Server Configuration Details

| Server | Credential | Server order (free tier first) | What It Unlocks |
|--------|------------|-------------------------------|-----------------|
| Ahrefs | OAuth, no token | 1 | Keyword research, search volume, backlinks |
| Canva | OAuth, no token | 2 | Design generation, template autofill, export |
| GA4 | Service Account JSON + Google Cloud project ID (free with GA4 access); needs `uv` | 3 | Funnel analytics, acquisition data |
| Notion | Integration token (free) | 4 | Document publishing, knowledge base pull |
| Slack | Your own Slack server: no script line | 5 | Team announcements, channel posting |
| Apollo.io | API key (free tier at app.apollo.io) | 6 | Prospect search, contact enrichment, org data |
| HubSpot | Private App token (free CRM) | 7 | Pipeline stages, deal tracking, CRM sync |

## Graceful Degradation

Every GTM agent works when an MCP server is not connected:

- No Ahrefs → web research, labeled "approximate, verify with Ahrefs"
- No HubSpot → you give the funnel metrics by hand
- No Apollo.io → the output holds ICP criteria for a manual search
- No Canva → the output holds the brief for the visual asset, with no file
- No GA4 → you give the visitor and sign-up counts by hand
- No Notion or Slack → the output stays in local files

## After Setup

Run `/gtm:run` to start the full build with live integrations, or run individual commands like `/gtm:marketing:launch` or `/gtm:sales:prospecting` to use specific integrations directly.
