import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

import type { Cache, Kind, MonthCost, RateLimits, Ttl, Window } from '../types'
import {
  addSpend,
  barSvg,
  COST_PREFIX,
  hitPercent,
  isMonthCost,
  learn,
  monthOf,
  monthTotal,
  newestRateLimits,
  parts,
  segments,
  sameWindow,
  SVG_HEIGHT,
} from './bar'

// Draws the Nord status bar in the row under the prompt, above the engine's
// own hint line. Every refresh reads all the bar shows into one state value;
// the drawing reads that value alone.

const bar = atom({ plugin: 'status', key: 'bar' } as const, null)

const TTL_KEY = 'learned-ttl'
// Version 0.2.1 and older kept the highest value under 'rate-limits', and a
// session that still runs that code keeps writing it there. So this key is new.
const RATE_KEY = 'rate-limits-newest'
// The plan of the machine: what the newest decision of any session was. A new or
// resumed session uses it until its own first reply.
const PLAN_KEY = 'plan-kind'
const TICK_MS = 15_000

// week: the 7-day window this session saw at the last refresh. null until the
// first refresh, which only notes the window: it can be old, from before a reload.
// kind: what the newest main reply of this session said (no window, or some).
// machine: the plan mark in the store, as far as this session wrote or read it.
// isMarkDue: the last reply decided a kind that the store mark does not hold yet.
// cost: the record of this session, and the last one that a `set` stored.
// others: the sum of the other sessions at the last read, and the time of that read.
type Live = {
  cache: Cache
  apiModel: string | undefined
  week: Window | undefined | null
  kind?: Kind
  machine?: Kind
  isMarkDue?: boolean
  // seq: the number of the last refresh that read `usage`. cost.applied: the number of the
  // refresh whose cost total is in cost.rec; a refresh with a lower number is older.
  seq?: number
  cost?: { id: string; rec?: MonthCost; written?: MonthCost; applied?: number }
  others?: { month: string; usd: number; at: number }
}

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
  if (changed && own.seven_day) {
    // The lock can refuse the set. Then the session keeps its old window, so the
    // next refresh sets the new one again, and the bar shows the new window now.
    const isStored = await $.store.set(RATE_KEY, own).then(() => true, () => false)
    if (isStored) live.week = own.seven_day
    return own
  }
  live.week = own.seven_day
  return newestRateLimits(nowSec, own, ((await $.store.get(RATE_KEY)) ?? {}) as RateLimits)
}

// The plan of this session: a session whose newest main reply had no rate-limit
// window pays by use, so the bar shows a cost and not the 7-day chip. Before its
// first reply a session uses the plan of the machine. The rule reads the full
// list, not `toRateLimits`, which keeps only `seven_day`.
async function hasNoLimit($: EngineInterface, live: Live, list: readonly SessionRateLimit[], replied: boolean) {
  if (replied) {
    live.kind = list.length === 0 ? 'none' : 'limit'
    live.isMarkDue = live.machine !== live.kind
  }
  if (live.isMarkDue && live.kind) {
    const kind = live.kind
    // Only a stored mark counts as stored: a refused set is tried again at the
    // next refresh. A kind that a reload restored from the saved bar is not due.
    const isStored = await $.store.set(PLAN_KEY, kind).then(() => true, () => false)
    if (isStored) {
      live.machine = kind
      live.isMarkDue = false
    }
  }
  return (live.kind ?? live.machine) === 'none'
}

// The month total that the bar shows, or undefined while it is not known. The
// record of this session is in memory and in its own store key; the other keys
// are read at most 1 time in 15 s.
async function monthCost(
  $: EngineInterface,
  live: Live,
  total: number | undefined,
  now: number,
  isNoLimit: boolean,
  seq: number,
) {
  const id = await $.session.id()
  const month = monthOf(now)
  const key = COST_PREFIX + id
  let own = live.cost?.id === id ? live.cost : undefined
  if (total !== undefined) {
    if (!own) {
      // A failed load makes no record: a record that starts from nothing would
      // write over the spend that is stored. The next refresh loads it again.
      const loaded = await $.store.get(key).then(v => ({ v }), () => undefined)
      if (!loaded) return undefined
      // Another refresh can have made the record while this one loaded.
      own = live.cost?.id === id ? live.cost : { id, ...(isMonthCost(loaded.v) ? { rec: loaded.v } : {}) }
    }
    // A refresh that read `usage` before the refresh of the record carries an older total.
    // Counting it would move `seen` down, and the next total would count that spend again.
    if (own.applied === undefined || seq > own.applied) {
      own = { ...own, rec: addSpend(own.rec, total, month, isNoLimit), applied: seq }
      live.cost = own
    }
  }
  const rec = own?.rec
  if (isNoLimit && rec && rec.usd > 0 && !sameRecord(rec, own?.written)) {
    // A refused set leaves `written` as it was, so the next refresh writes again.
    const isStored = await $.store.set(key, rec).then(() => true, () => false)
    if (isStored && live.cost?.id === id) live.cost = { ...live.cost, written: rec }
  }
  if (!isNoLimit) return undefined
  if (live.others?.month !== month || now - live.others.at >= TICK_MS) await readOthers($, live, key, month, now)
  return live.others?.month === month ? live.others.usd + (rec?.month === month ? rec.usd : 0) : undefined
}

function sameRecord(a: MonthCost | undefined, b: MonthCost | undefined) {
  return a?.month === b?.month && a?.usd === b?.usd && a?.seen === b?.seen
}

// The sum of the other sessions. When a call is refused, the last sum stays.
async function readOthers($: EngineInterface, live: Live, own: string, month: string, now: number) {
  const keys = await $.store.keys().catch(() => undefined)
  if (!keys) return
  const values = await Promise.all(
    keys.filter(k => k.startsWith(COST_PREFIX) && k !== own).map(k => $.store.get(k).then(v => ({ v }), () => undefined)),
  )
  if (values.some(v => v === undefined)) return
  live.others = { month, usd: monthTotal(month, values.map(v => v?.v)), at: now }
}

// A new month starts the total again: the keys of an older month go. A key goes
// only when its get resolves and holds a record of another month.
async function dropOldMonths($: EngineInterface, now: number) {
  const month = monthOf(now)
  const keys = await $.store.keys().catch(() => [] as string[])
  await Promise.all(
    keys
      .filter(k => k.startsWith(COST_PREFIX))
      .map(async k => {
        const got = await $.store.get(k).then(v => ({ v }), () => undefined)
        if (got && isMonthCost(got.v) && got.v.month !== month) await $.store.delete(k).catch(() => undefined)
      }),
  )
}

async function refresh($: EngineInterface, live: Live, replied = false) {
  const now = await $.clock.now()
  // Refreshes can overlap (the tick and a reply). The number says which one read `usage` last.
  const seq = (live.seq = (live.seq ?? 0) + 1)
  const [usage, model, cwd] = await Promise.all([$.session.usage(), $.session.model(), $.session.cwd()])
  const top = await git($, cwd, ['rev-parse', '--show-toplevel'])
  const branch = top ? await git($, cwd, ['branch', '--show-current']) : ''
  const rateLimits = await sharedRateLimits($, live, toRateLimits(usage.rateLimits), Math.floor(now / 1000))
  const isNoLimit = await hasNoLimit($, live, usage.rateLimits, replied)
  const monthUsd = await monthCost($, live, usage.cost?.usd, now, isNoLimit, seq)
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
    ...(live.kind === undefined ? {} : { kind: live.kind }),
    ...(isNoLimit ? { noLimit: true, ...(monthUsd === undefined ? {} : { monthUsd }) } : {}),
  }))
}

async function remember($: EngineInterface, live: Live, value: Ttl) {
  if (live.cache.fixed || live.cache.learned === value) return
  // The lock can refuse the set. Then the session has not learned the value yet,
  // so the next request that teaches it sets it again, and the refresh still runs.
  const isStored = await $.store.set(TTL_KEY, value).then(() => true, () => false)
  if (isStored) live.cache.learned = value
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
      if (saved.kind !== undefined) live.kind = saved.kind
    }
    // Before its first reply this session uses the plan of the machine.
    const machine = await $.store.get(PLAN_KEY).catch(() => undefined)
    if (machine === 'none' || machine === 'limit') live.machine = machine
    await dropOldMonths($, await $.clock.now())
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
      await refresh($, live, true)
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
