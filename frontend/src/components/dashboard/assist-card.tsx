import { Lightbulb, Sparkles, TrendingUp, UserCheck } from 'lucide-react'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Card } from '@/components/ui/card'
import type { DataMode } from '@/mocks/types'

const ICON = { skill: Lightbulb, trend: TrendingUp, fit: UserCheck }

/** Assistant notes (Halden "Assist" idea), written as things to weigh up, not instructions. */
export function AssistCard({ notes, mode }: { notes: { kind: keyof typeof ICON; text: string }[]; mode: DataMode }) {
  return (
    <Card className="flex flex-col">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="grid size-9 place-items-center rounded-full bg-primary text-primary-foreground" aria-hidden>
            <Sparkles className="size-[17px]" />
          </span>
          <h2 className="text-xl font-bold tracking-[-0.01em]">Things to weigh up</h2>
        </div>
        <DataModeBadge mode={mode} />
      </div>
      <ul className="grid gap-2.5">
        {notes.map((n) => {
          const Icon = ICON[n.kind]
          return (
            <li key={n.text} data-enter="item" className="flex gap-3 rounded-[16px] bg-well p-3">
              <Icon className="mt-0.5 size-4 flex-none text-primary" aria-hidden />
              <span className="text-md leading-snug">{n.text}</span>
            </li>
          )
        })}
      </ul>
      <p className="mt-auto pt-4 text-xs text-muted-foreground">Suggestions to help you think it through. The decision is yours.</p>
    </Card>
  )
}
