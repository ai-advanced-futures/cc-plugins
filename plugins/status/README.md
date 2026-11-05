# status

A mod that shows a Nord status bar in the row below the prompt. The bar shows:

- The model.
- The context bar and the context size.
- The prompt cache pill:
  - `❄ cold`: no request is in the cache.
  - `♨ warm <time left> <hit%>`: the cache is warm. The pill shows the time until the cache ends and the part of the last request that came from the cache.
- The 7-day usage limit.
- The folder, the worktree, and the git branch.

In the desktop app, the bar is a picture in the band above the prompt, because the desktop app does not draw the row below the prompt. The picture is a row of rounded chips in one font: the model, the context as a progress chip with the percent and size inside it (for example `36%/58K`), the cache pill, and the 7-day limit as a progress chip after a `⏱` icon. It leaves out the folder, the worktree, and the git branch, and it needs no Nerd Font.

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

## Test

```bash
claude plugin validate plugins/status
claude plugin test plugins/status
```
