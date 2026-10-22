import { Suspense, useLayoutEffect, useRef } from 'react'
import { Route, Routes } from 'react-router'
import { APP_ROUTES, NotFoundPage } from '@/app-routes'
import { Mesh } from '@/components/mesh'
import { markAppReady, shellGate } from '@/lib/app-ready'
import { gsap } from '@/lib/gsap'
import { dur, EASE, rise } from '@/lib/motion'
import { Dock } from './dock'
import { MobileTabs } from './mobile-tabs'
import { PageSkeleton } from './page-skeleton'
import { RouteTransition } from './route-transition'
import { TopBar } from './top-bar'

const visible = (els: HTMLElement[]) => els.filter((el) => el.offsetParent !== null)

/**
 * Everything after the landing page. Waits for fonts (max 1.5 s) and for the landing
 * hand-off if one is covering the screen, then plays the load sequence (Rapport idea):
 * mesh fades up, top bar items drop in, the dock slides in from the left and its buttons
 * stagger, and the first page enters.
 */
export function AppShell() {
  const shell = useRef<HTMLDivElement>(null)

  useLayoutEffect(() => {
    let cancelled = false
    const ctx = gsap.context(() => {}, shell)
    const fonts = Promise.race([document.fonts?.ready ?? Promise.resolve(), new Promise((r) => setTimeout(r, 1500))])
    Promise.all([fonts, shellGate()]).then(() => {
      if (cancelled || !shell.current) return
      markAppReady()
      ctx.add(() => {
        const root = shell.current!
        const q = (sel: string) => Array.from(root.querySelectorAll<HTMLElement>(sel))
        gsap
          .timeline()
          .fromTo('[data-mesh]', { opacity: 0 }, { opacity: 1, duration: dur(1.2), ease: 'power2.out' }, 0)
          .add(rise(visible(q('[data-shell-top]')), { y: -14, stagger: 0.06 }), 0.05)
          .fromTo('[data-shell="dock"]', { x: -90, opacity: 0 }, { x: 0, opacity: 1, duration: dur(0.9), ease: EASE.out, clearProps: 'transform,opacity' }, 0.1)
          .add(rise(visible(q('[data-dock-item]')), { y: 10, stagger: 0.035 }), 0.3)
          .fromTo('[data-shell="tabs"]', { y: 90, opacity: 0 }, { y: 0, opacity: 1, duration: dur(0.9), ease: EASE.out, clearProps: 'transform,opacity' }, 0.1)
      })
    })
    return () => {
      cancelled = true
      ctx.revert()
    }
  }, [])

  return (
    <div ref={shell} data-app className="min-h-dvh">
      <Mesh />
      <a
        href="#main"
        className="fixed top-3 left-3 z-[100] -translate-y-20 rounded-full bg-ink px-4 py-2.5 font-bold text-ink-foreground focus:translate-y-0"
      >
        Skip to content
      </a>
      <Dock />
      <div className="mx-auto max-w-[1440px] px-[var(--gutter)] pb-[calc(96px+env(safe-area-inset-bottom))] md:pb-10 lg:pl-[calc(var(--gutter)+76px)]">
        <TopBar />
        <main id="main" tabIndex={-1} className="outline-none">
          <RouteTransition>
            {(location) => (
              // the skeleton only shows on a cold load; later navigations preload first
              <Suspense fallback={<PageSkeleton />}>
                <Routes location={location}>
                  {APP_ROUTES.map(({ path, Page }) => (
                    <Route key={path} path={path} element={<Page />} />
                  ))}
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </Suspense>
            )}
          </RouteTransition>
        </main>
      </div>
      <MobileTabs />
    </div>
  )
}
