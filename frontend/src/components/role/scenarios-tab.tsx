import { FlaskConical, Gauge, Rocket } from 'lucide-react'
import { ApiWarnings } from '@/components/api-warnings'
import { ErrorNotice } from '@/components/api-states'
import { DataModeBadge } from '@/components/data-mode-badge'
import { CountUp } from '@/components/page/count-up'
import { Card, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { RequestState } from '@/hooks/use-request'
import type { APIEnvelope, ScenarioId, ScenarioPayload } from '@/types/api'

type Scenario = readonly [RequestState<APIEnvelope<ScenarioPayload>>, () => void]

const META: Record<ScenarioId, { title: string; Icon: typeof Gauge }> = {
  moderate: { title: 'Moderate change', Icon: Gauge },
  fast: { title: 'Fast change', Icon: Rocket },
}

function ScenarioCard({ id, state, retry, roleId, baseline }: { id: ScenarioId; state: RequestState<APIEnvelope<ScenarioPayload>>; retry: () => void; roleId: string; baseline?: number }) {
  const { title, Icon } = META[id]
  const env = state.status === 'ok' ? state.data : null
  const score = env?.data.matches.find((m) => m.role_id === roleId)?.score
  return (
    <Card aria-labelledby={`scenario-${id}`}>
      <CardHeader id={`scenario-${id}`} title={title} icon={Icon} action={env ? <DataModeBadge mode={env.data_mode} /> : undefined} />
      {state.status === 'loading' && <Skeleton className="h-48 rounded-tile" />}
      {state.status === 'error' && <ErrorNotice error={state.error} onRetry={retry} />}
      {env && (
        <>
          <div className="flex items-end gap-3">
            {score === undefined ? (
              <p className="text-muted-foreground">This role is not in the scenario’s top matches.</p>
            ) : (
              <>
                <CountUp value={score} className="text-[3.2rem] leading-[0.85] font-extrabold tracking-[-0.05em]" />
                <span className="pb-1 text-sm leading-tight font-semibold text-muted-foreground">
                  / 100 under this scenario
                  {baseline !== undefined && (
                    <>
                      <br />
                      {score === baseline ? 'same as today' : `${score > baseline ? '+' : ''}${Math.round(score - baseline)} vs today (${Math.round(baseline)})`}
                    </>
                  )}
                </span>
              </>
            )}
          </div>
          <p className="mt-5 mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">Assumptions</p>
          <ul className="grid gap-2">
            {env.data.assumptions.map((a) => (
              <li key={a} data-enter="item" className="rounded-[14px] bg-well p-3 text-sm leading-snug">
                {a}
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-muted-foreground italic">{env.data.uncertainty_note}</p>
          <ApiWarnings items={env.warnings} className="mt-4" />
        </>
      )}
    </Card>
  )
}

/** Both scenarios side by side, so the student sees the spread rather than one forecast. */
export function ScenariosTab({ roleId, baseline, moderate, fast }: { roleId: string; baseline?: number; moderate: Scenario; fast: Scenario }) {
  return (
    <div className="grid gap-4">
      <p data-enter="head" className="flex items-start gap-2 text-sm text-muted-foreground">
        <FlaskConical className="mt-0.5 size-4 flex-none" aria-hidden />
        Two “what if” views of how quickly this field could change. They are illustrations to think with, not forecasts.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <ScenarioCard id="moderate" state={moderate[0]} retry={moderate[1]} roleId={roleId} baseline={baseline} />
        <ScenarioCard id="fast" state={fast[0]} retry={fast[1]} roleId={roleId} baseline={baseline} />
      </div>
    </div>
  )
}
