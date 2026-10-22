import { useLayoutEffect, useRef, useState } from 'react'
import { INTRO_LINES } from '@/content/landing'
import { PRODUCT_NAME } from '@/config/product'
import { typeLines } from '@/lib/boot-type'
import { gsap } from '@/lib/gsap'

const HEX = '0123456789abcdef'

/**
 * Boot sequence in the spirit of 0xmyth.com: lines type out, the product name decrypts
 * out of hex glyphs and glitches as it locks, then the whole panel lifts like a curtain.
 * Any key or tap skips. `onLift` fires as the curtain starts moving so the hero can
 * enter underneath; `onDone` once it is gone.
 */
export function LandingIntro({ onLift, onDone }: { onLift: () => void; onDone: () => void }) {
  const root = useRef<HTMLDivElement>(null)
  const linesRef = useRef<HTMLDivElement>(null)
  const [showSkip, setShowSkip] = useState(false)

  useLayoutEffect(() => {
    const el = root.current!
    let typing: ReturnType<typeof typeLines> | null = null
    let tl: gsap.core.Timeline | null = null
    let lifted = false
    let cancelled = false
    const lift = () => {
      if (lifted) return
      lifted = true
      onLift()
    }

    const ctx = gsap.context(() => {
      const chars = gsap.utils.toArray<HTMLElement>('.wm-ch', el)
      const finals = chars.map((c) => c.textContent ?? '')

      const decrypt = () => {
        const t = gsap.timeline()
        chars.forEach((ch, i) => {
          if (!finals[i].trim()) return
          const at = 0.05 + i * 0.06
          const proxy = { p: 0 }
          t.fromTo(ch, { opacity: 0, yPercent: 26, scale: 1.3, filter: 'blur(10px)' }, { opacity: 1, yPercent: 0, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'power3.out' }, at).to(
            proxy,
            {
              p: 1,
              duration: 0.5 + i * 0.03,
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
        t.fromTo('.wm-scan', { left: '0%', opacity: 1 }, { left: '100%', duration: lockAt, ease: 'none' }, 0)
          .to('.wm-scan', { opacity: 0, duration: 0.2 }, lockAt)
          .to('.wm', { skewX: -7, x: 5, duration: 0.05, yoyo: true, repeat: 3, ease: 'none' }, lockAt)
          .set('.wm', { skewX: 0, x: 0 })
          .addLabel('lift', '+=0.35')
          .to(linesRef.current, { autoAlpha: 0, y: -24, duration: 0.5, ease: 'power2.in' }, 'lift')
          .call(lift, undefined, 'lift+=0.35')
          .to(el, { yPercent: -100, duration: 0.9, ease: 'expo.inOut' }, 'lift+=0.2')
        return t
      }

      typing = typeLines(linesRef.current!, INTRO_LINES)
      typing.finished.then(() => {
        if (cancelled || tl) return
        tl = ctx.add(() => decrypt().eventCallback('onComplete', onDone))
      })
    }, el)

    const skip = () => {
      typing?.finish()
      if (!tl) tl = ctx.add(() => gsap.timeline())
      lift()
      gsap.killTweensOf(el)
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
      cancelled = true
      typing?.cancel()
      clearTimeout(skipTimer)
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('pointerdown', skip)
      ctx.revert()
    }
    // onLift/onDone are stable callbacks from the landing page
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      ref={root}
      role="dialog"
      aria-label="Intro"
      className="fixed inset-0 z-[150] flex flex-col justify-center bg-[#0f2a31] px-[var(--gutter)] text-[#e6f2f3]"
    >
      <div className="mx-auto w-full max-w-4xl">
        <div ref={linesRef} className="boot-lines mb-10 min-h-[7.5em] font-mono text-sm leading-[1.9] sm:text-md" aria-live="polite" />
        <p className="wm relative inline-block font-extrabold tracking-[-0.04em] text-[clamp(2.6rem,1rem+7vw,6.5rem)] leading-none" aria-label={PRODUCT_NAME}>
          {Array.from(PRODUCT_NAME).map((ch, i) => (
            <span key={i} className="wm-ch inline-block opacity-0" aria-hidden>
              {ch === ' ' ? ' ' : ch}
            </span>
          ))}
          <span className="wm-scan pointer-events-none absolute top-[-6%] bottom-[-6%] w-[2px] bg-[#9fe3ec] opacity-0 shadow-[0_0_18px_4px_#9fe3ec]" aria-hidden />
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
