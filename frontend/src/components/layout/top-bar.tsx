import { useRef } from 'react'
import { UserRound } from 'lucide-react'
import { Link, useLocation } from 'react-router'
import { preloadRoute } from '@/app-routes'
import { Brand } from '@/components/brand'
import { ThemeToggle } from '@/components/theme-toggle'
import { useNavPill } from '@/hooks/use-nav-pill'
import { cn } from '@/lib/utils'
import { activeIndex, NAV } from './nav-items'

/** Brand left, centred pill tabs with a gliding active pill, tools right (Rapport/Mender idea). */
export function TopBar() {
  const { pathname } = useLocation()
  const active = activeIndex(pathname)
  const track = useRef<HTMLDivElement>(null)
  const pill = useRef<HTMLSpanElement>(null)
  useNavPill(track, pill, active, 'x')

  return (
    <header className="relative z-40 mb-2">
      <div className="flex h-[76px] items-center gap-4">
        <Link to="/" data-shell-top aria-label="Back to the landing page" className="rounded-xl">
          <Brand />
        </Link>

        <nav aria-label="Main" data-shell-top className="mx-auto hidden md:block">
          <div ref={track} className="relative flex rounded-full border border-line bg-glass-2 p-1 backdrop-blur-md">
            <span ref={pill} aria-hidden className="pointer-events-none absolute top-1 bottom-1 left-0 z-0 rounded-full bg-ink opacity-0 shadow-[0_8px_18px_-10px_#0008]" />
            {NAV.map((item, i) => (
              <Link
                key={item.to}
                to={item.to}
                aria-current={i === active ? 'page' : undefined}
                onPointerEnter={() => preloadRoute(item.to)}
                className={cn(
                  'relative z-[1] rounded-full px-[18px] py-2 text-md font-semibold transition-colors duration-200',
                  i === active ? 'text-ink-foreground' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>

        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <div data-shell-top className="lg:hidden">
            <ThemeToggle />
          </div>
          <Link
            to="/start"
            data-shell-top
            aria-label="Your profile"
            className="grid size-11 place-items-center rounded-full border-2 border-rim bg-[linear-gradient(140deg,color-mix(in_srgb,var(--tomato)_55%,#fff),var(--tomato))] text-deep-ink shadow-card"
          >
            <UserRound className="size-5" aria-hidden />
          </Link>
        </div>
      </div>
    </header>
  )
}
