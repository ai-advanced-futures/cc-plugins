#!/usr/bin/env bash
# GTM Plugin — MCP Server Setup
# Usage: bash setup_mcp.sh <name>   (name: all, hubspot, apollo, ahrefs, ga4, notion or canva)
#
# Path A (preferred): Docker MCP Toolkit — /plugin install docker-mcp-toolkit@docker
# Path B (this script): direct installation of each server at a pinned version
#
# Safe to run multiple times — checks if already configured before adding.

set -euo pipefail

# The pinned packages. Change a version only here, then change the README table and commands/setup.md.
HUBSPOT_PACKAGE="@hubspot/mcp-server@0.4.0"
APOLLO_PACKAGE="@thevgergroup/apollo-io-mcp@3.0.0"
NOTION_PACKAGE="@notionhq/notion-mcp-server@2.6.1"
CANVA_PACKAGE="@canva/cli@2.17.0"
ANALYTICS_PACKAGE="analytics-mcp==0.8.0"

# Escape a typed value for a JSON string. This function uses only shell builtins, so the value is in no argument list.
json_value() {
  local label="$1" value="$2" escaped="" char i
  if [[ -z "$value" ]]; then
    echo "✗ $label is empty. Nothing was added." >&2
    exit 1
  fi
  if [[ "$value" == *[[:cntrl:]]* ]]; then
    echo "✗ $label holds a control character. Nothing was added." >&2
    exit 1
  fi
  # One character at a time: the ${value//a/b} form treats a backslash differently in bash 3.2, the bash of macOS.
  for ((i = 0; i < ${#value}; i++)); do
    char="${value:i:1}"
    case "$char" in
      '\') escaped+='\\' ;;
      '"') escaped+='\"' ;;
      *) escaped+="$char" ;;
    esac
  done
  printf '%s' "$escaped"
}

# Return 0 when the server is configured. A configured server with another package gets a warning.
check_already_configured() {
  local server="$1" pin="${2:-}" line
  line="$(claude mcp list 2>/dev/null | grep "^$server:" || true)"
  [[ -n "$line" ]] || return 1
  if [[ -n "$pin" && "$line" != *"$pin"* ]]; then
    echo "! $server does not use $pin. To change it, run: claude mcp remove $server, then run this script again." >&2
  fi
  return 0
}

setup_hubspot() {
  if check_already_configured "hubspot" "$HUBSPOT_PACKAGE"; then
    echo "✓ HubSpot already configured — skipping"
    return
  fi
  echo "HubSpot: Create a Private App at app.hubspot.com/private-apps"
  echo "Required scopes (read only): crm.objects.contacts.read, crm.objects.companies.read, crm.objects.deals.read"
  read -rsp "Private App Token: " token; echo
  token="$(json_value "The token" "$token")"
  claude mcp add-json hubspot "{\"command\":\"npx\",\"args\":[\"-y\",\"$HUBSPOT_PACKAGE\"],\"env\":{\"PRIVATE_APP_ACCESS_TOKEN\":\"$token\"}}"
  echo "✓ HubSpot configured"
}

setup_apollo() {
  if check_already_configured "apollo" "$APOLLO_PACKAGE"; then
    echo "✓ Apollo.io already configured — skipping"
    return
  fi
  echo "Apollo.io: Get API key at app.apollo.io/settings/api"
  read -rsp "Apollo API Key: " key; echo
  key="$(json_value "The API key" "$key")"
  claude mcp add-json apollo "{\"command\":\"npx\",\"args\":[\"-y\",\"$APOLLO_PACKAGE\"],\"env\":{\"APOLLO_API_KEY\":\"$key\"}}"
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
  if check_already_configured "google-analytics" "$ANALYTICS_PACKAGE"; then
    echo "✓ Google Analytics 4 already configured — skipping"
    return
  fi
  echo "GA4: Requires uv, a Google Service Account JSON file and its Google Cloud project ID"
  echo "Create Service Account at console.cloud.google.com → IAM → Service Accounts"
  echo "Enable the Google Analytics Admin API and Data API in that project"
  echo "Grant role: Viewer on your GA4 property"
  read -rp "Path to Google credentials JSON: " creds
  read -rp "Google Cloud project ID: " project
  creds="$(json_value "The path" "$creds")"
  project="$(json_value "The project ID" "$project")"
  claude mcp add-json google-analytics "{\"command\":\"uvx\",\"args\":[\"--from\",\"$ANALYTICS_PACKAGE\",\"analytics-mcp\"],\"env\":{\"GOOGLE_APPLICATION_CREDENTIALS\":\"$creds\",\"GOOGLE_CLOUD_PROJECT\":\"$project\"}}"
  echo "✓ Google Analytics 4 configured"
}

setup_notion() {
  if check_already_configured "notion" "$NOTION_PACKAGE"; then
    echo "✓ Notion already configured — skipping"
    return
  fi
  echo "Notion: Create integration at notion.so/my-integrations"
  echo "Required capability: Read content (/gtm:learn)"
  echo "Grant pages access to any workspace pages you want GTM to read"
  read -rsp "Notion Integration Token: " token; echo
  token="$(json_value "The token" "$token")"
  claude mcp add-json notion "{\"command\":\"npx\",\"args\":[\"-y\",\"$NOTION_PACKAGE\"],\"env\":{\"NOTION_TOKEN\":\"$token\"}}"
  echo "✓ Notion configured"
}

setup_canva() {
  if check_already_configured "canva" "$CANVA_PACKAGE"; then
    echo "✓ Canva already configured — skipping"
    return
  fi
  echo "Canva: Uses OAuth — no token needed. Connecting..."
  claude mcp add-json canva "{\"command\":\"npx\",\"args\":[\"-y\",\"$CANVA_PACKAGE\",\"mcp\"]}"
  echo "✓ Canva configured (OAuth will be requested on first use)"
}

# Main dispatch
SERVER="${1:---server all}"
case "$SERVER" in
  --server\ all|all)
    echo "=== GTM Plugin — Full MCP Setup ==="
    setup_ga4; setup_notion; setup_apollo; setup_hubspot; setup_ahrefs; setup_canva
    echo ""
    echo "=== Setup Complete ==="
    echo "Run /gtm:setup to verify all connections."
    ;;
  *hubspot*)   setup_hubspot ;;
  *apollo*)    setup_apollo ;;
  *ahrefs*)    setup_ahrefs ;;
  *ga4*)       setup_ga4 ;;
  *notion*)    setup_notion ;;
  *canva*)     setup_canva ;;
  *slack*)     echo "This script has no Slack step. The gtm README says why, and what to do."; exit 1 ;;
  *) echo "Usage: $0 [all|hubspot|apollo|ahrefs|ga4|notion|canva]"; exit 1 ;;
esac
