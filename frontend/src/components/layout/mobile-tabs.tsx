import { useRef } from 'react'
import { Link, useLocation } from 'react-router'
import { preloadRoute } from '@/app-routes'
import { useNavPill } from '@/hooks/use-nav-pill'
import { cn } from '@/lib/utils'
import { activeIndex, NAV } from './nav-items'

/** On phones the dock becomes a floating bottom bar holding the main tabs (Rapport idea). */
export function MobileTabs() {
  const { pathname } = useLocation()
  const active = activeIndex(pathname)
  const track = useRef<HTMLDivElement>(null)
  const pill = useRef<HTMLSpanElement>(null)
  useNavPill(track, pill, active, 'x')

  return (
    <nav
      data-shell="tabs"
      aria-label="Main"
      className="fixed inset-x-0 bottom-[max(12px,env(safe-area-inset-bottom))] z-30 mx-auto w-fit rounded-full bg-ink p-1.5 text-ink-foreground shadow-pop md:hidden dark:border dark:border-line dark:bg-raised dark:text-foreground"
    >
      <div ref={track} className="relative flex">
        <span ref={pill} aria-hidden className="pointer-events-none absolute inset-y-0 left-0 z-0 rounded-full bg-primary opacity-0" />
        {NAV.map((item, i) => (
          <Link
            key={item.to}
            to={item.to}
            aria-current={i === active ? 'page' : undefined}
            onPointerDown={() => preloadRoute(item.to)}
            className={cn(
              'relative z-[1] flex h-12 min-w-[68px] flex-col items-center justify-center gap-0.5 rounded-full px-3 text-2xs font-bold transition-colors',
              i === active ? 'text-primary-foreground' : 'opacity-75',
            )}
          >
            <item.icon className="size-[18px]" aria-hidden />
            {item.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
