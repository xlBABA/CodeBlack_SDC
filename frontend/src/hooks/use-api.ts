import { useEffect, useState } from 'react'
import { APIError } from '@/mocks/api'
import type { APIEnvelope } from '@/mocks/types'

export type ApiState<T> =
  | { status: 'loading' }
  | { status: 'ok'; envelope: APIEnvelope<T> }
  | { status: 'error'; error: APIError }

/** Runs one request on mount; `retry()` runs it again. */
export function useApi<T>(request: () => Promise<APIEnvelope<T>>) {
  const [state, setState] = useState<ApiState<T>>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let alive = true
    request()
      .then((envelope) => alive && setState({ status: 'ok', envelope }))
      .catch((e: unknown) => alive && setState({ status: 'error', error: e instanceof APIError ? e : new APIError('PROVIDER_UNAVAILABLE', 503, String(e)) }))
    return () => {
      alive = false
    }
    // `request` is a stable module function; `attempt` re-runs it
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt])

  const retry = () => {
    setState({ status: 'loading' })
    setAttempt((a) => a + 1)
  }
  return [state, retry] as const
}
