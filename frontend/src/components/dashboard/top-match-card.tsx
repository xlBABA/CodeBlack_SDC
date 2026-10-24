import { ArrowUpRight, Info } from 'lucide-react'
import { Link } from 'react-router'
import { CountUp } from '@/components/page/count-up'
import { Card } from '@/components/ui/card'
import { DEFAULT_CAVEAT } from '@/lib/role-copy'
import type { RoleMatch } from '@/types/api'

// The current score uses skills and experience only: no catalogue role defines prerequisites or
// transferable skills yet, so the API's 0 for those two means "not assessed", not a low score.
const PARTS = [
  ['skills', 'Skills', true],
  ['experience', 'Experience', true],
  ['prerequisites', 'Prerequisites', false],
  ['transferable', 'Transferable', false],
] as const

/** Deep hero card for the best-aligned role (Halden idea): score, caveat, skill coverage, breakdown. */
export function TopMatchCard({ match, eyebrow = 'Your strongest alignment right now', workspaceLink = true }: { match: RoleMatch; eyebrow?: string; workspaceLink?: boolean }) {
  const have = match.matched_skills ?? []
  const missing = match.missing_skills ?? []
  const matched = have.length
  const total = matched + missing.length
  return (
    <Card variant="deep" className="grid h-full gap-6 p-5 sm:p-7 md:grid-cols-[minmax(0,1fr)_220px]" aria-labelledby="top-match-title">
      <div className="flex min-w-0 flex-col">
        <p className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          {eyebrow}
        </p>
        <h2 id="top-match-title" className="mt-2 text-[clamp(1.9rem,1.3rem+1.6vw,2.7rem)] leading-[1.05] font-extrabold tracking-[-0.03em]">
          {match.role_title}
        </h2>
        <div className="mt-4 flex items-end gap-3">
          <CountUp value={match.score} className="text-[clamp(3.6rem,2.6rem+3vw,5.4rem)] leading-[0.85] font-extrabold tracking-[-0.05em]" />
          <span className="pb-1.5 text-sm leading-tight font-semibold text-muted-foreground">
            / 100
            <br />
            alignment estimate
          </span>
        </div>
        <p className="mt-3 flex items-start gap-2 text-sm text-muted-foreground">
          <Info className="mt-0.5 size-4 flex-none" aria-hidden />
          {match.caveats?.[0] ?? DEFAULT_CAVEAT}
        </p>
        <p className="mt-2 text-sm text-muted-foreground">{match.explanation}</p>
        <ul className="mt-5 flex flex-wrap gap-1.5" aria-label="Skills for this role">
          {have.map((s) => (
            <li key={s.skill_id} data-enter="item" className="rounded-full bg-white/14 px-3 py-1 text-sm font-semibold">
              {s.name}
            </li>
          ))}
          {missing.map((s) => (
            <li key={s.skill_id} data-enter="item" className="rounded-full border border-dashed border-white/35 px-3 py-1 text-sm font-semibold text-on-deep/77">
              <span className="sr-only">Missing: </span>
              {s.name}
            </li>
          ))}
        </ul>
        <div className="mt-auto pt-6">
          <div className="mb-2 flex justify-between text-sm">
            <span>
              <b>{matched}</b> of {total} key skills matched
            </span>
            <span className="text-muted-foreground">{missing.length} to build</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-white/15">
            <i data-enter="bar" className="block h-full rounded-full bg-[linear-gradient(90deg,var(--deep-glow),var(--node))]" style={{ width: `${total ? (matched / total) * 100 : 0}%` }} />
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t border-white/15 pt-5 md:border-t-0 md:border-l md:pt-0 md:pl-6">
        <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">Breakdown</p>
        {PARTS.map(([key, label, assessed]) => (
          <div key={key} data-enter="item">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">{label}</span>
              {assessed ? <b>{Math.round(match.score_breakdown[key])}</b> : <span className="text-muted-foreground">Not assessed</span>}
            </div>
            {assessed && (
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/15">
                <i data-enter="bar" className="block h-full rounded-full bg-on-deep" style={{ width: `${match.score_breakdown[key]}%` }} />
              </div>
            )}
          </div>
        ))}
        {workspaceLink && (
          <Link
            to={`/roles/${match.role_id}`}
            className="mt-auto inline-flex h-11 items-center justify-center gap-2 rounded-full bg-on-deep px-5 font-bold whitespace-nowrap text-deep-ink transition hover:bg-white"
          >
            Open workspace
            <ArrowUpRight className="size-4" aria-hidden />
          </Link>
        )}
      </div>
    </Card>
  )
}
