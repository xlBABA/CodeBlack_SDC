import { CheckCheck, CircleDashed, LoaderCircle } from 'lucide-react'
import type { RoadmapStep } from '@/mocks/types'
import { cn } from '@/lib/utils'

const COLUMNS = [
  { key: 'todo', label: 'To learn', Icon: CircleDashed },
  { key: 'doing', label: 'In progress', Icon: LoaderCircle },
  { key: 'done', label: 'Done', Icon: CheckCheck },
] as const

/** Board of roadmap steps: pill column headers, cards joined by dotted connectors (Mender idea). */
export function LearningPipeline({ steps }: { steps: RoadmapStep[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {COLUMNS.map(({ key, label, Icon }) => {
        const items = steps.filter((s) => s.status === key)
        return (
          <section key={key} aria-label={`${label}: ${items.length}`}>
            <header className="flex h-11 items-center justify-center gap-2 rounded-full border border-line-2 font-semibold">
              {label}
              <span className="grid size-6 place-items-center rounded-full bg-well text-xs">{items.length}</span>
            </header>
            <ol className="grid">
              {items.map((s) => (
                <li key={s.step_id} data-enter="item" className="relative grid pt-5">
                  {/* dotted connector from the header or the card above */}
                  <span aria-hidden className="absolute top-0 left-1/2 h-5 border-l-2 border-dotted border-line-2" />
                  <span aria-hidden className="absolute top-[-3px] left-1/2 size-1.5 -translate-x-1/2 rounded-full bg-line-2" />
                  <div className={cn('flex items-center gap-3 rounded-[18px] border border-rim bg-raised p-3 shadow-card dark:border-line', key === 'doing' && 'ring-2 ring-primary/40')}>
                    <span className={cn('grid size-9 flex-none place-items-center rounded-full', key === 'done' ? 'bg-[color-mix(in_srgb,var(--good)_18%,transparent)] text-good' : 'bg-well text-muted-foreground', key === 'doing' && 'text-primary')}>
                      <Icon className="size-4" aria-hidden />
                    </span>
                    <span className="grid min-w-0">
                      <b className="truncate font-semibold">{s.title}</b>
                      <small className="text-sm text-muted-foreground">
                        {s.skill} · {s.hours} h
                      </small>
                    </span>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )
      })}
    </div>
  )
}
