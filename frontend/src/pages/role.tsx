import { useLayoutEffect, useRef, useState } from 'react'
import { BriefcaseBusiness, FolderKanban, Globe2, LayoutGrid, Route, Split, TrendingUp } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router'
import { EmptyState, ErrorState } from '@/components/api-states'
import { LearningPipeline } from '@/components/dashboard/learning-pipeline'
import { TrendSnapshot } from '@/components/dashboard/trend-snapshot'
import { DataModeBadge } from '@/components/data-mode-badge'
import { NoProfile } from '@/components/no-profile'
import { Page } from '@/components/page/page'
import { OverviewTab } from '@/components/role/overview-tab'
import { ProjectList } from '@/components/role/projects-tab'
import { ScenariosTab } from '@/components/role/scenarios-tab'
import { SdgList } from '@/components/role/sdg-list'
import { Segmented } from '@/components/role/segmented'
import { TabFrame } from '@/components/role/tab-frame'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useMatches } from '@/hooks/use-matches'
import { useNavPill } from '@/hooks/use-nav-pill'
import { useRequest } from '@/hooks/use-request'
import { api } from '@/lib/api'
import { useStoredProfile } from '@/lib/profile-store'
import { roleTitleFromId } from '@/lib/role-copy'
import { cn } from '@/lib/utils'

const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutGrid },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
  { id: 'scenarios', label: 'Scenarios', icon: Split },
  { id: 'roadmap', label: 'Roadmap', icon: Route },
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'sdgs', label: 'SDGs', icon: Globe2 },
] as const
type TabId = (typeof TABS)[number]['id']

const HOURS = [4, 8, 12, 20].map((h) => ({ value: h, label: `${h} h/wk` }))

function TabBar({ active }: { active: TabId }) {
  const track = useRef<HTMLDivElement>(null)
  const pill = useRef<HTMLSpanElement>(null)
  const scroller = useRef<HTMLElement>(null)
  useNavPill(track, pill, active, 'x')
  // on phones the bar scrolls sideways; keep the open tab in view
  useLayoutEffect(() => {
    const nav = scroller.current
    const item = nav?.querySelector<HTMLElement>('[aria-current="page"]')
    if (nav && item) nav.scrollLeft = item.offsetLeft - (nav.clientWidth - item.offsetWidth) / 2
  }, [active])
  return (
    <nav ref={scroller} aria-label="Role sections" data-enter="head" className="-mx-1 mb-4 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div ref={track} className="relative flex w-max rounded-full border border-line bg-glass-2 p-1 backdrop-blur-md">
        <span ref={pill} aria-hidden className="pointer-events-none absolute top-1 bottom-1 left-0 z-0 rounded-full bg-ink opacity-0 shadow-[0_8px_18px_-10px_#0008]" />
        {TABS.map((t) => (
          <Link
            key={t.id}
            to={t.id === 'overview' ? '?' : `?tab=${t.id}`}
            replace
            preventScrollReset
            aria-current={t.id === active ? 'page' : undefined}
            className={cn(
              'relative z-[1] flex items-center gap-1.5 rounded-full px-4 py-2 text-md font-semibold whitespace-nowrap transition-colors duration-200',
              t.id === active ? 'text-ink-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <t.icon className="size-4" aria-hidden />
            {t.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}

/**
 * Role workspace. Each tab calls its own endpoint the first time it is opened and keeps the
 * result while the student moves between tabs; the tab lives in ?tab= so links can open it.
 */
export default function Role() {
  const { roleId = '' } = useParams()
  const [params] = useSearchParams()
  const tab: TabId = TABS.some((t) => t.id === params.get('tab')) ? (params.get('tab') as TabId) : 'overview'
  const stored = useStoredProfile()
  const profile = stored?.profile
  const [match, retryMatch] = useMatches(stored)

  // fetch a tab's data on first visit, then keep it (reset when the role changes)
  const [visited, setVisited] = useState({ roleId, tabs: new Set<TabId>([tab]) })
  if (visited.roleId !== roleId) setVisited({ roleId, tabs: new Set([tab]) })
  else if (!visited.tabs.has(tab)) setVisited({ roleId, tabs: new Set(visited.tabs).add(tab) })
  const open = (t: TabId) => visited.roleId === roleId && visited.tabs.has(t)

  const [hours, setHours] = useState(8)
  const base = stored ? `${roleId}:${stored.analyzed_at}` : null
  const keyFor = (t: TabId, extra = '') => (base && open(t) ? `${t}:${base}${extra}` : null)

  const trends = useRequest(open('trends') ? `trends:${roleId}` : null, (signal) => api.getTrends({ role_id: roleId, limit: 20 }, { signal }))
  const moderate = useRequest(keyFor('scenarios', ':moderate'), (signal) => api.simulateScenario({ profile: profile!, scenario_id: 'moderate' }, { signal }))
  const fast = useRequest(keyFor('scenarios', ':fast'), (signal) => api.simulateScenario({ profile: profile!, scenario_id: 'fast' }, { signal }))
  const roadmap = useRequest(keyFor('roadmap', `:${hours}`), (signal) => api.generateRoadmap({ profile: profile!, role_id: roleId, hours_per_week: hours }, { signal }))
  const projects = useRequest(keyFor('projects'), (signal) => api.recommendProjects({ profile: profile!, role_id: roleId }, { signal }))
  const sdgs = useRequest(open('sdgs') ? `sdgs:${roleId}` : null, (signal) => api.getSdgs(roleId, { signal }))

  const env = match.status === 'ok' ? match.data : null
  const rank = env ? env.data.matches.findIndex((m) => m.role_id === roleId) : -1
  const role = rank >= 0 ? env!.data.matches[rank] : undefined
  const title = role?.role_title ?? roleTitleFromId(roleId)

  return (
    <Page
      title={title}
      crumbs={[{ label: 'Future roles', to: '/roles' }, { label: title }]}
      subtitle="How this role lines up with your profile, the trends behind it and a path to close the gap."
      meta={
        <>
          {env && <DataModeBadge mode={env.data_mode} />}
          {role && (
            <Badge tone="slate" dot>
              #{rank + 1} match · {Math.round(role.score)} / 100 alignment estimate
            </Badge>
          )}
          {stored?.demo && <Badge tone="primary">Demo student</Badge>}
        </>
      }
    >
      {!stored ? (
        <NoProfile what={`how ${title} lines up with your skills`} />
      ) : (
        <>
          <TabBar active={tab} />

          <div key={tab}>
            {tab === 'overview' && (
              <>
                {match.status === 'loading' && <Skeleton className="h-[360px] rounded-card" />}
                {match.status === 'error' && <ErrorState error={match.error} onRetry={retryMatch} />}
                {env && role && <OverviewTab match={role} rank={rank} envelope={env} />}
                {env && !role && (
                  <Card>
                    <EmptyState
                      title="Not among your matches"
                      body={`${title} is not in the ${env.data.matches.length} roles that line up with your profile right now, so there is no alignment estimate to show. The other tabs still work.`}
                      action={
                        <Button asChild variant="secondary">
                          <Link to="/roles">
                            <BriefcaseBusiness />
                            See your matches
                          </Link>
                        </Button>
                      }
                    />
                  </Card>
                )}
              </>
            )}

            {tab === 'trends' && (
              <TabFrame title="Skill trends" subtitle={`Dated GitHub developer-activity signals for ${title} skills`} icon={TrendingUp} state={trends[0]} retry={trends[1]}>
                {(d) => <TrendSnapshot trends={d} />}
              </TabFrame>
            )}

            {tab === 'scenarios' && <ScenariosTab roleId={roleId} baseline={role?.score} moderate={moderate} fast={fast} />}

            {tab === 'roadmap' && (
              <TabFrame
                title="Learning roadmap"
                subtitle={roadmap[0].status === 'ok' ? `${roadmap[0].data.data.total_estimated_hours} h in total · about ${Math.ceil((roadmap[0].data.data.total_estimated_hours / hours) * 10) / 10} weeks at ${hours} h a week` : `Steps to close the gap for ${title}`}
                icon={Route}
                state={roadmap[0]}
                retry={roadmap[1]}
                controls={<Segmented label="Hours per week" value={hours} options={HOURS} onChange={setHours} />}
              >
                {(d) =>
                  d.steps.length ? (
                    <LearningPipeline steps={d.steps} skills={role?.missing_skills} detailed />
                  ) : (
                    <EmptyState title="No roadmap steps" body="Either nothing is missing for this role, or none of the missing skills has a learning resource in the catalogue yet." />
                  )
                }
              </TabFrame>
            )}

            {tab === 'projects' && (
              <TabFrame title="Portfolio projects" subtitle="Real public datasets and tutorials; hours are team estimates" icon={FolderKanban} state={projects[0]} retry={projects[1]}>
                {(d) =>
                  d.projects.length ? (
                    <ProjectList projects={d.projects} profile={profile!} roleId={roleId} />
                  ) : (
                    <EmptyState title="No projects yet" body="No verified projects are catalogued for this role yet." />
                  )
                }
              </TabFrame>
            )}

            {tab === 'sdgs' && (
              <TabFrame title="Sustainable Development Goals" subtitle="How this role and its skills connect to the UN SDGs" icon={Globe2} state={sdgs[0]} retry={sdgs[1]}>
                {(d) => <SdgList data={d} match={role} />}
              </TabFrame>
            )}
          </div>
        </>
      )}
    </Page>
  )
}
