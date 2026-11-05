// One `@@` hunk, or one file that has no hunk (binary, a pure rename).
export type Chunk = {
  id: string
  path: string
  // The `@@ -a,b +c,d @@` line; empty for a file with no hunk.
  header: string
  // The header line and the hunk under it; empty for a file with no hunk.
  body: string
  oldStart: number
  oldLines: number
  newStart: number
  newLines: number
  kind: 'hunk' | 'empty'
  // The added and removed line counts, taken while the parser walks the hunk.
  // The row label reads them, so no view code walks the body a second time.
  added: number
  removed: number
  // A reload replaced this chunk after it was accepted.
  isChanged: boolean
}

// What the store keeps of a chunk: everything the reload merge reads, with no
// diff body, so one PR's entry stays far under the 4 MiB store. The body comes
// back from `gh pr diff` on every load.
export type SavedChunk = Omit<Chunk, 'body'>

export type Group = { label: string; chunkIds: string[] }

// One drawn row of the chunk list. `index` numbers chunks only, from 1.
export type Row =
  | { kind: 'heading'; key: string; label: string }
  | { kind: 'chunk'; key: string; id: string; index: number }

export type Thread = { question: string; answer: string }

// A draft whose chunk left the diff: it posts as text in the review body.
export type Orphan = { path: string; header: string; text: string }

export type Pr = {
  number: number
  title: string
  body: string
  author: string
  headRefOid: string
  url: string
  owner: string
  repo: string
}

// What `$.store` holds under `pr:<owner>/<repo>#<n>`.
export type Saved = Pick<
  Review,
  'groups' | 'summary' | 'notes' | 'accepted' | 'threads' | 'drafts' | 'orphanDrafts' | 'reviewedHead'
> & {
  // The reload merge needs the chunks of the reviewed head, not only their ids.
  chunks: SavedChunk[]
  savedAt: number
}

export type Review = {
  pr: Pr
  // The reviewer's own gh login.
  login: string
  // The raw `gh pr diff` text a question is asked over, kept as `gh` returned
  // it. `Saved` picks its fields by name, so this never reaches the store.
  diff: string
  chunks: Chunk[]
  groups: Group[]
  summary: string | null
  // Why the story order is off; null when the model gave the order.
  orderNote: string | null
  notes: Record<string, string>
  accepted: string[]
  threads: Record<string, Thread[]>
  drafts: Record<string, string>
  orphanDrafts: Orphan[]
  reviewedHead: string
  hasNewCommits: boolean
}

// Which Input shows and what it holds. `id` is a chunk id.
export type Editing = {
  kind: 'comment' | 'question'
  id: string
  text: string
  isEdit: boolean
  // The text typed so far: the draw counts the box's rows from it.
  typed: string
}

export type Pane = {
  // What the command was given: a PR number, a url, or '' for the branch.
  // The Try again button loads it again.
  ref: string
  status: 'loading' | 'ready' | 'failed'
  cursor: string | null
  // The first diff line the open chunk shows; a cursor move sets it to 0.
  chunkOffset: number
  // True when `a` accepted the last open chunk: the pane then shows the "all
  // chunks are reviewed" panel in place of the chunk. A move turns it off.
  isDone: boolean
  editing: Editing | null
  // The chunk id whose question or explain call runs.
  busy: string | null
  // One line: a `gh` error, or the posted review URL.
  message: string | null
  isPosted: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'code-review': {
      review: Review | null
      pane: Pane | null
      // True while the review pane is open. The band draws the Ctrl+X P
      // Button only while it is false: a band control is the first stop of
      // Ctrl+X Tab, so it would take a press from the way to the pane.
      isUp: boolean
    }
  }
}
