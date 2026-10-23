import { useRef } from 'react'
import { Activity } from 'lucide-react'
import { BrandMark } from '@/components/brand'
import { Badge } from '@/components/ui/badge'
import { HERO } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { HeroCtas } from './hero-ctas'
import { RichLine } from './rich-text'

// floating "pieces of the product" inside the window; depth drives the parallax speed
const CHIPS = [
  { depth: 1.2, className: 'top-[14%] left-[7%]', body: <ChipRole /> },
  { depth: 0.6, className: 'top-[18%] right-[8%]', body: <ChipTrend /> },
  { depth: 1.6, className: 'bottom-[22%] left-[12%]', body: <ChipSkill /> },
  { depth: 0.9, className: 'right-[11%] bottom-[16%]', body: <ChipSdg /> },
  { depth: 0.4, className: 'top-[48%] right-[24%] hidden md:block', body: <ChipHours /> },
]

function Chip({ children }: { children: React.ReactNode }) {
  return <div className="rounded-[18px] border border-white/20 bg-white/12 px-4 py-3 text-on-deep shadow-[0_20px_40px_-20px_#0008] backdrop-blur-md">{children}</div>
}
function ChipRole() {
  return (
    <Chip>
      <small className="block text-xs opacity-75">Top match · demo</small>
      <b className="text-lg">Data analyst</b>
      <span className="mt-1 block text-sm opacity-85">
        <b className="text-2xl">76</b> alignment estimate
      </span>
    </Chip>
  )
}
function ChipTrend() {
  return (
    <Chip>
      <span className="flex items-center gap-2 font-bold">
        <Activity className="size-4 text-deep-glow" aria-hidden /> Developer activity
      </span>
      <small className="block text-xs opacity-70">GitHub signals, dated · not job demand</small>
    </Chip>
  )
}
function ChipSkill() {
  return (
    <Chip>
      <span className="flex items-center gap-2 text-sm font-semibold">
        <i className="size-2 rounded-full bg-deep-warm" /> Excel · advanced
      </span>
      <span className="mt-1 flex items-center gap-2 text-sm font-semibold">
        <i className="size-2 rounded-full bg-deep-glow" /> Python · intermediate
      </span>
    </Chip>
  )
}
function ChipSdg() {
  return (
    <Chip>
      <small className="mb-1.5 block text-xs opacity-75">Linked goals</small>
      <span className="flex gap-1">
        {[8, 9, 4, 13].map((g) => (
          <i key={g} className="grid size-7 place-items-center rounded-full text-xs font-extrabold not-italic" style={{ background: `var(--sdg-${g})` }}>
            {g}
          </i>
        ))}
      </span>
    </Chip>
  )
}
function ChipHours() {
  return (
    <Chip>
      <b className="text-2xl">96 h</b>
      <small className="block text-xs opacity-75">roadmap · demo</small>
    </Chip>
  )
}

/**
 * Hero. Headline lines rise out of masks (0xmyth line reveal), then a framed "window" of
 * the product expands to full-bleed as you scroll: a CSS variable --clip goes 1 → 0 and
 * clip-path reads it (the Apple technique). Chips inside drift at different depths and the
 * caption is uncovered by a growing ellipse (the Lando mask).
 */
export function HeroWindow({ ready }: { ready: boolean }) {
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (prefersReducedMotion()) {
        gsap.set('[data-window]', { '--clip': 0 })
        return
      }
      const lines = gsap.utils.toArray<HTMLElement>('[data-line]')
      const rises = gsap.utils.toArray<HTMLElement>('[data-hero-rise]')
      if (!ready) {
        gsap.set(lines, { yPercent: 110 })
        gsap.set(rises, { y: 30, opacity: 0 })
        gsap.set('[data-window]', { y: 80, opacity: 0 })
        return
      }
      gsap
        .timeline()
        .to(lines, { yPercent: 0, duration: 1.1, ease: 'power4.out', stagger: 0.12 })
        .to(rises, { y: 0, opacity: 1, duration: 0.9, ease: 'expo.out', stagger: 0.08, clearProps: 'transform,opacity' }, 0.35)
        .to('[data-window]', { y: 0, opacity: 1, duration: 1.2, ease: 'expo.out', clearProps: 'transform,opacity' }, 0.45)

      const win = root.current!.querySelector('[data-window]')!
      gsap.fromTo(win, { '--clip': 1 }, { '--clip': 0, ease: 'none', scrollTrigger: { trigger: win, start: 'top 82%', end: 'top 6%', scrub: true } })
      gsap.utils.toArray<HTMLElement>('[data-depth]').forEach((chip) => {
        gsap.to(chip, { y: -110 * Number(chip.dataset.depth), ease: 'none', scrollTrigger: { trigger: win, start: 'top bottom', end: 'bottom top', scrub: true } })
      })
      gsap.fromTo('[data-mark]', { scale: 0.8, rotation: -8 }, { scale: 1.06, rotation: 0, ease: 'none', scrollTrigger: { trigger: win, start: 'top bottom', end: 'bottom top', scrub: true } })
      gsap.fromTo(
        '[data-caption]',
        { clipPath: 'ellipse(100% 0% at 50% 100%)' },
        { clipPath: 'ellipse(150% 150% at 50% 100%)', ease: 'power3.out', scrollTrigger: { trigger: win, start: 'top 45%', end: 'top 5%', scrub: true } },
      )
    },
    { scope: root, dependencies: [ready] },
  )

  return (
    <section ref={root} id="top" aria-labelledby="hero-title">
      <div className="mx-auto max-w-[1440px] px-[var(--gutter)] pt-32 pb-10 sm:pt-36">
        <div data-hero-rise className="mb-6">
          <Badge tone="primary" dot enter={false} className="max-w-full whitespace-normal">
            {HERO.eyebrow}
          </Badge>
        </div>
        <h1 id="hero-title" className="text-[clamp(2.9rem,1.1rem+6.6vw,8.2rem)] leading-[0.94] font-extrabold tracking-[-0.055em]">
          {HERO.lines.map((line) => (
            <span key={line} className="block overflow-hidden pb-[0.06em]">
              <span data-line className="block">
                <RichLine text={line} />
              </span>
            </span>
          ))}
        </h1>
        <div className="mt-8 grid items-end gap-6 md:grid-cols-[minmax(0,1fr)_auto]">
          <p data-hero-rise className="max-w-[54ch] text-lg text-muted-foreground sm:text-xl">
            {HERO.body}
          </p>
          <div data-hero-rise>
            <HeroCtas />
          </div>
        </div>
      </div>

      <div className="px-0">
        <div
          data-window
          aria-hidden
          className="grid-tex relative mx-auto h-[min(82svh,820px)] overflow-hidden bg-[radial-gradient(120%_90%_at_30%_10%,var(--deep-a),var(--deep-b)_55%,color-mix(in_srgb,var(--deep-b)_55%,#000))] [--clip:1] [clip-path:inset(calc(var(--clip)*5%)_calc(var(--clip)*var(--gutter)*1.6)_round_calc(var(--clip)*34px))]"
        >
          <div data-mark className="absolute inset-0 grid place-items-center">
            <div className="relative">
              <span className="absolute inset-[-40%] rounded-full bg-[radial-gradient(closest-side,color-mix(in_srgb,var(--node)_33%,transparent),transparent)] blur-2xl" />
              {/* on the deep backdrop the mark sits on a glass plate so its tile never blends in */}
              <span className="relative grid place-items-center rounded-[30%] border border-white/25 bg-white/10 p-4 sm:p-5 shadow-[0_30px_60px_-20px_#000a] backdrop-blur-md">
                <BrandMark className="size-[clamp(120px,19vw,224px)]" />
              </span>
            </div>
          </div>
          {CHIPS.map((c, i) => (
            <div key={i} data-depth={c.depth} className={`absolute ${c.className}`}>
              {c.body}
            </div>
          ))}
          <p data-caption className="absolute bottom-[7%] left-1/2 w-[min(92%,720px)] -translate-x-1/2 text-center text-[clamp(1.3rem,0.9rem+1.6vw,2.4rem)] leading-tight font-bold text-on-deep">
            One student. Every <span className="serif text-deep-glow">verified</span> role, side by side.
          </p>
        </div>
      </div>
    </section>
  )
}
