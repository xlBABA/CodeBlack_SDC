import { Check, Plus } from 'lucide-react'
import type { RoleMatch } from '@/mocks/types'

/** Chunky segmented bar (Rapport "stage mix" idea): solid = skills you have, hatched = to build. */
export function SkillGap({ match }: { match: RoleMatch }) {
  const chunks = [...match.matched_skills.map((s) => ({ s, have: true })), ...match.missing_skills.map((s) => ({ s, have: false }))]
  return (
    <div>
      <p className="mb-3 text-sm text-muted-foreground">
        For <b className="text-foreground">{match.title}</b>
      </p>
      <div className="flex h-11 gap-1.5" role="img" aria-label={`${match.matched_skills.length} skills matched, ${match.missing_skills.length} to build`}>
        {chunks.map((c, i) => (
          <i
            key={c.s}
            data-enter="pop"
            title={c.s}
            className={c.have ? 'flex-1 rounded-[12px] bg-primary' : 'hatch flex-1 rounded-[12px]'}
            style={{ opacity: c.have ? 1 - i * 0.07 : 1 }}
          />
        ))}
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">You have</p>
          <ul className="flex flex-wrap gap-1.5">
            {match.matched_skills.map((s) => (
              <li key={s} data-enter="item" className="inline-flex items-center gap-1.5 rounded-full bg-well px-2.5 py-1 text-sm font-semibold">
                <Check className="size-3.5 text-good" aria-hidden />
                {s}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">To build</p>
          <ul className="flex flex-wrap gap-1.5">
            {match.missing_skills.map((s) => (
              <li key={s} data-enter="item" className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-line-2 px-2.5 py-1 text-sm font-semibold">
                <Plus className="size-3.5 text-tomato" aria-hidden />
                {s}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
