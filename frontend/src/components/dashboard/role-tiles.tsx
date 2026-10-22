import { useRef } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router'
import { SdgBadges } from '@/components/sdg-badges'
import { TrendArrow } from '@/components/trend-arrow'
import { CountUp } from '@/components/page/count-up'
import { useLift } from '@/hooks/use-hover-fx'
import type { RoleMatch } from '@/mocks/types'
import { cn } from '@/lib/utils'

// solid colour tiles, one per rank (Rapport idea)
const TILE = [
  'bg-ink text-ink-foreground',
  'bg-primary text-primary-foreground',
  'bg-tomato text-tomato-foreground',
  'bg-butter text-butter-foreground',
]

function RoleTile({ match, rank }: { match: RoleMatch; rank: number }) {
  const ref = useRef<HTMLAnchorElement>(null)
  useLift(ref, true)
  return (
    <Link
      ref={ref}
      to={`/roles/${match.role_id}`}
      data-enter="item"
      className={cn('group flex min-h-[208px] flex-col rounded-tile p-4 shadow-card transition-shadow hover:shadow-pop', TILE[rank % TILE.length])}
    >
      <span className="flex items-center justify-between text-xs font-semibold opacity-80">
        #{rank + 1} match
        <span className="grid size-8 place-items-center rounded-full border border-current/25 transition group-hover:bg-current/10" aria-hidden>
          <ArrowUpRight className="size-4" />
        </span>
      </span>
      <span className="mt-1 text-lg leading-tight font-bold tracking-[-0.01em]">{match.title}</span>
      <TrendArrow direction={match.trend} withLabel className="mt-1 !text-current opacity-85" />
      <span className="mt-auto flex items-end justify-between gap-2 pt-4">
        <span className="grid">
          <span className="flex items-baseline gap-1">
            <CountUp value={match.alignment_estimate} className="text-[2rem] leading-none font-extrabold tracking-[-0.04em]" />
            <small className="text-xs font-semibold opacity-75">alignment estimate</small>
          </span>
          {/* every score sits next to at least one caveat */}
          <small className="mt-1 line-clamp-2 text-xs leading-snug opacity-80">{match.caveats[0]}</small>
        </span>
        <SdgBadges goals={match.sdgs.slice(0, 2)} size="sm" className="flex-none" />
      </span>
    </Link>
  )
}

export function RoleTiles({ matches }: { matches: RoleMatch[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {matches.map((m, i) => (
        <RoleTile key={m.role_id} match={m} rank={i} />
      ))}
    </div>
  )
}
