import type { Chunk, Group, Orphan, Pr, Review, Row, SavedChunk, Thread } from '../types'
import { commentRange, overlap } from './diff'

// The chunk ids of the rows drawn, in the drawn order: the order `j` and `k`
// walk. A heading is never a cursor stop. `rows` holds the one grouping rule,
// so the drawn order and the cursor order can never disagree.
export function orderOf(rowList: readonly Row[]): string[] {
  return rowList.flatMap(row => (row.kind === 'chunk' ? [row.id] : []))
}

export function chunkOrder(groups: readonly Group[], chunks: readonly Chunk[]): string[] {
  return orderOf(rows(groups, chunks))
}

// The rows drawn, heading rows included. A group whose chunks all left the
// diff draws nothing, so a reload never leaves an empty heading behind.
export function rows(groups: readonly Group[], chunks: readonly Chunk[]): Row[] {
  const known = new Set(chunks.map(c => c.id))
  const seen = new Set<string>()
  const out: Row[] = []
  let index = 0
  groups.forEach((group, g) => {
    const ids: string[] = []
    for (const id of group.chunkIds) {
      if (!known.has(id) || seen.has(id)) continue
      seen.add(id)
      ids.push(id)
    }
    if (ids.length === 0) return
    out.push({ kind: 'heading', key: `group:${g}`, label: group.label })
    for (const id of ids) {
      index += 1
      out.push({ kind: 'chunk', key: `chunk:${id}`, id, index })
    }
  })
  return out
}

// `j` (step 1) and `k` (step -1). The list clamps at both ends: a review list
// that wraps moves the reviewer away from where they were reading.
// [inferred: the spec names no wrap for j and k.]
export function moveCursor(order: readonly string[], cursor: string | null, step: number): string | null {
  if (order.length === 0) return null
  const at = cursor ? order.indexOf(cursor) : -1
  if (at < 0) return order[step > 0 ? 0 : order.length - 1] ?? null
  return order[Math.min(order.length - 1, Math.max(0, at + step))] ?? null
}

// 4.4 items 2 and 3, which `u` uses too: the next chunk below that is not
// accepted, else the first from the top. Null when every chunk is accepted.
export function nextOpen(order: readonly string[], accepted: readonly string[], cursor: string | null): string | null {
  const done = new Set(accepted)
  const at = cursor ? order.indexOf(cursor) : -1
  return order.slice(at + 1).find(id => !done.has(id)) ?? order.find(id => !done.has(id)) ?? null
}

export function isAllAccepted(order: readonly string[], accepted: readonly string[]): boolean {
  const done = new Set(accepted)
  return order.length > 0 && order.every(id => done.has(id))
}

// `a` on the cursor chunk: 4.4 items 1 to 5 in one step.
export function accept(
  order: readonly string[],
  accepted: readonly string[],
  id: string,
): { accepted: string[]; cursor: string } {
  if (accepted.includes(id)) return { accepted: accepted.filter(x => x !== id), cursor: id }
  const next = [...accepted, id]
  return { accepted: next, cursor: nextOpen(order, next, id) ?? id }
}

export const MAX_LINES = 6000
export const MAX_CHUNKS = 150

// The model wraps JSON in a fence more often than not.
export function stripFence(text: string): string {
  const m = /```(?:json)?\s*([\s\S]*?)```/.exec(text)
  return (m?.[1] ?? text).trim()
}

export function fileOrder(chunks: readonly Chunk[]): Group[] {
  return chunks.length === 0 ? [] : [{ label: 'All files', chunkIds: chunks.map(c => c.id) }]
}

// Why the story order is off, or null when the call may run.
export function orderLimit(diff: string, chunks: readonly Chunk[]): string | null {
  if (chunks.length > MAX_CHUNKS) return `Story order is off: ${chunks.length} chunks is over ${MAX_CHUNKS}.`
  const lines = diff.split('\n').length
  if (lines > MAX_LINES) return `Story order is off: ${lines} diff lines is over ${MAX_LINES}.`
  return null
}

export function orderPrompt(pr: Pr, chunks: readonly Chunk[]): string {
  const list = chunks.map(c => {
    const head = c.body.split('\n').slice(1, 7).join('\n')
    return `id: ${c.id}\npath: ${c.path}\nhunk: ${c.header || '(no hunk)'}\n${head}`
  })
  return [
    `PR #${pr.number}: ${pr.title}`,
    pr.body.trim(),
    '',
    'Group the chunks below into the order a reader follows to understand this PR.',
    'Answer with JSON only, and use the ids given:',
    '[{"label": "a short group name", "chunkIds": ["id", "id"]}]',
    '',
    ...list,
  ].join('\n')
}

// Null means the reply gave no usable order: the caller uses file order.
export function parseOrder(reply: string, chunks: readonly Chunk[]): Group[] | null {
  let data: unknown
  try {
    data = JSON.parse(stripFence(reply))
  } catch {
    return null
  }
  const list = Array.isArray(data) ? data : (data as { groups?: unknown } | null)?.groups
  if (!Array.isArray(list)) return null
  const known = new Set(chunks.map(c => c.id))
  const used = new Set<string>()
  const groups: Group[] = []
  for (const raw of list) {
    const g = (raw ?? {}) as { label?: unknown; chunkIds?: unknown }
    const rawIds = Array.isArray(g.chunkIds) ? g.chunkIds : []
    const ids: string[] = []
    for (const id of rawIds) {
      if (typeof id !== 'string' || !known.has(id) || used.has(id)) continue
      used.add(id)
      ids.push(id)
    }
    if (ids.length === 0) continue
    const label = typeof g.label === 'string' && g.label.trim() ? g.label.trim() : 'Changes'
    groups.push({ label, chunkIds: ids })
  }
  if (groups.length === 0) return null
  const left = chunks.filter(c => !used.has(c.id)).map(c => c.id)
  if (left.length > 0) groups.push({ label: 'Other changes', chunkIds: left })
  return groups
}

export const LOAD_MS = 60000
export const HEAD_MS = 30000

export function parseRepo(url: string): { owner: string; repo: string } | null {
  const m = /^https?:\/\/[^/]+\/([^/]+)\/([^/]+)\/pull\/\d+/.exec(url.trim())
  return m?.[1] && m[2] ? { owner: m[1], repo: m[2] } : null
}

// The `gh pr view` arguments for what the command got: a number, a url, a
// branch, or `owner/repo#N`. `gh` reads no `owner/repo#N` of its own, so that
// form becomes the number and `-R owner/repo`. Empty means the current branch.
export function refArgs(ref: string): string[] {
  const r = ref.trim()
  const m = /^([\w.-]+\/[\w.-]+)#(\d+)$/.exec(r)
  if (m) return [m[2]!, '-R', m[1]!]
  return r ? [r] : []
}

// The repo flag of every later `gh pr` call: the PR may live in a repo other
// than the one the session runs in, and `gh` alone looks in the session's.
export function repoArgs(pr: Pick<Pr, 'owner' | 'repo'>): string[] {
  return ['-R', `${pr.owner}/${pr.repo}`]
}

export function prKey(pr: Pr): string {
  return `${pr.owner}/${pr.repo}#${pr.number}`
}

export const PRUNE_MS = 30 * 24 * 60 * 60 * 1000

// The diff body never goes to the store: it comes back from `gh pr diff`.
export function slim(chunks: readonly Chunk[]): SavedChunk[] {
  return chunks.map(({ body: _body, ...rest }) => rest)
}

export const ORDER_MODEL = 'sonnet'
export const SUMMARY_MODEL = 'haiku'
export const NOTE_MODEL = 'haiku'
export const QUESTION_MODEL = 'sonnet'

// The cached prompt prefix the notes and the questions share. With no summary
// the PR title and body take its place (spec 5.5 and the error table).
export function prefix(pr: Pr, summary: string | null, groups: readonly Group[]): string {
  return [
    `PR #${pr.number}: ${pr.title}`,
    summary ? `Summary: ${summary}` : pr.body.trim(),
    `Story order: ${groups.map(g => g.label).join(' | ') || 'file order'}`,
  ].join('\n')
}

// The open chunk shows at least this many rows, and more when the pane
// has room: the diff takes the rows the parts above it leave.
export const CHUNK_LINES = 6

const HUNK = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$/

// The lines of a hunk that a window starting at `offset` skips or shows, as
// old-file and new-file line counts. A `\` line (no newline at end) is neither.
function hunkCounts(lines: readonly string[]): { old: number; new: number } {
  let old = 0
  let added = 0
  for (const line of lines) {
    if (line.startsWith('+')) added += 1
    else if (line.startsWith('-')) old += 1
    else if (!line.startsWith('\\')) {
      old += 1
      added += 1
    }
  }
  return { old, new: added }
}

// What the pane shows of a chunk: `size` rows, its `@@` header first, from
// hunk line `offset`. The header is made again for the lines shown, so the
// Code element still reads a valid diff and draws its colours; a slice under
// the first header fails its line counts and draws as plain code. The offset
// stays inside the hunk, so a press past either end does nothing. `total` and
// `count` are hunk lines: the header is not one.
export function chunkWindow(
  body: string,
  offset: number,
  size: number,
): { lines: string[]; offset: number; total: number; count: number } {
  const all = body.split('\n')
  const m = HUNK.exec(all[0] ?? '')
  if (!m) {
    const at = Math.max(0, Math.min(offset, all.length - size))
    const lines = all.slice(at, at + size)
    return { lines, offset: at, total: all.length, count: lines.length }
  }
  const rest = all.slice(1)
  const room = Math.max(1, size - 1)
  const at = Math.max(0, Math.min(offset, rest.length - room))
  const shown = rest.slice(at, at + room)
  if (at === 0 && shown.length === rest.length) return { lines: all, offset: 0, total: rest.length, count: shown.length }
  const skip = hunkCounts(rest.slice(0, at))
  const count = hunkCounts(shown)
  // A side with no lines names the line before the hunk, as git does.
  const start = (from: number, skipped: number, n: number) => Math.max(0, from + skipped - (n === 0 ? 1 : 0))
  const header = `@@ -${start(Number(m[1]), skip.old, count.old)},${count.old} +${start(Number(m[2]), skip.new, count.new)},${count.new} @@${m[3]}`
  return { lines: [header, ...shown], offset: at, total: rest.length, count: shown.length }
}

// The rows a text takes when the terminal wraps it at `width` cells. A word
// that does not fit moves whole to the next row, and a word wider than a row
// is cut, so this follows the wrap rather than counting characters.
export function textRows(text: string, width: number): number {
  const w = Math.max(1, width)
  let rows = 0
  for (const line of text.split('\n')) {
    let at = 0
    rows += 1
    for (const word of line.split(' ')) {
      if (at === 0) at = word.length
      else if (at + 1 + word.length <= w) at += 1 + word.length
      else {
        rows += 1
        at = word.length
      }
      while (at > w) {
        rows += 1
        at -= w
      }
    }
  }
  return rows
}

// The comment box grows with its text from 2 rows to 5, then the text
// scrolls inside it. The engine types a newline on Shift+Enter only in a box
// of 2 rows or more, so the box never has 1 row.
const INPUT_MIN_ROWS = 2
const INPUT_MAX_ROWS = 5

// The rows a box needs for `text` in a pane of `columns` cells. The engine
// wraps the text at the pane's columns less the label and `: ` before it and
// the hint after it, the hint in its long form only when the text keeps half
// the width. A terminal with no Shift+Enter shows a shorter hint (`\⏎`): the
// count then can give one row too many, never one too few.
export function inputRows(text: string, label: string, columns: number): number {
  const room = columns - (label.length + 2)
  const long = ' ⏎ submit · shift+⏎ new line'
  const hint = room - long.length >= columns / 2 ? long : ' ⏎ submit'
  const rows = textRows(text, room - hint.length)
  return Math.min(INPUT_MAX_ROWS, Math.max(INPUT_MIN_ROWS, rows))
}

// The story heading over the chunk `id`: the pane shows one chunk, so its
// group label moves onto the position line.
export function groupOf(rowList: readonly Row[], id: string | null): string | null {
  let label: string | null = null
  for (const row of rowList) {
    if (row.kind === 'heading') label = row.label
    else if (row.id === id) return label
  }
  return null
}

// Text cut to `max` characters, with an ellipsis when it was cut.
export function clipText(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, Math.max(1, max - 1)).trimEnd()}…`
}

// Cut a text so that it wraps to `rows` rows at most. A word wrap leaves the
// end of each row empty, so a cut by characters alone gives one row too many.
export function clipRows(text: string, width: number, rows: number): string {
  let out = text
  for (let max = rows * width; max > 1 && textRows(out, width) > rows; max -= 2) out = clipText(text, max)
  return out
}

// What the merge reads of the reviewed head. A live `Review` fits it too, so
// the `r` press and the load both call `merge` with the same shape.
export type MergeInput = {
  chunks: readonly SavedChunk[]
  groups: readonly Group[]
  accepted: readonly string[]
  notes: Readonly<Record<string, string>>
  threads: Readonly<Record<string, Thread[]>>
  drafts: Readonly<Record<string, string>>
  orphanDrafts: readonly Orphan[]
}

export type MergeOutput = Pick<
  Review,
  'chunks' | 'groups' | 'accepted' | 'notes' | 'threads' | 'drafts' | 'orphanDrafts'
>

// Spec 6.3 items 2 to 7. The merge never changes the story order and never
// calls the model.
export function merge(before: MergeInput, next: readonly Chunk[]): MergeOutput {
  const oldById = new Map(before.chunks.map(c => [c.id, c]))
  const nextIds = new Set(next.map(c => c.id))
  const fresh = next.filter(c => !oldById.has(c.id))
  const gone = before.chunks.filter(c => !nextIds.has(c.id))

  // Decided: one old chunk is taken by at most one new chunk, the one with the
  // largest old-file line overlap. Every other overlapping new chunk is new,
  // so a draft is never copied twice.
  const goneByPath = new Map<string, SavedChunk[]>()
  for (const g of gone) goneByPath.set(g.path, [...(goneByPath.get(g.path) ?? []), g])
  const pairs: { fresh: Chunk; gone: SavedChunk; score: number }[] = []
  for (const f of fresh) {
    for (const g of goneByPath.get(f.path) ?? []) {
      const score = overlap(f, g)
      if (score > 0) pairs.push({ fresh: f, gone: g, score })
    }
  }
  pairs.sort((a, b) => b.score - a.score || a.fresh.id.localeCompare(b.fresh.id))
  // `takes` is new id to old chunk; `takenBy` is old id to new chunk.
  const takes = new Map<string, SavedChunk>()
  const takenBy = new Map<string, Chunk>()
  for (const p of pairs) {
    if (takes.has(p.fresh.id) || takenBy.has(p.gone.id)) continue
    takes.set(p.fresh.id, p.gone)
    takenBy.set(p.gone.id, p.fresh)
  }

  const wasAccepted = new Set(before.accepted)
  const chunks: Chunk[] = []
  const accepted: string[] = []
  const notes: Record<string, string> = {}
  const threads: Record<string, Thread[]> = {}
  const drafts: Record<string, string> = {}
  for (const c of next) {
    const same = oldById.get(c.id)
    if (same) {
      chunks.push({ ...c, isChanged: same.isChanged })
      const note = before.notes[c.id]
      const thread = before.threads[c.id]
      const draft = before.drafts[c.id]
      if (note !== undefined) notes[c.id] = note
      if (thread !== undefined) threads[c.id] = thread
      if (draft !== undefined) drafts[c.id] = draft
      if (wasAccepted.has(c.id)) accepted.push(c.id)
      continue
    }
    const old = takes.get(c.id)
    if (old) {
      // It loses the accept mark and the note, and shows `changed`.
      // Decided: the agent implementing Task 17 clears `isChanged` in the `accept` case of
      // `act`, since accepting the new text is what retires the `changed` label. [inferred]
      chunks.push({ ...c, isChanged: true })
      const thread = before.threads[old.id]
      const draft = before.drafts[old.id]
      if (thread !== undefined) threads[c.id] = thread
      if (draft !== undefined) drafts[c.id] = draft
      continue
    }
    chunks.push({ ...c, isChanged: false })
  }

  // A draft on a chunk nobody took posts as text in the review body.
  const orphanDrafts = [...before.orphanDrafts]
  for (const g of gone) {
    const text = before.drafts[g.id]
    if (text === undefined || takenBy.has(g.id)) continue
    orphanDrafts.push({ path: g.path, header: g.header, text })
  }

  const live = new Set(chunks.map(c => c.id))
  const groups: Group[] = before.groups
    .map(group => ({
      label: group.label,
      chunkIds: group.chunkIds
        .map(id => (live.has(id) ? id : takenBy.get(id)?.id))
        .filter((id): id is string => id !== undefined && live.has(id)),
    }))
    .filter(group => group.chunkIds.length > 0)
  const placed = new Set(groups.flatMap(g => g.chunkIds))
  const added = chunks.filter(c => !placed.has(c.id)).map(c => c.id)
  if (added.length > 0) {
    const pushed = groups.find(g => g.label === NEW_IN_PUSH)
    if (pushed) pushed.chunkIds.push(...added)
    else groups.push({ label: NEW_IN_PUSH, chunkIds: added })
  }

  return { chunks, groups, accepted, notes, threads, drafts, orphanDrafts }
}

// The group of the chunks that no story step holds. A second push adds to it,
// so the list never shows two headings of the same name.
export const NEW_IN_PUSH = 'New in this push'

// The PR this session is about, when the command got no argument. `texts` is
// the messages, newest first. The newest message that names a PR wins: its
// last GitHub PR url, else its last `PR #N`. Null when no message names one,
// and the pane then asks `gh` for the PR of the current branch.
const PR_URL = /https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/pull\/\d+/g
const PR_NUMBER = /\bPR #(\d+)\b/g

export function sessionPr(texts: readonly string[]): string | null {
  for (const text of texts) {
    const urls = text.match(PR_URL)
    if (urls) return urls.at(-1)!
    const numbers = [...text.matchAll(PR_NUMBER)]
    if (numbers.length > 0) return numbers.at(-1)![1]!
  }
  return null
}

// The footer keys, in the order drawn. `hint` is the word the FOOTER line
// shows; `k` carries none because `j/k move` already names both. The pane
// draws this table and `FOOTER` reads it, so a renamed key moves once.
export type PaneKey = { key: string; label: string; hotkey: string; hint?: string }

export const PANE_KEYS: readonly PaneKey[] = [
  { key: 'move:next', label: 'next chunk', hotkey: 'n', hint: 'n/p chunk' },
  { key: 'move:prev', label: 'previous chunk', hotkey: 'p' },
  { key: 'accept', label: 'accept', hotkey: 'a', hint: 'a accept' },
  { key: 'next-open', label: 'next open', hotkey: 'u', hint: 'u next open' },
  { key: 'comment', label: 'comment', hotkey: 'c', hint: 'c comment' },
  { key: 'question', label: 'questions on the chunk', hotkey: 'q', hint: 'q questions' },
  { key: 'explain', label: 'explain', hotkey: 'e', hint: 'e explain' },
  { key: 'send', label: 'put every comment in the prompt box', hotkey: 's', hint: 's send to chat' },
  { key: 'scroll:down', label: 'scroll the diff down', hotkey: 'j', hint: 'j/k scroll the diff' },
  { key: 'scroll:up', label: 'scroll the diff up', hotkey: 'k' },
  { key: 'refresh', label: 'refresh', hotkey: 'r', hint: 'r refresh' },
  { key: 'close', label: 'close', hotkey: 'x', hint: 'x close' },
  { key: 'keys', label: 'help', hotkey: 'h', hint: 'h help' },
]

export const FOOTER = PANE_KEYS.flatMap(k => k.hint ?? []).join('  ')

// The chords that approve the PR and post the drafts. A pane key is one
// lowercase letter, so Shift+A is `a`, and a one-key Shift binding presses no
// mod Button: each of these keys must be a chord. A mod cannot name an action
// of its own, so each Button borrows an engine one that is unbound by default
// and handled only by the engine's diff panel or dialog. The person binds them
// in ~/.claude/keybindings.json: { "context": "Pane", "bindings": {
// "ctrl+x shift+a": "app:toggleDiffNoiseFilter",
// "ctrl+x shift+p": "app:toggleDiffPreSession",
// "ctrl+x shift+c": "app:cycleDiffBase" } }.
export const APPROVE_ACTION = 'app:toggleDiffNoiseFilter'
export const POST_ALL_ACTION = 'app:toggleDiffPreSession'
export const POST_CHUNK_ACTION = 'app:cycleDiffBase'

// The chord keys, in the order the help dialog lists them. The Button keys
// are the `act` cases.
export const CHORD_KEYS: readonly { key: string; action: string; chord: string; label: string }[] = [
  { key: 'approve', action: APPROVE_ACTION, chord: 'ctrl+x shift+a', label: 'approve the PR, when every chunk is accepted' },
  { key: 'post:all', action: POST_ALL_ACTION, chord: 'ctrl+x shift+p', label: 'post every comment now' },
  { key: 'post:chunk', action: POST_CHUNK_ACTION, chord: 'ctrl+x shift+c', label: 'post the comment of this chunk now' },
]

// What the h dialog shows: one line per key. A pane key is one letter or one
// digit only, so `?` cannot open it. The dialog wants a question at the end.
export const HELP_TEXT = [
  'The review pane keys:',
  ...PANE_KEYS.filter(k => k.key !== 'keys').map(k => `${k.hotkey}   ${k.label}`),
  ...CHORD_KEYS.map(k => `${k.chord}   ${k.label}`),
  'Esc gives the keys back to the prompt.',
  'Close this list?',
].join('\n')

// The labels that close the q dialog. Anything else the reviewer types in the
// dialog's "Type something" row is a new question.
export const QA_CLOSE: readonly string[] = ['Close', 'Back to the review']

// What the q dialog shows: the full note (the pane shows one line of it), the
// questions on the chunk so far, then the ask. The questions and answers never
// draw in the pane itself.
export function questionText(label: string, threads: readonly Thread[], note: string | null = null): string {
  const past = threads.flatMap(t => [`Q: ${t.question}`, `A: ${t.answer}`, ''])
  return [`Questions on ${label}`, '', ...(note ? [`Why: ${note}`, ''] : []), ...past, 'Type a new question in "Type something", or close?'].join('\n')
}

// What the post asks GitHub for. GitHub refuses an approval from the PR's
// author, so on the reviewer's own PR the same key posts the comments only.
export type ReviewEvent = 'APPROVE' | 'COMMENT'

export function reviewEvent(r: Pick<Review, 'pr' | 'login'>): ReviewEvent {
  return isOwnPr(r) ? 'COMMENT' : 'APPROVE'
}

// The comments the post carries: one per draft, outdated drafts too.
export function draftCount(r: Pick<Review, 'drafts' | 'orphanDrafts'>): number {
  return Object.keys(r.drafts).length + r.orphanDrafts.length
}

// One item of `comments[]`, in the API's own names.
export type PostedComment = {
  path: string
  side: 'RIGHT' | 'LEFT'
  line: number
  start_line?: number
  // GitHub needs `start_side` beside `start_line` on a multi-line comment, and
  // refuses the whole review without it. It is always the side of `line`: a
  // range this code makes holds added lines only, or removed lines only.
  start_side?: 'RIGHT' | 'LEFT'
  body: string
}

export type Payload = {
  commit_id: string
  event: ReviewEvent
  body: string
  comments: PostedComment[]
}

// One formatter for an outdated draft, as `reviewBody` posts it.
export function orphanLine(d: Orphan): string {
  return `${orphanRef(d)}: ${d.text}`
}

// Where an outdated draft was: its file and its `@@` header.
function orphanRef(d: Orphan): string {
  return `\`${d.path}\` ${d.header} (outdated)`
}

// Spec 7. A draft that cannot attach to a line, and a draft whose chunk left
// the diff, both go into `body` as text: a dropped draft would lose the
// reviewer's own words without saying so.
export function reviewBody(state: MergeOutput & { reviewedHead: string }, event: ReviewEvent): Payload {
  const byId = new Map(state.chunks.map(c => [c.id, c]))
  const comments: PostedComment[] = []
  const extra: string[] = []
  for (const [id, text] of Object.entries(state.drafts)) {
    const chunk = byId.get(id)
    if (!chunk) continue
    const range = commentRange(chunk)
    if (!range) {
      extra.push(`\`${chunk.path}\`: ${text}`)
      continue
    }
    comments.push({
      path: range.path,
      side: range.side,
      ...(range.startLine === undefined ? {} : { start_line: range.startLine, start_side: range.side }),
      line: range.line,
      body: text,
    })
  }
  for (const d of state.orphanDrafts) extra.push(orphanLine(d))
  return {
    commit_id: state.reviewedHead,
    event,
    body: extra.join('\n\n'),
    comments,
  }
}

// The state a post of the one draft on chunk `id` sends: that draft alone,
// and no outdated draft. `reviewBody` then puts it on its line, or into the
// body as text when it cannot attach to one.
export function oneDraft<T extends MergeOutput>(state: T, id: string): T {
  const text = state.drafts[id]
  return { ...state, drafts: text === undefined ? {} : { [id]: text }, orphanDrafts: [] }
}

// Where a draft is: the file, the lines it posts on, and the `@@` header.
// A hunk of removed lines only names lines of the old file.
function hunkRef(chunk: Chunk): string {
  const range = commentRange(chunk)
  const lines = !range ? '' : range.startLine === undefined ? `:${range.line}` : `:${range.startLine}-${range.line}`
  const side = range?.side === 'LEFT' ? ' (old file)' : ''
  return `\`${chunk.path}${lines}\`${side}${chunk.header ? ` ${chunk.header}` : ''}`
}

// What the s key puts in the prompt box: each draft under the place it is
// on, in the order the pane walks the chunks, then the outdated drafts.
export function chatText(r: Pick<Review, 'pr' | 'chunks' | 'drafts' | 'orphanDrafts'>, order: readonly string[]): string {
  const byId = new Map(r.chunks.map(c => [c.id, c]))
  const ids = [...order, ...Object.keys(r.drafts).filter(id => !order.includes(id))]
  const item = (where: string, text: string) => [`- ${where}`, ...text.split('\n').map(line => `  ${line}`)].join('\n')
  const items = ids.flatMap(id => {
    const chunk = byId.get(id)
    const text = r.drafts[id]
    return chunk && text !== undefined ? [item(hunkRef(chunk), text)] : []
  })
  for (const d of r.orphanDrafts) items.push(item(orphanRef(d), d.text))
  return [`Review comments on PR #${r.pr.number} (${r.pr.url}):`, '', items.join('\n\n')].join('\n')
}

export function isOwnPr(r: Pick<Review, 'pr' | 'login'>): boolean {
  return r.pr.author !== '' && r.pr.author === r.login
}
