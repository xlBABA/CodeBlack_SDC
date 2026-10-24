import { Badge } from '@/components/ui/badge'
import type { DataMode } from '@/types/api'

const MODES: Record<DataMode, { label: string; tone: 'good' | 'sky' | 'warn'; hint: string }> = {
  live: { label: 'Live', tone: 'good', hint: 'Fetched just now from the analysis service' },
  cached: { label: 'Cached', tone: 'sky', hint: 'From a checked dataset the team saved earlier' },
  fixture: { label: 'Demo data', tone: 'warn', hint: 'Example data bundled with the prototype, not live' },
}

/** Shows where the numbers on screen came from, from the API's data_mode. "Demo data" appears only for "fixture". */
export function DataModeBadge({ mode, className }: { mode: DataMode; className?: string }) {
  const m = MODES[mode]
  return (
    <Badge tone={m.tone} live={mode === 'live'} dot={mode !== 'live'} title={m.hint} className={className}>
      {m.label}
    </Badge>
  )
}
