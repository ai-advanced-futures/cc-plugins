export type Report = { text: string; at: string }
// The name of this team session (<prefix>-<role>[-n]), or '' for any other session.
export type Session = { name: string }

declare module 'claude-code' {
  interface PluginState {
    sofa: { report: Shaped<Report>; session: Shaped<Session> }
  }
}
