// Resolves once the app shell has measured fonts and started its load timeline. Pages wait
// on it so their entrance plays after the shell is visible, not behind the hidden shell.
let resolveReady: () => void = () => {}
let ready = false
let promise = new Promise<void>((resolve) => {
  resolveReady = resolve
})

// The landing → app curtain holds the shell back until it starts lifting, so the
// sidebar and first page animate in as the curtain uncovers them.
let gate: Promise<void> = Promise.resolve()

export const isAppReady = () => ready
export const whenAppReady = () => promise
export const shellGate = () => gate

export function markAppReady() {
  if (ready) return
  ready = true
  document.documentElement.classList.add('is-ready')
  resolveReady()
}

/** Re-arms readiness for the next shell mount and returns the function that releases it. */
export function holdShell(): () => void {
  ready = false
  document.documentElement.classList.remove('is-ready')
  promise = new Promise<void>((resolve) => {
    resolveReady = resolve
  })
  let release: () => void = () => {}
  gate = new Promise<void>((resolve) => {
    release = resolve
  })
  return release
}
