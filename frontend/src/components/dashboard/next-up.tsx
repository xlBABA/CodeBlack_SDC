import { ArrowRight, Clock } from 'lucide-react'
import { Link } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import type { Roadmap } from '@/mocks/types'

/** The step you are on (Halden "Next up" idea), on a soft primary tint. */
export function NextUp({ roadmap }: { roadmap: Roadmap }) {
  const step = roadmap.steps.find((s) => s.status === 'doing') ?? roadmap.steps.find((s) => s.status === 'todo')
  const doneHours = roadmap.steps.filter((s) => s.status === 'done').reduce((n, s) => n + s.hours, 0)
  return (
    <Card className="flex h-full flex-col border-[color-mix(in_srgb,var(--primary)_30%,transparent)] bg-[color-mix(in_srgb,var(--primary)_12%,var(--glass))]">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-xl font-bold tracking-[-0.01em]">Next up</h2>
        <Badge tone="primary" dot>
          {step?.status === 'doing' ? 'In progress' : 'Not started'}
        </Badge>
      </div>
      {step ? (
        <>
          <p className="text-[1.6rem] leading-[1.1] font-extrabold tracking-[-0.025em]">{step.title}</p>
          <p className="mt-2 flex items-center gap-1.5 text-muted-foreground">
            <Clock className="size-4" aria-hidden />
            {step.skill} · {step.hours} h
          </p>
          <div className="mt-auto pt-6">
            <p className="mb-1.5 text-sm text-muted-foreground">
              {doneHours} of {roadmap.total_hours} roadmap hours done
            </p>
            <div className="h-2 overflow-hidden rounded-full bg-well">
              <i data-enter="bar" className="block h-full rounded-full bg-primary" style={{ width: `${(doneHours / roadmap.total_hours) * 100}%` }} />
            </div>
            <Link
              to={`/roles/${roadmap.role_id}`}
              className="mt-4 flex h-11 items-center justify-center gap-2 rounded-full bg-primary font-bold text-primary-foreground transition hover:brightness-110"
            >
              Open roadmap
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </div>
        </>
      ) : (
        <p className="text-muted-foreground">No roadmap steps yet.</p>
      )}
    </Card>
  )
}
