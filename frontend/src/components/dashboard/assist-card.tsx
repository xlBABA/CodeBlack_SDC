import { Lightbulb, Sparkles, UserCheck } from 'lucide-react'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Card } from '@/components/ui/card'
import type { DataMode, RoleMatch } from '@/types/api'

/**
 * "Things to weigh up" (Halden "Assist" idea). Only the API's own explanation and caveats
 * for the top match are shown; there is no separate insights service, so nothing is invented.
 */
export function AssistCard({ match, mode }: { match: RoleMatch; mode: DataMode }) {
  const notes = [{ Icon: UserCheck, text: match.explanation }, ...(match.caveats ?? []).map((text) => ({ Icon: Lightbulb, text }))]
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
        {notes.map(({ Icon, text }) => (
          <li key={text} data-enter="item" className="flex gap-3 rounded-[16px] bg-well p-3">
            <Icon className="mt-0.5 size-4 flex-none text-primary" aria-hidden />
            <span className="text-md leading-snug">{text}</span>
          </li>
        ))}
      </ul>
      <p className="mt-auto pt-4 text-xs text-muted-foreground">Notes from the matching service about {match.role_title}. The decision is yours.</p>
    </Card>
  )
}
