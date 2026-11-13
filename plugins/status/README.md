# status

A mod that shows a Nord status bar in the row below the prompt. The bar shows:

- The model.
- The context bar and the context size.
- The prompt cache pill:
  - `❄ cold`: no request is in the cache.
  - `♨ warm <time left> <hit%>`: the cache is warm. The pill shows the time until the cache ends and the part of the last request that came from the cache.
- The 7-day usage limit. On a session with no usage limit, the bar shows the cost of this month (`$ 12.34`) in its place.
- The folder, the worktree, and the git branch.

In the desktop app, the bar is a picture in the band above the prompt, because the desktop app does not draw the row below the prompt. The picture is a row of rounded chips in one font: the model, the context as a progress chip with the percent and size inside it (for example `36%/58K`), the cache pill, and the 7-day limit as a progress chip after a `⏱` icon (or the cost of this month as a chip, `$12.34`). It leaves out the folder, the worktree, and the git branch, and it needs no Nerd Font.

The bar draws again at once when you change the model, the settings, the folder, or the worktree, after a compaction, and after each Bash command. It also draws again every 15 seconds.

## Install

At the prompt of a Claude Code session:

```text
/plugin install status --marketplace ai-advanced-futures/cc-plugins
```

Type `y` to add the marketplace, then select a scope.

From a shell:

```bash
claude plugin install status --marketplace ai-advanced-futures/cc-plugins
```

## Font

The bar uses Nerd Font glyphs for the folder, the branch, and the gauge. Set your terminal to a [Nerd Font](https://www.nerdfonts.com/). Without one, these glyphs show as empty boxes.

## Options

| Option | Values | Default | What it does |
|---|---|---|---|
| `ttl` | `auto`, `5m`, `1h` | `auto` | Sets how long the prompt cache stays warm after a request. |

With `auto`, the mod starts from the plan: 1 hour on a Claude subscription within its plan usage, else 5 minutes. Then it learns the real lifetime from the cache counts of each request. Set `5m` or `1h` to use a fixed value.

## The cost of this month

A session with no usage limit has no 7-day window, so the 7-day chip would show `--% -d -h`. The bar shows the cost of this month instead: `$ ` and the total with 2 decimals (`$ 12.34`). The total is the sum of the spend of all sessions of this month. It starts again on the first day of each month.

- **The rule.** The newest main reply of the session reported no rate-limit window. A Claude subscription (Pro, Max, Ultra) reports a window, so it keeps the 7-day chip. An enterprise seat, an API key, a cloud provider (Bedrock, Vertex), and a gateway with no spend limit report no window, so they get the `$` chip. A gateway with a spend limit reports a window, so it keeps the 7-day chip.
- **Before the first reply.** A new or resumed session has no reply yet, so it uses the plan that the newest session on the machine had. With no such session, the bar is as before. After the first reply, the session uses its own plan.
- **No total yet.** When the mod cannot read the spend of the sessions (the store refuses a read), the chip shows `$ --` until the next read works.
- **Team seat.** The docs list the rate limits for Pro, Max, and Ultra only. A claude.ai Team seat can report no window, so it gets the `$` chip. There the chip shows an estimate of the cost, not a limit. The mod cannot tell a Team seat, an enterprise seat, and an API key apart.
- **The limits of the total.**
  - It counts the sessions that load this install of the plugin in the same Claude Code configuration folder, from the time that the install has this version. A session in another configuration folder (`CLAUDE_CONFIG_DIR`), from another marketplace, or from a `--plugin-dir` copy has its own total.
  - It is the estimate of Claude Code (`/cost`), not your bill.
  - The spend that a resumed or forked session already has does not count again.

## Test

```bash
claude plugin validate plugins/status
claude plugin test plugins/status
```
