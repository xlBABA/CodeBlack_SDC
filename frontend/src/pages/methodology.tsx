import { Ban, Calculator, Database, Scale } from 'lucide-react'
import { Page } from '@/components/page/page'
import { Card, CardHeader } from '@/components/ui/card'

// Step 2 placeholder for the methodology page (step 4).
export default function Methodology() {
  return (
    <Page
      title="How it works"
      crumbs={[{ label: 'Understand' }, { label: 'Methodology' }]}
      subtitle="What the alignment estimate measures, where data comes from and what the system does not do."
    >
      <div className="grid gap-4 md:grid-cols-2">
        {[
          { icon: Calculator, title: 'The alignment estimate' },
          { icon: Database, title: 'Live, cached and demo data' },
          { icon: Ban, title: 'What it does not do' },
          { icon: Scale, title: 'Fairness' },
        ].map((c) => (
          <Card key={c.title}>
            <CardHeader icon={c.icon} title={c.title} />
            <p data-enter="item" className="text-muted-foreground">
              Written in step 4.
            </p>
          </Card>
        ))}
      </div>
    </Page>
  )
}
