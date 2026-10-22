import { BookOpen } from 'lucide-react'
import { skillName } from '@/content/skills'
import type { RoadmapStep, SkillRef } from '@/types/api'
import { cn } from '@/lib/utils'

/**
 * The roadmap in order: a pill header per step and its card hanging off a dotted connector
 * (Mender idea). The API orders the steps; nothing is re-ranked here.
 */
export function LearningPipeline({ steps, skills, detailed = false }: { steps: RoadmapStep[]; skills?: SkillRef[]; detailed?: boolean }) {
  return (
    <ol className={cn('grid gap-4', steps.length > 1 && 'md:grid-cols-2', steps.length > 2 && 'xl:grid-cols-3')}>
      {steps.map((s, i) => (
        <li key={`${s.skill_id}-${s.resource_id}`} aria-label={`Step ${i + 1}: ${skillName(s.skill_id, skills)}`}>
          <header className="flex h-11 items-center justify-center gap-2 rounded-full border border-line-2 font-semibold">
            Step {i + 1}
            <span className="grid h-6 place-items-center rounded-full bg-well px-2 text-xs">{s.estimated_hours} h</span>
          </header>
          <div data-enter="item" className="relative grid pt-5">
            {/* dotted connector from the header */}
            <span aria-hidden className="absolute top-0 left-1/2 h-5 border-l-2 border-dotted border-line-2" />
            <span aria-hidden className="absolute top-[-3px] left-1/2 size-1.5 -translate-x-1/2 rounded-full bg-line-2" />
            <div className={cn('grid gap-2 rounded-[18px] border border-rim bg-raised p-3 shadow-card dark:border-line', i === 0 && 'ring-2 ring-primary/40')}>
              <div className="flex items-center gap-3">
                <span className={cn('grid size-9 flex-none place-items-center rounded-full bg-well', i === 0 ? 'text-primary' : 'text-muted-foreground')}>
                  <BookOpen className="size-4" aria-hidden />
                </span>
                <span className="grid min-w-0">
                  <b className="truncate font-semibold">{skillName(s.skill_id, skills)}</b>
                  <small className="truncate font-mono text-xs text-muted-foreground">{s.resource_id}</small>
                </span>
              </div>
              <p className={cn('text-sm leading-snug text-muted-foreground', !detailed && 'line-clamp-3')}>{s.reason}</p>
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}
