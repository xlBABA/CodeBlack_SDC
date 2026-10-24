import { FileUp, Wrench } from 'lucide-react'
import { Link } from 'react-router'
import { EmptyState } from '@/components/api-states'
import { ApiWarnings } from '@/components/api-warnings'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { ProfileSource } from '@/lib/profile-store'

/** Shown instead of ranked roles when nothing in the profile counts toward a role. */
export function NoRecognizedSkills({ source, warnings }: { source?: ProfileSource; warnings: string[] }) {
  const cv = source === 'cv'
  return (
    <Card>
      <EmptyState
        title="No recognized skills yet"
        body="Add at least one recognized skill to get meaningful career recommendations."
        action={
          <Button asChild>
            <Link to={cv ? '/start?path=cv&step=review' : '/start?step=skills'}>
              {cv ? <FileUp /> : <Wrench />}
              {cv ? 'Back to your CV review' : 'Back to your skills'}
            </Link>
          </Button>
        }
      />
      <ApiWarnings items={warnings} open className="mt-4" />
    </Card>
  )
}
