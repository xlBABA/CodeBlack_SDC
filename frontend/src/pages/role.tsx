import { useParams } from 'react-router'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Page } from '@/components/page/page'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

const TABS = ['Overview', 'Trends', 'Scenarios', 'Roadmap', 'Projects', 'SDGs']

const titleFromId = (id = '') => id.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

// Step 2 placeholder for the role workspace (step 4).
export default function Role() {
  const { roleId } = useParams()
  const title = titleFromId(roleId)
  return (
    <Page
      title={title || 'Role'}
      crumbs={[{ label: 'Future roles', to: '/dashboard' }, { label: title }]}
      subtitle="How this role lines up with your profile, the trends behind it and a path to close the gap."
      meta={<DataModeBadge mode="fixture" />}
    >
      <Card>
        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <Badge key={t} tone="slate">
              {t}
            </Badge>
          ))}
        </div>
      </Card>
    </Page>
  )
}
