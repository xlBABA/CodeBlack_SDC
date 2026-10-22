import { BriefcaseBusiness, History, Layers, Route, Timer, TrendingUp, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { EmptyState, ErrorState } from '@/components/api-states'
import { AssistCard } from '@/components/dashboard/assist-card'
import { KpiChip } from '@/components/dashboard/kpi-chip'
import { LearningPipeline } from '@/components/dashboard/learning-pipeline'
import { NextUp } from '@/components/dashboard/next-up'
import { RoleTiles } from '@/components/dashboard/role-tiles'
import { SkillGap } from '@/components/dashboard/skill-gap'
import { TopMatchCard } from '@/components/dashboard/top-match-card'
import { TrendSnapshot } from '@/components/dashboard/trend-snapshot'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Page } from '@/components/page/page'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useApi } from '@/hooks/use-api'
import { useDemoStudent } from '@/hooks/use-demo-student'
import { api } from '@/mocks/api'

function DashboardSkeleton() {
  return (
    <div role="status" aria-label="Loading your overview" className="grid gap-4 lg:grid-cols-12">
      <Skeleton className="h-[330px] rounded-card lg:col-span-7" />
      <div className="grid grid-cols-2 gap-3 lg:col-span-5">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-[158px] rounded-tile" />
        ))}
      </div>
      <Skeleton className="h-[260px] rounded-card lg:col-span-5" />
      <Skeleton className="h-[260px] rounded-card lg:col-span-4" />
      <Skeleton className="h-[260px] rounded-card lg:col-span-3" />
    </div>
  )
}

/**
 * Overview. Layout ideas: header with KPI chips and solid role tiles (Rapport), a deep hero
 * card, hatched bars, "next up" and an assist card (Halden), a dotted-connector board (Mender).
 * Every number on this page comes from the API envelopes; nothing is scored here.
 */
export default function Dashboard() {
  const demo = useDemoStudent()
  const [analysis, retryAnalysis] = useApi(api.analyze)
  const [trends] = useApi(api.getTrends)
  const [roadmap] = useApi(api.getRoadmap)
  const [insights] = useApi(api.getInsights)

  const a = analysis.status === 'ok' ? analysis.envelope : null
  const matches = a?.data.matches ?? []
  const top = matches[0]

  return (
    <Page
      title="Career overview"
      docTitle="Overview"
      subtitle="Where your skills point today, what is shifting in the market, and what to learn next. It informs your choice; it does not make it."
      meta={
        <>
          {a && <DataModeBadge mode={a.data_mode} />}
          {demo && <Badge tone="primary">Demo student</Badge>}
          {a && (
            <Badge tone="slate" dot>
              {a.data.catalog.roles_verified} of {a.data.catalog.roles_total} roles verified
            </Badge>
          )}
        </>
      }
      actions={[
        <Button key="edit" variant="secondary" asChild>
          <Link to="/start">
            <UserRoundPen />
            Edit profile
          </Link>
        </Button>,
      ]}
    >
      {analysis.status === 'loading' && <DashboardSkeleton />}
      {analysis.status === 'error' && <ErrorState error={analysis.error} onRetry={retryAnalysis} />}

      {a && !top && (
        <Card>
          <EmptyState
            title="No role matches yet"
            body="Add a few skills and a project to your profile and we will show the roles they line up with."
            action={
              <Button asChild>
                <Link to="/start">Add skills</Link>
              </Button>
            }
          />
        </Card>
      )}

      {a && top && (
        <div className="grid gap-4 lg:grid-cols-12">
          <div data-enter="head" className="flex flex-wrap gap-x-10 gap-y-4 py-1 lg:col-span-12">
            <KpiChip icon={BriefcaseBusiness} value={matches.length} label="roles matched to your profile" />
            <KpiChip icon={Layers} value={top.missing_skills.length} label={`skills to build for ${top.title.toLowerCase()}`} />
            {roadmap.status === 'ok' && <KpiChip icon={Timer} value={roadmap.envelope.data.total_hours} format="hours" label="on your current roadmap" />}
          </div>

          <div className="lg:col-span-7">
            <TopMatchCard match={top} />
          </div>
          <Card className="lg:col-span-5" aria-labelledby="matches-title">
            <CardHeader id="matches-title" title="All matches" subtitle="Ranked by alignment estimate" icon={BriefcaseBusiness} />
            <RoleTiles matches={matches} />
          </Card>

          <Card className="lg:col-span-5" aria-labelledby="gap-title">
            <CardHeader id="gap-title" title="Skill gap" icon={Layers} />
            <SkillGap match={top} />
          </Card>

          <Card className="lg:col-span-4" aria-labelledby="trend-title">
            <CardHeader
              id="trend-title"
              title="Trend snapshot"
              subtitle={trends.status === 'ok' ? trends.envelope.data.window : 'Skill demand signals'}
              icon={TrendingUp}
              action={trends.status === 'ok' ? <DataModeBadge mode={trends.envelope.data_mode} /> : undefined}
            />
            {trends.status === 'loading' && <Skeleton className="h-56 rounded-tile" />}
            {trends.status === 'error' && <p className="text-muted-foreground">Trend signals are unavailable right now ({trends.error.code}).</p>}
            {trends.status === 'ok' &&
              (trends.envelope.data.signals.length ? (
                <TrendSnapshot signals={trends.envelope.data.signals} />
              ) : (
                <EmptyState title="No signals yet" body="Trend data has not been collected for this window." />
              ))}
          </Card>

          <div className="lg:col-span-3">{roadmap.status === 'ok' && <NextUp roadmap={roadmap.envelope.data} />}</div>

          <Card className="lg:col-span-8" aria-labelledby="pipeline-title">
            <CardHeader
              id="pipeline-title"
              title="Learning pipeline"
              subtitle={roadmap.status === 'ok' ? `${top.title} roadmap · ${roadmap.envelope.data.total_hours} h in total` : undefined}
              icon={Route}
              action={roadmap.status === 'ok' ? <DataModeBadge mode={roadmap.envelope.data_mode} /> : undefined}
            />
            {roadmap.status === 'ok' ? <LearningPipeline steps={roadmap.envelope.data.steps} /> : <Skeleton className="h-48 rounded-tile" />}
          </Card>

          <div className="grid gap-4 lg:col-span-4">
            {insights.status === 'ok' && <AssistCard notes={insights.envelope.data.notes} mode={insights.envelope.data_mode} />}
            {/* reserved slot for the future "What changed" panel */}
            <Card className="border-dashed !bg-transparent !shadow-none" aria-labelledby="changed-title">
              <div className="flex items-center gap-2.5">
                <span className="grid size-9 place-items-center rounded-full bg-well" aria-hidden>
                  <History className="size-[17px]" />
                </span>
                <h2 id="changed-title" className="text-lg font-bold">
                  What changed
                </h2>
                <Badge tone="faint" enter={false} className="ml-auto">
                  Coming soon
                </Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Compare this analysis with your next one: new skills, moved roles, fresher signals.</p>
            </Card>
          </div>

          {a.warnings.length > 0 && (
            <p data-enter="head" className="text-sm text-muted-foreground lg:col-span-12">
              {a.warnings.join(' ')}
            </p>
          )}
        </div>
      )}
    </Page>
  )
}
