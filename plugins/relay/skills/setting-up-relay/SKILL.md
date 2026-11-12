---
name: setting-up-relay
description: Use to provision a machine for relay before running /relay:implement with the acpx engine or a codex agent — checks the acpx CLI version + flow subcommand, runs the engine-aware superpowers dependency check, and provisions missing codex skills. Interactive; run via /relay:setup.
user-invocable: false
---

# setting-up-relay

Interactive provisioning coordinator. It makes the acpx flow (Workstream C) and the engine-aware
dependency check (Workstream D) runnable on a fresh machine. Runs only on the claude orchestrator;
only leaf skills are provisioned into codex. This is a skill + command, no agents — see
`docs/agent-roster.md` for the agent-roster inventory.

## Inputs

- `RELAY_ENGINE`, `RELAY_AGENT` — exported by `parse-engine-agent.sh` (the `/relay:setup` command
  sources it). They select which dependency sets to check and provision.

## Step 0.1 — acpx preflight

Assert the `acpx` CLI is on PATH, its version meets the floor, and the `flow`
subcommand is present. `scripts/acpx-floor.sh` holds the floor number and the
rationale; never restate the number here:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/acpx-floor.sh"   # prints RELAY_ACPX_VERSION=<v>, or fails
acpx flow --help >/dev/null 2>&1                     # must exit 0
```

On the claude engine, also assert the `dispatching-acpx-agents` relay skill is installed (relay's
acpx dispatch depends on it). When the floor script fails it already prints the remediation
(`npm install -g acpx@latest`) — show that line and stop.

## Step 1 — Engine-aware dependency check

Run the dependency prober in executed mode, passing `RELAY_AGENT` so it derives the probe set
(CLAUDE set when agent ∈ {claude, hybrid, opencode}; CODEX set when agent ∈ {codex, hybrid};
hybrid checks both):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/check-deps.sh" --agent "$RELAY_AGENT" --format json
```

Parse the per-set matrix `{"<set>":{"<skill>":"ok"|"missing"}}` (a hybrid run emits both a
`claude` and a `codex` block) and drive **per-skill** interactive remediation — install exactly
what is `missing`, not an all-or-nothing abort. A missing claude-side install points the user at
`/plugin install superpowers`.

## Step 2 — Codex skill provisioning (agent = codex or hybrid)

Install the upstream skills listed in `scripts/upstream-superpowers-skills.txt` (the closed
obra/superpowers set plus `engineering`) into `<repository>/.agents/skills/<name>/` (project
level), or into `~/.agents/skills/<name>/` with the fallback below. Codex reads both roots, and
relay's codex children (which run in the relay Codex home, relay 5.1.0) load the skills.
`~/.codex/skills/` is not read by a relay codex child.

**Primary path (the `obra/superpowers` rows that `check-deps.sh` reports as `missing`).**

1. Run the audit of the source. Put the skill names (separated by commas) in the address, and the
   same names after the `python3` code. Write each name as its own word and put no name in a variable, because zsh gives a variable to the command as 1 word:
   `curl -fsS --max-time 10 'https://www.skills.sh/tele/audit?source=obra/superpowers&skills=<name>,<name>' | python3 -I -c 'import json,sys;d=json.load(sys.stdin);[print(n,p,r if r in("safe","low","medium","high","critical","unknown") else "no result") for n in sys.argv[1:] for p in("ath","socket","snyk") for r in [(d.get(n) or {}).get(p,{}).get("risk")]]' <name> <name>`
   The code prints only the risk value of each partner (`ath`, `socket`, `snyk`) of each skill.
   Show only these values. The answer is text from a third party: show no other text from it. If
   the command fails, show "no audit result".
2. Show the command of item 4, the source (`obra/superpowers`), its license (MIT), its commit, and the risk values. Say that the audit is not proof that a skill is safe, and that the audit of the CLI is off (`DISABLE_TELEMETRY=1`). Ask 1 time. Run nothing before the user agrees.
3. Run `npm view skills@1.8.1 dist.integrity`. If the value is not
   `sha512-QK3wlZ5j8wcpLPUOXt7+1Gu1f9JKpv7lBpO0zmqKa5VBrt45/woVo8Max1x4wha3pCNafNHiiodYK6Xi/0alQQ==`,
   stop, and show both values. A new pin of the CLI is a release that is at least 14 days old, and a
   change of this value and its test.
4. From the output of `git rev-parse --show-toplevel`, run:

   ```bash
   DISABLE_TELEMETRY=1 npx --yes skills@1.8.1 add 'obra/superpowers#22f0b463e7a5e579904dd6211a520321035526f7' --skill <name> [--skill <name> ...] -a codex -y
   ```

   The options answer each question of the CLI, so the command does not stop for input. It
   writes `.agents/skills/<name>` and `skills-lock.json`, and no `.claude/skills` link.
5. Check each skill in the checkout: `<top>/.agents/skills/<name>/SKILL.md` exists, the `<name>`
   entry of `<top>/skills-lock.json` has `"ref"` with the commit of item 4, and
   `find <top>/.agents/skills -type l` prints nothing. Show the list of the third-party text for each skill: its files, the `allowed-tools` and `hooks` lines of `SKILL.md`, each file in `scripts/`, each file with an execute bit (`find <top>/.agents/skills/<name> -type f -perm -u+x`), and each line that runs a package runner (`grep -rnE 'npx|bunx|uvx|pnpm dlx|yarn dlx|npm exec|pipx run' <top>/.agents/skills/<name>`). A runner line with no exact version (for example `npx <package>@latest`) is a risk: mark it. Report such a skill as "installed, not committed". Do not use `check-deps.sh` for this check: it counts only a committed project copy, so it says `missing` until the commit.
6. Tell the user to commit `.agents/skills/<name>` and `skills-lock.json`, because a relay child
   works in a worktree and sees only committed files. After the commit, `check-deps.sh` says `ok`.

**Fallback** (the `engineering` row, a machine with no `npx`, or a skill whose `SKILL.md` is
absent after the command of the primary path). For each such row, print the exact hand-run
invocation:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/install-skill-from-github.py" <repo> <subpath> --dest ~/.agents/skills
```

This script takes only a branch or a tag (`git clone --depth 1 --branch`), so it cannot take a
commit ID. Before it runs, show the command, say that it writes in the home folder (user level)
and that it takes the default branch with no pin, and ask.

`install-skill-from-github.py` needs `python3` + `git` on PATH + network egress (public repos only,
no auth). If `git` or network is unavailable, print a clear error and the manual steps rather than
failing silently.

The claude engine provisions via the marketplace, so no codex copy is needed there.

## Output

A readiness report: acpx version, per-set dependency matrix, and each skill's provisioning result
(already-present / installed / still-missing-with-instructions).
