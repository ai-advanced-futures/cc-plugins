# Changelog

## 0.3.0

### Added
- A session with no usage limit shows the cost of this month in the bar (`$ 12.34`), not the 7-day chip, which showed `--% -d -h` there. The rule: the newest main reply of the session reported no rate-limit window. It finds an enterprise seat, an API key, a cloud provider, and a gateway with no spend limit, and also a claude.ai Team seat. A subscription, and a gateway with a spend limit, keep the 7-day chip. In the desktop app the chip is `$12.34`.
- The month total is the sum of the spend of all sessions that load this install of the plugin in the same Claude Code configuration folder. Each session writes only its own store key, `month-cost:<session id>`, so 2 sessions never write the same key. The total starts again on the first day of each month, and the keys of an older month go at the start of a session. It is the estimate of Claude Code (`/cost`), not the bill. A session in another configuration folder, from another marketplace, or from a `--plugin-dir` copy has its own total.
- A new or resumed session uses the plan mark of the machine (the store key `plan-kind`) until its first reply, so on a machine with no usage limit the `$` chip shows at once.

### Fixed
- A store write that the lock refuses ("Lock file is already being held") no longer stops the refresh. The 7-day window and the learned cache lifetime are set again at the next refresh, and the bar still draws.

## 0.2.3

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `status@cc-plugins`. The homepage and the repository fields point at the public repository, and the README names it. Install the plugins again from the new marketplace.

## 0.2.2

- The 7-day limit shows the newest value that any session saw. Before, the bar kept the highest value, and the window with the later reset. An idle session holds its last window until that window resets, so an old window could stay on the bar of all sessions after the week changed.
- A session stores its 7-day window only when the window changes, because a change means a new response came.

## 0.2.1

- The CHANGELOG names no private repository.

## 0.2.0

- The desktop app now shows the bar. It does not draw the hint line, so there the bar is a picture in the band above the prompt: a row of rounded chips in one font. The chips are the model, the context as a progress chip with the percent and size inside it (`36%/58K`), the cache pill, and the 7-day quota as a progress chip after a `⏱` icon. The terminal keeps the text bar.
- The picture bar leaves out the folder, the worktree, and the git branch, and uses no Nerd Font glyphs.
- The mod keeps the time of the last reply in the session, so a reload of the mod no longer shows the cache as cold.

## 0.1.0

First release in this marketplace. It was the `statusbar` mod in a private repository of the author.

- A Nord status bar below the prompt: the model, the context, the 7-day limit, the folder, the worktree, and the git branch.
- A prompt cache pill: `❄ cold`, or `♨ warm` with the time left and the hit percent.
- The `ttl` option: `auto`, `5m`, or `1h`.
