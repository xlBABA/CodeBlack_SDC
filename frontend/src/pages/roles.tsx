import { BriefcaseBusiness, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { ApiWarnings } from '@/components/api-warnings'
import { EmptyState, ErrorState } from '@/components/api-states'
import { RoleTiles } from '@/components/dashboard/role-tiles'
import { DataModeBadge } from '@/components/data-mode-badge'
import { NoProfile } from '@/components/no-profile'
import { Page } from '@/components/page/page'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useMatches } from '@/hooks/use-matches'
import { useStoredProfile } from '@/lib/profile-store'

/** Every role the matching service returned for this profile, best-aligned first. */
export default function Roles() {
  const stored = useStoredProfile()
  const [match, retry] = useMatches(stored)
  const env = match.status === 'ok' ? match.data : null
  const matches = env?.data.matches ?? []

  return (
    <Page
      title="Future roles"
      crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Roles' }]}
      subtitle="The verified roles your profile lines up with, ranked by alignment estimate. Open one to see its trends, scenarios, roadmap, projects and SDG links."
      meta={
        env && (
          <>
            <DataModeBadge mode={env.data_mode} />
            <Badge tone="slate" dot>
              {env.data.catalog_coverage.verified} of {env.data.catalog_coverage.total_target} roles verified
            </Badge>
          </>
        )
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
      {!stored && <NoProfile what="the roles your skills line up with" />}
      {stored && match.status === 'loading' && (
        <div role="status" aria-label="Loading roles" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-[208px] rounded-tile" />
          ))}
        </div>
      )}
      {stored && match.status === 'error' && <ErrorState error={match.error} onRetry={retry} />}
      {env && (
        <Card aria-labelledby="roles-title">
          <CardHeader id="roles-title" title={`${matches.length} matched roles`} subtitle="The catalogue is still growing; roles not verified yet are never shown." icon={BriefcaseBusiness} />
          {matches.length ? (
            <RoleTiles matches={matches} className="lg:grid-cols-3" />
          ) : (
            <EmptyState title="No role matches yet" body="None of the verified roles lines up with this profile yet. Add a few skills and a project and try again." />
          )}
          <ApiWarnings items={env.warnings} className="mt-5" />
        </Card>
      )}
    </Page>
  )
}
