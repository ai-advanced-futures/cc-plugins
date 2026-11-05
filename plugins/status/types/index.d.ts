export type Ttl = '5m' | '1h'

// One rate-limit window: percent used, and when it resets (epoch seconds).
export type Window = { used: number; resetsAt: number }

export type RateLimits = { seven_day?: Window }

export type Cache = {
  // The lifetime the ttl option sets, or the one the mod learned.
  fixed?: Ttl
  learned?: Ttl
  // The end of the last main request (ms), and its cache hit percent.
  lastAt?: number
  hit?: number
  // True on a Claude subscription within its plan usage. There the main
  // conversation gets the 1h lifetime; on usage credits or an API key, 5m.
  plan?: boolean
}

// All the status bar draws from, read once per refresh.
export type Bar = {
  now: number
  model: string
  contextWindow: number
  contextPercent: number
  contextTokens?: number
  rateLimits: RateLimits
  cwd: string
  worktree: string
  branch: string
  cache: Cache
  // The API's model id of the last request, kept so a reload of the mod has it.
  apiModel?: string
}

declare module 'claude-code' {
  interface PluginState {
    status: { bar: Bar | null }
  }
}
