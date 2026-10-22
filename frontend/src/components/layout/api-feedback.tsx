import { useLayoutEffect, useRef } from 'react'
import { CloudOff, RotateCcw, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { clearOutage, retryOutage, useInflight, useOutage } from '@/lib/api-status'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { cn } from '@/lib/utils'

/**
 * Thin indeterminate bar along the top while any API call is in flight. It only appears
 * after 150 ms, so fast responses don't flicker it.
 */
export function ApiProgress() {
  const busy = useInflight() > 0
  return (
    <div
      aria-hidden
      className={cn(
        'pointer-events-none fixed inset-x-0 top-0 z-[90] h-[3px] overflow-hidden transition-opacity',
        busy ? 'opacity-100 delay-150 duration-200' : 'opacity-0 duration-300',
      )}
    >
      <span className="api-progress block h-full w-2/5 rounded-full bg-primary" />
    </div>
  )
}

/** App-wide banner for 503 PROVIDER_UNAVAILABLE, with one "Try again" for every failed call. */
export function OutageBanner() {
  const outage = useOutage()
  const el = useRef<HTMLDivElement>(null)

  useLayoutEffect(() => {
    if (!outage || !el.current || prefersReducedMotion()) return
    gsap.fromTo(el.current, { y: -10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: 'expo.out' })
  }, [outage])

  if (!outage) return null
  return (
    <div
      ref={el}
      role="status"
      aria-live="polite"
      className="mb-4 flex flex-wrap items-center gap-3 rounded-tile border border-[color-mix(in_srgb,var(--warn)_35%,transparent)] bg-[color-mix(in_srgb,var(--warn)_10%,var(--glass))] p-3 pl-4 backdrop-blur-md"
    >
      <CloudOff className="size-5 flex-none text-warn" aria-hidden />
      <p className="min-w-0 flex-1 text-sm">
        <b>Live data is temporarily unavailable.</b> <span className="text-muted-foreground">{outage.message}</span>
      </p>
      <Button size="sm" variant="secondary" onClick={retryOutage}>
        <RotateCcw />
        Try again
      </Button>
      <button type="button" aria-label="Dismiss" onClick={clearOutage} className="grid size-8 place-items-center rounded-full text-muted-foreground hover:bg-well">
        <X className="size-4" aria-hidden />
      </button>
    </div>
  )
}
