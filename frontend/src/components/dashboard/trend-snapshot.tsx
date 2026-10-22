import { TrendArrow } from '@/components/trend-arrow'
import { Badge } from '@/components/ui/badge'
import { skillName } from '@/content/skills'
import { fmtDate } from '@/lib/role-copy'
import type { TrendSignal, TrendsPayload } from '@/types/api'

const STATUS = {
  ok: { tone: 'good', label: 'Sources up to date' },
  stale: { tone: 'warn', label: 'Sources stale' },
  unavailable: { tone: 'bad', label: 'Sources unavailable' },
} as const

const metric = (s: TrendSignal) =>
  s.metric_value == null ? s.metric_name.replace(/_/g, ' ') : `${s.metric_name.replace(/_/g, ' ')}: ${s.metric_value}${s.unit ? ` ${s.unit}` : ''}`

/**
 * Dated skill-demand signals exactly as the API sends them: direction, metric, source and
 * both dates. No bar lengths are drawn because the signals carry no comparable magnitude.
 * Stale sources use the hatched swatch (Halden idea) and say so in words too.
 */
export function TrendSnapshot({ trends, limit }: { trends: TrendsPayload; limit?: number }) {
  const signals = (trends.signals ?? []).slice(0, limit)
  const status = STATUS[trends.source_status]
  return (
    <div className="grid gap-3.5">
      <p className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <Badge tone={status.tone} dot enter={false} className="py-0 text-2xs">
          {status.label}
        </Badge>
        {trends.last_successful_refresh_at ? `last refreshed ${fmtDate(trends.last_successful_refresh_at)}` : 'never refreshed from a live source'}
      </p>
      <ul className="grid gap-3">
        {signals.map((s) => (
          <li key={s.signal_id} data-enter="item" className="rounded-[16px] bg-well p-3">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-semibold">{skillName(s.skill_id)}</span>
              <TrendArrow direction={s.direction} withLabel />
            </div>
            <div className="relative mt-2 h-2 rounded-full bg-raised">
              <i
                data-enter="bar"
                aria-hidden
                className={trends.source_status === 'ok' ? 'block h-full w-full rounded-full bg-line-2' : 'hatch block h-full w-full rounded-full'}
              />
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
              {metric(s)} · {s.signal_type.replace(/_/g, ' ')} · source <code className="font-mono">{s.source_id}</code> · observed {fmtDate(s.observed_at)} · retrieved {fmtDate(s.retrieved_at)}
            </p>
            <p className="mt-1 text-xs leading-relaxed italic">{s.confidence_note}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
