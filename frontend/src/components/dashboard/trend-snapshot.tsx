import { ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { TrendSignal } from '@/mocks/types'
import { cn } from '@/lib/utils'

const fmt = (d: string) => new Date(`${d}T12:00:00`).toLocaleDateString('en-MY', { day: 'numeric', month: 'short', year: 'numeric' })

/**
 * Diverging bars around a centre line: rising to the right, declining to the left.
 * Stale signals use the hatched fill (Halden idea) and say so in words too.
 */
export function TrendSnapshot({ signals }: { signals: TrendSignal[] }) {
  const max = Math.max(...signals.map((s) => Math.abs(s.change_pct)), 1)
  return (
    <ul className="grid gap-3.5">
      {signals.map((s) => {
        const w = (Math.abs(s.change_pct) / max) * 50
        const rising = s.change_pct >= 0
        return (
          <li key={s.skill} data-enter="item">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-semibold">{s.skill}</span>
              <span className={cn('text-sm font-bold tabular-nums', s.direction === 'rising' ? 'text-good' : s.direction === 'declining' ? 'text-tomato' : 'text-muted-foreground')}>
                {rising ? '+' : ''}
                {s.change_pct}%
              </span>
            </div>
            <div className="relative mt-1.5 h-2.5 rounded-full bg-well">
              <span aria-hidden className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px bg-line-2" />
              <i
                data-enter="bar"
                aria-hidden
                className={cn('absolute inset-y-0 block rounded-full', s.status === 'stale' ? 'hatch' : rising ? 'bg-good' : 'bg-tomato')}
                style={rising ? { left: '50%', width: `${w}%` } : { right: '50%', width: `${w}%`, transformOrigin: '100% 50%' }}
              />
            </div>
            <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
              <a href={s.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline-offset-2 hover:underline">
                {s.source}
                <ExternalLink className="size-3" aria-hidden />
              </a>
              <span>· observed {fmt(s.observed_at)}</span>
              <span>· retrieved {fmt(s.retrieved_at)}</span>
              {s.status !== 'fresh' && (
                <Badge tone={s.status === 'stale' ? 'warn' : 'bad'} enter={false} className="py-0 text-2xs">
                  {s.status}
                </Badge>
              )}
            </p>
          </li>
        )
      })}
    </ul>
  )
}
