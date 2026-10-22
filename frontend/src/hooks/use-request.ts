import { useCallback, useEffect, useEffectEvent, useState } from 'react'
import { useNavigate } from 'react-router'
import { useToast } from '@/components/ui/toast'
import { ApiError, noteOutage } from '@/lib/api'
import { clearProfile } from '@/lib/profile-store'

export type RequestState<T> = { status: 'loading' } | { status: 'ok'; data: T } | { status: 'error'; error: ApiError }
type Settled<T> = Exclude<RequestState<T>, { status: 'loading' }>

const asApiError = (e: unknown) =>
  e instanceof ApiError ? e : new ApiError({ kind: 'http', status: 0, code: 'UNKNOWN', message: e instanceof Error ? e.message : String(e) })

/**
 * Runs `run` whenever `key` changes (pass null to wait), cancelling the previous call.
 * - 404 PROFILE_NOT_FOUND sends the student back to the intake with an explanation
 * - 503 PROVIDER_UNAVAILABLE also raises the app-wide banner, whose "Try again" re-runs this
 * Network errors and timeouts were already retried by the client before reaching here.
 */
export function useRequest<T>(key: string | null, run: (signal: AbortSignal) => Promise<T>) {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<{ id: string; state: Settled<T> } | null>(null)
  const navigate = useNavigate()
  const toast = useToast()

  const id = key === null ? null : `${key}#${attempt}`
  // anything not yet settled for the current request is loading, so no state reset is needed
  const state: RequestState<T> = result && result.id === id ? result.state : { status: 'loading' }

  const retry = useCallback(() => setAttempt((a) => a + 1), [])
  const execute = useEffectEvent((signal: AbortSignal) => run(signal))
  const onError = useEffectEvent((error: ApiError) => {
    noteOutage(error, retry)
    if (error.code === 'PROFILE_NOT_FOUND') {
      clearProfile()
      toast('We could not find your profile. Please enter it again.')
      navigate('/start', { replace: true, state: { reason: 'profile-not-found' } })
    }
  })

  useEffect(() => {
    if (id === null) return
    const controller = new AbortController()
    execute(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setResult({ id, state: { status: 'ok', data } })
      })
      .catch((e: unknown) => {
        if (controller.signal.aborted) return
        const error = asApiError(e)
        setResult({ id, state: { status: 'error', error } })
        onError(error)
      })
    return () => controller.abort()
  }, [id])

  return [state, retry] as const
}
