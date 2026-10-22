import { useState } from 'react'
import { Activity } from 'lucide-react'
import { ErrorNotice } from '@/components/api-states'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader } from '@/components/ui/card'
import { useRequest } from '@/hooks/use-request'
import { api, simulatedError, USE_MOCKS } from '@/lib/api'
import type { StudentProfile } from '@/types/api'

type Probe = 'health' | 'invalid' | 'PROFILE_NOT_FOUND' | 'PROVIDER_UNAVAILABLE' | 'NETWORK_ERROR'

const PROBES: { probe: Probe; label: string; hint: string }[] = [
  { probe: 'health', label: 'Health check', hint: 'GET /health on the real API' },
  { probe: 'invalid', label: 'Invalid profile (422)', hint: 'Sends a malformed body; the API answers 422' },
  { probe: 'PROVIDER_UNAVAILABLE', label: 'Simulate 503', hint: 'Shows the outage banner' },
  { probe: 'NETWORK_ERROR', label: 'Simulate network error', hint: 'Shows the retry notice' },
  { probe: 'PROFILE_NOT_FOUND', label: 'Simulate 404 profile', hint: 'Sends you back to the intake' },
]

/** Development-only panel that exercises every error path of the API client. */
export function ApiDiagnostics() {
  const [run, setRun] = useState<{ probe: Probe; n: number } | null>(null)
  const [result] = useRequest(run && `${run.probe}-${run.n}`, async (signal) => {
    const started = performance.now()
    if (run?.probe === 'health') {
      const h = await api.health({ signal })
      return `${h.status} · version ${h.version} · ${Math.round(performance.now() - started)} ms`
    }
    if (run?.probe === 'invalid') {
      // deliberately wrong types, to see the backend's 422 VALIDATION_ERROR end to end
      await api.analyzeProfile({ interests: 'not a list', skills: 'nope', projects: [] } as unknown as StudentProfile, { signal })
      return 'unexpected success'
    }
    throw simulatedError(run!.probe as Exclude<Probe, 'health' | 'invalid'>)
  })

  return (
    <Card className="lg:col-span-2">
      <CardHeader
        icon={Activity}
        title="API diagnostics"
        subtitle={`Base ${import.meta.env.VITE_API_BASE_URL || '/api/v1'} · development only`}
        action={<Badge tone={USE_MOCKS ? 'warn' : 'good'}>{USE_MOCKS ? 'Mocks on' : 'Live API'}</Badge>}
      />
      <div className="flex flex-wrap gap-2">
        {PROBES.map((p) => (
          <Button key={p.probe} variant="secondary" size="sm" title={p.hint} onClick={() => setRun((r) => ({ probe: p.probe, n: (r?.n ?? 0) + 1 }))}>
            {p.label}
          </Button>
        ))}
      </div>
      <div className="mt-4" aria-live="polite">
        {!run && <p className="text-sm text-muted-foreground">Pick a check to run.</p>}
        {run && result.status === 'loading' && <p className="text-sm text-muted-foreground">Running…</p>}
        {run && result.status === 'ok' && <p className="rounded-tile bg-well p-3 font-mono text-sm">{result.data}</p>}
        {run && result.status === 'error' && <ErrorNotice error={result.error} onRetry={() => setRun((r) => r && { ...r, n: r.n + 1 })} />}
      </div>
    </Card>
  )
}
