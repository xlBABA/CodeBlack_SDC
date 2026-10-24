import { useRef } from 'react'
import { Check } from 'lucide-react'
import { BrandMark } from '@/components/brand'
import { CINEMA } from '@/content/landing'
import { useMediaQuery } from '@/hooks/use-media-query'
import { gsap, REDUCED_MOTION, useGSAP } from '@/lib/gsap'
import { canHover } from '@/lib/motion'
import { HeroCtas } from './hero-ctas'
// where each badge flies in from, and its resting tilt (Mango "cinema" idea)
const FROM = [
  { x: 150, y: 100, r: -2.5 },
  { x: -150, y: 100, r: 2.5 },
  { x: 170, y: -20, r: -1.5 },
  { x: -170, y: -20, r: 1.5 },
]
const SPOTS = ['top-[6%] left-1/2 -translate-x-1/2', 'top-1/2 right-[-6%] -translate-y-1/2', 'bottom-[6%] left-1/2 -translate-x-1/2', 'top-1/2 left-[-6%] -translate-y-1/2']

function Report() {
  const rows: [string, number][] = [['Data analyst', 76], ['Financial analyst', 65], ['Sustainability coordinator', 59], ['Mechanical design engineer', 40]]
  return (
    <div className="glass w-[min(420px,86vw)] rounded-card bg-raised p-6 shadow-pop">
      <p className="text-sm font-semibold text-muted-foreground">Demo student · sample report</p>
      <p className="mt-1 text-2xl font-extrabold tracking-[-0.03em]">{CINEMA.title}</p>
      <ul className="mt-4 grid gap-3">
        {rows.map(([t, n]) => (
          <li key={t}>
            <div className="flex justify-between text-sm font-semibold">
              <span>{t}</span>
              <span>
                {n} <small className="font-medium text-muted-foreground">alignment estimate</small>
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-well">
              <i className="block h-full rounded-full bg-primary" style={{ width: `${n}%` }} />
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-muted-foreground">Estimates use self-rated skills. Treat them as a starting point.</p>
    </div>
  )
}

function Offer({ className }: { className?: string }) {
  return (
    <div data-offer className={className}>
      <ul className="grid gap-3">
        {CINEMA.offer.map((o) => (
          <li key={o} data-offer-item className="flex items-center gap-3 text-xl font-bold tracking-[-0.015em]">
            <span className="grid size-8 flex-none place-items-center rounded-full bg-primary text-primary-foreground" aria-hidden>
              <Check className="size-4" />
            </span>
            {o}
          </li>
        ))}
      </ul>
      <div data-offer-item className="mt-7">
        <HeroCtas size="default" />
      </div>
    </div>
  )
}

/**
 * Pinned "cinema" (Mango technique, our content): role badges fly in around the mark and the
 * ring turns, the mark bursts, the sample report cuts in, then the offer list arrives: beside
 * the report on wide screens, in its place on narrow ones. Only reduced motion gets the
 * report and list stacked, with no pinning.
 */
export function Cinema() {
  const reduced = useMediaQuery(REDUCED_MOTION)
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (reduced) return
      const mm = gsap.matchMedia(root.current!)
      mm.add({ wide: '(min-width: 960px)', narrow: 'not all and (min-width: 960px)' }, (ctx) => {
        const aside = ctx.conditions?.wide ? { x: () => -0.17 * innerWidth, scale: 0.94 } : { y: -40, scale: 0.9, opacity: 0 }
        const badges = gsap.utils.toArray<HTMLElement>('[data-badge]')
        const items = gsap.utils.toArray<HTMLElement>('[data-offer-item]')
        gsap.set('[data-cut]', { opacity: 0, scale: 0.5, rotation: -18 })
        gsap.set('[data-burst]', { scale: 0, opacity: 0 })
        badges.forEach((b, i) => gsap.set(b, { opacity: 0, scale: 0.5, x: FROM[i].x, y: FROM[i].y, rotation: FROM[i].r }))
        gsap.set(items, { opacity: 0, x: -36 })
        gsap.set('[data-offer]', { opacity: 0 })

        const tl = gsap.timeline({
          defaults: { ease: 'none' },
          scrollTrigger: { trigger: root.current, start: 'top top', end: '+=240%', pin: true, scrub: 1.6, anticipatePin: 1, invalidateOnRefresh: true },
        })
        tl.fromTo('[data-whole]', { scale: 0.96, rotation: -3 }, { scale: 1.04, rotation: 3, duration: 1.6 }, 0)
          .to('[data-intro]', { opacity: 0, y: -30, duration: 0.25, ease: 'power2.in' }, 0.35)
        badges.forEach((b, i) => {
          tl.to(b, { opacity: 1, scale: 1, x: 0, y: 0, duration: 0.5, ease: 'back.out(1.5)' }, 0.45 + i * 0.09)
          tl.to(b, { rotation: FROM[i].r - 24, duration: 0.75 }, 0.95)
        })
        tl.to('[data-ring]', { rotation: 24, duration: 0.75 }, 0.95)
          .to(badges, { opacity: 0, y: -30, duration: 0.3, stagger: 0.04, ease: 'power2.in' }, 1.55)
          .to('[data-ring]', { opacity: 0, scale: 1.08, duration: 0.35, ease: 'power2.in' }, 1.6)
          .to('[data-whole]', { scale: 1.3, rotation: 16, opacity: 0, duration: 0.4, ease: 'power2.in' }, 1.75)
          .to('[data-burst]', { scale: 1.5, opacity: 0.7, duration: 0.25, ease: 'power1.out' }, 2.05)
          .to('[data-burst]', { scale: 2.3, opacity: 0, duration: 0.4 }, 2.3)
          .to('[data-cut]', { opacity: 1, scale: 1.12, rotation: 5, duration: 0.45, ease: 'power2.out' }, 2.1)
          .to('[data-cut]', { scale: 1, rotation: 0, duration: 0.3 }, 2.55)
          .to({}, { duration: 0.25 })
          .to('[data-cut]', { ...aside, duration: 0.6, ease: 'power2.inOut' }, 2.9)
          .to('[data-offer]', { opacity: 1, duration: 0.2 }, 3.05)
          .to(items, { opacity: 1, x: 0, duration: 0.45, stagger: 0.09, ease: 'power2.out' }, 3.1)
          .to({}, { duration: 0.5 })

        // the mark leans toward the pointer while it is on stage
        if (canHover()) {
          const mx = gsap.quickTo('[data-lean]', 'x', { duration: 0.6, ease: 'power3.out' })
          const my = gsap.quickTo('[data-lean]', 'y', { duration: 0.6, ease: 'power3.out' })
          const move = (e: PointerEvent) => {
            mx((e.clientX / innerWidth - 0.5) * 24)
            my((e.clientY / innerHeight - 0.5) * 16)
          }
          root.current!.addEventListener('pointermove', move)
          return () => root.current?.removeEventListener('pointermove', move)
        }
      })
      return () => mm.revert()
    },
    { scope: root, dependencies: [reduced], revertOnUpdate: true },
  )

  if (reduced) {
    return (
      <section ref={root} id="report" aria-labelledby="report-title" className="grid gap-8 px-[var(--gutter)] py-20">
        <h2 id="report-title" className="text-[clamp(2.2rem,1.4rem+3vw,3.6rem)] leading-[1.02] font-extrabold tracking-[-0.04em]">
          {CINEMA.intro}
        </h2>
        <div>
          <Report />
        </div>
        <div>
          <Offer />
        </div>
      </section>
    )
  }

  return (
    <section ref={root} id="report" aria-labelledby="report-title" className="relative h-svh overflow-hidden">
      <h2 id="report-title" data-intro className="absolute top-[13%] left-1/2 w-full -translate-x-1/2 px-[var(--gutter)] text-center text-[clamp(2.2rem,1.2rem+3vw,4.4rem)] leading-none font-extrabold tracking-[-0.045em]">
        {CINEMA.intro}
      </h2>
      <div className="absolute top-[56%] left-1/2 size-[min(540px,62svh,88vw)] -translate-x-1/2 -translate-y-1/2">
        <div data-ring className="absolute inset-0 z-[2] rounded-full border-2 border-dashed border-line-2">
          {CINEMA.badges.map((b, i) => (
            <span key={b} className={`absolute ${SPOTS[i]}`}>
              <span data-badge className="glass inline-block rounded-full px-4 py-2 font-bold whitespace-nowrap shadow-pop max-sm:px-3 max-sm:py-1.5 max-sm:text-sm">
                {b}
              </span>
            </span>
          ))}
        </div>
        <div data-whole className="absolute inset-[22%] z-[1] grid place-items-center">
          <div data-lean className="relative">
            <span aria-hidden className="absolute inset-[-35%] rounded-full bg-[radial-gradient(closest-side,color-mix(in_srgb,var(--primary)_45%,transparent),transparent)] blur-2xl" />
            <BrandMark className="relative size-[clamp(140px,18vh,220px)] drop-shadow-[0_30px_50px_#0006]" />
          </div>
        </div>
        <span data-burst aria-hidden className="absolute inset-[18%] rounded-full bg-[radial-gradient(closest-side,var(--butter),transparent)]" />
      </div>
      {/* centring lives on the wrapper: GSAP owns the inner element's transform */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <div data-cut>
          <Report />
        </div>
      </div>
      <Offer className="absolute top-1/2 left-1/2 w-[min(440px,86vw)] -translate-x-1/2 -translate-y-1/2 min-[960px]:right-[max(var(--gutter),6vw)] min-[960px]:left-auto min-[960px]:w-[min(440px,38vw)] min-[960px]:translate-x-0" />
    </section>
  )
}
