import { useRef } from 'react'
import { Link } from 'react-router'
import { BrandMark, Wordmark } from '@/components/brand'
import { OnetAttribution } from '@/components/onet-attribution'
import { CharText } from '@/components/page/char-text'
import { FOOTER_LINE, SDG_SOURCE, UN_DISCLAIMER } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { HeroCtas } from './hero-ctas'

/** Closing call to action over a parallax backdrop; the title rises letter by letter (Mango footer). */
export function FooterCta() {
  const root = useRef<HTMLElement>(null)
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.fromTo('[data-bg]', { yPercent: -7, scale: 1.15 }, { yPercent: 7, scale: 1.02, ease: 'none', scrollTrigger: { trigger: root.current, start: 'top bottom', end: 'bottom top', scrub: 1.6 } })
      gsap.set('.split-ch', { yPercent: 110 })
      gsap
        .timeline({ scrollTrigger: { trigger: '[data-final-title]', start: 'top 85%', once: true } })
        .to('.split-ch', { yPercent: 0, duration: 1, ease: 'expo.out', stagger: 0.05 })
        .from('[data-final-rise]', { y: 24, opacity: 0, duration: 0.8, ease: 'expo.out', stagger: 0.1 }, 0.4)
    },
    { scope: root },
  )
  return (
    <footer ref={root} className="relative mt-10 overflow-hidden">
      <div data-bg aria-hidden className="grid-tex absolute inset-0 bg-[radial-gradient(100%_80%_at_50%_100%,var(--deep-a),var(--deep-b)_50%,color-mix(in_srgb,var(--deep-b)_55%,#000))]" />
      <div className="relative mx-auto max-w-[1440px] px-[var(--gutter)] pt-28 pb-10 text-center text-on-deep">
        <BrandMark className="mx-auto size-16" />
        <h2 data-final-title className="mt-8 text-[clamp(3.2rem,1rem+8vw,10rem)] leading-[0.9] font-extrabold tracking-[-0.06em]">
          <CharText text={FOOTER_LINE} />
        </h2>
        <p data-final-rise className="mx-auto mt-6 max-w-[46ch] text-lg text-on-deep/77">
          Map your own future, or try the whole flow with a demo student first.
        </p>
        <div data-final-rise className="mt-8 flex justify-center">
          <HeroCtas onDark />
        </div>
        <div className="mt-24 flex flex-wrap items-center justify-between gap-3 border-t border-white/15 pt-6 text-sm text-on-deep/70">
          <span className="flex items-center gap-2 text-on-deep">
            <Wordmark className="text-sm" /> · SDC Hackathon 2026 · Domain 1 · Sponsor: Aiversecity
          </span>
          <span className="flex items-center gap-4">
            Prototype with demo data
            <Link to="/methodology" className="font-semibold text-on-deep hover:underline">
              Methodology
            </Link>
          </span>
        </div>
        <p className="mt-4 text-left text-xs text-on-deep/70">
          SDG icons from the{' '}
          <a href={SDG_SOURCE} target="_blank" rel="noreferrer" className="font-semibold text-on-deep underline underline-offset-2">
            United Nations Sustainable Development Goals
          </a>
          . {UN_DISCLAIMER}
        </p>
        <OnetAttribution className="mt-2 text-left text-on-deep/70" linkClassName="text-on-deep" />
      </div>
    </footer>
  )
}
