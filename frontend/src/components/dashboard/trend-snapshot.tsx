import { ExternalLink } from 'lucide-react'
import { EmptyState } from '@/components/api-states'
import { TrendArrow } from '@/components/trend-arrow'
import { Badge } from '@/components/ui/badge'
import { skillName } from '@/content/skills'
import type { TrendSignal, TrendsPayload } from '@/types/api'

const STATUS = {
  ok: { tone: 'good', label: 'Source up to date' },
  stale: { tone: 'warn', label: 'Stale · cached snapshot' },
  unavailable: { tone: 'bad', label: 'Source unavailable' },
} as const

// The API sends only a source_id; these links come from the team's source register.
const SOURCES: Record<string, { label: string; url: string }> = {
  github_search_repos: { label: 'GitHub Search API (repositories)', url: 'https://docs.github.com/en/rest/search/search#search-repositories' },
}

const words = (id: string) => id.replace(/_/g, ' ')

// Source timestamps are UTC and the confidence notes quote them in UTC, so show the UTC date.
const utcDate = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('en-MY', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
}

const metric = (s: TrendSignal) =>
  s.metric_value == null ? `${words(s.metric_name)}: no value` : `${words(s.metric_name)}: ${s.metric_value.toLocaleString('en-MY')}${s.unit ? ` ${s.unit}` : ''}`

function Source({ id }: { id: string }) {
  const source = SOURCES[id]
  if (!source) {
    return (
      <>
        <code className="font-mono">{id}</code> (no public link)
      </>
    )
  }
  return (
    <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-primary hover:underline">
      {source.label}
      <ExternalLink className="size-3" aria-hidden />
      <span className="sr-only">(opens in a new tab)</span>
    </a>
  )
}

function Stamp({ label, iso }: { label: string; iso: string }) {
  return (
    <div className="flex gap-1">
      <dt>{label}</dt>
      <dd className="font-semibold text-foreground">
        <time dateTime={iso} title={iso}>
          {utcDate(iso)}
        </time>
      </dd>
    </div>
  )
}

/**
 * Dated developer-activity signals exactly as the API sends them: direction, metric, source,
 * both dates and the source's freshness. No bar lengths are drawn because the signals carry no
 * comparable magnitude. Stale sources use the hatched swatch and say so in words too.
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
        {trends.last_successful_refresh_at ? `last successful refresh ${utcDate(trends.last_successful_refresh_at)}` : 'no successful refresh recorded'}
      </p>
      {signals.length === 0 ? (
        <EmptyState
          title="No signals yet"
          body={
            trends.source_status === 'unavailable'
              ? 'No signal is available for this role. Either none of its skills is tracked yet, or the trend source could not be read.'
              : 'No GitHub developer-activity signal covers the skills of this role yet.'
          }
        />
      ) : (
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
                {metric(s)} · {words(s.signal_type)}
              </p>
              <dl className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                <div className="flex gap-1">
                  <dt>Source</dt>
                  <dd>
                    <Source id={s.source_id} />
                  </dd>
                </div>
                <Stamp label="Observed" iso={s.observed_at} />
                <Stamp label="Retrieved" iso={s.retrieved_at} />
              </dl>
              <p className="mt-1 text-xs leading-relaxed italic">{s.confidence_note}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
