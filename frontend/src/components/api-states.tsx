import { CloudOff, RotateCcw, SearchX, TriangleAlert, UserRoundPen, WifiOff } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

/** What the error UI needs; satisfied by ApiError (lib/api) and the legacy mock error. */
export type ShownError = {
  code: string
  status: number
  message: string
  kind?: 'http' | 'validation' | 'network' | 'timeout'
  requestId?: string
  issues?: string[]
}

function describe(error: ShownError) {
  if (error.code === 'PROFILE_NOT_FOUND') return { Icon: SearchX, title: 'We could not find your profile', action: 'profile' as const }
  if (error.status === 503) return { Icon: CloudOff, title: 'Data is taking a break', action: 'retry' as const }
  if (error.kind === 'network' || error.kind === 'timeout') return { Icon: WifiOff, title: 'Can’t reach the server', action: 'retry' as const }
  if (error.kind === 'validation') return { Icon: TriangleAlert, title: 'Some details need fixing', action: 'profile' as const }
  return { Icon: TriangleAlert, title: 'Something went wrong', action: 'retry' as const }
}

function ErrorBody({ error, onRetry, compact = false }: { error: ShownError; onRetry: () => void; compact?: boolean }) {
  const { Icon, title, action } = describe(error)
  const transient = error.kind === 'network' || error.kind === 'timeout'
  return (
    <>
      <span className={compact ? 'grid size-10 flex-none place-items-center rounded-full bg-well text-tomato' : 'grid size-14 place-items-center rounded-full bg-well text-tomato'} aria-hidden>
        <Icon className={compact ? 'size-5' : 'size-6'} />
      </span>
      <div className={compact ? 'min-w-0 flex-1' : 'grid justify-items-center gap-3'}>
        <h2 className={compact ? 'font-bold' : 'text-2xl font-extrabold tracking-[-0.02em]'}>{title}</h2>
        <p className="max-w-[52ch] text-muted-foreground">
          {error.message}
          {transient && ' We already tried a few times.'}
        </p>
        {error.issues && error.issues.length > 0 && (
          <ul className={compact ? 'mt-2 grid gap-1 text-sm' : 'grid gap-1 text-left text-sm'}>
            {error.issues.map((i) => (
              <li key={i} className="rounded-lg bg-well px-2.5 py-1 font-mono text-xs">
                {i}
              </li>
            ))}
          </ul>
        )}
        <code className={compact ? 'mt-2 inline-block rounded-full bg-well px-3 py-1 font-mono text-xs text-muted-foreground' : 'rounded-full bg-well px-3 py-1 font-mono text-xs text-muted-foreground'}>
          {error.status ? `${error.status} ` : ''}
          {error.code}
          {error.requestId ? ` · request ${error.requestId.slice(0, 8)}` : ''}
        </code>
        <div className={compact ? 'mt-3 flex flex-wrap gap-2' : 'mt-2 flex flex-wrap justify-center gap-2.5'}>
          {action === 'profile' ? (
            <Button asChild size={compact ? 'sm' : 'default'}>
              <Link to="/start">
                <UserRoundPen />
                {error.code === 'PROFILE_NOT_FOUND' ? 'Build a profile' : 'Review profile'}
              </Link>
            </Button>
          ) : (
            <Button size={compact ? 'sm' : 'default'} onClick={onRetry}>
              <RotateCcw />
              Try again
            </Button>
          )}
        </div>
      </div>
    </>
  )
}

/** Full-width error card for a page whose main request failed. */
export function ErrorState({ error, onRetry }: { error: ShownError; onRetry: () => void }) {
  return (
    <Card role="alert" className="grid place-items-center gap-3 py-12 text-center">
      <ErrorBody error={error} onRetry={onRetry} />
    </Card>
  )
}

/** Inline error for one widget or panel; the rest of the page keeps working. */
export function ErrorNotice({ error, onRetry }: { error: ShownError; onRetry: () => void }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-tile border border-line bg-well/50 p-4">
      <ErrorBody error={error} onRetry={onRetry} compact />
    </div>
  )
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: React.ReactNode }) {
  return (
    <div className="grid place-items-center gap-2 rounded-tile border border-dashed border-line-2 px-6 py-10 text-center">
      <p className="text-lg font-bold">{title}</p>
      <p className="max-w-[40ch] text-muted-foreground">{body}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
