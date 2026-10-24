import { useRef } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { CountUp } from '@/components/page/count-up'
import { STATS } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { COUNT_FORMATS, countUp, prefersReducedMotion, type CountFormat } from '@/lib/motion'
import { cn } from '@/lib/utils'

/**
 * Published figures, each with its source linked under it. Each card unmasks from its corner
 * (0xmyth certificate reveal: inset(100% 0 0 100%) → inset(0), power4.inOut) while its
 * contents settle from 1.25×.
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
        <h2 id="numbers-title" className="text-[clamp(2.4rem,1.4rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.045em]">
          The change, in <span className="serif text-primary">numbers</span>.
        </h2>
        <p className="max-w-[40ch] text-muted-foreground">Published figures on AI and skills in Malaysia and worldwide. Each links to its source.</p>
      </div>
      <dl data-numbers className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        {STATS.map((s, i) => (
          <div
            key={s.label}
            data-unmask
            className={cn(
              'rounded-card p-6',
              i % 2 ? 'bg-primary text-primary-foreground' : 'bg-ink text-ink-foreground',
              i < 3 ? 'lg:col-span-2' : 'lg:col-span-3',
              i === STATS.length - 1 && 'sm:col-span-2 lg:col-span-3',
            )}
          >
            <div data-unmask-inner className="flex min-h-[200px] flex-col">
              <dt className="sr-only">{s.label}</dt>
              <dd className="flex flex-1 flex-col">
                <CountUp value={s.value} format={s.format} className="text-[clamp(3rem,2rem+3vw,4.6rem)] leading-none font-extrabold tracking-[-0.05em]" />
                <span className="mt-auto pt-6 text-lg font-semibold opacity-90">{s.label}</span>
                <a href={s.href} target="_blank" rel="noreferrer" className="mt-3 inline-flex w-fit items-start gap-1 text-sm underline underline-offset-2 opacity-90 hover:opacity-100">
                  {s.source}
                  <ArrowUpRight className="mt-0.5 size-3.5 flex-none" aria-hidden />
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              </dd>
            </div>
          </div>
        ))}
      </dl>
    </section>
  )
}
