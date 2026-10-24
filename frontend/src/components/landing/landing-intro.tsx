import { Fragment, useLayoutEffect, useRef, useState } from 'react'
import { BrandMark } from '@/components/brand'
import { PRODUCT_NAME, PRODUCT_TAGLINE } from '@/config/product'
import { gsap } from '@/lib/gsap'

const HEX = '0123456789abcdef'

/** Letters stay in one inline-block per word, so a word never breaks across lines. */
function Words({ text, className, word }: { text: string; className: string; word?: string }) {
  return text.split(' ').map((w, k) => (
    <Fragment key={k}>
      {k > 0 && ' '}
      <span className={word ?? 'inline-block whitespace-nowrap'}>
        {word ? (
          <span className={className}>{w}</span>
        ) : (
          Array.from(w).map((ch, i) => (
            <span key={i} data-ch={ch} className={className} aria-hidden>
              {ch}
            </span>
          ))
        )}
      </span>
    </Fragment>
  ))
}

/**
 * Intro in the spirit of 0xmyth.com: the mark's rising line draws itself and its node lights
 * up, the product name decrypts out of hex glyphs letter by letter, a light rule sweeps under
 * it and the tagline rises, the name glitches as it locks, then the panel lifts like a curtain
 * (about 4.8 s). Any key or tap skips; reduced motion never shows it. `onLift` fires as the
 * curtain starts moving so the hero can enter underneath; `onDone` once it is gone.
 */
export function LandingIntro({ onLift, onDone }: { onLift: () => void; onDone: () => void }) {
  const root = useRef<HTMLDivElement>(null)
  const [showSkip, setShowSkip] = useState(false)

  useLayoutEffect(() => {
    const el = root.current!
    let tl: gsap.core.Timeline | null = null
    let lifted = false
    const lift = () => {
      if (lifted) return
      lifted = true
      onLift()
    }
    const chars = gsap.utils.toArray<HTMLElement>('.wm-ch', el)
    // from the markup's data, never from the live text: a scramble may still be showing
    const finals = chars.map((c) => c.dataset.ch ?? '')
    const settle = () => chars.forEach((ch, i) => (ch.textContent = finals[i]))

    const ctx = gsap.context(() => {
      const t = gsap.timeline({ onComplete: onDone })
      tl = t
      const line = el.querySelector<SVGPathElement>('.intro-mark path')!
      const length = line.getTotalLength()
      const [halo, node] = gsap.utils.toArray<SVGCircleElement>('.intro-mark circle')

      t.fromTo('.intro-glow', { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 1.6, ease: 'power2.out' }, 0)
        .fromTo('.intro-mark', { scale: 0.6, rotation: -12, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: 0.9, ease: 'back.out(1.7)' }, 0.15)
        .fromTo(line, { strokeDasharray: length, strokeDashoffset: length }, { strokeDashoffset: 0, duration: 0.9, ease: 'power2.inOut' }, 0.4)
        .fromTo(node, { scale: 0 }, { scale: 1, duration: 0.5, ease: 'back.out(3)', svgOrigin: '36.5 14.5' }, 1.2)
        .fromTo(halo, { scale: 0, opacity: 0.9 }, { scale: 2.6, opacity: 0, duration: 0.9, ease: 'power2.out', svgOrigin: '36.5 14.5' }, 1.3)
        .set(halo, { scale: 1, opacity: 0.25 }, 2.2)

      chars.forEach((ch, i) => {
        const at = 0.9 + i * 0.1
        const proxy = { p: 0 }
        t.fromTo(ch, { opacity: 0, yPercent: 26, scale: 1.3, filter: 'blur(10px)' }, { opacity: 1, yPercent: 0, scale: 1, filter: 'blur(0px)', duration: 0.8, ease: 'power3.out' }, at).to(
          proxy,
          {
            p: 1,
            duration: 0.85 + i * 0.04,
            ease: 'none',
            onUpdate: () => {
              ch.textContent = proxy.p < 0.88 ? HEX[(Math.random() * 16) | 0] : finals[i]
            },
            onComplete: () => {
              ch.textContent = finals[i]
            },
          },
          at,
        )
      })
      const lockAt = t.duration()
      t.fromTo('.wm-scan', { left: '0%', opacity: 1 }, { left: '100%', duration: lockAt - 0.9, ease: 'none' }, 0.9)
        .to('.wm-scan', { opacity: 0, duration: 0.2 }, lockAt)
        .fromTo('.intro-rule', { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: 'expo.inOut' }, lockAt - 0.7)
        .fromTo('.intro-word', { yPercent: 110 }, { yPercent: 0, duration: 0.7, ease: 'expo.out', stagger: 0.035 }, lockAt - 0.35)
        .to('.wm', { skewX: -7, x: 5, duration: 0.05, yoyo: true, repeat: 3, ease: 'none' }, lockAt)
        .set('.wm', { skewX: 0, x: 0 })
        .to(node, { scale: 1.35, duration: 0.18, yoyo: true, repeat: 1, ease: 'power1.inOut', svgOrigin: '36.5 14.5' }, lockAt)
        .addLabel('lift', lockAt + 0.6)
        .call(lift, undefined, 'lift+=0.35')
        .to(el, { yPercent: -100, duration: 0.9, ease: 'expo.inOut' }, 'lift+=0.2')
    }, el)

    const skip = () => {
      tl?.kill()
      settle()
      lift()
      gsap.to(el, { yPercent: -100, duration: 0.55, ease: 'expo.inOut', onComplete: onDone })
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') return
      skip()
    }
    window.addEventListener('keydown', onKey, { once: true })
    window.addEventListener('pointerdown', skip, { once: true })
    const skipTimer = setTimeout(() => setShowSkip(true), 900)

    return () => {
      clearTimeout(skipTimer)
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('pointerdown', skip)
      ctx.revert()
      settle()
    }
    // onLift/onDone are stable callbacks from the landing page
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      ref={root}
      role="dialog"
      aria-label="Intro"
      className="grid-tex fixed inset-0 z-[150] flex flex-col justify-center overflow-hidden bg-[radial-gradient(120%_90%_at_30%_10%,#0e7c99,var(--deep-ink)_55%,#071417)] px-[var(--gutter)] text-[#e6f2f3]"
    >
      <div className="relative mx-auto w-full max-w-5xl">
        <div className="flex flex-col items-start gap-5 sm:flex-row sm:items-center sm:gap-[clamp(20px,2.5vw,36px)]">
          <div className="relative flex-none">
            <span aria-hidden className="intro-glow absolute inset-[-70%] rounded-full bg-[radial-gradient(closest-side,color-mix(in_srgb,var(--node)_30%,transparent),transparent)] opacity-0 blur-2xl" />
            <div className="intro-mark relative opacity-0">
              <BrandMark className="size-[clamp(64px,9vw,128px)]" />
            </div>
          </div>
          <p className="wm relative inline-block text-[clamp(2.6rem,1rem+7vw,6.5rem)] leading-none font-extrabold tracking-[-0.04em]" aria-label={PRODUCT_NAME}>
            <Words text={PRODUCT_NAME} className="wm-ch inline-block opacity-0" />
            <span className="wm-scan pointer-events-none absolute top-[-6%] bottom-[-6%] w-[2px] bg-deep-glow opacity-0 shadow-[0_0_18px_4px_var(--deep-glow)]" aria-hidden />
          </p>
        </div>
        <span aria-hidden className="intro-rule mt-7 block h-px w-full origin-left bg-[linear-gradient(90deg,var(--deep-glow),transparent)]" />
        <p className="mt-5 max-w-[46ch] font-mono text-sm leading-relaxed text-[#e6f2f3b8] sm:text-md">
          <Words text={PRODUCT_TAGLINE} className="intro-word inline-block" word="split-word" />
        </p>
      </div>
      <button
        type="button"
        className={`absolute right-[var(--gutter)] bottom-[max(24px,env(safe-area-inset-bottom))] rounded-full border border-white/15 px-4 py-2 font-mono text-xs text-[#e6f2f3a3] transition-opacity duration-500 ${showSkip ? 'opacity-100' : 'opacity-0'}`}
        // the window pointerdown/keydown listeners do the skipping; this is the visible affordance
      >
        press any key to skip
      </button>
    </div>
  )
}
