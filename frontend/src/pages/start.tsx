import { GraduationCap, Heart, ListChecks, Sparkles, Wrench } from 'lucide-react'
import { Page } from '@/components/page/page'
import { Card, CardHeader } from '@/components/ui/card'

const STEPS = [
  { icon: GraduationCap, label: 'Education', text: 'Level, degree and semester' },
  { icon: Wrench, label: 'Skills', text: 'Searchable chips with a self-rated level' },
  { icon: Sparkles, label: 'Projects & experience', text: 'What you have built or done' },
  { icon: Heart, label: 'Interests', text: 'Fields and causes you care about' },
  { icon: ListChecks, label: 'Review', text: 'Check everything, then analyse' },
]

// Step 2 placeholder for the intake wizard (step 4).
export default function Start() {
  return (
    <Page
      title="Build your profile"
      crumbs={[{ label: 'Workspace', to: '/dashboard' }, { label: 'Profile' }]}
      subtitle="Five short steps. Nothing about your age, gender or background is asked or used."
    >
      <Card className="max-w-3xl">
        <CardHeader title="What we'll ask" icon={ListChecks} />
        <ol className="grid gap-1">
          {STEPS.map((s, i) => (
            <li key={s.label} data-enter="item" className="flex items-center gap-3 rounded-tile px-2 py-2.5 hover:bg-well">
              <span className="grid size-9 flex-none place-items-center rounded-[10px] bg-well font-mono font-bold text-muted-foreground">
                {i + 1}
              </span>
              <s.icon className="size-[18px] flex-none text-primary" aria-hidden />
              <span className="grid">
                <b>{s.label}</b>
                <small className="text-sm text-muted-foreground">{s.text}</small>
              </span>
            </li>
          ))}
        </ol>
      </Card>
    </Page>
  )
}
