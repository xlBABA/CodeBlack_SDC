import { flushSync } from 'react-dom'
import { STORAGE_PREFIX } from '@/config/product'
import { EASE, prefersReducedMotion } from './motion'

export type ThemePref = 'light' | 'dark' | 'system'
export type Theme = 'light' | 'dark'
export const ACCENTS = ['teal', 'emerald', 'indigo', 'tomato'] as const
export type Accent = (typeof ACCENTS)[number]

const THEME_KEY = `${STORAGE_PREFIX}:theme`
const ACCENT_KEY = `${STORAGE_PREFIX}:accent`
const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
const listeners = new Set<() => void>()

function read<T extends string>(key: string, fallback: T, allowed: readonly T[]): T {
  try {
    const v = JSON.parse(localStorage.getItem(key) ?? JSON.stringify(fallback))
    return allowed.includes(v) ? v : fallback
  } catch {
    return fallback
  }
}
function write(key: string, value: string) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // private mode: the change still applies for this visit
  }
}

export const getPref = () => read<ThemePref>(THEME_KEY, 'system', ['light', 'dark', 'system'])
export const resolve = (pref = getPref()): Theme => (pref === 'system' ? (systemDark.matches ? 'dark' : 'light') : pref)
export const currentTheme = (): Theme => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light')
export const currentAccent = (): Accent => ACCENTS.find((a) => a === document.documentElement.dataset.accent) ?? 'teal'

export function subscribe(fn: () => void) {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

/** Browser bar colour follows whatever --bg the current theme resolves to. */
export function syncThemeColor() {
  const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()
  if (bg) document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.setAttribute('content', bg)
}

function notify() {
  listeners.forEach((fn) => fn())
}

let fadeTimer = 0
/** Fallback where View Transitions are missing: colours cross-fade for .4s. */
function crossFade(change: () => void) {
  const html = document.documentElement
  html.classList.add('theming')
  clearTimeout(fadeTimer)
  fadeTimer = window.setTimeout(() => html.classList.remove('theming'), 450)
  change()
}

/**
 * Applies a colour change. With an origin element the new colours are revealed by a circle
 * growing out of it (View Transitions, 520 ms, cubic-bezier(.6,0,.2,1));
 * without View Transitions it cross-fades; under reduced motion it swaps instantly.
 */
function transition(change: () => void, origin?: Element | null) {
  const run = () => {
    change()
    syncThemeColor()
    notify()
  }
  if (prefersReducedMotion()) return run()
  if (!origin || !document.startViewTransition) return crossFade(run)

  const r = origin.getBoundingClientRect()
  const x = r.left + r.width / 2
  const y = r.top + r.height / 2
  const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
  // flushSync so React state that depends on the theme (knob, icons) is in the new snapshot
  document
    .startViewTransition(() => flushSync(run))
    .ready.then(() => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        { duration: 520, easing: EASE.wipe, pseudoElement: '::view-transition-new(root)' },
      )
    })
    .catch(() => {})
}

function applyTheme() {
  document.documentElement.dataset.theme = resolve()
}

systemDark.addEventListener('change', () => {
  if (getPref() === 'system') transition(applyTheme)
})

export function setTheme(pref: ThemePref, origin?: Element | null) {
  write(THEME_KEY, pref)
  if (resolve(pref) === currentTheme()) {
    notify()
    return
  }
  transition(applyTheme, origin)
}

/** Halden-style accent: only the accent tokens change, revealed with the same wipe. */
export function setAccent(accent: Accent, origin?: Element | null) {
  write(ACCENT_KEY, accent)
  if (accent === currentAccent()) return
  transition(() => {
    if (accent === 'teal') delete document.documentElement.dataset.accent
    else document.documentElement.dataset.accent = accent
  }, origin)
}
