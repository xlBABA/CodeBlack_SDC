import { gsap, REDUCED_MOTION } from './gsap'

// App motion vocabulary. Page entrances follow the Mender reference (title letters and
// panels on expo.out).
//
// Pages mark elements declaratively and enterPage()/revealNew() animate them:
//   data-page-title        h1 rendered by <CharText>, letters rise and fade in (.7s, stagger .018)
//   data-enter="head"      crumbs / subtitle            (y 8)
//   data-enter="action"    header buttons and stats     (y 14, stagger .07)
//   data-enter="card"      panels                       (y 26, scale .985, .75s expo.out)
//   data-enter="item"      rows and list items          (y 10, stagger .03)
//   data-enter="pop"       pills and badges             (scale .7 → 1, back.out(3))
//   data-enter="bar"       horizontal bars              (scaleX 0 → 1)
//   data-enter="ring"      SVG arcs: data-ring-c (circumference), data-ring-p (0..1)
//   data-count="123"       numbers count up; data-format picks the formatter

const reducedMq = window.matchMedia(REDUCED_MOTION)
const hoverMq = window.matchMedia('(hover: hover) and (pointer: fine)')

export const prefersReducedMotion = () => reducedMq.matches
export const canHover = () => hoverMq.matches

/** Every duration goes through this so reduced motion collapses it to zero. */
export const dur = (seconds: number) => (reducedMq.matches ? 0 : seconds)

export const EASE = {
  out: 'power3.out',
  inOut: 'power3.inOut',
  in: 'power2.in',
  title: 'expo.out',
  panel: 'expo.out',
  pop: 'back.out(3)',
  toast: 'back.out(1.8)',
  pill: 'back.out(1.25)',
  wipe: 'cubic-bezier(.6,0,.2,1)',
} as const

const ENTERED = 'data-entered'

type Targets = HTMLElement[]

function fresh(root: ParentNode, selector: string): Targets {
  const found = Array.from(root.querySelectorAll<HTMLElement>(selector)).filter((el) => !el.hasAttribute(ENTERED))
  found.forEach((el) => el.setAttribute(ENTERED, ''))
  return found
}

export function revealChars(title: Element, delay = 0) {
  const chars = title.querySelectorAll('.split-ch')
  if (!chars.length) return gsap.timeline()
  return gsap.fromTo(
    chars,
    { yPercent: 110, opacity: 0 },
    { yPercent: 0, opacity: 1, duration: dur(0.7), ease: EASE.title, stagger: dur(0.018), delay: dur(delay), clearProps: 'transform,opacity' },
  )
}

export function rise(targets: Targets, { x = 0, y = 12, stagger = 0.045, delay = 0 } = {}) {
  if (!targets.length) return gsap.timeline()
  return gsap.fromTo(
    targets,
    { opacity: 0, x, y },
    { opacity: 1, x: 0, y: 0, duration: dur(0.55), ease: EASE.out, stagger: dur(stagger), delay: dur(delay), clearProps: 'transform,opacity' },
  )
}

export function riseCards(targets: Targets, { y = 26, stagger = 0.07, delay = 0 } = {}) {
  if (!targets.length) return gsap.timeline()
  return gsap.fromTo(
    targets,
    { opacity: 0, y, scale: 0.985 },
    { opacity: 1, y: 0, scale: 1, duration: dur(0.75), ease: EASE.panel, stagger: dur(stagger), delay: dur(delay), clearProps: 'transform,opacity' },
  )
}

export function pop(targets: Targets, { from = 0.7, stagger = 0.02, delay = 0 } = {}) {
  if (!targets.length || prefersReducedMotion()) return gsap.timeline()
  return gsap.fromTo(
    targets,
    { scale: from, opacity: 0 },
    { scale: 1, opacity: 1, duration: 0.6, ease: EASE.pop, stagger, delay, overwrite: 'auto', clearProps: 'transform,opacity' },
  )
}

export function growBars(targets: Targets, delay = 0) {
  if (!targets.length) return gsap.timeline()
  return gsap.fromTo(
    targets,
    { scaleX: 0 },
    // bars that grow leftwards set their own transform-origin inline
    { scaleX: 1, transformOrigin: (_: number, el: HTMLElement) => el.style.transformOrigin || '0 50%', duration: dur(0.8), ease: EASE.out, stagger: dur(0.08), delay: dur(delay), clearProps: 'transform' },
  )
}

export function drawRings(targets: Targets, delay = 0) {
  const tl = gsap.timeline({ delay: dur(delay) })
  targets.forEach((el) => {
    const c = Number(el.dataset.ringC)
    const p = Number(el.dataset.ringP)
    tl.fromTo(el, { attr: { 'stroke-dashoffset': c } }, { attr: { 'stroke-dashoffset': c * (1 - p) }, duration: dur(1.3), ease: EASE.inOut }, 0)
  })
  return tl
}

// Formatters for data-count. Add one here rather than formatting inside a page.
export const COUNT_FORMATS = {
  int: (v: number) => Math.round(v).toLocaleString('en-MY'),
  percent: (v: number) => `${Math.round(v)}%`,
  hours: (v: number) => `${Math.round(v)} h`,
  decimal: (v: number) => v.toFixed(1),
} satisfies Record<string, (v: number) => string>

export type CountFormat = keyof typeof COUNT_FORMATS

export function countUp(targets: Targets, delay = 0) {
  targets.forEach((el, i) => {
    const to = Number(el.dataset.count)
    const format = COUNT_FORMATS[(el.dataset.format as CountFormat) ?? 'int'] ?? COUNT_FORMATS.int
    if (prefersReducedMotion() || !Number.isFinite(to)) {
      el.textContent = format(to)
      return
    }
    const state = { v: 0 }
    el.textContent = format(0)
    gsap.to(state, {
      v: to,
      duration: 1.4,
      delay: delay + i * 0.06,
      ease: EASE.out,
      onUpdate: () => {
        el.textContent = format(state.v)
      },
      onComplete: () => {
        el.textContent = format(to)
      },
    })
  })
}

/** First paint of a page: header, then cards, then everything inside them. */
export function enterPage(root: HTMLElement) {
  const tl = gsap.timeline()
  const title = root.querySelector('[data-page-title]')
  if (title && !title.hasAttribute(ENTERED)) {
    title.setAttribute(ENTERED, '')
    tl.add(revealChars(title), 0)
  }
  tl.add(rise(fresh(root, '[data-enter="head"]'), { y: 8 }), 0)
  tl.add(rise(fresh(root, '[data-enter="action"]'), { y: 14, stagger: 0.07 }), 0.12)
  tl.add(riseCards(fresh(root, '[data-enter="card"]'), { stagger: 0.07 }), 0.06)
  tl.add(rise(fresh(root, '[data-enter="item"]'), { y: 10, stagger: 0.03 }), 0.45)
  tl.add(pop(fresh(root, '[data-enter="pop"]'), { stagger: 0.02 }), 0.5)
  tl.add(growBars(fresh(root, '[data-enter="bar"]')), 0.35)
  tl.add(drawRings(fresh(root, '[data-enter="ring"]')), 0.3)
  // not on the timeline: countUp zeroes the text right away so the final value never flashes
  countUp(fresh(root, '[data-count]'), 0.35)
  return tl
}

/** Content that appears later (data arriving, a tab switching) gets a shorter version. */
export function revealNew(root: HTMLElement) {
  riseCards(fresh(root, '[data-enter="card"]'), { y: 20, stagger: 0.05 })
  rise(fresh(root, '[data-enter="head"], [data-enter="action"]'), { y: 8 })
  rise(fresh(root, '[data-enter="item"]'), { y: 10, stagger: 0.03, delay: 0.1 })
  pop(fresh(root, '[data-enter="pop"]'), { delay: 0.15 })
  growBars(fresh(root, '[data-enter="bar"]'), 0.1)
  drawRings(fresh(root, '[data-enter="ring"]'), 0.1)
  countUp(fresh(root, '[data-count]'), 0.1)
}

/** Clears the markers so a reverted context (StrictMode, HMR) can animate again. */
export function resetEntered(root: HTMLElement) {
  root.querySelectorAll(`[${ENTERED}]`).forEach((el) => el.removeAttribute(ENTERED))
}

/** Icon "press" feedback on click. */
export function pressPop(el: Element) {
  if (prefersReducedMotion()) return
  const target = el.querySelector('svg') ?? el
  gsap.fromTo(target, { scale: 0.72 }, { scale: 1, duration: 0.55, ease: EASE.pop, overwrite: true })
}

/** A value just changed: nudge it and flash it coral. */
export function flashValue(el: HTMLElement) {
  el.classList.remove('is-flash')
  void el.offsetWidth
  el.classList.add('is-flash')
  if (prefersReducedMotion()) return
  gsap.fromTo(el, { y: -4, scale: 1.06 }, { y: 0, scale: 1, duration: 0.55, ease: 'back.out(2.4)', overwrite: 'auto', clearProps: 'transform' })
}
