import { Sparkles, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { EmptyState } from '@/components/api-states'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

/** Shown instead of results when no profile has been analysed in this session yet. */
export function NoProfile({ what = 'your results' }: { what?: string }) {
  return (
    <Card>
      <EmptyState
        title="No profile yet"
        body={`Build your profile (about two minutes) or try the synthetic demo student to see ${what}.`}
        action={
          <div className="flex flex-wrap justify-center gap-2.5">
            <Button asChild>
              <Link to="/start">
                <UserRoundPen />
                Build my profile
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/dashboard?demo=1">
                <Sparkles />
                Try the demo student
              </Link>
            </Button>
          </div>
        }
      />
    </Card>
  )
}
