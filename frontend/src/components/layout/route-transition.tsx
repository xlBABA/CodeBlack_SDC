import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useLocation, type Location } from 'react-router'
import { preloadRoute } from '@/app-routes'
import { gsap } from '@/lib/gsap'
import { EASE, prefersReducedMotion } from '@/lib/motion'

type View = { loc: Location; leaving: boolean }

/**
 * Cross-fade overlap (Halden idea): the outgoing page is lifted out of the flow, held where
 * it was on screen, and fades (.3s, y -6) while the incoming page enters underneath at the
 * same time. Views are keyed by location so the outgoing one keeps its React state instead
 * of remounting. The next chunk is preloaded first so nothing suspends mid-swap.
 */
export function RouteTransition({ children }: { children: (location: Location) => React.ReactNode }) {
  const location = useLocation()
  const [views, setViews] = useState<View[]>([{ loc: location, leaving: false }])
  const current = views.find((v) => !v.leaving)!.loc
  const leavingEl = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (location.key === current.key) return
    let alive = true
    preloadRoute(location.pathname).then(() => {
      if (!alive) return
      const animate = location.pathname !== current.pathname && !prefersReducedMotion()
      setViews((prev) => [
        ...(animate ? prev.filter((v) => !v.leaving).map((v) => ({ ...v, leaving: true })) : []),
        { loc: location, leaving: false },
      ])
    })
    return () => {
      alive = false
    }
  }, [location, current])

  const leavingKey = views.find((v) => v.leaving)?.loc.key
  useLayoutEffect(() => {
    const el = leavingEl.current
    // keep the outgoing page exactly where it was on screen while the window jumps to the top
    if (el) el.style.top = `${-window.scrollY}px`
    window.scrollTo({ top: 0 })
    if (!el) return
    const fade = gsap.to(el, {
      opacity: 0,
      y: -6,
      duration: 0.3,
      ease: EASE.in,
      onComplete: () => setViews((prev) => prev.filter((v) => !v.leaving)),
    })
    return () => {
      fade.kill()
    }
  }, [leavingKey, current.key])

  return (
    <div className="relative">
      {views.map((v) => (
        <div
          key={v.loc.key}
          ref={v.leaving ? leavingEl : undefined}
          aria-hidden={v.leaving || undefined}
          inert={v.leaving || undefined}
          className={v.leaving ? 'pointer-events-none absolute inset-x-0 z-0' : 'relative z-[1]'}
        >
          {children(v.loc)}
        </div>
      ))}
    </div>
  )
}
