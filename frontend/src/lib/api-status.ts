import { useSyncExternalStore } from 'react'

// App-wide request state: how many API calls are in flight (drives the top loading bar)
// and whether the data provider reported 503 (drives the outage banner).

type Outage = { message: string; requestId?: string }

let inflight = 0
let outage: Outage | null = null
const retries = new Set<() => void>()
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((fn) => fn())

const subscribe = (fn: () => void) => {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

export function trackRequest() {
  inflight++
  emit()
  return () => {
    inflight = Math.max(0, inflight - 1)
    emit()
  }
}

/** A request got 503 PROVIDER_UNAVAILABLE; `retry` re-runs it when the user asks. */
export function reportOutage(message: string, retry?: () => void, requestId?: string) {
  outage = { message, requestId }
  if (retry) retries.add(retry)
  emit()
}

/** Any successful response means the provider is reachable again. */
export function clearOutage() {
  if (!outage) return
  outage = null
  retries.clear()
  emit()
}

export function retryOutage() {
  const pending = [...retries]
  outage = null
  retries.clear()
  emit()
  pending.forEach((fn) => fn())
}

export const useInflight = () => useSyncExternalStore(subscribe, () => inflight)
export const useOutage = () => useSyncExternalStore(subscribe, () => outage)
