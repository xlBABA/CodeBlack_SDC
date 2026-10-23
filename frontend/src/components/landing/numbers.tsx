import { useRef } from 'react'
import { CountUp } from '@/components/page/count-up'
import { Badge } from '@/components/ui/badge'
import { DEMO_STATS } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { COUNT_FORMATS, countUp, prefersReducedMotion, type CountFormat } from '@/lib/motion'

/**
 * DEMO numbers. Each card unmasks from its corner (0xmyth certificate reveal:
 * inset(100% 0 0 100%) → inset(0), power4.inOut) while its contents settle from 1.25×.
 */
export function Numbers() {
  const root = useRef<HTMLElement>(null)
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      const cards = gsap.utils.toArray<HTMLElement>('[data-unmask]')
      const counts = gsap.utils.toArray<HTMLElement>('[data-count]')
      gsap.set(cards, { clipPath: 'inset(100% 0% 0% 100% round 26px)' })
      counts.forEach((el) => (el.textContent = COUNT_FORMATS[(el.dataset.format as CountFormat) ?? 'int'](0)))
      gsap
        .timeline({ scrollTrigger: { trigger: '[data-numbers]', start: 'top 75%', once: true } })
        .to(cards, { clipPath: 'inset(0% 0% 0% 0% round 26px)', duration: 1.4, ease: 'power4.inOut', stagger: 0.12 })
        .from('[data-unmask-inner]', { scale: 1.25, duration: 1.8, ease: 'power3.out', stagger: 0.12 }, 0)
        .call(() => countUp(counts), undefined, 0.5)
    },
    { scope: root },
  )
  return (
    <section ref={root} id="numbers" aria-labelledby="numbers-title" className="mx-auto max-w-[1440px] px-[var(--gutter)] py-24">
      <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <Badge tone="warn" dot enter={false}>
            DEMO numbers, not real yet
          </Badge>
          <h2 id="numbers-title" className="mt-4 text-[clamp(2.4rem,1.4rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.045em]">
            The change, in <span className="serif text-primary">numbers</span>.
          </h2>
        </div>
        <p className="max-w-[40ch] text-muted-foreground">Placeholder figures for layout. Each will be replaced with a cited statistic before submission.</p>
      </div>
      <dl data-numbers className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {DEMO_STATS.map((s, i) => (
          <div key={s.label} data-unmask className={i % 2 ? 'rounded-card bg-primary p-6 text-primary-foreground' : 'rounded-card bg-ink p-6 text-ink-foreground'}>
            <div data-unmask-inner className="flex min-h-[200px] flex-col">
              <dt className="sr-only">{s.label}</dt>
              <dd className="flex flex-1 flex-col">
                <span className="flex items-start justify-between">
                  <CountUp value={s.value} format={s.format} className="text-[clamp(3rem,2rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.05em]" />
                  <span className="rounded-full border border-current/30 px-2 py-0.5 text-2xs font-bold tracking-[0.1em]">DEMO</span>
                </span>
                <span className="mt-auto pt-6 text-lg font-semibold opacity-85">{s.label}</span>
              </dd>
            </div>
          </div>
        ))}
      </dl>
    </section>
  )
}
