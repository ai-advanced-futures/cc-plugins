import { expect, test } from 'claude-code/testing'

// The mod runs on session.start and turn.complete, not on classic.SessionStart and classic.Stop:
// a machine with managed settings skips each classic.* hook of a plugin (cc-plugin-sec-default).
const NAME = 'clc-implementer-1'
const ADLC = ['| Team prefix | `clc` |', '', '| Role | Model |', '| --- | --- |', '| implementer | claude-sonnet-5-5 |'].join('\n')

function stand($: any, on: any, env: Record<string, string>, calls: string[][]) {
  on('command.register', () => ({ value: { command: 'sofa-dashboard' } }))
  on('session.start', (_: unknown, e: { cwd: string }) => ({ cwd: e.cwd }))
  on('turn.complete', () => ({ text: '' }))
  on('env.get', (_: unknown, e: { name: string }) => ({ value: env[e.name] }))
  on('session.id', () => ({ value: 'sid-1' }))
  on('session.cwd', () => ({ value: '/main' }))
  on('fs.exists', () => ({ value: true }))
  on('fs.read', (_: unknown, e: { path: string }) => ({ value: e.path.endsWith('adlc.md') ? ADLC : '| Role | Colour |\n| --- | --- |\n| implementer | green |' }))
  on('command.run', () => ({ value: { text: '' } }))
  on('ui.log', () => ({ value: undefined }))
  on('process.run', (_: unknown, e: { argv: string[] }) => {
    calls.push(e.argv.slice(1))
    return { value: { exitCode: 0, stdout: JSON.stringify([{ name: NAME, id: 'sid-1' }]), stderr: '' } }
  })
}

test('session.start with SOFA_SESSION_NAME upserts the session; turn.complete sends the heartbeat', async ($, on) => {
  const calls: string[][] = []
  stand($, on, { SOFA_SESSION_NAME: NAME }, calls)
  await $.session.start({ cwd: '/main', surface: null, isInteractive: false })
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })
  expect(calls.some(c => c[0] === 'session' && c[1] === 'upsert' && c.includes(NAME) && c.includes('sid-1'))).toBe(true)
  expect(calls.some(c => c[0] === 'session' && c[1] === 'heartbeat' && c.includes(NAME))).toBe(true)
})

test('turn.complete of a subagent sends no heartbeat', async ($, on) => {
  const calls: string[][] = []
  stand($, on, { SOFA_SESSION_NAME: NAME }, calls)
  await $.session.start({ cwd: '/main', surface: null, isInteractive: false })
  calls.length = 0
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't2', agentId: 'a1', reason: 'answer' })
  expect(calls.filter(c => c[1] === 'heartbeat')).toEqual([])
})

test('without SOFA_SESSION_NAME the name comes from session list --json by session id', async ($, on) => {
  const calls: string[][] = []
  stand($, on, {}, calls)
  await $.session.start({ cwd: '/main', surface: null, isInteractive: false })
  expect(calls).toEqual([])
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't3', reason: 'answer' })
  expect(calls.some(c => c[1] === 'list')).toBe(true)
  expect(calls.some(c => c[1] === 'heartbeat' && c.includes(NAME))).toBe(true)
})
