import { useRef } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router'
import { CountUp } from '@/components/page/count-up'
import { useLift } from '@/hooks/use-hover-fx'
import { DEFAULT_CAVEAT } from '@/lib/role-copy'
import type { RoleMatch } from '@/types/api'
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
  const have = match.matched_skills?.length ?? 0
  const total = have + (match.missing_skills?.length ?? 0)
  useLift(ref, true)
  return (
    <Link
      ref={ref}
      to={`/roles/${match.role_id}`}
      data-enter="item"
      className={cn('group flex min-h-[208px] flex-col rounded-tile p-4 shadow-card transition-shadow hover:shadow-pop', TILE[rank % TILE.length])}
    >
      <span className="flex items-center justify-between text-xs font-semibold opacity-90">
        #{rank + 1} match
        <span className="grid size-8 place-items-center rounded-full border border-current/25 transition group-hover:bg-current/10" aria-hidden>
          <ArrowUpRight className="size-4" />
        </span>
      </span>
      <span className="mt-1 text-lg leading-tight font-bold tracking-[-0.01em]">{match.role_title}</span>
      <span className="mt-1 text-sm font-semibold opacity-90">
        {have} of {total} core skills
      </span>
      <div className="mt-auto grid pt-4">
        <span className="flex items-baseline gap-1">
          <CountUp value={match.score} className="text-[2rem] leading-none font-extrabold tracking-[-0.04em]" />
          <small className="text-xs font-semibold opacity-90">alignment estimate</small>
        </span>
        {/* every score sits next to its caveats, shown in full */}
        <ul className="mt-1 grid gap-1 text-xs leading-snug opacity-90">
          {(match.caveats?.length ? match.caveats : [DEFAULT_CAVEAT]).map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </div>
    </Link>
  )
}

export function RoleTiles({ matches, className }: { matches: RoleMatch[]; className?: string }) {
  return (
    <div className={cn('grid gap-3 sm:grid-cols-2', className)}>
      {matches.map((m, i) => (
        <RoleTile key={m.role_id} match={m} rank={i} />
      ))}
    </div>
  )
}
