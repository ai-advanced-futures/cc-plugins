import type { Chunk } from '../types'

const FILE = /^diff --git a\/(.+?) b\/(.+)$/
// Git quotes a path that holds a `"`, a `\\`, a control character or a byte
// over 0x7f, and writes those as C escapes and octal bytes.
const QUOTED_FILE = /^diff --git (?:"a\/(?:[^"\\]|\\.)*"|a\/\S+) "b\/((?:[^"\\]|\\.)*)"$/
const ESCAPES: Record<string, string> = { a: '\x07', b: '\b', t: '\t', n: '\n', v: '\v', f: '\f', r: '\r' }

// The path inside git's quotes. A run of octal bytes is UTF-8: it is decoded
// with `decodeURIComponent`, as the module has no TextDecoder.
export function unquotePath(text: string): string {
  let out = ''
  let bytes = ''
  const flush = () => {
    if (!bytes) return
    try {
      out += decodeURIComponent(bytes)
    } catch {
      out += bytes
    }
    bytes = ''
  }
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]!
    const octal = ch === '\\' ? /^[0-7]{3}/.exec(text.slice(i + 1)) : null
    if (octal) {
      bytes += `%${parseInt(octal[0], 8).toString(16).padStart(2, '0')}`
      i += 3
      continue
    }
    flush()
    if (ch !== '\\') {
      out += ch
      continue
    }
    const next = text[i + 1] ?? ''
    out += ESCAPES[next] ?? next
    i += 1
  }
  flush()
  return out
}

function filePath(line: string): string | null {
  const quoted = QUOTED_FILE.exec(line)
  if (quoted) return unquotePath(quoted[1]!)
  return FILE.exec(line)?.[2] ?? null
}

const HUNK = /^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/

// FNV-1a over the path and the hunk text: a stable id with no async hash, so
// the parser stays a set of pure synchronous functions.
export function chunkId(path: string, text: string): string {
  let h = 0x811c9dc5
  for (const ch of `${path} ${text}`) {
    h ^= ch.codePointAt(0) ?? 0
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h.toString(16).padStart(8, '0')
}

export function parseDiff(text: string): Chunk[] {
  const out: Chunk[] = []
  let path = ''
  let hunks = 0
  let open: { header: string; lines: string[]; m: RegExpExecArray } | null = null

  const closeHunk = () => {
    if (!open || !path) {
      open = null
      return
    }
    // A trailing blank line is the split of the final newline: drop it, so the
    // id does not change with the last newline.
    const lines = [...open.lines]
    while (lines.length > 0 && lines[lines.length - 1] === '') lines.pop()
    const body = [open.header, ...lines].join('\n')
    out.push({
      id: chunkId(path, body),
      path,
      header: open.header,
      body,
      oldStart: Number(open.m[1]),
      oldLines: open.m[2] === undefined ? 1 : Number(open.m[2]),
      newStart: Number(open.m[3]),
      newLines: open.m[4] === undefined ? 1 : Number(open.m[4]),
      kind: 'hunk',
      added: lines.filter(l => l.startsWith('+')).length,
      removed: lines.filter(l => l.startsWith('-')).length,
      isChanged: false,
    })
    open = null
  }

  const closeFile = () => {
    closeHunk()
    if (path && hunks === 0) {
      out.push({
        id: chunkId(path, ''),
        path,
        header: '',
        body: '',
        oldStart: 0,
        oldLines: 0,
        newStart: 0,
        newLines: 0,
        kind: 'empty',
        added: 0,
        removed: 0,
        isChanged: false,
      })
    }
  }

  for (const line of text.split('\n')) {
    const file = filePath(line)
    if (file) {
      closeFile()
      path = file
      hunks = 0
      continue
    }
    const hunk = HUNK.exec(line)
    if (hunk) {
      closeHunk()
      open = { header: line, lines: [], m: hunk }
      hunks += 1
      continue
    }
    if (open) open.lines.push(line)
  }
  closeFile()
  return out
}

// What a GitHub review comment needs to attach to this chunk, in TypeScript
// names; `reviewBody` maps them to the API's `start_line` and `line`.
export type CommentRange = {
  path: string
  side: 'RIGHT' | 'LEFT'
  line: number
  startLine?: number
}

// Null means no comment can attach: a file with no hunk, or a hunk that only
// holds context. Such a draft posts as text in the review body instead.
export function commentRange(chunk: Chunk): CommentRange | null {
  if (chunk.kind === 'empty') return null
  const added: number[] = []
  const removed: number[] = []
  let newAt = chunk.newStart
  let oldAt = chunk.oldStart
  for (const line of chunk.body.split('\n').slice(1)) {
    if (line.startsWith('\\')) continue
    if (line.startsWith('+')) {
      added.push(newAt)
      newAt += 1
      continue
    }
    if (line.startsWith('-')) {
      removed.push(oldAt)
      oldAt += 1
      continue
    }
    newAt += 1
    oldAt += 1
  }
  const side = added.length > 0 ? 'RIGHT' : 'LEFT'
  const nums = added.length > 0 ? added : removed
  const first = nums[0]
  const last = nums[nums.length - 1]
  if (first === undefined || last === undefined) return null
  return first === last
    ? { path: chunk.path, side, line: last }
    : { path: chunk.path, side, line: last, startLine: first }
}

// The part of a chunk the overlap reads. The reload merge compares a saved
// chunk, which has no diff body, against a chunk fresh from `gh pr diff`.
export type Span = Pick<Chunk, 'path' | 'oldStart' | 'oldLines'>

// How many old-file lines the two chunks share. 0 for other files, so the
// reload merge never pairs chunks across files.
export function overlap(a: Span, b: Span): number {
  if (a.path !== b.path) return 0
  const start = Math.max(a.oldStart, b.oldStart)
  const end = Math.min(a.oldStart + a.oldLines, b.oldStart + b.oldLines)
  return Math.max(0, end - start)
}
