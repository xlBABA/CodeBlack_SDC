import { CloudOff, RotateCcw, SearchX, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { APIError } from '@/mocks/api'

/** 404 PROFILE_NOT_FOUND and 503 PROVIDER_UNAVAILABLE, explained in plain words with a way out. */
export function ErrorState({ error, onRetry }: { error: APIError; onRetry: () => void }) {
  const notFound = error.code === 'PROFILE_NOT_FOUND'
  const Icon = notFound ? SearchX : CloudOff
  return (
    <Card role="alert" className="grid place-items-center gap-3 py-12 text-center">
      <span className="grid size-14 place-items-center rounded-full bg-well text-tomato" aria-hidden>
        <Icon className="size-6" />
      </span>
      <h2 className="text-2xl font-extrabold tracking-[-0.02em]">{notFound ? 'We could not find your profile' : 'Data is taking a break'}</h2>
      <p className="max-w-[46ch] text-muted-foreground">{error.message}</p>
      <code className="rounded-full bg-well px-3 py-1 font-mono text-xs text-muted-foreground">
        {error.status} {error.code}
      </code>
      <div className="mt-2 flex flex-wrap justify-center gap-2.5">
        {notFound ? (
          <Button asChild>
            <Link to="/start">
              <UserRoundPen />
              Build a profile
            </Link>
          </Button>
        ) : (
          <Button onClick={onRetry}>
            <RotateCcw />
            Try again
          </Button>
        )}
      </div>
    </Card>
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
