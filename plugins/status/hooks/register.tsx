import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

import type { Cache, RateLimits, Ttl, Window } from '../types'
import { barSvg, hitPercent, learn, newestRateLimits, parts, segments, sameWindow, SVG_HEIGHT } from './bar'

// Draws the Nord status bar in the row under the prompt, above the engine's
// own hint line. Every refresh reads all the bar shows into one state value;
// the drawing reads that value alone.

const bar = atom({ plugin: 'status', key: 'bar' } as const, null)

const TTL_KEY = 'learned-ttl'
// Version 0.2.1 and older kept the highest value under 'rate-limits', and a
// session that still runs that code keeps writing it there. So this key is new.
const RATE_KEY = 'rate-limits-newest'
const TICK_MS = 15_000

// week: the 7-day window this session saw at the last refresh. null until the
// first refresh, which only notes the window: it can be old, from before a reload.
type Live = { cache: Cache; apiModel: string | undefined; week: Window | undefined | null }

function toRateLimits(list: readonly SessionRateLimit[]): RateLimits {
  const out: RateLimits = {}
  for (const r of list) {
    if (r.kind === 'seven_day' && r.resetsAt) {
      out.seven_day = { used: r.percentUsed, resetsAt: Math.floor(Date.parse(r.resetsAt) / 1000) }
    }
  }
  return out
}

// A subscription reports its plan limits; at 100% the session uses usage credits.
function onPlan(list: readonly SessionRateLimit[]): boolean {
  return list.length > 0 && list.every(r => r.percentUsed < 100)
}

async function git($: EngineInterface, cwd: string, args: string[]): Promise<string> {
  const run = await $.process.run(['git', ...args], { cwd }).catch(() => undefined)
  return run && run.exitCode === 0 ? run.stdout.trim() : ''
}

async function sharedRateLimits($: EngineInterface, live: Live, own: RateLimits, nowSec: number) {
  const changed = live.week !== null && !sameWindow(live.week, own.seven_day)
  live.week = own.seven_day
  if (changed && own.seven_day) {
    await $.store.set(RATE_KEY, own)
    return own
  }
  return newestRateLimits(nowSec, own, ((await $.store.get(RATE_KEY)) ?? {}) as RateLimits)
}

async function refresh($: EngineInterface, live: Live) {
  const now = await $.clock.now()
  const [usage, model, cwd] = await Promise.all([$.session.usage(), $.session.model(), $.session.cwd()])
  const top = await git($, cwd, ['rev-parse', '--show-toplevel'])
  const branch = top ? await git($, cwd, ['branch', '--show-current']) : ''
  const rateLimits = await sharedRateLimits($, live, toRateLimits(usage.rateLimits), Math.floor(now / 1000))
  await update($, bar, () => ({
    now,
    // The API's model id names the version; the session's name says [1m].
    model: live.apiModel ? live.apiModel + (/1m/i.test(model) ? '[1m]' : '') : model,
    ...(live.apiModel === undefined ? {} : { apiModel: live.apiModel }),
    contextWindow: usage.context.window,
    contextPercent: usage.context.percent ?? 0,
    ...(usage.context.tokens === undefined ? {} : { contextTokens: usage.context.tokens }),
    rateLimits,
    cwd,
    worktree: top ? top.split('/').at(-1) ?? '' : '',
    branch,
    cache: { ...live.cache, plan: onPlan(usage.rateLimits) },
  }))
}

async function remember($: EngineInterface, live: Live, value: Ttl) {
  if (live.cache.fixed || live.cache.learned === value) return
  live.cache.learned = value
  await $.store.set(TTL_KEY, value)
}

export const register: Register = (on, options) => {
  const fixed = options.ttl === '5m' || options.ttl === '1h' ? options.ttl : undefined
  const live: Live = { cache: fixed ? { fixed } : {}, apiModel: undefined, week: null }

  on('session.start', async ($, e, next) => {
    const stored = await $.store.get(TTL_KEY)
    if (stored === '5m' || stored === '1h') live.cache.learned = stored
    // A reload of the mod starts its variables over; the session kept the last
    // bar, so the cache stays warm across the reload.
    const saved = await read($, bar)
    if (saved) {
      if (saved.cache.lastAt !== undefined) live.cache.lastAt = saved.cache.lastAt
      if (saved.cache.hit !== undefined) live.cache.hit = saved.cache.hit
      live.apiModel = saved.apiModel
    }
    $.clock.every(TICK_MS, () => refresh($, live))
    await refresh($, live)
    return next(e)
  })

  // Each main request: learn the lifetime from the gap, then mark the cache warm.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId !== undefined) return yield* next(e)
    const startedAt = await $.clock.now()
    const result = yield* next(e)
    if (result.usage) {
      const { lastAt } = live.cache
      const value = lastAt === undefined ? undefined : learn(startedAt - lastAt, result.usage)
      if (value) await remember($, live, value)
      live.cache.lastAt = await $.clock.now()
      live.cache.hit = hitPercent(result.usage)
      live.apiModel = result.usage.model
      await refresh($, live)
    }
    return result
  })

  // A resumed session: start from the time of its last reply, unless Claude
  // Code, which knows the real lifetime, says the cache likely expired.
  on('classic.SessionStart', async ($, e, next) => {
    if (e.prompt_cache_likely_expired) {
      delete live.cache.lastAt
      delete live.cache.hit
    } else if (e.seconds_since_last_response !== undefined) {
      live.cache.lastAt = (await $.clock.now()) - e.seconds_since_last_response * 1000
      delete live.cache.hit
    }
    await refresh($, live)
    return next(e)
  }).catch(($, e, next) => next(e))

  // Claude Code states the lifetime and the new model id here; the new model
  // starts with no cache. The session's own name can be an alias ("opus"),
  // so the bar takes the id from the event, not from the next request.
  on('classic.PostModelSwitch', async ($, e, next) => {
    await remember($, live, e.cache_ttl)
    delete live.cache.lastAt
    delete live.cache.hit
    live.apiModel = e.to_model
    await refresh($, live)
    return next(e)
  }).catch(($, e, next) => next(e))

  // Each change that alters what the bar shows redraws it at once, not at the
  // next tick: settings, the folder, a worktree, a compaction.
  on('classic.ConfigChange', async ($, e, next) => {
    await refresh($, live)
    return next(e)
  }).catch(($, e, next) => next(e))
  on('classic.CwdChanged', async ($, e, next) => {
    await refresh($, live)
    return next(e)
  }).catch(($, e, next) => next(e))
  on('classic.WorktreeCreate', async ($, e, next) => {
    const result = await next(e)
    await refresh($, live)
    return result
  }).catch(($, e, next) => next(e))
  on('classic.WorktreeRemove', async ($, e, next) => {
    const result = await next(e)
    await refresh($, live)
    return result
  }).catch(($, e, next) => next(e))
  on('classic.PostCompact', async ($, e, next) => {
    await refresh($, live)
    return next(e)
  }).catch(($, e, next) => next(e))

  // A Bash command can change the branch (git checkout, git switch).
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const result = await next(e)
    await refresh($, live)
    return result
  }).catch(($, e, next) => next(e))

  on('session.end', async ($, e, next) => {
    if (e.reason === 'clear') {
      delete live.cache.lastAt
      delete live.cache.hit
    }
    return next(e)
  })

  on('ui.render', { component: 'PromptHint' }, async ($, e, next) => {
    const engine = await next(e)
    const value = await read($, bar)
    if (!value) return engine
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Text>
          {segments(value).map(r => (
            <Text color={r.color} backgroundColor={r.bg}>
              {r.text}
            </Text>
          ))}
        </Text>
        {engine}
      </Box>
    )
  })

  // The desktop app does not draw the hint line, so there the bar is a picture
  // in the band above the prompt. The terminal keeps the text bar on the hint line.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.surface === 'terminal' || e.props.hasSurvey) return next(e)
    const { Box, Svg } = $.ui.resolve(e)
    const value = await read($, bar)
    if (!value) return next(e)
    const p = parts(value)
    return (
      <Box>
        <Svg source={barSvg(p)} alt={`${p.model.text}, context ${Math.floor(p.pct)}% ${p.size}, ${p.cache.text.trim()}`} height={SVG_HEIGHT} />
      </Box>
    )
  })
}
