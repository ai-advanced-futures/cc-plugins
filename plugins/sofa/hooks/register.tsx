import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Report } from '../types'

// The names the built-in /color takes.
const COLOURS = new Set(['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan'])
const PANE = 'sofa-dashboard'
// Change the tag when Report changes: it declines what an earlier version stored.
const report = atom({ plugin: 'sofa', key: 'report' } as const, { text: '', at: '' }, { shape: 'report-1' })
// The team session name, kept from session.start for the turn.complete hook. In $.state, because a reload resets the module variables.
const session = atom({ plugin: 'sofa', key: 'session' } as const, { name: '' }, { shape: 'session-1' })

// The team prefix in section 1 of an ADLC file, or null. A Markdown formatter
// (Prettier) pads the cells of a table, so the spaces around a cell are free.
export function teamPrefix(adlc: string): string | null {
  return /^\|\s*Team prefix\s*\|\s*`([^`<>]+)`/m.exec(adlc)?.[1] ?? null
}

// One column of the roles table in an ADLC file: role name to cell value.
// Empty when the table has no such column (a file from an older template).
export function roleColumn(adlc: string, name: string): Map<string, string> {
  const values = new Map<string, string>()
  const lines = adlc.split('\n')
  const cells = (line: string) => line.split('|').slice(1, -1).map(cell => cell.trim().replaceAll('`', ''))
  // The roles table is the first table whose first column is Role and that has the column.
  const header = lines.findIndex(line => line.startsWith('|') && cells(line)[0] === 'Role' && cells(line).includes(name))
  if (header === -1) return values
  const column = cells(lines[header] ?? '').indexOf(name)
  if (column === -1) return values
  for (const line of lines.slice(header + 2)) {
    if (!line.startsWith('|')) break
    const row = cells(line)
    const role = row[0]
    const value = row[column]
    if (role !== undefined && value !== undefined) values.set(role, value)
  }
  return values
}

// The Colour column of a colour file: role name to colour, known colours only.
export function roleColours(table: string): Map<string, string> {
  return new Map([...roleColumn(table, 'Colour')].filter(([, colour]) => COLOURS.has(colour)))
}

// The colour of a role: docs/adlc/colours.md of the repository wins, then
// references/colours.md of the plugin.
export async function roleColour(fs: Fs, cwd: string, role: string, pluginRoot: string): Promise<string | null> {
  const local = `${cwd}/docs/adlc/colours.md`
  const own = (await fs.exists(local)) ? roleColours(await fs.read(local)).get(role) : undefined
  return own ?? roleColours(await fs.read(`${pluginRoot}/references/colours.md`)).get(role) ?? null
}

// The role of a session named <prefix>-<role> or <prefix>-<role>-<n>, or null.
export function roleOf(name: string, prefix: string): string | null {
  if (!name.startsWith(`${prefix}-`)) return null
  return name.slice(prefix.length + 1).replace(/-\d+$/, '') || null
}

type Fs = { exists: (path: string) => Promise<boolean>; read: (path: string) => Promise<string> }
export type Member = { role: string; colour: string | null; model: string | null }

// The team role of a session, or null for any other session. A session of
// the team has the name <prefix>-<role>[-n] and starts in the main folder,
// which holds docs/adlc.md.
export async function memberOf(fs: Fs, cwd: string, name: string, pluginRoot: string): Promise<Member | null> {
  const path = `${cwd}/docs/adlc.md`
  if (!(await fs.exists(path))) return null
  const adlc = await fs.read(path)
  const prefix = teamPrefix(adlc)
  const role = prefix === null ? null : roleOf(name, prefix)
  if (role === null) return null
  const colour = await roleColour(fs, cwd, role, pluginRoot)
  return { role, colour, model: roleColumn(adlc, 'Model').get(role) ?? null }
}

// The colour of a team session, or null for any other session.
export async function colourFor(fs: Fs, cwd: string, name: string, pluginRoot: string): Promise<string | null> {
  return (await memberOf(fs, cwd, name, pluginRoot))?.colour ?? null
}

// The sofa-state arguments that record a session start.
export function upsertArgs(name: string, id: string, member: Member): string[] {
  const args = ['session', 'upsert', '--name', name, '--id', id, '--role', member.role, '--state', 'live']
  return member.model === null ? args : [...args, '--model', member.model]
}

// The sofa-state arguments that record the colour /color set.
export function colourArgs(name: string, colour: string): string[] {
  return ['session', 'colour', '--name', name, '--colour', colour]
}

// The name of the session row with this id in the output of `sofa-state session list --json`, or ''.
// The fallback of a session that has no SOFA_SESSION_NAME in its env.
export function nameById(listJson: string, id: string): string {
  try {
    const rows: unknown = JSON.parse(listJson)
    if (!Array.isArray(rows)) return ''
    const row = rows.find((r: unknown) => typeof r === 'object' && r !== null && (r as { id?: unknown }).id === id)
    const name = (row as { name?: unknown } | undefined)?.name
    return typeof name === 'string' ? name : ''
  } catch {
    return ''
  }
}

export const register: Register = on => {
  let timer: { cancel: () => void } | undefined
  // The hooks are 'session.start' and 'turn.complete', not the classic.SessionStart and classic.Stop
  // events: a managed-settings machine (cc-plugin-sec-default) skips each classic.* hook of a plugin.
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: PANE, description: 'Show the sofa team dashboard in a pane' })
    const result = await next(e)
    const log = (error: unknown) =>
      $.ui.log(`sofa: ${error instanceof Error ? error.message : String(error)}`, { to: 'debug' })
    // dispatch.sh puts the session name in the env of --settings. A session with no name is not a team session.
    const name = await $.env.get('SOFA_SESSION_NAME').catch(() => undefined)
    if (name === undefined || name === '') return result
    const fs: Fs = { exists: path => $.fs.exists(path), read: path => $.fs.read(path) }
    const member = await memberOf(fs, e.cwd, name, $.plugin.root).catch((error: unknown) => {
      log(error)
      return null
    })
    if (member === null) {
      // A folder with docs/adlc.md and a session that is not of the team: say so, so the next fault shows.
      if (await $.fs.exists(`${e.cwd}/docs/adlc.md`).catch(() => false))
        log(new Error(`${name} is not a team session of ${e.cwd} (no team prefix, or the name does not match)`))
      return result
    }
    await update($, session, () => ({ name })).catch(log)
    const state = async (args: string[]) => {
      const run = await $.process.run([`${$.plugin.root}/scripts/sofa-state`, ...args], { cwd: e.cwd, timeoutMs: 10_000 })
      if (run.exitCode !== 0) throw new Error(`sofa-state ${args.slice(0, 2).join(' ')}: ${run.stderr.trim()}`)
    }
    const id = await $.session.id()
    // Not awaited: the run waits until the session is idle, and this hook must not.
    // The store gets the colour only when /color is done, so the orchestrator
    // sees a session that has no colour.
    const colour = member.colour
    if (colour !== null)
      $.command
        .run({ command: 'color', args: colour })
        .then(() => state(colourArgs(name, colour)))
        .catch(log)
    state(upsertArgs(name, id, member)).catch(log)
    return result
  })

  // A heartbeat at each turn end of a team session, so the dashboard and the
  // orchestrator see a live session. Only the main loop counts: a subagent turn has an agentId.
  // The name is from session.start ($.state). With no saved name (a session that has no
  // SOFA_SESSION_NAME), the name is the row of this session id in the state store.
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) return result
    const log = (error: unknown) =>
      $.ui.log(`sofa: heartbeat: ${error instanceof Error ? error.message : String(error)}`, { to: 'debug' })
    const cwd = await $.session.cwd().catch(() => undefined)
    const sofaState = `${$.plugin.root}/scripts/sofa-state`
    let { name } = await read($, session).catch(error => {
      log(error)
      return { name: '' }
    })
    if (name === '') {
      const env = await $.env.get('SOFA_SESSION_NAME').catch(() => undefined)
      if (env !== undefined && env !== '') {
        name = env
      } else {
        const id = await $.session.id().catch(() => '')
        if (id === '') return result
        const run = await $.process.run([sofaState, 'session', 'list', '--json'], { cwd, timeoutMs: 10_000 }).catch(() => undefined)
        name = run !== undefined && run.exitCode === 0 ? nameById(run.stdout, id) : ''
      }
      // No row for this id: not a team session, or the station has not written its row yet. Look again at the next turn end.
      if (name === '') return result
      const found = name
      await update($, session, () => ({ name: found })).catch(log)
    }
    // No store check: the name is set only when the store has this session
    // (sofa-state puts it in the main folder, which is not always the cwd).
    $.process
      .run([sofaState, 'session', 'heartbeat', '--name', name], { cwd, timeoutMs: 10_000 })
      .then(run => {
        if (run.exitCode !== 0) throw new Error(run.stderr.trim())
      })
      .catch(log)
    return result
  })

  on('command.run', { command: PANE }, async ($, e) => {
    const refresh = async () => {
      const run = await $.process.run([`${$.plugin.root}/scripts/sofa-state`, 'report'], { cwd: e.cwd, timeoutMs: 10_000 })
      const text = run.exitCode === 0 ? run.stdout : `sofa-state report failed: ${run.stderr.trim()}`
      await update($, report, () => ({ text, at: new Date().toISOString() }))
    }
    await refresh().catch(async (error: unknown) => {
      await update($, report, () => ({ text: `sofa-state did not run: ${String(error)}`, at: '' }))
    })
    // One timer only: a second /sofa-dashboard replaces the first timer.
    timer?.cancel()
    timer = $.clock.every(30_000, () => void refresh().catch(() => undefined))
    await $.ui.open({ id: PANE, title: 'sofa team' })
    return { text: 'sofa dashboard opened. It refreshes every 30 seconds.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const { text, at } = await read($, report)
    const room = Math.max(1, (e.viewport?.rows ?? 24) - 3)
    const lines = text === '' ? ['No state store yet. Start the team with /sofa:start.'] : text.trimEnd().split('\n')
    return (
      <Box flexDirection="column">
        {lines.slice(0, room).map(line => (
          <Text>{line}</Text>
        ))}
        {at !== '' && <Text dimColor>updated {at.slice(11, 19)} UTC</Text>}
      </Box>
    )
  })
}
