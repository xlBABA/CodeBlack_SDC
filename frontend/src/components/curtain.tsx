import { createContext, useCallback, useContext, useRef } from 'react'
import { useNavigate } from 'react-router'
import { BrandMark } from '@/components/brand'
import type { BootSegment } from '@/content/landing'
import { holdShell } from '@/lib/app-ready'
import { typeLines } from '@/lib/boot-type'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'

type Go = (to: string, options?: { origin?: Element | null; lines?: BootSegment[][] }) => void
const CurtainContext = createContext<Go>(() => {})

/**
 * Landing → app hand-off. The clicked button's own outline grows into a full-screen
 * window (clip-path inset from the button rect to the viewport, Apple-style), types a
 * couple of boot lines, navigates underneath, then dissolves (fade + slight scale) while
 * the app shell plays its load sequence. Lives above the router so it survives the switch.
 */
export function CurtainProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const panel = useRef<HTMLDivElement>(null)
  const linesRef = useRef<HTMLDivElement>(null)
  const busy = useRef(false)

  const go = useCallback<Go>(
    (to, { origin, lines = [] } = {}) => {
      const el = panel.current
      if (!el || busy.current || prefersReducedMotion()) {
        navigate(to)
        return
      }
      busy.current = true
      const r = origin?.getBoundingClientRect() ?? new DOMRect(innerWidth / 2 - 80, innerHeight / 2 - 24, 160, 48)
      const from = `inset(${r.top}px ${innerWidth - r.right}px ${innerHeight - r.bottom}px ${r.left}px round ${r.height / 2}px)`

      gsap.set(el, { visibility: 'visible', opacity: 1, scale: 1, clipPath: from })
      gsap.set('[data-curtain-inner]', { autoAlpha: 0, y: 16 })
      gsap
        .timeline()
        .to(el, { clipPath: 'inset(0px 0px 0px 0px round 0px)', duration: 0.75, ease: 'expo.inOut' })
        .to('[data-curtain-inner]', { autoAlpha: 1, y: 0, duration: 0.45, ease: 'expo.out' }, 0.45)
        .call(async () => {
          const typing = typeLines(linesRef.current!, lines, { step: 12, gap: 140 })
          await typing.finished
          await new Promise((res) => setTimeout(res, 180))
          const release = holdShell()
          navigate(to)
          await new Promise((res) => setTimeout(res, 240))
          release()
          gsap.to(el, {
            opacity: 0,
            scale: 1.06,
            duration: 0.75,
            ease: 'power2.inOut',
            onComplete: () => {
              gsap.set(el, { visibility: 'hidden', clearProps: 'clipPath,transform,opacity' })
              busy.current = false
            },
          })
        })
    },
    [navigate],
  )

  return (
    <CurtainContext.Provider value={go}>
      {children}
      <div
        ref={panel}
        aria-hidden
        className="grid-tex invisible fixed inset-0 z-[180] grid place-items-center bg-[radial-gradient(120%_90%_at_30%_10%,#0e7c99,#0f2a31_55%,#071417)] px-[var(--gutter)] text-[#e6f2f3]"
      >
        <div data-curtain-inner className="grid w-full max-w-xl justify-items-start gap-8">
          <BrandMark className="size-16" />
          <div ref={linesRef} className="boot-lines w-full font-mono text-sm leading-[1.9] sm:text-md" />
        </div>
      </div>
    </CurtainContext.Provider>
  )
}

/** onClick for links that should travel through the curtain; modified clicks open normally. */
// oxlint-disable-next-line react/only-export-components
export function useCurtainLink(to: string, lines?: BootSegment[][]) {
  const go = useContext(CurtainContext)
  return (e: React.MouseEvent<HTMLElement>) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return
    e.preventDefault()
    go(to, { origin: e.currentTarget, lines })
  }
}
