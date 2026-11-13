import type { TurnUsage } from 'claude-code'

import type { Bar, Cache, MonthCost, RateLimits, Ttl, Window } from '../types'

// The status bar as colored runs: model, context, 7-day limit (or, with no usage
// limit, the cost of this month), folder, branch, with the prompt cache pill in
// the context segment.

export type Run = { text: string; color?: string; bg?: string }
type Colored = { text: string; color: string }
type Pill = Colored & { bg: string }

// Nord palette
export const NORD = {
  n0: '#2E3440', // bar label on a filled cell, warm cache text
  n3: '#4C566A', // dim, separators, empty cells
  n7: '#8FBCBB', // frost teal (<20%)
  n6: '#ECEFF4', // snow white (cold cache text)
  n8: '#88C0D0', // frost cyan (sonnet)
  n9: '#81A1C1', // frost blue (opus, folder)
  n10: '#5E81AC', // frost deep blue (<20% on a 1M window, cold cache background)
  n11: '#BF616A', // aurora red (>=80%, warm cache background)
  n12: '#D08770', // aurora orange (>=60%)
  n13: '#EBCB8B', // aurora yellow (>=40%, haiku)
  n14: '#A3BE8C', // aurora green (>=20%, branch)
  n15: '#B48EAD', // aurora purple (worktree)
} as const

const GH_ICON = ''
const BRANCH_ICON = ''
const FOLDER = ''
const GAUGE = '\u{f04c5}' // 7d usage

// ---- prompt cache -------------------------------------------------------

export const TTL_MS: Record<Ttl, number> = { '5m': 5 * 60_000, '1h': 60 * 60_000 }
// A gap longer than this and shorter than one hour tells the two lifetimes apart.
const PROBE_MS = TTL_MS['5m'] + 30_000

export function hitPercent(u: TurnUsage): number | undefined {
  const all = u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens
  return all > 0 ? Math.round((u.cache_read_input_tokens / all) * 100) : undefined
}

// What one request after a gap says about the lifetime, or undefined. Other
// sessions can keep the shared system prompt warm, so a small read is no proof
// of the 1h lifetime: the conversation itself must come from the cache.
export function learn(gapMs: number, u: TurnUsage): Ttl | undefined {
  if (gapMs <= PROBE_MS || gapMs >= TTL_MS['1h']) return undefined
  const hit = hitPercent(u)
  if (hit === undefined) return undefined
  if (hit >= 50) return '1h'
  if (u.cache_creation_input_tokens > 0) return '5m'
  return undefined
}

export function formatSpan(ms: number): string {
  const min = Math.max(0, Math.floor(ms / 60_000))
  if (min < 1) return '<1m'
  if (min < 60) return `${min}m`
  return min % 60 ? `${Math.floor(min / 60)}h ${min % 60}m` : `${min / 60}h`
}

// A pill: white on frost deep blue when cold, dark on aurora red when warm.
const cold = (text: string): Pill => ({ text: ` ${text} `, color: NORD.n6, bg: NORD.n10 })
const warm = (text: string): Pill => ({ text: ` ${text} `, color: NORD.n0, bg: NORD.n11 })

export function cacheRun(cache: Cache, now: number): Pill {
  if (cache.lastAt === undefined) return cold('❄ cold')
  const ttl = cache.fixed ?? cache.learned ?? (cache.plan ? '1h' : '5m')
  const idle = now - cache.lastAt
  const left = TTL_MS[ttl] - idle
  if (left <= 0) return cold(`❄ cold ${formatSpan(idle)}`)
  const hit = cache.hit === undefined ? '' : ` ${cache.hit}%`
  return warm(`♨ warm ${formatSpan(left)}${hit}`)
}

// ---- rate limits ----------------------------------------------------------

// Each session gets rate limits only from its own API responses, and keeps the
// last ones while it is idle, until their reset. So an idle session can hold an
// old window. A session stores its window only when the window changes, which
// means a new response came. Every session shows the stored window, the newest
// one seen, and its own window when nothing stored is still before its reset.
export function newestRateLimits(nowSec: number, own: RateLimits, stored: RateLimits): RateLimits {
  const live = [stored.seven_day, own.seven_day].find(w => w !== undefined && w.resetsAt > nowSec)
  return live ? { seven_day: live } : {}
}

export function sameWindow(a: Window | undefined, b: Window | undefined): boolean {
  return a?.used === b?.used && a?.resetsAt === b?.resetsAt
}

// ---- month cost -----------------------------------------------------------------

// Each session keeps its own spend of the month under its own store key. Nothing
// reads, adds to and writes a shared number, so 2 sessions never write 1 key, and
// the total is the sum of the keys.
export const COST_PREFIX = 'month-cost:'

// The local calendar month of a time, as YYYY-MM.
export function monthOf(ms: number): string {
  const d = new Date(ms)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export function isMonthCost(value: unknown): value is MonthCost {
  if (typeof value !== 'object' || value === null) return false
  const r = value as Record<string, unknown>
  return typeof r.month === 'string' && Number.isFinite(r.usd) && Number.isFinite(r.seen)
}

// The record of a session after a refresh with `total`, the cost total of the
// session. The first sight of a session, and a new month, start at 0: the cost
// that a resume or a fork restores is not new spend. A total below `seen` (after
// /clear) moves `seen` down and adds nothing. `counts` is false on a session that
// pays no use (a subscription): it follows `seen` and adds nothing.
export function addSpend(rec: MonthCost | undefined, total: number, month: string, counts: boolean): MonthCost {
  const from: MonthCost = !rec ? { month, usd: 0, seen: total } : rec.month === month ? rec : { month, usd: 0, seen: rec.seen }
  return { month, usd: from.usd + (counts ? Math.max(0, total - from.seen) : 0), seen: total }
}

// The spend of the month in a list of values from the store. A value of another
// shape, or of another month, adds nothing.
export function monthTotal(month: string, records: readonly unknown[]): number {
  return records.reduce<number>((sum, r) => (isMonthCost(r) && r.month === month ? sum + r.usd : sum), 0)
}

export function costRun(usd: number | undefined): Colored {
  return usd === undefined ? { text: '--', color: NORD.n3 } : { text: usd.toFixed(2), color: NORD.n14 }
}

// ---- the line ---------------------------------------------------------------

function tier(pct: number, low: string): string {
  if (pct >= 80) return NORD.n11
  if (pct >= 60) return NORD.n12
  if (pct >= 40) return NORD.n13
  if (pct >= 20) return NORD.n14
  return low
}

// Normalize: try a claude-{family}-{maj}-{min} id; else "Family X.Y" from a name.
export function modelName(raw: string, contextWindow: number): string {
  const id = /claude-(sonnet|opus|haiku)-(\d+)-(\d+)/i.exec(raw)
  const named = /(sonnet|opus|haiku)\s*(\d+\.\d+)/i.exec(raw)
  const cap = (s: string) => s[0]!.toUpperCase() + s.slice(1).toLowerCase()
  const base = id
    ? `${cap(id[1]!)} ${id[2]}.${id[3]}`
    : named
      ? `${cap(named[1]!)} ${named[2]}`
      : raw
  const is1m = /1m/i.test(raw) || contextWindow >= 1_000_000
  return base + (is1m ? ' [1M]' : '')
}

function modelColor(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('haiku')) return NORD.n13
  if (n.includes('opus')) return NORD.n9
  return NORD.n8
}

// Context usage %.
//  - 200K window: usable = 80% of total -> multiply by 1.25 (80% reads as 100%).
//  - 1M window: rescale so 400K tokens = 100%.
export function contextPercent(usedPct: number, window: number): number {
  const raw = window >= 1_000_000 ? ((usedPct / 100) * window) / 400_000 * 100 : usedPct * 1.25
  return Math.min(raw, 100)
}

const rep = (s: string, n: number) => (n > 0 ? s.repeat(n) : '')

// A bar of `width` cells with the percentage centered. The label is the bar
// color on the dark background on the empty side, and dark on the bar color
// where the bar fills it.
export function renderBar(pct: number, width: number, color: string): Run[] {
  const f = Math.min(Math.max(Math.floor((pct / 100) * width), 0), width)
  const lbl = `${Math.floor(pct)}%`
  const ls = Math.floor((width - lbl.length) / 2)
  const le = ls + lbl.length
  const lfill = Math.min(f, ls)
  const rfill = Math.min(Math.max(0, f - le), width - le)
  const runs: Run[] = [
    { text: rep('█', lfill), color },
    { text: rep('░', ls - lfill), color: NORD.n3 },
  ]
  for (let p = ls; p < le; p++) {
    const ch = lbl[p - ls]!
    runs.push(p < f ? { text: ch, color: NORD.n0, bg: color } : { text: ch, color, bg: NORD.n0 })
  }
  runs.push({ text: rep('█', rfill), color }, { text: rep('░', width - le - rfill), color: NORD.n3 })
  return runs.filter(r => r.text !== '')
}

function sevenDayRun(w: Window | undefined, nowSec: number): Colored {
  if (!w) return { text: '--% -d -h', color: NORD.n3 }
  const h = Math.floor(Math.max(0, w.resetsAt - nowSec) / 3600)
  return { text: `${Math.floor(w.used)}% ${Math.floor(h / 24)}d ${h % 24}h`, color: tier(w.used, NORD.n7) }
}

export function compactCwd(cwd: string): string {
  const all = cwd.split('/')
  return all.length <= 2 ? cwd : all.slice(-2).join('/')
}

const SEP: Run[] = [{ text: ' ' }, { text: '│', color: NORD.n3 }, { text: ' ' }]

// What both bars show, worked out once: the terminal's text bar and the
// desktop's picture bar draw from it.
export function parts(bar: Bar) {
  const name = modelName(bar.model, bar.contextWindow)
  const pct = contextPercent(bar.contextPercent, bar.contextWindow)
  const tokens = bar.contextTokens ?? (bar.contextPercent / 100) * bar.contextWindow
  return {
    model: { text: name, color: modelColor(name) },
    pct,
    color: tier(pct, bar.contextWindow >= 1_000_000 ? NORD.n10 : NORD.n7),
    size: `${Math.round(tokens / 1000)}K`,
    cache: cacheRun(bar.cache, bar.now),
    quota: sevenDayRun(bar.rateLimits.seven_day, Math.floor(bar.now / 1000)),
    quotaPct: bar.rateLimits.seven_day?.used ?? 0,
    // On a session with no usage limit this chip takes the place of the 7-day chip.
    cost: bar.noLimit ? costRun(bar.monthUsd) : undefined,
  }
}

export function segments(bar: Bar): Run[] {
  const p = parts(bar)
  const runs: Run[] = [
    p.model,
    ...SEP,
    ...renderBar(p.pct, 20, p.color),
    { text: ' ' },
    { text: p.size, color: p.color },
    // The prompt cache is part of the context segment.
    { text: ' ' },
    p.cache,
    ...SEP,
    ...(p.cost ? [{ text: '$ ', color: NORD.n3 }, p.cost] : [{ text: `${GAUGE} `, color: NORD.n3 }, p.quota]),
    ...SEP,
    { text: `${FOLDER} ${compactCwd(bar.cwd)}`, color: NORD.n9 },
  ]
  if (bar.worktree) {
    runs.push(...SEP, { text: `${GH_ICON} ${bar.worktree}`, color: NORD.n15 })
    if (bar.branch) {
      runs.push({ text: ' ', color: NORD.n15 }, { text: BRANCH_ICON, color: NORD.n3 }, { text: ' ' }, { text: bar.branch, color: NORD.n14 })
    }
  }
  return runs
}

// The whole bar as one picture: a row of chips drawn the same way, a rounded
// track, a filled part, and a centered light label with a dark outline.
const FONT = `font-family="-apple-system, system-ui, sans-serif" font-size="13" font-weight="600"`
const CH = 7.8 // estimated width of one character at this size, to size each chip
const OUTLINE = `stroke="${NORD.n0}" stroke-width="3" paint-order="stroke" stroke-linejoin="round"`
export const SVG_HEIGHT = 26
const CHIP_H = 20
const PAD = 24 // room around a label inside its chip
const GAP = 8 // room between chips
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
const widthOf = (s: string) => [...s].length * CH

type Chip = { label: string; fill: string; pct?: number; width?: number }

export function barSvg(p: ReturnType<typeof parts>): string {
  const mid = SVG_HEIGHT / 2
  const y = (SVG_HEIGHT - CHIP_H) / 2
  const r = CHIP_H / 2
  const out: string[] = []
  let x = 0
  // A chip with no pct is filled whole; with one, the fill is that part of the track.
  const chip = ({ label, fill, pct = 100, width = widthOf(label) + PAD }: Chip) => {
    const f = Math.round((Math.min(Math.max(pct, 0), 100) / 100) * width)
    out.push(`<rect x="${x}" y="${y}" width="${width}" height="${CHIP_H}" rx="${r}" fill="${NORD.n3}"/>`)
    if (f > 0) out.push(`<rect x="${x}" y="${y}" width="${Math.max(f, CHIP_H)}" height="${CHIP_H}" rx="${r}" fill="${fill}"/>`)
    out.push(
      `<text x="${x + width / 2}" y="${mid}" text-anchor="middle" dominant-baseline="central" ${FONT} ` +
        `fill="${NORD.n6}" ${OUTLINE}>${esc(label)}</text>`,
    )
    x += width + GAP
  }

  chip({ label: p.model.text, fill: p.model.color })
  chip({ label: `${Math.floor(p.pct)}%/${p.size}`, fill: p.color, pct: p.pct, width: 165 })
  chip({ label: p.cache.text.trim(), fill: p.cache.bg })
  if (p.cost) chip({ label: `$${p.cost.text}`, fill: p.cost.color })
  else chip({ label: `⏱ ${p.quota.text}`, fill: p.quota.color, pct: p.quotaPct, width: 130 })
  const width = Math.ceil(x - GAP)
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${SVG_HEIGHT}" viewBox="0 0 ${width} ${SVG_HEIGHT}">${out.join('')}</svg>`
}
