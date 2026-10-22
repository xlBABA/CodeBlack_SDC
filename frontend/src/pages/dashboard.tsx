import { BriefcaseBusiness, History, Layers, Route, Timer, TrendingUp, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { ApiWarnings } from '@/components/api-warnings'
import { EmptyState, ErrorNotice, ErrorState } from '@/components/api-states'
import { AssistCard } from '@/components/dashboard/assist-card'
import { KpiChip } from '@/components/dashboard/kpi-chip'
import { LearningPipeline } from '@/components/dashboard/learning-pipeline'
import { NextUp } from '@/components/dashboard/next-up'
import { RoleTiles } from '@/components/dashboard/role-tiles'
import { SkillGap } from '@/components/dashboard/skill-gap'
import { TopMatchCard } from '@/components/dashboard/top-match-card'
import { TrendSnapshot } from '@/components/dashboard/trend-snapshot'
import { DataModeBadge } from '@/components/data-mode-badge'
import { NoProfile } from '@/components/no-profile'
import { Page } from '@/components/page/page'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useDemoStudent } from '@/hooks/use-demo-student'
import { useMatches } from '@/hooks/use-matches'
import { useRequest } from '@/hooks/use-request'
import { api } from '@/lib/api'
import { useStoredProfile } from '@/lib/profile-store'

/** Hours per week the dashboard roadmap assumes; the role workspace lets the student change it. */
const HOURS_PER_WEEK = 8

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
  const stored = useStoredProfile()
  // while the demo student is being analysed, don't match the previous profile
  const profile = demo.loading || demo.error ? null : stored
  const [match, retryMatch] = useMatches(profile)

  const m = match.status === 'ok' ? match.data : null
  const matches = m?.data.matches ?? []
  const top = matches[0]
  const roleKey = profile && top ? `${top.role_id}:${profile.analyzed_at}` : null

  const [trends, retryTrends] = useRequest(roleKey && `trends:${roleKey}`, (signal) => api.getTrends({ role_id: top!.role_id, limit: 4 }, { signal }))
  const [roadmap, retryRoadmap] = useRequest(roleKey && `roadmap:${roleKey}`, (signal) =>
    api.generateRoadmap({ profile: profile!.profile, role_id: top!.role_id, hours_per_week: HOURS_PER_WEEK }, { signal }),
  )
  const road = roadmap.status === 'ok' ? roadmap.data : null

  return (
    <Page
      title="Career overview"
      docTitle="Overview"
      subtitle="Where your skills point today, what is shifting in the market, and what to learn next. It informs your choice; it does not make it."
      meta={
        <>
          {m && <DataModeBadge mode={m.data_mode} />}
          {stored?.demo && <Badge tone="primary">Demo student</Badge>}
          {m && (
            <Badge tone="slate" dot>
              {m.data.catalog_coverage.verified} of {m.data.catalog_coverage.total_target} roles verified
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
      {demo.error && <ErrorState error={demo.error} onRetry={demo.retry} />}
      {!demo.error && !profile && !demo.loading && <NoProfile what="the roles your skills line up with" />}
      {(demo.loading || (profile && match.status === 'loading')) && <DashboardSkeleton />}
      {match.status === 'error' && profile && <ErrorState error={match.error} onRetry={retryMatch} />}

      {m && !top && (
        <Card>
          <EmptyState
            title="No role matches yet"
            body="None of the verified roles lines up with this profile yet. Add a few skills and a project and try again."
            action={
              <Button asChild>
                <Link to="/start">Add skills</Link>
              </Button>
            }
          />
        </Card>
      )}

      {m && top && profile && (
        <div className="grid gap-4 lg:grid-cols-12">
          <div data-enter="head" className="flex flex-wrap gap-x-10 gap-y-4 py-1 lg:col-span-12">
            <KpiChip icon={BriefcaseBusiness} value={matches.length} label={`roles matched, of ${m.data.catalog_coverage.verified} verified`} />
            <KpiChip icon={Layers} value={top.missing_skills?.length ?? 0} label={`skills to build for ${top.role_title.toLowerCase()}`} />
            {road && <KpiChip icon={Timer} value={road.data.total_estimated_hours} format="hours1" label="on your current roadmap" />}
          </div>

          <div className="lg:col-span-7">
            <TopMatchCard match={top} />
          </div>
          <Card className="lg:col-span-5" aria-labelledby="matches-title">
            <CardHeader
              id="matches-title"
              title="All matches"
              subtitle="Ranked by alignment estimate"
              icon={BriefcaseBusiness}
              action={
                <Link to="/roles" className="text-sm font-semibold text-primary hover:underline">
                  See all {matches.length}
                </Link>
              }
            />
            <RoleTiles matches={matches.slice(0, 4)} />
          </Card>

          <Card className="lg:col-span-5" aria-labelledby="gap-title">
            <CardHeader id="gap-title" title="Skill gap" icon={Layers} />
            <SkillGap match={top} />
          </Card>

          <Card className="lg:col-span-4" aria-labelledby="trend-title">
            <CardHeader
              id="trend-title"
              title="Trend snapshot"
              subtitle={`Skill signals for ${top.role_title}`}
              icon={TrendingUp}
              action={trends.status === 'ok' ? <DataModeBadge mode={trends.data.data_mode} /> : undefined}
            />
            {trends.status === 'loading' && <Skeleton className="h-56 rounded-tile" />}
            {trends.status === 'error' && <ErrorNotice error={trends.error} onRetry={retryTrends} />}
            {trends.status === 'ok' &&
              (trends.data.data.signals?.length ? (
                <TrendSnapshot trends={trends.data.data} limit={3} />
              ) : (
                <EmptyState title="No signals yet" body="No dated trend signals have been collected for this role." />
              ))}
            {trends.status === 'ok' && <ApiWarnings items={trends.data.warnings} className="mt-3" />}
          </Card>

          <div className="lg:col-span-3">
            {roadmap.status === 'loading' && <Skeleton className="h-full min-h-[260px] rounded-card" />}
            {road && <NextUp roadmap={road.data} roleId={top.role_id} roleTitle={top.role_title} skills={top.missing_skills} />}
          </div>

          <Card className="lg:col-span-8" aria-labelledby="pipeline-title">
            <CardHeader
              id="pipeline-title"
              title="Learning pipeline"
              subtitle={road ? `${top.role_title} roadmap · ${road.data.total_estimated_hours} h at ${HOURS_PER_WEEK} h a week` : undefined}
              icon={Route}
              action={road ? <DataModeBadge mode={road.data_mode} /> : undefined}
            />
            {roadmap.status === 'loading' && <Skeleton className="h-48 rounded-tile" />}
            {roadmap.status === 'error' && <ErrorNotice error={roadmap.error} onRetry={retryRoadmap} />}
            {road &&
              (road.data.steps.length ? (
                <LearningPipeline steps={road.data.steps} skills={top.missing_skills} />
              ) : (
                <EmptyState
                  title="No roadmap steps"
                  body={top.missing_skills?.length ? 'None of the missing skills has a learning resource in the catalogue yet.' : `You already have every core skill listed for ${top.role_title}.`}
                />
              ))}
            {road && <ApiWarnings items={road.warnings} className="mt-4" />}
          </Card>

          <div className="grid gap-4 lg:col-span-4">
            <AssistCard match={top} mode={m.data_mode} />
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

          <ApiWarnings items={m.warnings} className="lg:col-span-12" />
        </div>
      )}
    </Page>
  )
}
