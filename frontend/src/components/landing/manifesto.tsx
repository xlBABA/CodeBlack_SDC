import { useRef } from 'react'
import { MANIFESTO } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { cn } from '@/lib/utils'
import { richWords } from '@/lib/rich-words'

/** Big paragraph whose words fill in one by one as you scroll through it (0xmyth "whoami"). */
export function Manifesto() {
  const root = useRef<HTMLElement>(null)
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.fromTo(
        '[data-word]',
        { opacity: 0.16 },
        { opacity: 1, stagger: 0.1, ease: 'none', scrollTrigger: { trigger: '[data-words]', start: 'top 78%', end: 'bottom 48%', scrub: true } },
      )
    },
    { scope: root },
  )
  return (
    <section ref={root} aria-label="Why it matters" className="mx-auto max-w-[1240px] px-[var(--gutter)] py-28 sm:py-40">
      <p className="mb-8 font-mono text-sm font-semibold text-primary">// why it matters</p>
      <p data-words className="text-[clamp(1.8rem,1rem+2.9vw,3.9rem)] leading-[1.12] font-bold tracking-[-0.035em]">
        {richWords(MANIFESTO).map((w, i) => (
          <span key={i}>
            {i > 0 && ' '}
            <span data-word className={cn(w.accent && 'serif text-primary')}>
              {w.word}
            </span>
          </span>
        ))}
      </p>
    </section>
  )
}
