import { FileSearch, Layers } from 'lucide-react'
import { ApiWarnings } from '@/components/api-warnings'
import { AssistCard } from '@/components/dashboard/assist-card'
import { SkillGap } from '@/components/dashboard/skill-gap'
import { TopMatchCard } from '@/components/dashboard/top-match-card'
import { Card, CardHeader } from '@/components/ui/card'
import type { APIEnvelope, MatchPayload, RoleMatch } from '@/types/api'

/** Score, breakdown, skill gap and the evidence behind them, for one role. */
export function OverviewTab({ match, rank, envelope }: { match: RoleMatch; rank: number; envelope: APIEnvelope<MatchPayload> }) {
  return (
    <div className="grid gap-4 lg:grid-cols-12">
      <div className="lg:col-span-7">
        <TopMatchCard match={match} eyebrow={`#${rank + 1} of your ${envelope.data.matches.length} matches`} workspaceLink={false} />
      </div>
      <div className="lg:col-span-5">
        <AssistCard match={match} mode={envelope.data_mode} />
      </div>
      <Card className="lg:col-span-7" aria-labelledby="role-gap-title">
        <CardHeader id="role-gap-title" title="Skill gap" icon={Layers} />
        <SkillGap match={match} />
      </Card>
      <Card className="lg:col-span-5" aria-labelledby="evidence-title">
        <CardHeader id="evidence-title" title="Evidence" subtitle="Where this estimate comes from" icon={FileSearch} />
        <dl className="grid gap-2 text-sm">
          {[
            ['Score type', match.score_type?.replace(/_/g, ' ') ?? 'alignment estimate'],
            ['Method version', envelope.data.methodology_version],
            ['Catalogue', `${envelope.data.catalog_coverage.verified} of ${envelope.data.catalog_coverage.total_target} target roles verified`],
          ].map(([k, v]) => (
            <div key={k} data-enter="item" className="flex justify-between gap-4 rounded-[14px] bg-well px-3 py-2">
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="text-right font-semibold">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">Evidence records</p>
        {match.evidence_ids?.length ? (
          <ul className="flex flex-wrap gap-1.5">
            {match.evidence_ids.map((id) => (
              <li key={id} data-enter="item" className="rounded-full bg-well px-2.5 py-1 font-mono text-xs">
                {id}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No evidence records were returned for this role.</p>
        )}
      </Card>
      <ApiWarnings items={envelope.warnings} open className="lg:col-span-12" />
    </div>
  )
}
