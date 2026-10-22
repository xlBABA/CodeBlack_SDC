import { useState } from 'react'
import { ArrowRight, Check, Clock, Database, FlaskConical, LoaderCircle, Plus } from 'lucide-react'
import { ErrorNotice } from '@/components/api-states'
import { DataModeBadge } from '@/components/data-mode-badge'
import { CountUp } from '@/components/page/count-up'
import { Button } from '@/components/ui/button'
import { skillName } from '@/content/skills'
import { useRequest } from '@/hooks/use-request'
import { api } from '@/lib/api'
import type { RecommendedProject, StudentProfile } from '@/types/api'

/** POST /projects/simulate for one project, run only when the student asks for it. */
function Simulation({ profile, roleId, project }: { profile: StudentProfile; roleId: string; project: RecommendedProject }) {
  const [state, retry] = useRequest(`sim:${roleId}:${project.project_id}`, (signal) => api.simulateProject({ profile, role_id: roleId, project_id: project.project_id }, { signal }))
  if (state.status === 'loading')
    return (
      <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground">
        <LoaderCircle className="size-4 animate-spin" aria-hidden />
        Recalculating as if you had these skills…
      </p>
    )
  if (state.status === 'error') return <ErrorNotice error={state.error} onRetry={retry} />
  const { data, data_mode } = state.data
  return (
    <div data-enter="item" className="rounded-[16px] border border-dashed border-line-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">What if you built this</p>
        <DataModeBadge mode={data_mode} />
      </div>
      <div className="mt-2 flex items-center gap-3">
        <CountUp value={data.baseline_score} className="text-3xl font-extrabold tracking-[-0.04em] text-muted-foreground" />
        <ArrowRight className="size-5 text-primary" aria-hidden />
        <CountUp value={data.simulated_score} className="text-3xl font-extrabold tracking-[-0.04em]" />
        <span className="text-sm text-muted-foreground">alignment estimate</span>
      </div>
      {data.assumed_skill_ids.length > 0 && (
        <p className="mt-2 text-sm">
          Assumes you gain: <b>{data.assumed_skill_ids.map((id) => skillName(id)).join(', ')}</b>
        </p>
      )}
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground italic">{data.disclaimer}</p>
    </div>
  )
}

function ProjectCard({ project, profile, roleId }: { project: RecommendedProject; profile: StudentProfile; roleId: string }) {
  const [simulate, setSimulate] = useState(false)
  const owned = new Set(profile.skills.map((s) => s.skill_id))
  return (
    <li data-enter="item" className="grid content-start gap-4 rounded-tile border border-line bg-raised p-4 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-lg font-bold tracking-[-0.01em]">{project.title}</h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Clock className="size-4" aria-hidden />
              {project.estimated_hours} h
            </span>
            {project.source_ids.map((s) => (
              <span key={s} className="inline-flex items-center gap-1">
                <Database className="size-4" aria-hidden />
                <code className="font-mono text-xs">{s}</code>
              </span>
            ))}
          </p>
        </div>
        {!simulate && (
          <Button size="sm" variant="secondary" onClick={() => setSimulate(true)}>
            <FlaskConical />
            Simulate impact
          </Button>
        )}
      </div>
      <ul className="flex flex-wrap gap-1.5" aria-label="Skills this project uses">
        {project.skill_ids.map((id) => {
          const have = owned.has(id)
          return (
            <li key={id} className={have ? 'inline-flex items-center gap-1.5 rounded-full bg-well px-2.5 py-1 text-sm font-semibold' : 'inline-flex items-center gap-1.5 rounded-full border border-dashed border-line-2 px-2.5 py-1 text-sm font-semibold'}>
              {have ? <Check className="size-3.5 text-good" aria-hidden /> : <Plus className="size-3.5 text-tomato" aria-hidden />}
              <span className="sr-only">{have ? 'You have: ' : 'You would build: '}</span>
              {skillName(id)}
            </li>
          )
        })}
      </ul>
      {project.milestones.length > 0 && (
        <ol className="grid gap-1.5 text-sm">
          {project.milestones.map((m, i) => (
            <li key={m} className="flex gap-3">
              <span className="grid size-6 flex-none place-items-center rounded-full bg-well text-xs font-bold">{i + 1}</span>
              <span className="pt-0.5">{m}</span>
            </li>
          ))}
        </ol>
      )}
      {simulate && <Simulation profile={profile} roleId={roleId} project={project} />}
    </li>
  )
}

export function ProjectList({ projects, profile, roleId }: { projects: RecommendedProject[]; profile: StudentProfile; roleId: string }) {
  return (
    <ul className="grid gap-3 lg:grid-cols-2">
      {projects.map((p) => (
        <ProjectCard key={p.project_id} project={p} profile={profile} roleId={roleId} />
      ))}
    </ul>
  )
}
