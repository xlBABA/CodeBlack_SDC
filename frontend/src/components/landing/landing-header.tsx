import { useEffect, useRef, useState, type RefObject } from 'react'
import type Lenis from 'lenis'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router'
import { Brand } from '@/components/brand'
import { useCurtainLink } from '@/components/curtain'
import { ThemeToggle } from '@/components/theme-toggle'
import { CURTAIN_LINES } from '@/content/landing'
import { gsap, useGSAP } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { cn } from '@/lib/utils'

const LINKS = [
  { href: '#journey', label: 'How it works' },
  { href: '#report', label: 'The report' },
  { href: '#numbers', label: 'Numbers' },
]

/** Floating glass capsule that drops in after the intro and tightens once you scroll. */
export function LandingHeader({ ready, lenis }: { ready: boolean; lenis: RefObject<Lenis | null> }) {
  const root = useRef<HTMLElement>(null)
  const [scrolled, setScrolled] = useState(false)
  const toApp = useCurtainLink('/dashboard', CURTAIN_LINES.dashboard)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      if (!ready) gsap.set(root.current, { yPercent: -160 })
      else gsap.to(root.current, { yPercent: 0, duration: 1, ease: 'expo.out', delay: 0.3, clearProps: 'transform' })
    },
    { dependencies: [ready] },
  )

  const jump = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    const target = document.querySelector<HTMLElement>(href)
    if (!target) return
    e.preventDefault()
    if (lenis.current) lenis.current.scrollTo(target, { duration: 1.6 })
    else target.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
  }

  return (
    <header ref={root} className="pointer-events-none fixed inset-x-0 top-3 z-50 px-3">
      <div
        className={cn(
          'pointer-events-auto mx-auto flex items-center gap-3 rounded-full border px-2 py-2 pl-3 transition-all duration-500',
          scrolled ? 'glass max-w-[880px] shadow-pop' : 'max-w-[1400px] border-transparent',
        )}
      >
        <Link to="/" aria-label="Home" className="rounded-full">
          <Brand />
        </Link>
        <nav aria-label="Sections" className="mx-auto hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} onClick={(e) => jump(e, l.href)} className="rounded-full px-3.5 py-2 font-semibold text-muted-foreground transition-colors hover:bg-well hover:text-foreground">
              {l.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <ThemeToggle />
          <Link
            to="/dashboard"
            onClick={toApp}
            className="hidden h-11 items-center gap-2 rounded-full bg-ink px-5 font-bold text-ink-foreground transition hover:brightness-110 sm:inline-flex"
          >
            Dashboard
            <ArrowRight className="size-4" aria-hidden />
          </Link>
        </div>
      </div>
    </header>
  )
}
