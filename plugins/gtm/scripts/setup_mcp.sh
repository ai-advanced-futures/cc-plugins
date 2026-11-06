#!/usr/bin/env bash
# GTM Plugin — MCP Server Setup
# Usage: bash setup_mcp.sh <name>   (name: all, hubspot, apollo, ahrefs, ga4, notion, slack or canva)
#
# Path A (preferred): Docker MCP Toolkit — /plugin install docker-mcp-toolkit@docker
# Path B (this script): Direct npm-based MCP server installation
#
# Safe to run multiple times — checks if already configured before adding.

set -euo pipefail

check_already_configured() {
  local server="$1"
  claude mcp list 2>/dev/null | grep -q "^$server" && return 0 || return 1
}

setup_hubspot() {
  if check_already_configured "hubspot"; then
    echo "✓ HubSpot already configured — skipping"
    return
  fi
  echo "HubSpot: Create a Private App at app.hubspot.com/private-apps"
  echo "Required scopes: contacts, deals, companies, marketing (read + write)"
  read -rsp "Private App Token: " token; echo
  claude mcp add-json hubspot "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@hubspot/mcp-server\"],
    \"env\": {\"PRIVATE_APP_ACCESS_TOKEN\": \"$token\"}
  }"
  echo "✓ HubSpot configured"
}

setup_apollo() {
  if check_already_configured "apollo"; then
    echo "✓ Apollo.io already configured — skipping"
    return
  fi
  echo "Apollo.io: Get API key at app.apollo.io/settings/api"
  read -rsp "Apollo API Key: " key; echo
  claude mcp add-json apollo "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@thevgergroup/apollo-io-mcp\"],
    \"env\": {\"APOLLO_API_KEY\": \"$key\"}
  }"
  echo "✓ Apollo.io configured"
}

setup_ahrefs() {
  if check_already_configured "ahrefs"; then
    echo "✓ Ahrefs already configured — skipping"
    return
  fi
  echo "Ahrefs: Uses OAuth — no token needed. Connecting remote server..."
  claude mcp add --transport sse ahrefs https://api.ahrefs.com/mcp/mcp
  echo "✓ Ahrefs configured (OAuth will be requested on first use)"
}

setup_ga4() {
  if check_already_configured "google-analytics"; then
    echo "✓ Google Analytics 4 already configured — skipping"
    return
  fi
  echo "GA4: Requires Google Service Account JSON file + Property ID"
  echo "Create Service Account at console.cloud.google.com → IAM → Service Accounts"
  echo "Grant role: Viewer on your GA4 property"
  read -rp "Path to Google credentials JSON: " creds
  read -rp "GA4 Property ID (numeric, e.g. 123456789): " prop_id
  claude mcp add-json google-analytics "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"mcp-server-google-analytics\"],
    \"env\": {
      \"GA4_PROPERTY_ID\": \"$prop_id\",
      \"GOOGLE_APPLICATION_CREDENTIALS\": \"$creds\"
    }
  }"
  echo "✓ Google Analytics 4 configured"
}

setup_notion() {
  if check_already_configured "notion"; then
    echo "✓ Notion already configured — skipping"
    return
  fi
  echo "Notion: Create integration at notion.so/my-integrations"
  echo "Grant pages access to any workspace pages you want GTM to read/write"
  read -rsp "Notion Integration Token: " token; echo
  claude mcp add-json notion "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@notionhq/notion-mcp-server\"],
    \"env\": {
      \"OPENAPI_MCP_HEADERS\": \"{\\\"Authorization\\\": \\\"Bearer $token\\\"}\"
    }
  }"
  echo "✓ Notion configured"
}

setup_slack() {
  if check_already_configured "slack"; then
    echo "✓ Slack already configured — skipping"
    return
  fi
  echo "Slack: Create Bot at api.slack.com/apps"
  echo "Required scopes: channels:read, chat:write, files:write"
  read -rsp "Slack Bot Token (xoxb-...): " bot_token; echo
  read -rp  "Slack Team ID (T...): " team_id
  claude mcp add-json slack "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@modelcontextprotocol/server-slack\"],
    \"env\": {
      \"SLACK_BOT_TOKEN\": \"$bot_token\",
      \"SLACK_TEAM_ID\": \"$team_id\"
    }
  }"
  echo "✓ Slack configured"
}

setup_canva() {
  if check_already_configured "canva"; then
    echo "✓ Canva already configured — skipping"
    return
  fi
  echo "Canva: Uses OAuth — no token needed. Connecting..."
  claude mcp add-json canva "{
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@canva/cli\", \"mcp\"]
  }"
  echo "✓ Canva configured (OAuth will be requested on first use)"
}

# Main dispatch
SERVER="${1:---server all}"
case "$SERVER" in
  --server\ all|all)
    echo "=== GTM Plugin — Full MCP Setup ==="
    setup_ga4; setup_notion; setup_slack; setup_apollo; setup_hubspot; setup_ahrefs; setup_canva
    echo ""
    echo "=== Setup Complete ==="
    echo "Run /gtm:setup to verify all connections."
    ;;
  *hubspot*)   setup_hubspot ;;
  *apollo*)    setup_apollo ;;
  *ahrefs*)    setup_ahrefs ;;
  *ga4*)       setup_ga4 ;;
  *notion*)    setup_notion ;;
  *slack*)     setup_slack ;;
  *canva*)     setup_canva ;;
  *) echo "Usage: $0 [all|hubspot|apollo|ahrefs|ga4|notion|slack|canva]"; exit 1 ;;
esac
