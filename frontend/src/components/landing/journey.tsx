import { useRef } from 'react'
import { JOURNEY } from '@/content/landing'
import { useMediaQuery } from '@/hooks/use-media-query'
import { gsap, ScrollTrigger, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { JourneyArt } from './journey-art'

const PINNED = '(min-width: 960px) and (min-height: 600px) and (prefers-reduced-motion: no-preference)'

function Panel({ i }: { i: number }) {
  const s = JOURNEY[i]
  return (
    <article data-panel className="glass relative grid h-full w-[min(80vw,1020px)] flex-none grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] items-center gap-10 overflow-hidden rounded-card p-10">
      <span data-ghost aria-hidden className="pointer-events-none absolute -right-6 -bottom-16 text-[18rem] leading-none font-extrabold tracking-[-0.06em] text-foreground opacity-[0.04]">
        0{i + 1}
      </span>
      <div className="relative">
        <span data-circle className="grid size-16 place-items-center rounded-full bg-primary font-mono text-lg font-bold text-primary-foreground">
          0{i + 1}
        </span>
        <h3 className="mt-6 overflow-hidden text-[clamp(2.2rem,1.4rem+2vw,3.6rem)] leading-[1.02] font-extrabold tracking-[-0.04em]">
          {Array.from(s.title).map((ch, k) => (
            <span key={k} data-ch className="inline-block whitespace-pre">
              {ch}
            </span>
          ))}
        </h3>
        <p data-note className="mt-4 max-w-[36ch] text-lg text-muted-foreground">
          {s.body}
        </p>
      </div>
      <div data-photo className="relative rounded-tile bg-solid p-5 shadow-card">
        <div data-par>
          <JourneyArt kind={s.kind} />
        </div>
      </div>
    </article>
  )
}

/**
 * Five steps on a horizontal track. Wide screens pin the section and scroll it sideways
 * (Lando/Mango technique): each panel's parts enter as it slides in (containerAnimation)
 * and its art drifts against the track. Phones get a light vertical list.
 */
export function Journey() {
  const pinned = useMediaQuery(PINNED)
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      if (!pinned) {
        ScrollTrigger.batch('[data-m-step]', {
          start: 'top 86%',
          once: true,
          onEnter: (els) => gsap.fromTo(els, { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, stagger: 0.08, ease: 'expo.out' }),
        })
        return
      }
      const track = root.current!.querySelector<HTMLElement>('[data-track]')!
      const distance = () => track.scrollWidth - innerWidth
      const slide = gsap.to(track, {
        x: () => -distance(),
        ease: 'none',
        scrollTrigger: { trigger: root.current, start: 'top top', end: () => `+=${distance()}`, pin: true, scrub: 1, anticipatePin: 1, invalidateOnRefresh: true },
      })
      gsap.fromTo('[data-progress]', { scaleX: 0 }, { scaleX: 1, ease: 'none', scrollTrigger: { trigger: root.current, start: 'top top', end: () => `+=${distance()}`, scrub: true } })

      gsap.utils.toArray<HTMLElement>('[data-panel]').forEach((panel, i) => {
        const trigger = i === 0 ? { trigger: root.current, start: 'top 60%', once: true } : { trigger: panel, containerAnimation: slide, start: 'left 70%', once: true }
        gsap
          .timeline({ scrollTrigger: trigger })
          .fromTo(panel.querySelector('[data-circle]'), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.9, ease: 'back.out(1.6)' }, 0)
          .fromTo(panel.querySelectorAll('[data-ch]'), { yPercent: 115 }, { yPercent: 0, duration: 0.7, stagger: 0.025, ease: 'expo.out' }, 0.1)
          .fromTo(panel.querySelector('[data-photo]'), { opacity: 0, scale: 0.82, rotation: -8, y: 60 }, { opacity: 1, scale: 1, rotation: 0, y: 0, duration: 0.9, ease: 'back.out(1.4)' }, 0.2)
          .fromTo(panel.querySelector('[data-note]'), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.7, ease: 'expo.out' }, 0.45)
        const parallax = { trigger: panel, containerAnimation: slide, start: 'left right', end: 'right left', scrub: true }
        gsap.fromTo(panel.querySelector('[data-par]'), { x: '-2.5rem' }, { x: '2.5rem', ease: 'none', scrollTrigger: parallax })
        gsap.fromTo(panel.querySelector('[data-ghost]'), { xPercent: 18 }, { xPercent: -18, ease: 'none', scrollTrigger: parallax })
      })
    },
    { scope: root, dependencies: [pinned], revertOnUpdate: true },
  )

  const heading = (
    <div className="flex flex-wrap items-end justify-between gap-4 px-[var(--gutter)]">
      <div>
        <p className="font-mono text-sm font-semibold text-primary">// how it works</p>
        <h2 className="mt-2 text-[clamp(2.4rem,1.4rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.045em]">
          Five steps from <span className="serif text-primary">today</span>.
        </h2>
      </div>
      {pinned && (
        <div className="mb-2 h-1.5 w-[min(320px,40vw)] overflow-hidden rounded-full bg-well" aria-hidden>
          <i data-progress className="block h-full origin-left rounded-full bg-primary" />
        </div>
      )}
    </div>
  )

  if (!pinned) {
    return (
      <section ref={root} id="journey" aria-labelledby="journey-title" className="py-16">
        <div id="journey-title">{heading}</div>
        <ol className="mt-10 grid gap-5 px-[var(--gutter)]">
          {JOURNEY.map((s, i) => (
            <li key={s.title} data-m-step className="glass rounded-card p-6">
              <span className="grid size-12 place-items-center rounded-full bg-primary font-mono font-bold text-primary-foreground">0{i + 1}</span>
              <h3 className="mt-4 text-3xl font-extrabold tracking-[-0.035em]">{s.title}</h3>
              <p className="mt-2 text-lg text-muted-foreground">{s.body}</p>
              <div className="mt-5 rounded-tile bg-solid p-4">
                <JourneyArt kind={s.kind} />
              </div>
            </li>
          ))}
        </ol>
      </section>
    )
  }

  return (
    <section ref={root} id="journey" aria-labelledby="journey-title" className="flex h-dvh flex-col justify-center gap-8 overflow-hidden pt-20 pb-8">
      <div id="journey-title">{heading}</div>
      <div data-track className="flex h-[min(64vh,600px)] w-max gap-6 px-[var(--gutter)]">
        {JOURNEY.map((s, i) => (
          <Panel key={s.title} i={i} />
        ))}
      </div>
    </section>
  )
}
