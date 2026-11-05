import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Chunk, Editing, Group, Pane, Pr, Review, Row, Saved, Thread } from '../types'
import { parseDiff } from './diff'
import {
  APPROVE_ACTION,
  CHORD_KEYS,
  chunkWindow,
  CHUNK_LINES,
  chatText,
  clipRows,
  draftCount,
  groupOf,
  inputRows,
  textRows,
  accept,
  chunkOrder,
  fileOrder,
  FOOTER,
  HELP_TEXT,
  QA_CLOSE,
  questionText,
  HEAD_MS,
  isAllAccepted,
  isOwnPr,
  LOAD_MS,
  merge,
  moveCursor,
  nextOpen,
  NOTE_MODEL,
  oneDraft,
  orderLimit,
  orderOf,
  orderPrompt,
  ORDER_MODEL,
  PANE_KEYS,
  parseOrder,
  parseRepo,
  prefix,
  prKey,
  PRUNE_MS,
  refArgs,
  repoArgs,
  QUESTION_MODEL,
  reviewBody,
  reviewEvent,
  rows,
  sessionPr,
  slim,
  SUMMARY_MODEL,
} from './review'
import type { ReviewEvent } from './review'

const PANE = 'pr-flow-review'
// Every Button needs an `onPress`; the `ui.press` hook acts on the key instead,
// because a press during a redraw can be lost in a closure.
const NOOP = () => undefined
const POLL_MS = 60000
// Spec 6.2's refusal, and 6.2 names the `r` key, which only the list view
// draws: the refusal goes back to that view, so the key the message names is a
// key the reviewer can press.
const STALE_HEAD = 'New commits since you reviewed: press r'
const STORE = 'pr:'
// The pane wants room for the header, the summary, the open chunk and the keys.
const OPEN = { id: PANE, title: 'PR review', focus: true, rows: 40 } as const
const FOCUS_MS = 300
// The chord that opens and closes the pane from the prompt. A mod cannot name
// an action of its own, so the band's hidden Button borrows this engine one: it
// is Global, unbound by default, and only Claude Code's earlier diff panel
// handles it, which the built-in diff mod replaces. The person binds the chord
// in ~/.claude/keybindings.json: { "context": "Global", "bindings":
// { "ctrl+x p": "app:toggleReplTab" } }.
export const TOGGLE_ACTION = 'app:toggleReplTab'
// The label chips of the summary and the Why frames are one width, so the
// text beside them starts in one column: ` Summary ` and one space.
const LABEL_WIDTH = ' Summary '.length
// The body columns left of that text: the frame's border and padding, the
// chip and the space after it.
const TEXT_INDENT = 4 + LABEL_WIDTH + 1
// How many of the newest messages the PR search reads.
const SEARCH_MESSAGES = 200

// The chunks whose explain call failed: the chunk then shows `(no note)`, and
// the next e press asks again.
let noteFailed = new Set<string>()

// The diff rows the last draw showed: j and k move half of it. The render
// sets it, because only the render knows the room the pane has.
let diffRows = CHUNK_LINES
// The rows above the cursor row the list keeps, so the diff gets the rest.

// The poll timer this module started. A mod reload stops every timer and
// empties this, which is how the first render after a reload knows to start it.
let poll: { cancel: () => void } | null = null

const reviewAtom = atom({ plugin: 'code-review', key: 'review' } as const, null)
const paneAtom = atom({ plugin: 'code-review', key: 'pane' } as const, null)
const isUpAtom = atom({ plugin: 'code-review', key: 'isUp' } as const, false)

function fresh(ref: string): Pane {
  return {
    ref,
    status: 'loading',
    cursor: null,
    chunkOffset: 0,
    isDone: false,
    editing: null,
    busy: null,
    message: null,
    isPosted: false,
  }
}

async function setPane($: EngineInterface, patch: Partial<Pane>): Promise<void> {
  await update($, paneAtom, p => (p ? { ...p, ...patch } : p))
}

function failureText(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

// A failed `gh` call throws with the text the pane shows: the command and what
// it said. A silent empty list is the one failure the pane must never show.
// Every function below that calls `gh` or `$.model.complete` or `$.store.*` is
// declared in this file: the engine follows `$` only into a function declared
// in the same file as the hook that holds it, never across an import.
export async function gh(
  $: EngineInterface,
  argv: readonly string[],
  init: { timeoutMs?: number; stdin?: string } = {},
): Promise<string> {
  const r = await $.process.run(argv, { timeoutMs: init.timeoutMs ?? LOAD_MS, stdin: init.stdin })
  if (r.exitCode !== 0) {
    const why = (r.stderr || r.stdout).trim() || `exit ${r.exitCode}`
    throw new Error(`${argv.join(' ')}: ${why}`)
  }
  return r.stdout
}

export async function loadPr($: EngineInterface, ref: string): Promise<Pr> {
  const argv = ['gh', 'pr', 'view', ...refArgs(ref), '--json', 'number,title,body,author,headRefOid,url']
  const raw = JSON.parse(await gh($, argv)) as {
    number: number
    title: string
    body: string | null
    author: { login: string } | null
    headRefOid: string
    url: string
  }
  const repo = parseRepo(raw.url)
  if (!repo) throw new Error(`gh pr view: the PR url did not parse (${raw.url})`)
  return {
    number: raw.number,
    title: raw.title,
    body: raw.body ?? '',
    author: raw.author?.login ?? '',
    headRefOid: raw.headRefOid,
    url: raw.url,
    ...repo,
  }
}

export async function loadDiff($: EngineInterface, pr: Pr): Promise<{ diff: string; chunks: Chunk[] }> {
  const diff = await gh($, ['gh', 'pr', 'diff', String(pr.number), ...repoArgs(pr)])
  return { diff, chunks: parseDiff(diff) }
}

export async function loadLogin($: EngineInterface): Promise<string> {
  return (await gh($, ['gh', 'api', 'user', '-q', '.login'], { timeoutMs: HEAD_MS })).trim()
}

export async function loadHead($: EngineInterface, pr: Pr): Promise<string> {
  const argv = ['gh', 'pr', 'view', String(pr.number), '--json', 'headRefOid', '-q', '.headRefOid', ...repoArgs(pr)]
  return (await gh($, argv, { timeoutMs: HEAD_MS })).trim()
}

export async function readSaved($: EngineInterface, key: string): Promise<Saved | null> {
  const raw = (await $.store.get(STORE + key)) as Saved | undefined
  return raw && Array.isArray(raw.groups) ? raw : null
}

export async function saveState($: EngineInterface, key: string, r: Review, now: number): Promise<void> {
  const saved: Saved = {
    chunks: slim(r.chunks),
    groups: r.groups,
    summary: r.summary,
    notes: r.notes,
    accepted: r.accepted,
    threads: r.threads,
    drafts: r.drafts,
    orphanDrafts: r.orphanDrafts,
    reviewedHead: r.reviewedHead,
    savedAt: now,
  }
  await $.store.set(STORE + key, saved)
}

export async function clearState($: EngineInterface, key: string): Promise<void> {
  await $.store.delete(STORE + key)
}

// At load: an entry nobody touched for 30 days goes. It returns the keys it
// deleted, so a test sees the work rather than an empty success.
export async function prune($: EngineInterface, now: number): Promise<string[]> {
  const keys = (await $.store.keys()).filter(key => key.startsWith(STORE))
  const ages = await Promise.all(
    keys.map(async key => {
      const raw = (await $.store.get(key)) as Saved | undefined
      return typeof raw?.savedAt === 'number' ? raw.savedAt : 0
    }),
  )
  const gone = keys.filter((_key, i) => now - (ages[i] ?? 0) > PRUNE_MS)
  await Promise.all(gone.map(key => $.store.delete(key)))
  return gone
}

// Made on the first e press, never at load. Null when the model gave no
// answer: the header then shows no summary line, and the notes and the
// questions run with the PR title and body instead.
export async function summarize($: EngineInterface, pr: Pr): Promise<string | null> {
  const r = await $.model.complete({
    model: SUMMARY_MODEL,
    prompt: `Summarize this pull request in one or two plain sentences of at most 40 words.\n\nPR #${pr.number}: ${pr.title}\n\n${pr.body}`,
    maxTokens: 160,
  })
  return r.isAnswered ? r.text.trim() : null
}

export async function askOrder($: EngineInterface, pr: Pr, chunks: readonly Chunk[]): Promise<Group[] | null> {
  const r = await $.model.complete({ model: ORDER_MODEL, prompt: orderPrompt(pr, chunks), maxTokens: 4000 })
  return r.isAnswered ? parseOrder(r.text, chunks) : null
}

// Made on an e press only. Null when the model gave no answer: the chunk then
// shows `(no note)`, and the next e press asks again.
export async function noteFor($: EngineInterface, head: string, chunk: Chunk): Promise<string | null> {
  const ask = `\n\nChunk: ${chunk.path} ${chunk.header}\n${chunk.body}\n\nIn one short sentence of at most 15 words, say what this chunk does for the goal of the PR. Do not explain the code.`
  const r = await $.model.complete({
    model: NOTE_MODEL,
    prompt: [{ text: head, cache: true }, { text: ask }],
    maxTokens: 80,
  })
  return r.isAnswered ? r.text.trim() : null
}

// 5.6: the prefix and the full diff are the cached block; the chunk, the
// earlier Q and A of that chunk, and the question follow it.
export async function answerFor(
  $: EngineInterface,
  head: string,
  diff: string,
  chunk: Chunk,
  thread: readonly Thread[],
  question: string,
): Promise<{ answer: string } | { reason: string }> {
  const earlier = thread.map(t => `Q: ${t.question}\nA: ${t.answer}`).join('\n')
  const ask = `\n\nChunk: ${chunk.path} ${chunk.header}\n${chunk.body}\n\n${earlier}\n\nQ: ${question}\nAnswer in plain language, in three lines at most.`
  const r = await $.model.complete({
    model: QUESTION_MODEL,
    prompt: [{ text: `${head}\n\nFull diff:\n${diff}`, cache: true }, { text: ask }],
    maxTokens: 800,
  })
  return r.isAnswered ? { answer: r.text.trim() } : { reason: r.reason }
}

// The whole of spec 5.1. A `gh` failure throws, and the caller writes the text
// into the pane with a Try again button; it never draws an empty list.
export async function load($: EngineInterface, ref: string, now: number): Promise<Review> {
  await prune($, now)
  const pr = await loadPr($, ref)
  const [{ diff, chunks }, login, saved] = await Promise.all([loadDiff($, pr), loadLogin($), readSaved($, prKey(pr))])

  if (!saved) {
    const limit = orderLimit(diff, chunks)
    // The summary waits for the first e press, so a load makes one model call.
    const asked = limit ? null : await askOrder($, pr, chunks)
    return {
      pr,
      login,
      diff,
      chunks,
      groups: asked ?? fileOrder(chunks),
      summary: null,
      orderNote: limit ?? (asked ? null : 'Story order is off: the model gave no usable order.'),
      notes: {},
      accepted: [],
      threads: {},
      drafts: {},
      orphanDrafts: [],
      reviewedHead: pr.headRefOid,
      hasNewCommits: false,
    }
  }

  // 5.1 item 5: a saved head that is not the current head merges once here, so
  // the mark and the `changed` labels show on the first draw. The reviewed head
  // stays the saved one until an `r` press, which is what 6.3 item 8 says.
  //
  // The merge runs even when the head has not moved: it is then the identity on
  // the saved marks, and it is the one thing that keeps the saved state and the
  // fresh diff in step. `gh pr diff` is the diff against the merge base, so a
  // push to the BASE branch changes the chunks while the head stands still. A
  // saved mark or draft on a chunk the new diff no longer holds would otherwise
  // stay in the state, and `reviewBody` drops a draft whose chunk it cannot
  // find. The merge turns it into an `outdated` draft the body still says.
  const isNew = saved.reviewedHead !== pr.headRefOid
  const merged = merge(saved, chunks)
  // `MergeOutput` is exactly the subset of the saved state the merge rewrites,
  // so it spreads over it; `savedAt` belongs to the store alone.
  const { savedAt: _savedAt, ...keep } = saved
  return {
    pr,
    login,
    diff,
    orderNote: null,
    ...keep,
    ...merged,
    hasNewCommits: isNew,
  }
}

// What `r` runs: 6.3 item 1 reads the new head and the new diff, and item 8
// saves that head as the reviewed head, which clears the New commits mark.
export async function refresh($: EngineInterface, r: Review): Promise<Review> {
  const [head, { diff, chunks }] = await Promise.all([loadHead($, r.pr), loadDiff($, r.pr)])
  const merged = merge(r, chunks)
  return { ...r, ...merged, diff, pr: { ...r.pr, headRefOid: head }, reviewedHead: head, hasNewCommits: false }
}

// Spec 6.2 and 7. The head is read again first: a review posted against an old
// head attaches its comments to lines the author already moved. `r` holds the
// drafts to send: all of them, or one (`oneDraft`). The caller clears what was
// posted, so a failed post keeps every draft.
export async function post(
  $: EngineInterface,
  r: Review,
  event: ReviewEvent,
): Promise<{ url: string } | { error: string; isStale?: true }> {
  try {
    const head = await loadHead($, r.pr)
    if (head !== r.reviewedHead) return { error: STALE_HEAD, isStale: true }
    const payload = reviewBody(r, event)
    const argv = ['gh', 'api', `repos/${r.pr.owner}/${r.pr.repo}/pulls/${r.pr.number}/reviews`, '--method', 'POST', '--input', '-']
    const out = await gh($, argv, { stdin: JSON.stringify(payload) })
    // Parse first: a reply that is not JSON throws here, before the drafts go.
    const url = (JSON.parse(out) as { html_url?: string }).html_url
    return { url: url ?? r.pr.url }
  } catch (error) {
    return { error: failureText(error) }
  }
}

async function persist($: EngineInterface): Promise<void> {
  const r = await read($, reviewAtom)
  if (r) await saveState($, prKey(r.pr), r, await $.clock.now())
}

// The e key: a short note on the cursor chunk, and on the first press a short
// summary of the PR too. It runs from a handler, never from a render, because
// a hook has 10 s of its own time.
async function explain($: EngineInterface): Promise<void> {
  const r = await read($, reviewAtom)
  const pane = await read($, paneAtom)
  const id = pane?.cursor
  if (!r || !pane || !id || pane.busy) return
  const chunk = r.chunks.find(c => c.id === id)
  if (!chunk) return
  await setPane($, { busy: id })
  try {
    let summary = r.summary
    if (summary === null) {
      summary = await summarize($, r.pr)
      if (summary !== null) await update($, reviewAtom, cur => (cur ? { ...cur, summary } : cur))
    }
    if (r.notes[id] === undefined) {
      const note = await noteFor($, prefix(r.pr, summary, r.groups), chunk)
      if (note === null) noteFailed.add(id)
      else {
        noteFailed.delete(id)
        await update($, reviewAtom, cur => (cur ? { ...cur, notes: { ...cur.notes, [id]: note } } : cur))
      }
    }
  } finally {
    // A model call that throws must not leave `Thinking…` up and `e` dead.
    await setPane($, { busy: null })
  }
  await persist($)
}

// j and k: half the diff window at a time, held inside the hunk.
async function scrollChunk($: EngineInterface, step: number): Promise<void> {
  const r = await read($, reviewAtom)
  const pane = await read($, paneAtom)
  const chunk = r?.chunks.find(c => c.id === pane?.cursor)
  if (!pane || !chunk) return
  const { offset } = chunkWindow(chunk.body, pane.chunkOffset + step * Math.max(1, Math.floor(diffRows / 2)), diffRows)
  if (offset !== pane.chunkOffset) await setPane($, { chunkOffset: offset })
}

// The PR this session is about: the newest one its messages name. Empty when
// none does, or when the messages cannot be read; `gh` then uses the branch.
async function findSessionPr($: EngineInterface): Promise<string> {
  try {
    const messages = await $.session.messages()
    if ('deny' in messages) return ''
    const texts = messages.slice(-SEARCH_MESSAGES).reverse().map(m => m.text ?? '')
    return sessionPr(texts) ?? ''
  } catch {
    return ''
  }
}

// Asks for the keys again when the pane is open and does not hold them.
async function takeFocus($: EngineInterface): Promise<void> {
  try {
    const pane = (await $.ui.panes()).find(p => p.id === PANE)
    if (pane && !pane.isFocused) await $.ui.open(OPEN)
  } catch {
    // A refused request leaves the hint in the pane: ctrl+x tab.
  }
}

async function runLoad($: EngineInterface, ref: string): Promise<void> {
  // A failed note of an earlier pane must not silence this one: the ids live in
  // one module-level set, so the load starts it over.
  noteFailed = new Set()
  try {
    const r = await load($, ref, await $.clock.now())
    await update($, reviewAtom, () => r)
    const order = chunkOrder(r.groups, r.chunks)
    await setPane($, {
      status: 'ready',
      cursor: nextOpen(order, r.accepted, null) ?? order[0] ?? null,
      message: null,
    })
    // 6.1: starts here, a handler, rather than from `ui.render`: a render hook
    // is pure, and `$.state.set` while drawing is refused.
    startPoll($)
    await persist($)
  } catch (error) {
    await setPane($, { status: 'failed', message: failureText(error) })
  }
}

// The counts beside the cursor position: the position line says how many
// chunks there are, so this says only how many are done.
function progressText(r: Review): string {
  const drafts = Object.keys(r.drafts).length
  return [
    `${r.accepted.length} viewed`,
    drafts > 0 ? `${drafts} draft${drafts === 1 ? '' : 's'}` : '',
  ]
    .filter(Boolean)
    .join(' · ')
}

// Two columns, cursor then accept state, so an accepted cursor row still
// shows its mark instead of losing it to the cursor arrow. [inferred]
function rowMark(done: ReadonlySet<string>, id: string, cursor: string | null): string {
  const cursorMark = id === cursor ? '▶' : ' '
  const acceptMark = done.has(id) ? '✓' : '·'
  return `${cursorMark} ${acceptMark}`
}

// The added and removed line counts come from the parser, not the `@@` header:
// the open chunk's Code already shows that header, in full, below this row.
function rowLabel(chunk: Chunk, index: number): string {
  const counts = chunk.kind === 'empty' ? 'no diff' : `+${chunk.added} -${chunk.removed}`
  return `${index} ${chunk.path}  ${counts}${chunk.isChanged ? '   changed' : ''}`
}

// Null until an e press asks for the note.
const APPROVE_CHORD = CHORD_KEYS.find(k => k.key === 'approve')!.chord

// The done panel's line: the chord, and what it posts.
function doneText(r: Review): string {
  const n = draftCount(r)
  const comments = n === 1 ? '1 comment' : `${n} comments`
  if (isOwnPr(r)) {
    const own = 'This is your PR, so GitHub does not let you approve it.'
    return n === 0 ? `${own} You have no comments to post.` : `${own} Press ${APPROVE_CHORD} to post your ${comments}.`
  }
  return n === 0 ? `Press ${APPROVE_CHORD} to approve the PR.` : `Press ${APPROVE_CHORD} to approve the PR with your ${comments}.`
}

function noteText(r: Review, id: string): string | null {
  const note = r.notes[id]
  if (note !== undefined) return note
  return noteFailed.has(id) ? '(no note)' : null
}

async function moveTo($: EngineInterface, cursor: string | null): Promise<void> {
  if (!cursor) return
  // A new chunk starts at the top of its diff, and a move leaves the done panel.
  await setPane($, { cursor, chunkOffset: 0, isDone: false })
}

async function doRefresh($: EngineInterface): Promise<void> {
  const r = await read($, reviewAtom)
  if (!r) return
  try {
    const next = await refresh($, r)
    await update($, reviewAtom, () => next)
    const order = chunkOrder(next.groups, next.chunks)
    const pane = await read($, paneAtom)
    const cursor = pane?.cursor && order.includes(pane.cursor) ? pane.cursor : (order[0] ?? null)
    noteFailed = new Set()
    await setPane($, { cursor, chunkOffset: 0, message: null })
    await persist($)
  } catch (error) {
    await setPane($, { message: failureText(error) })
  }
}

async function closePane($: EngineInterface): Promise<void> {
  // The one place the poll timer is cancelled. A write to the pane atom here
  // could start a render that starts a new timer that nothing then cancels,
  // since `fresh(ref)` already sets `poll: 'none'` on the next open.
  poll?.cancel()
  poll = null
  await $.ui.close({ id: PANE }).catch(() => undefined)
}

function inputFooter(editing: Editing): string {
  return editing.isEdit ? 'Enter save  empty Enter delete' : 'Enter send  empty Enter cancel'
}

function inputLabel(editing: Pick<Editing, 'kind'>): string {
  return editing.kind === 'comment' ? 'Draft' : 'Question'
}

async function openInput($: EngineInterface, editing: Omit<Editing, 'typed'>): Promise<void> {
  await setPane($, { editing: { ...editing, typed: editing.text } })
  await $.ui.focus({ requestId: PANE, key: `input:${editing.kind}` }).catch(() => undefined)
}

async function runQuestion($: EngineInterface, id: string, question: string): Promise<void> {
  await setPane($, { busy: id })
  try {
    const r = await read($, reviewAtom)
    const chunk = r?.chunks.find(c => c.id === id)
    if (!r || !chunk) return
    const out = await answerFor($, prefix(r.pr, r.summary, r.groups), r.diff, chunk, r.threads[id] ?? [], question)
    const answer = 'answer' in out ? out.answer : `No answer: ${out.reason}`
    await update($, reviewAtom, cur =>
      cur ? { ...cur, threads: { ...cur.threads, [id]: [...(cur.threads[id] ?? []), { question, answer }] } } : cur,
    )
    await persist($)
  } finally {
    await setPane($, { busy: null })
  }
}

// The engine's own question dialog, the one pop-up a mod can open. Null when
// the person dismissed it, a normal close. When it closes the keys go to the
// prompt, so the pane asks for them back once the dialog is gone.
async function dialog($: EngineInterface, text: string, header: string): Promise<string | null> {
  try {
    return await $.ui.ask(text, { header, options: QA_CLOSE })
  } catch {
    return null
  } finally {
    $.clock.after(FOCUS_MS, () => {
      void takeFocus($)
    })
  }
}

// The q dialog: the questions on the chunk so far, and a new one typed in the
// dialog. After the answer the dialog opens again with it, for the next one.
async function askAbout($: EngineInterface, id: string): Promise<void> {
  const r = await read($, reviewAtom)
  const chunk = r?.chunks.find(c => c.id === id)
  if (!r || !chunk) return
  const label = rowLabel(chunk, chunkOrder(r.groups, r.chunks).indexOf(id) + 1)
  const question = (await dialog($, questionText(label, r.threads[id] ?? [], r.notes[id] ?? null), 'Questions'))?.trim()
  if (!question || QA_CLOSE.includes(question)) return
  await runQuestion($, id, question)
  await askAbout($, id)
}

async function checkHead($: EngineInterface): Promise<void> {
  const r = await read($, reviewAtom)
  if (!r || r.hasNewCommits) return
  const head = await loadHead($, r.pr)
  if (head === r.reviewedHead) return
  // 6.1: the pane never loads the new commits without an `r` press.
  await update($, reviewAtom, cur => (cur ? { ...cur, hasNewCommits: true } : cur))
}

// Does not write `pane.poll`: nothing reads that field once the pane starts,
// and an unawaited write here could race the very next `$.ui.focus` call a
// handler makes, landing on the drawing before the one it names its key in.
function startPoll($: EngineInterface): void {
  poll?.cancel()
  poll = $.clock.every(POLL_MS, () => {
    void checkHead($).catch(() => undefined)
  })
}

async function refuseStale($: EngineInterface): Promise<void> {
  await closeInput($, { message: STALE_HEAD })
}

// Every close of the Input. An open Input held the focus and is gone: keep the
// keys in the pane, so the next key is a pane key and not text in the prompt
// box. With no Input open (a post chord from the prompt) the focus stays.
async function closeInput($: EngineInterface, patch: Partial<Pane> = {}): Promise<void> {
  const wasOpen = (await read($, paneAtom))?.editing != null
  await setPane($, { ...patch, editing: null })
  if (wasOpen) await takeFocus($)
}

// What a post sends: the whole review (the approve key), every draft as a
// comment review, or the one draft on a chunk.
type PostKind = { kind: 'review'; event: ReviewEvent } | { kind: 'comments' } | { kind: 'chunk'; id: string }

async function doPost($: EngineInterface, what: PostKind): Promise<void> {
  const r = await read($, reviewAtom)
  if (!r) return
  // 6.2: the mark shows and no `r` was pressed, so the post would attach its
  // comments to lines the author already moved.
  if (r.hasNewCommits) {
    await refuseStale($)
    return
  }
  const event = what.kind === 'review' ? what.event : 'COMMENT'
  const sent = what.kind === 'chunk' ? oneDraft(r, what.id) : r
  const out = await post($, sent, event)
  if ('error' in out) {
    // The head moved under the post: the mark belongs on the `r` key now.
    if (out.isStale) {
      await update($, reviewAtom, cur => (cur ? { ...cur, hasNewCommits: true } : cur))
      await refuseStale($)
      return
    }
    await setPane($, { message: out.error })
    return
  }
  if (what.kind === 'review') {
    // The drafts, the marks and the Q and A of this PR are done with.
    await clearState($, prKey(r.pr))
    const done = event === 'APPROVE' ? 'The PR is approved' : 'The comments are posted'
    await setPane($, { message: `${done}: ${out.url}`, isPosted: true })
    return
  }
  // The review goes on: only the drafts that were sent go, so a draft written
  // while the post ran stays, and the marks and the Q and A stay.
  const gone = new Set(Object.keys(sent.drafts))
  const orphans = sent.orphanDrafts.length
  await update($, reviewAtom, cur => {
    if (!cur) return cur
    const drafts = Object.fromEntries(Object.entries(cur.drafts).filter(([id]) => !gone.has(id)))
    return { ...cur, drafts, orphanDrafts: cur.orphanDrafts.slice(orphans) }
  })
  await persist($)
  const n = draftCount(sent)
  const posted = n === 1 ? 'The comment is posted' : `The ${n} comments are posted`
  await setPane($, { message: `${posted}: ${out.url}` })
}

// A `gh` call can take 60 s, and a hook has 10 s of its own time: the work
// runs as its own dispatch, as the PR load does. A failure goes to the pane.
let isPosting = false

function dispatch($: EngineInterface, work: () => Promise<void>): void {
  $.clock.after(0, () => {
    void work().catch(error => setPane($, { message: failureText(error) }).catch(() => undefined))
  })
}

// A second press while a post runs would post twice: one post at a time.
async function startPost($: EngineInterface, what: PostKind, busy: string): Promise<void> {
  if (isPosting) return
  isPosting = true
  await setPane($, { message: busy })
  dispatch($, async () => {
    try {
      await doPost($, what)
    } finally {
      isPosting = false
    }
  })
}

// One switch on the Button key. A press during a redraw can be lost in an
// `onPress` closure, so every Button carries a no-op one and the work is here.
async function act($: EngineInterface, key: string): Promise<void> {
  const pane = await read($, paneAtom)
  if (!pane) return
  // 6.1: a mod reload stops every timer and empties `poll`; a press is a
  // handler, so restarting it here (never from `ui.render`) is legal.
  if (!poll && pane.status === 'ready') startPoll($)
  // 7: after a successful post the next press closes the pane.
  if (pane.isPosted) {
    await closePane($)
    return
  }
  if (key === 'retry') {
    await setPane($, { status: 'loading', message: null })
    dispatch($, () => runLoad($, pane.ref))
    return
  }
  const r = await read($, reviewAtom)
  if (!r || pane.status !== 'ready') return
  const order = chunkOrder(r.groups, r.chunks)
  switch (key) {
    case 'move:next':
      await moveTo($, moveCursor(order, pane.cursor, 1))
      return
    case 'move:prev':
      await moveTo($, moveCursor(order, pane.cursor, -1))
      return
    case 'next-open':
      await moveTo($, nextOpen(order, r.accepted, pane.cursor))
      return
    case 'accept': {
      // On the done panel every chunk is accepted: an `a` there would clear a
      // mark the reviewer cannot see.
      if (!pane.cursor || pane.isDone) return
      const out = accept(order, r.accepted, pane.cursor)
      await update($, reviewAtom, cur =>
        cur
          ? {
              ...cur,
              accepted: out.accepted,
              // Accepting the new text retires the `changed` label. [inferred]
              chunks: cur.chunks.map(c => (c.id === pane.cursor ? { ...c, isChanged: false } : c)),
            }
          : cur,
      )
      await persist($)
      await moveTo($, out.cursor)
      if (isAllAccepted(order, out.accepted)) {
        await setPane($, { isDone: true })
        // The chunk line held the focus and is gone: give the keys back.
        await takeFocus($)
      }
      return
    }
    case 'comment': {
      if (!pane.cursor) return
      const draft = r.drafts[pane.cursor]
      await openInput($, { kind: 'comment', id: pane.cursor, text: draft ?? '', isEdit: draft !== undefined })
      return
    }
    case 'question': {
      // A dialog stays up longer than a hook may run: it runs as its own
      // dispatch, as the PR load does.
      const id = pane.cursor
      if (!id) return
      dispatch($, () => askAbout($, id))
      return
    }
    case 'keys':
      // A dialog stays up longer than a hook may run: it runs as its own
      // dispatch, as the PR load does.
      $.clock.after(0, () => {
        void dialog($, HELP_TEXT, 'Keys')
      })
      return
    case 'explain':
      await explain($)
      return
    case 'send':
      await sendToChat($, r, order)
      return
    case 'scroll:down':
      await scrollChunk($, 1)
      return
    case 'scroll:up':
      await scrollChunk($, -1)
      return
    case 'approve': {
      // The chord works in every view, but approves only once every chunk is
      // accepted: it says how many are still open.
      if (!isAllAccepted(order, r.accepted)) {
        const done = new Set(r.accepted)
        const open = order.filter(id => !done.has(id)).length
        await setPane($, { message: `Accept every chunk first: ${open} ${open === 1 ? 'is' : 'are'} still open.` })
        return
      }
      const event = reviewEvent(r)
      // On the reviewer's own PR the key posts the comments, and with none
      // there is nothing to post.
      if (event === 'COMMENT' && draftCount(r) === 0) {
        await setPane($, { message: 'There are no comments to post.' })
        return
      }
      await startPost($, { kind: 'review', event }, 'Posting the review…')
      return
    }
    case 'post:all': {
      // Every draft as a comment review, at any point of the review.
      if (draftCount(r) === 0) {
        await setPane($, { message: 'There are no comments to post.' })
        return
      }
      await startPost($, { kind: 'comments' }, 'Posting the comments…')
      return
    }
    case 'post:chunk': {
      const id = pane.cursor
      if (!id || pane.isDone || r.drafts[id] === undefined) {
        await setPane($, { message: 'This chunk has no draft comment.' })
        return
      }
      await startPost($, { kind: 'chunk', id }, 'Posting the comment…')
      return
    }
    case 'refresh':
      dispatch($, () => doRefresh($))
      return
    case 'close':
    case 'toggle':
      await closePane($)
      return
    default: {
      const id = key.startsWith('chunk:') ? key.slice('chunk:'.length) : ''
      if (order.includes(id)) await moveTo($, id)
    }
  }
}

// A change in the box: keep the text, so the draw counts the rows it needs.
// The engine keeps the typed text itself, so the box's `value` stays as it
// was opened, and a draw that changes only `rows` keeps the text and the cursor.
// One update reads and writes the pane, so a change that lands after a submit
// does not open the closed box again.
async function grow($: EngineInterface, value: string): Promise<void> {
  await update($, paneAtom, p =>
    p?.editing && value !== p.editing.typed ? { ...p, editing: { ...p.editing, typed: value } } : p,
  )
}

// The s key: close the pane and put every draft in the prompt box, so the
// person can add to it and send it to the model. The drafts stay, and can
// still go to GitHub.
async function sendToChat($: EngineInterface, r: Review, order: readonly string[]): Promise<void> {
  if (draftCount(r) === 0) {
    await setPane($, { message: 'No comments to send: press c to write one.' })
    return
  }
  const text = chatText(r, order)
  await closePane($)
  // The pane is closed, so a failure shows in a toast, not in the pane.
  try {
    const box = await $.prompt.read()
    const filled = await $.prompt.fill({ text: box.text.trim() ? `\n\n${text}` : text, mode: 'append' })
    if (!filled.isFilled) $.ui.toast(`code-review: the prompt box did not take the comments (${filled.refusal ?? 'refused'}).`)
  } catch (error) {
    $.ui.toast(`code-review: the prompt box did not take the comments (${failureText(error)}).`)
  }
}

// Enter in one of the pane's Inputs.
async function submit($: EngineInterface, value: string): Promise<void> {
  const pane = await read($, paneAtom)
  if (!pane?.editing) return
  const { kind, id, isEdit } = pane.editing
  const text = value.trim()
  await closeInput($)
  if (kind === 'comment') {
    // An empty Enter on a new comment cancels; on an edit it deletes the draft.
    if (!text && !isEdit) return
    await update($, reviewAtom, cur => {
      if (!cur) return cur
      const drafts = { ...cur.drafts }
      if (text) drafts[id] = text
      else delete drafts[id]
      return { ...cur, drafts }
    })
    await persist($)
    return
  }
  if (kind === 'question') {
    if (!text) return
    await runQuestion($, id, text)
  }
}

// Open the pane on a PR and load it: the command, and the chord on a pane
// that has no review to show again. Returns the line the command prints.
async function openReview($: EngineInterface, given: string): Promise<string> {
  const ref = given || (await findSessionPr($))
  await update($, reviewAtom, () => null)
  await update($, paneAtom, () => fresh(ref))
  const opened = await $.ui.open(OPEN)
  if (!opened.isPlaced) return `The review pane did not open (${opened.reason}).`
  await update($, isUpAtom, () => true)
  // The load holds two 60 s `gh` calls, and a hook has 10 s of its own time:
  // it runs as its own dispatch, and the pane shows `Loading PR…` until it
  // writes the review into the state.
  $.clock.after(0, () => {
    void runLoad($, ref)
  })
  // `focus` is a request: the engine refuses it while the command still holds
  // the prompt. Ask again once the command is done.
  $.clock.after(FOCUS_MS, () => {
    void takeFocus($)
  })
  const what = given ? given : ref ? `${ref} (found in this session)` : 'the current branch'
  return `The review pane is open for ${what}. Press h in the pane for help.`
}

// The chord: close an open pane; else show the review it closed on, at the
// same chunk, or load a new one as the command with no argument does.
async function togglePane($: EngineInterface): Promise<void> {
  if ((await $.ui.panes()).some(p => p.id === PANE)) {
    await closePane($)
    return
  }
  const pane = await read($, paneAtom)
  const r = await read($, reviewAtom)
  if (!pane || !r || pane.status !== 'ready' || pane.isPosted) {
    const text = await openReview($, '')
    if (!text.startsWith('The review pane is open')) $.ui.toast(text)
    return
  }
  const opened = await $.ui.open(OPEN)
  if (!opened.isPlaced) {
    $.ui.toast(`The review pane did not open (${opened.reason}).`)
    return
  }
  await update($, isUpAtom, () => true)
  // `closePane` stopped the poll for new commits.
  startPoll($)
  $.clock.after(FOCUS_MS, () => {
    void takeFocus($)
  })
}

export const register: Register = on => {
  on('command.run', { command: 'code-review:review-pane' }, async ($, e) => ({
    text: await openReview($, e.args.trim()),
  })).catch((_$, _e, next) => ({ text: `The review pane failed (${failureText(next.error)}).` }))

  // A mod reload drops no pane but starts the module again: read what is open.
  on('session.start', async ($, e, next) => {
    const isUp = (await $.ui.panes()).some(p => p.id === PANE)
    await update($, isUpAtom, () => isUp)
    return next(e)
  }).catch(async ($, e, next) => {
    // Not known: say closed, so the band keeps the chord that opens it.
    await update($, isUpAtom, () => false).catch(() => undefined)
    return next(e)
  })

  // Every close: the `x` key, the chord, the engine's close mark, ctrl+x x.
  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) await update($, isUpAtom, () => false)
    return next(e)
  }).catch(($, e, next) => next(e))

  // While the pane is closed the band holds one hidden Button, so the chord
  // bound to TOGGLE_ACTION opens it: a Button with an `action` is pressed by
  // its chord only while it is drawn. The band draws no row: the Box is
  // hidden. While the pane is open its own hidden Button closes it.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, isUpAtom))) return next(e)
    const { Box, Button } = $.ui.resolve(e)
    return (
      <Box display="none">
        <Button key="toggle" label="Open or close the review pane" action={TOGGLE_ACTION} plain onPress={NOOP} />
      </Box>
    )
  })

  on('ui.press', { component: 'AbovePrompt' }, async ($, e) => {
    if (e.element === 'toggle') await togglePane($)
    return { element: e.element }
  }).catch(async ($, e, next) => {
    $.ui.toast(`code-review: ${failureText(next.error)}`)
    return { element: e.element }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    // Spec 1: the pane is terminal- and desktop-only. Narrowing `e.surface`
    // here, rather than destructuring the unnarrowed union, is what gives
    // `Input` a type on the elements table below: vscode and mobile lack it.
    if (e.surface !== 'terminal' && e.surface !== 'desktop') {
      const { Text } = $.ui.resolve(e)
      return <Text dimColor>The review pane needs the terminal or the desktop app.</Text>
    }
    const { Box, Button, Code, Input, Text } = $.ui.resolve(e)
    const pane = await read($, paneAtom)
    if (!pane) return <Text dimColor>Run /code-review:review-pane to review a PR.</Text>
    if (pane.status === 'loading') {
      return (
        <Box flexDirection="column" rowGap={1}>
          <Text dimColor>{pane.ref ? `Loading PR ${pane.ref}…` : 'Loading PR…'}</Text>
        </Box>
      )
    }
    const r = await read($, reviewAtom)
    if (pane.status === 'failed' || !r) {
      return (
        <Box flexDirection="column" rowGap={1}>
          <Text color="error">{pane.message ?? 'The PR did not load.'}</Text>
          <Button key="retry" label="Try again" hotkey="t" plain onPress={NOOP} />
        </Box>
      )
    }
    const byId = new Map(r.chunks.map(c => [c.id, c]))
    // A background marks the few things the eye must find first: the PR, the
    // section labels, a draft and the New commits alert. Theme keys keep them
    // readable in the light and the dark theme.
    // A chip never shrinks: a long text beside it took a column from the chip,
    // and its last space wrapped to the next row with the background. Its row
    // has alignItems flex-start, so the chip is not stretched to that height.
    const chip = (text: string, bg: 'success' | 'suggestion' | 'warning' | 'cyan', width?: number) => (
      <Box flexShrink={0} width={width}>
        <Text bold color="inverseText" backgroundColor={bg} wrap="truncate-end">{` ${text} `}</Text>
      </Box>
    )
    // A frame gives a part its own space: the summary, the diff.
    const frame = { borderStyle: 'round', paddingX: 1, flexDirection: 'column' } as const
    // The title in a frame of its own, one row: a long title is cut, and the
    // author stays at the right end.
    const title = (
      <Box {...frame} borderColor="success">
        <Box flexDirection="row" columnGap={1}>
          {chip(`PR #${r.pr.number}`, 'success')}
          <Box flexGrow={1} flexShrink={1}>
            <Text bold wrap="truncate-end">{r.pr.title}</Text>
          </Box>
          <Box flexShrink={0}>
            <Text dimColor>{`@${r.pr.author}`}</Text>
          </Box>
        </Box>
      </Box>
    )
    const message = pane.message && <Text color="warning">{pane.message}</Text>
    // One walk of the groups for the whole draw: the cursor walks the same
    // order the position line counts.
    const rowList = rows(r.groups, r.chunks)
    const order = orderOf(rowList)
    const done = new Set(r.accepted)
    const cursorChunk = pane.cursor ? byId.get(pane.cursor) : undefined
    const why = pane.cursor ? noteText(r, pane.cursor) : null
    const draft = pane.cursor ? r.drafts[pane.cursor] : undefined
    const isTyping = pane.editing !== null
    const isDone = pane.isDone && !pane.editing && isAllAccepted(order, r.accepted)
    const group = groupOf(rowList, pane.cursor)
    const cols = e.props.bodyColumns
    const inputHeight = pane.editing ? inputRows(pane.editing.typed, inputLabel(pane.editing), cols) : 0
    // Three lines at most inside each frame, beside the chip.
    const summary = r.summary && clipRows(r.summary, cols - TEXT_INDENT, 3)
    const whyText = why === null ? null : clipRows(why, cols - TEXT_INDENT, 3)
    // A draft can hold many lines: show 5 at most, as the box that wrote it,
    // so the diff keeps its rows. `c` opens the whole draft.
    const draftText = draft === undefined ? undefined : clipRows(draft, cols - 8, 5)
    // The pane shows one chunk, and the whole tree fits the pane's rows: a tree
    // taller than the pane scrolls and the diff frame does not close. So each
    // part is counted row by row: a text that can wrap by `textRows`, the rest
    // one row cut at the edge. The diff frame gets the rows left over.
    const bodyRows = e.props.scroll.bodyRows
    const used =
      3 + // the title and its frame
      (pane.editing ? inputHeight + 1 : 1) + // the input and its footer, or the bottom line
      (pane.message ? textRows(pane.message, cols) : 0) +
      (summary ? 2 + textRows(summary, cols - TEXT_INDENT) : 0) +
      (r.orderNote ? 1 : 0) +
      2 + // the position line and the chunk line
      (group ? 1 : 0) + // the story heading
      (whyText !== null ? 2 + textRows(whyText, cols - TEXT_INDENT) : 0) +
      (pane.busy ? 1 : 0) +
      (draftText !== undefined ? textRows(draftText, cols - 8) : 0)
    // The frame's two border rows, and one spare row for a wrap counted short.
    const room = bodyRows - used - 3
    const bodyLines = cursorChunk && cursorChunk.body !== '' ? cursorChunk.body.split('\n').length : 0
    // A chunk that does not fit shows "lines a-b of n" on the bottom line. It
    // takes a row of its own only while the input holds the bottom.
    const size = Math.max(1, bodyLines <= room || !isTyping ? room : room - 1)
    diffRows = size
    const diff = bodyLines > 0 ? chunkWindow(cursorChunk!.body, pane.chunkOffset, size) : null
    const scrollText =
      diff && diff.total > diff.count
        ? `lines ${diff.offset + 1}-${diff.offset + diff.count} of ${diff.total} · j/k scroll`
        : null
    // Every key is a Button, so its hotkey works, in a hidden Box: a plain
    // Button draws its "n:" before any child, so a drawn one is noise. The one
    // line the reviewer sees is "press h for help", and the New commits alert.
    const keysLine = (
      <Box flexDirection="row">
        <Text dimColor>press </Text>
        <Text bold color="suggestion">h</Text>
        <Text dimColor> for help</Text>
        {r.hasNewCommits && (
          <Text bold color="inverseText" backgroundColor="warning">{' r: New commits '}</Text>
        )}
        <Box display="none">
          <Button key="toggle" label="Close the review pane" action={TOGGLE_ACTION} plain onPress={NOOP} />
          {/* The done panel draws its own approve Button with the chord. */}
          {CHORD_KEYS.filter(k => !(isDone && k.key === 'approve')).map(k => (
            <Button key={k.key} label={k.label} action={k.action} plain onPress={NOOP} />
          ))}
          {PANE_KEYS.map(k => (
            <Button
              key={k.key}
              // `r` is the one key whose label answers the state: 6.1 names
              // the new commits on the key that loads them.
              label={k.key === 'refresh' && r.hasNewCommits ? 'New commits' : k.label}
              hotkey={k.hotkey}
              plain
              onPress={NOOP}
            />
          ))}
        </Box>
      </Box>
    )
    const chunkLabel = cursorChunk
      ? `${rowMark(done, cursorChunk.id, pane.cursor)} ${rowLabel(cursorChunk, order.indexOf(cursorChunk.id) + 1)}`
      : 'No chunks'
    // No blank rows between the parts: the frames and the colours keep them
    // apart, and every row saved goes to the diff.
    return (
      <Box flexDirection="column">
        {title}
        {message}
        {summary && (
          <Box {...frame} borderColor="suggestion">
            <Box flexDirection="row" columnGap={1} alignItems="flex-start">
              {chip('Summary', 'suggestion', LABEL_WIDTH)}
              <Text>{summary}</Text>
            </Box>
          </Box>
        )}
        {r.orderNote && <Text dimColor wrap="truncate-end">{r.orderNote}</Text>}
        {isDone && (
          // Every chunk is accepted: the chunk part says so, and names the key
          // that ends the review.
          <Box {...frame} borderColor="success">
            <Text bold color="success">{`✅ All ${order.length} chunks are reviewed.`}</Text>
            <Text>{doneText(r)}</Text>
            <Text dimColor>
              {draftCount(r) > 0
                ? 'Press n or p to see a chunk again, or s to put the comments in the prompt box.'
                : 'Press n or p to see a chunk again.'}
            </Text>
            {/* The one Button the panel shows: it holds the focus that the
                chunk line held, so the pane keeps the keys. */}
            <Button
              key="approve"
              label={isOwnPr(r) ? 'Post the comments' : 'Approve PR'}
              action={APPROVE_ACTION}
              onPress={NOOP}
            />
          </Box>
        )}
        {!isDone && (
          <Box flexDirection="column">
        {/* The position line: where the cursor is and what is done. */}
        <Box flexDirection="row" columnGap={1}>
          <Text bold color="success">{`${order.indexOf(pane.cursor ?? '') + 1}/${order.length}`}</Text>
          <Text dimColor>{progressText(r)}</Text>
        </Box>
        {group && (
          <Text bold color="cyan" wrap="truncate-end">
            {group}
          </Text>
        )}
        {/* The chunk line. A Button takes no style of its own; its Text child carries it. */}
        <Box flexDirection="row">
          {cursorChunk ? (
            <Button key={`chunk:${cursorChunk.id}`} label={chunkLabel} plain onPress={NOOP}>
              <Text bold wrap="truncate-end">
                {chunkLabel}
              </Text>
            </Button>
          ) : (
            <Text dimColor>{chunkLabel}</Text>
          )}
        </Box>
        {whyText !== null && (
          // Three rows at most: the full note is in the q dialog.
          <Box {...frame} borderColor="cyan">
            <Box flexDirection="row" columnGap={1} alignItems="flex-start">
              {chip('Why', 'cyan', LABEL_WIDTH)}
              <Text>{whyText}</Text>
            </Box>
          </Box>
        )}
        {pane.busy && <Text dimColor>Thinking…</Text>}
        {draft !== undefined && (
          <Box flexDirection="row" columnGap={1} alignItems="flex-start">
            {chip('Draft', 'warning')}
            <Text>{draftText}</Text>
          </Box>
        )}
        {diff && (
          <Box {...frame} borderDimColor>
            <Code source={diff.lines.join('\n')} format="diff" wrap="truncate-end" />
          </Box>
        )}
          </Box>
        )}
        {/* At the bottom, under the diff frame, so the frame closes first. While
            an Input holds the keys no hotkey Button draws: it would take a
            letter the reviewer types. */}
        {isTyping && pane.editing && scrollText !== null && (
          <Text dimColor wrap="truncate-end">{scrollText}</Text>
        )}
        {isTyping && pane.editing ? (
          // No frame: the engine wraps the text at the pane's columns, and a
          // frame takes 4 of them, so the text would run past its edge.
          <Box flexDirection="column">
            <Input
              key={`input:${pane.editing.kind}`}
              label={inputLabel(pane.editing)}
              value={pane.editing.text}
              rows={inputHeight}
              autoFocus
              // The engine raises a change only for an Input with `onInput`:
              // the `ui.input` hook grows the box on each one.
              onInput={NOOP}
              onSubmit={NOOP}
            />
            <Text dimColor wrap="truncate-end">{inputFooter(pane.editing)}</Text>
          </Box>
        ) : (
          // One line: the scroll hint at the left, the keys at the right.
          <Box flexDirection="row" justifyContent="space-between" columnGap={2}>
            <Text dimColor wrap="truncate-end">{isDone ? '' : (scrollText ?? '')}</Text>
            {keysLine}
          </Box>
        )}
      </Box>
    )
  }).catch(($, e, next) => {
    // Spec 8: every hook has a `.catch` and writes one error line to the pane.
    const { Text } = $.ui.resolve(e)
    return <Text>code-review: the pane did not draw ({failureText(next.error)}).</Text>
  })

  on('ui.press', { component: 'Pane', requestId: PANE }, async ($, e) => {
    await act($, e.element)
    return { element: e.element }
  }).catch(async ($, e, next) => {
    await setPane($, { message: `code-review: ${failureText(next.error)}` })
    return { element: e.element }
  })

  on('ui.input', { component: 'Pane', requestId: PANE }, async ($, e) => {
    if (e.kind === 'submit') await submit($, e.value)
    else await grow($, e.value)
    return { element: e.element, value: e.value }
  }).catch(async ($, e, next) => {
    await setPane($, { message: `code-review: ${failureText(next.error)}` })
    return { element: e.element, value: e.value }
  })
}
