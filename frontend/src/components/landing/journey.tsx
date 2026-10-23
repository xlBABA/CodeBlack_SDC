import { useRef } from 'react'
import { CharText } from '@/components/page/char-text'
import { JOURNEY } from '@/content/landing'
import { useMediaQuery } from '@/hooks/use-media-query'
import { gsap, REDUCED_MOTION, useGSAP } from '@/lib/gsap'
import { JourneyArt } from './journey-art'

function Panel({ i }: { i: number }) {
  const s = JOURNEY[i]
  return (
    <article
      data-panel
      className="glass relative grid h-full w-[172vw] flex-none grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] items-center gap-[clamp(16px,2.6vw,40px)] overflow-hidden rounded-card p-[clamp(20px,min(3vw,4.5svh),40px)] md:w-[min(86vw,1020px)]"
    >
      <span data-ghost aria-hidden className="pointer-events-none absolute -right-6 -bottom-16 text-[clamp(9rem,20vw,18rem)] leading-none font-extrabold tracking-[-0.06em] text-foreground opacity-[0.04]">
        0{i + 1}
      </span>
      <div className="relative">
        <span data-circle className="grid size-12 place-items-center rounded-full bg-primary font-mono font-bold text-primary-foreground md:size-16 md:text-lg">
          0{i + 1}
        </span>
        <h3 className="mt-[clamp(12px,2.5svh,24px)] text-[clamp(1.75rem,1.2rem+3vw,2.2rem)] leading-[1.02] font-extrabold tracking-[-0.04em] md:text-[clamp(2.2rem,1.4rem+2vw,3.6rem)]">
          <CharText text={s.title} />
        </h3>
        <p data-note className="mt-[clamp(8px,2svh,16px)] max-w-[36ch] text-muted-foreground md:text-lg">
          {s.body}
        </p>
      </div>
      <div data-photo className="relative rounded-tile bg-solid p-4 shadow-card md:p-5">
        <div data-par>
          <JourneyArt kind={s.kind} />
        </div>
      </div>
    </article>
  )
}

const PHOTO_FROM = { opacity: 0, scale: 0.82, rotation: -8, y: 60 }
const PHOTO_TO = { opacity: 1, scale: 1, rotation: 0, y: 0, duration: 0.9, ease: 'back.out(1.4)' }

/**
 * Five steps on a horizontal track, at every screen size: the section pins and scrolls
 * sideways (Lando/Mango technique), each panel's parts enter as it slides in
 * (containerAnimation) and its art drifts against the track. On phones a panel is two
 * screens wide, text then art, so neither is squeezed. Widths and distances are functions,
 * so ScrollTrigger re-measures them on every resize and orientation change.
 * Only reduced motion gets a plain vertical list.
 */
export function Journey() {
  const reduced = useMediaQuery(REDUCED_MOTION)
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (reduced) return
      const mm = gsap.matchMedia(root.current!)
      mm.add({ wide: '(min-width: 768px)', narrow: 'not all and (min-width: 768px)' }, (ctx) => {
        const wide = ctx.conditions?.wide
        const drift = wide ? '2.5rem' : '0.75rem'
        const track = root.current!.querySelector<HTMLElement>('[data-track]')!
        const distance = () => track.scrollWidth - innerWidth
        const slide = gsap.to(track, {
          x: () => -distance(),
          ease: 'none',
          scrollTrigger: { trigger: root.current, start: 'top top', end: () => `+=${distance()}`, pin: true, scrub: 1, anticipatePin: 1, invalidateOnRefresh: true },
        })
        gsap.fromTo('[data-progress]', { scaleX: 0 }, { scaleX: 1, ease: 'none', scrollTrigger: { trigger: root.current, start: 'top top', end: () => `+=${distance()}`, scrub: true, invalidateOnRefresh: true } })

        gsap.utils.toArray<HTMLElement>('[data-panel]').forEach((panel, i) => {
          const trigger = i === 0 ? { trigger: root.current, start: 'top 60%', once: true } : { trigger: panel, containerAnimation: slide, start: 'left 70%', once: true }
          const photo = panel.querySelector('[data-photo]')
          const tl = gsap
            .timeline({ scrollTrigger: trigger })
            .fromTo(panel.querySelector('[data-circle]'), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.9, ease: 'back.out(1.6)' }, 0)
            .fromTo(panel.querySelectorAll('.split-ch'), { yPercent: 115 }, { yPercent: 0, duration: 0.7, stagger: 0.025, ease: 'expo.out' }, 0.1)
            .fromTo(panel.querySelector('[data-note]'), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.7, ease: 'expo.out' }, 0.45)
          // on phones the art is a screen further along, so it enters on its own
          if (wide) tl.fromTo(photo, PHOTO_FROM, PHOTO_TO, 0.2)
          else gsap.fromTo(photo, PHOTO_FROM, { ...PHOTO_TO, scrollTrigger: { trigger: photo, containerAnimation: slide, start: 'left 85%', once: true } })
          const parallax = { trigger: panel, containerAnimation: slide, start: 'left right', end: 'right left', scrub: true }
          gsap.fromTo(panel.querySelector('[data-par]'), { x: `-${drift}` }, { x: drift, ease: 'none', scrollTrigger: parallax })
          gsap.fromTo(panel.querySelector('[data-ghost]'), { xPercent: 18 }, { xPercent: -18, ease: 'none', scrollTrigger: parallax })
        })
      })
      return () => mm.revert()
    },
    { scope: root, dependencies: [reduced], revertOnUpdate: true },
  )

  const heading = (
    <div className="flex flex-wrap items-end justify-between gap-4 px-[var(--gutter)]">
      <div>
        <p className="font-mono text-sm font-semibold text-primary">// how it works</p>
        <h2 className="mt-2 text-[clamp(2.4rem,1.4rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.045em]">
          Five steps from <span className="serif text-primary">today</span>.
        </h2>
      </div>
      {!reduced && (
        <div className="mb-2 h-1.5 w-[min(320px,40vw)] overflow-hidden rounded-full bg-well" aria-hidden>
          <i data-progress className="block h-full origin-left rounded-full bg-primary" />
        </div>
      )}
    </div>
  )

  if (reduced) {
    return (
      <section ref={root} id="journey" aria-labelledby="journey-title" className="py-16">
        <div id="journey-title">{heading}</div>
        <ol className="mt-10 grid gap-5 px-[var(--gutter)]">
          {JOURNEY.map((s, i) => (
            <li key={s.title} className="glass rounded-card p-6">
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
    <section
      ref={root}
      id="journey"
      aria-labelledby="journey-title"
      className="flex h-svh flex-col justify-center gap-[clamp(16px,4svh,32px)] overflow-hidden pt-20 pb-[clamp(16px,4svh,32px)]"
    >
      <div id="journey-title">{heading}</div>
      <div data-track className="flex h-[min(74svh,600px)] min-h-0 w-max gap-[clamp(12px,2vw,24px)] px-[var(--gutter)] md:h-[min(64svh,600px)]">
        {JOURNEY.map((s, i) => (
          <Panel key={s.title} i={i} />
        ))}
      </div>
    </section>
  )
}
