import { useRef } from 'react'
import { QUOTE } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'

/** One line of principle; words tip upright as they arrive (Mango quote). */
export function Quote() {
  const root = useRef<HTMLElement>(null)
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.fromTo(
        '[data-qw]',
        { opacity: 0, y: 40, rotation: 4 },
        { opacity: 1, y: 0, rotation: 0, duration: 0.8, stagger: 0.06, ease: 'expo.out', scrollTrigger: { trigger: root.current, start: 'top 75%', once: true } },
      )
    },
    { scope: root },
  )
  return (
    <section ref={root} aria-label="Our principle" className="mx-auto max-w-[1200px] px-[var(--gutter)] py-24 text-center">
      <blockquote className="serif text-[clamp(2.4rem,1.2rem+4.4vw,6rem)] leading-[1.02] text-foreground">
        <span aria-hidden>“</span>
        {QUOTE.split(' ').map((w, i) => (
          <span key={i}>
            {i > 0 && ' '}
            <span data-qw className="inline-block origin-bottom-left">
              {w}
            </span>
          </span>
        ))}
        <span aria-hidden>”</span>
      </blockquote>
      <p className="mt-6 font-semibold text-muted-foreground">The principle behind every screen.</p>
    </section>
  )
}
