import type { LucideIcon } from 'lucide-react'
import { ApiWarnings } from '@/components/api-warnings'
import { ErrorNotice } from '@/components/api-states'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Card, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { RequestState } from '@/hooks/use-request'
import type { APIEnvelope } from '@/types/api'

type TabFrameProps<T> = {
  title: string
  subtitle?: React.ReactNode
  icon: LucideIcon
  state: RequestState<APIEnvelope<T>>
  retry: () => void
  /** extra header controls, shown before the data-mode badge */
  controls?: React.ReactNode
  children: (data: T, envelope: APIEnvelope<T>) => React.ReactNode
}

/** One card per workspace tab: loading skeleton, inline error, then the data with its badge and notes. */
export function TabFrame<T>({ title, subtitle, icon, state, retry, controls, children }: TabFrameProps<T>) {
  return (
    <Card>
      <CardHeader
        title={title}
        subtitle={subtitle}
        icon={icon}
        action={
          <div className="flex flex-wrap items-center gap-2">
            {controls}
            {state.status === 'ok' && <DataModeBadge mode={state.data.data_mode} />}
          </div>
        }
      />
      {state.status === 'loading' && (
        <div role="status" aria-label={`Loading ${title.toLowerCase()}`} className="grid gap-3">
          <Skeleton className="h-24 rounded-tile" />
          <Skeleton className="h-24 rounded-tile" />
        </div>
      )}
      {state.status === 'error' && <ErrorNotice error={state.error} onRetry={retry} />}
      {state.status === 'ok' && (
        <>
          {children(state.data.data, state.data)}
          <ApiWarnings items={state.data.warnings} className="mt-5" />
        </>
      )}
    </Card>
  )
}
