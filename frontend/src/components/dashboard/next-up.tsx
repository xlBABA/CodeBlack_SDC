import { ArrowRight, BookOpen, Clock } from 'lucide-react'
import { Link } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { skillName } from '@/content/skills'
import type { RoadmapPayload, SkillRef } from '@/types/api'

/** The first step of the roadmap (Halden "Next up" idea), on a soft primary tint. */
export function NextUp({ roadmap, roleId, roleTitle, skills }: { roadmap: RoadmapPayload; roleId: string; roleTitle: string; skills?: SkillRef[] }) {
  const step = roadmap.steps[0]
  const share = step && roadmap.total_estimated_hours ? (step.estimated_hours / roadmap.total_estimated_hours) * 100 : 0
  return (
    <Card className="flex h-full flex-col border-[color-mix(in_srgb,var(--primary)_30%,transparent)] bg-[color-mix(in_srgb,var(--primary)_12%,var(--glass))]">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-xl font-bold tracking-[-0.01em]">Next up</h2>
        {step && (
          <Badge tone="primary" dot>
            Step 1 of {roadmap.steps.length}
          </Badge>
        )}
      </div>
      {step ? (
        <>
          <p className="text-[1.6rem] leading-[1.1] font-extrabold tracking-[-0.025em]">{skillName(step.skill_id, skills)}</p>
          <p className="mt-2 flex items-center gap-1.5 text-muted-foreground">
            <Clock className="size-4" aria-hidden />
            {step.estimated_hours} h · for {roleTitle}
          </p>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
            <BookOpen className="size-4" aria-hidden />
            <code className="truncate font-mono text-xs">{step.resource_id}</code>
          </p>
          <div className="mt-auto pt-6">
            <p className="mb-1.5 text-sm text-muted-foreground">
              {step.estimated_hours} of {roadmap.total_estimated_hours} roadmap hours
            </p>
            <div className="h-2 overflow-hidden rounded-full bg-well">
              <i data-enter="bar" className="block h-full rounded-full bg-primary" style={{ width: `${share}%` }} />
            </div>
            <Link
              to={`/roles/${roleId}?tab=roadmap`}
              className="mt-4 flex h-11 items-center justify-center gap-2 rounded-full bg-primary font-bold text-primary-foreground transition hover:brightness-110"
            >
              Open roadmap
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </div>
        </>
      ) : (
        <p className="text-muted-foreground">
          {skills?.length ? 'No roadmap steps yet: none of the missing skills has a learning resource in the catalogue.' : `Nothing to close: you already have every core skill listed for ${roleTitle}.`}
        </p>
      )}
    </Card>
  )
}
