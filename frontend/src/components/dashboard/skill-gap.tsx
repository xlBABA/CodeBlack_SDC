import { Check, Plus } from 'lucide-react'
import type { RoleMatch } from '@/types/api'

/** Chunky segmented bar (Rapport "stage mix" idea): solid = skills you have, hatched = to build. */
export function SkillGap({ match }: { match: RoleMatch }) {
  const have = match.matched_skills ?? []
  const missing = match.missing_skills ?? []
  const chunks = [...have.map((s) => ({ s, have: true })), ...missing.map((s) => ({ s, have: false }))]
  if (!chunks.length) return <p className="text-muted-foreground">The catalogue lists no core skills for {match.role_title} yet.</p>
  return (
    <div>
      <p className="mb-3 text-sm text-muted-foreground">
        For <b className="text-foreground">{match.role_title}</b>
      </p>
      <div className="flex h-11 gap-1.5" role="img" aria-label={`${have.length} skills matched, ${missing.length} to build`}>
        {chunks.map((c, i) => (
          <i
            key={c.s.skill_id}
            data-enter="pop"
            title={c.s.name}
            className={c.have ? 'flex-1 rounded-[12px] bg-primary' : 'hatch flex-1 rounded-[12px]'}
            style={{ opacity: c.have ? 1 - i * 0.07 : 1 }}
          />
        ))}
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">You have</p>
          <ul className="flex flex-wrap gap-1.5">
            {have.length === 0 && <li className="text-sm text-muted-foreground">None of the core skills yet</li>}
            {have.map((s) => (
              <li key={s.skill_id} data-enter="item" className="inline-flex items-center gap-1.5 rounded-full bg-well px-2.5 py-1 text-sm font-semibold">
                <Check className="size-3.5 text-good" aria-hidden />
                {s.name}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">To build</p>
          <ul className="flex flex-wrap gap-1.5">
            {missing.length === 0 && <li className="text-sm text-muted-foreground">Nothing missing from the core list</li>}
            {missing.map((s) => (
              <li key={s.skill_id} data-enter="item" className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-line-2 px-2.5 py-1 text-sm font-semibold">
                <Plus className="size-3.5 text-tomato" aria-hidden />
                {s.name}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
