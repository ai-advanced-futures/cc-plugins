---
name: setting-up-engines
description: Use to configure and verify the codex and opencode engines for acpx dispatch from claude — binary/version preflight, per-provider auth checks, live pinned-model probes, and a served-model audit against each engine's own session records. Interactive assistant; run via /relay:engines.
user-invocable: false
---

# setting-up-engines

Interactive assistant that walks the user through making the **codex** and **opencode**
engines dispatchable from claude via acpx, then PROVES it with live probes. Complements
`setting-up-relay` (which provisions relay's own skills/deps); this skill owns the two
external engines end to end: install → auth → probe → audit.

Run every step, report each result as you go, and finish with the readiness table
(Step 5). When a step fails, show the remediation command and — where the fix is
interactive (logins, browser auth) — ask the user to run it, then re-run the failed
probe before moving on. Never mark an engine ready on config inspection alone; only a
live served-model audit counts.

## Step 0 — acpx preflight

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/acpx-floor.sh"   # prints RELAY_ACPX_VERSION=<v>, or fails
```

`scripts/acpx-floor.sh` is the only place that states the floor. It prints the
remediation on failure, so this step never repeats the number.

### Upgrading acpx

- Never upgrade acpx while a relay run is in progress, because session owners from two
  versions do not cooperate. acpx says so in its 0.17.0, 0.18.0 and 0.19.0 upgrade notes.
- After an upgrade, before the first dispatch, list and close every open relay session:

  ```bash
  acpx claude sessions list --local
  acpx --cwd <dir> claude sessions close <name>   # for each open record, using that record's own `--cwd`
  ```

  The list is unfiltered on purpose: an operator cannot enumerate every directory relay
  has run in, and the unfiltered list names each record's own directory. Close every open
  record the list shows, not only ones matching a `relay-` prefix. relay's sessions carry
  two name shapes — the verify loop's `relay-verify-<kind>-r<N>` and the drivers'
  `<run id>-<role slug>` — and the second has no prefix to filter on. Or wait out the
  owner lease.
- Records made before 0.17.0 hold no watch history, so a watch of one never ends by
  itself. relay's watch reader bounds itself, so this is a wasted slice, not a hang.
  Close them.
- Once a month, `acpx claude sessions prune --older-than 30` keeps the store small.

## Step 1 — resolve the models to verify

Probe the models relay will actually dispatch, not hardcoded ids. Read them from the
active bindings:

```bash
yq '.roles[].modalities.codex.model'    "${CLAUDE_PLUGIN_ROOT}/bindings/presets.yaml" | sort -u
yq '.roles[].modalities.opencode.model' "${CLAUDE_PLUGIN_ROOT}/bindings/presets.yaml" | sort -u
```

## Step 2 — codex: auth + live probe

Relay runs codex in its own Codex home, `$RELAY_CODEX_HOME` (default
`~/.relay/codex-home`). Every block below gets that home from
`relay_codex_home_resolve`, the same resolver the dispatcher runs. So an override is
probed too, and the resolver's refusals apply here as they do to a dispatch: the
desktop home `~/.codex` (in any spelling), a relative path, a `..` segment, and a set
`CODEX_SQLITE_HOME`. The resolver also expands a leading `~` and makes the directory
(mode 700), which codex needs: codex exits with an error when `CODEX_HOME` does not
exist. When it refuses, the block stops before codex runs. Show its message, and mark
codex NOT READY in Step 5. Each block runs in a new shell, so each one resolves again.

Binary and auth state:

```bash
. "${CLAUDE_PLUGIN_ROOT}/scripts/codex-home.sh"
RC_HOME="$(relay_codex_home_resolve)" || exit 1
CODEX_HOME="$RC_HOME" codex login status || true
```

`|| true` is on purpose: "not signed in" is a state that the Step 5 report records, not
an error that stops the setup. A refused home is not hidden by it, because the resolve
line stops the block first.

Live probe (mirrors relay's real one-shot dispatch shape — plain model id, `mode` and
`reasoning_effort` set with `exec --config-option`, acpx >= 0.14.0):

```bash
. "${CLAUDE_PLUGIN_ROOT}/scripts/codex-home.sh"
RC_HOME="$(relay_codex_home_resolve)" || exit 1
CODEX_HOME="$RC_HOME" acpx --cwd /tmp --model "<codex model from Step 1>" --approve-all --timeout 180 \
  codex exec --config-option mode=agent-full-access \
  --config-option reasoning_effort=low "Reply with exactly: OK"
```

Audit what actually served — codex records model AND effort per turn in its rollout:

```bash
. "${CLAUDE_PLUGIN_ROOT}/scripts/codex-home.sh"
RC_HOME="$(relay_codex_home_resolve)" || exit 1
F=$(ls -t "$RC_HOME"/sessions/*/*/*/rollout-*.jsonl | head -1)
grep -o '"model": "[^"]*"' "$F" | head -1
grep -o '"effort": "[^"]*"' "$F" | head -1
```

Both must match the probe's requested model and effort. A rejected `--config-option`
makes acpx exit non-zero before the prompt runs; `effort` still at its default with a
zero exit means the option never reached the adapter.

Remediation: the sign-in block under "Codex state" below (interactive), or an API key
in the environment; model not advertised → check the plan tier in
`$RC_HOME/models_cache.json` (`supported_in_api` flags).

## Step 3 — opencode: auth + live probe

Provider credentials (opencode routes a model to a provider by the model-id **prefix**,
e.g. `opencode-go/kimi-k2.6` can only bill to the `opencode-go` provider):

```bash
jq -r 'keys[]' ~/.local/share/opencode/auth.json   # must list every provider prefix from Step 1
opencode models | grep -F "<opencode model from Step 1>"
```

Live probe (mirrors relay's opencode-session-driver flow: ensure → set model → prompt
→ close; the model binds at the session's first prompt — a later `set model` on a live
session reports success but does not switch the serving model, so always probe with a
fresh session):

```bash
S=relay-engine-probe
acpx --cwd /tmp opencode sessions ensure --name "$S"
acpx --cwd /tmp opencode set model "<opencode model from Step 1>" -s "$S"
acpx --cwd /tmp --timeout 180 opencode prompt -s "$S" "Reply with exactly: OK"
acpx --cwd /tmp opencode sessions close "$S"
```

Audit what actually served — opencode records provider + model per message in its
sqlite store:

```bash
sqlite3 ~/.local/share/opencode/opencode.db \
  "SELECT json_extract(data,'\$.providerID'), json_extract(data,'\$.modelID')
   FROM message WHERE json_extract(data,'\$.role')='assistant'
   ORDER BY json_extract(data,'\$.time.created') DESC LIMIT 1;"
```

The row must equal the pinned `provider|model` exactly.

Remediation by error:

| Error | Fix |
|---|---|
| `Invalid API key` | Re-connect the provider: `opencode auth login` (interactive), pick the failing provider — a key minted before a subscription activates is invalid |
| `Insufficient balance` | Model went to a pay-per-token provider (e.g. `opencode/...` Zen) instead of the subscription provider — fix the model-id prefix, or top up |
| `Cannot apply --model ... did not advertise model support` | acpx too old — Step 0 |
| `effort not found` on `set effort` | Expected for open-weight models: they define no acpx effort values; relay's driver soft-degrades and the session runs at the model's default reasoning |

## Step 4 — dry-run relay's own dispatch (optional but recommended)

Confirm relay resolves the same binding end to end without spending tokens:

```bash
ACPX_ROLE_SLUG=code-reviewer ACPX_BINDING_PRESET=code-reviewer \
ACPX_INPUTS_JSON='{}' ACPX_RUN_ID=engine-setup-dryrun ACPX_DRY_RUN=1 \
bash "${CLAUDE_PLUGIN_ROOT}/skills/dispatching-acpx-agents/acpx-dispatch.sh"
```

## Codex state

Relay keeps its Codex sessions away from the Codex desktop app.

- **Interactive Codex and the desktop app:** no change. They use `~/.codex`.
- **Relay automation:** every relay codex child uses `$RELAY_CODEX_HOME` (default
  `~/.relay/codex-home`). Named sessions resume in that home. Relay refuses to use
  `~/.codex` as this home.
- **One-time sign-in:** sign in in the relay home, or put an API key in the environment.
  Do not copy `auth.json`. The resolver makes the directory and refuses a home that a
  dispatch would refuse, so the sign-in never writes into `~/.codex`.

  ```bash
  . "${CLAUDE_PLUGIN_ROOT}/scripts/codex-home.sh"
  RC_HOME="$(relay_codex_home_resolve)" || exit 1
  CODEX_HOME="$RC_HOME" codex login
  ```
- **Skills:** relay's codex children run in this home, so they do not read
  `~/.codex/skills`. `/relay:setup` installs codex skills into `~/.agents/skills`, which
  Codex reads for every Codex home, the desktop one too.
- **Configuration:** if you need one, write a small `config.toml` in the relay home. Do not
  copy `~/.codex/config.toml`: an MCP server entry can set `CODEX_HOME` back to the desktop
  home. Do not set `sqlite_home`, and do not set `CODEX_SQLITE_HOME` for relay runs. Relay
  refuses both.
- **Disposable runs:** `codex exec --ephemeral` is for your own direct calls. Relay's routes
  go through acpx, which has no ephemeral option.
- **After the upgrade:** sessions already in `~/.codex` stay there. Relay does not touch
  them. An acpx session whose queue owner started before the upgrade keeps the old home
  until the owner stops (TTL 300 s) or you close the session.

## Step 5 — readiness report

Emit one table: engine · binary version · auth state · probed model · served
provider/model (from the engine's own records) · verdict. An engine is READY only when
the audit row matches the pinned model; everything else is NOT READY with its
remediation from above.
