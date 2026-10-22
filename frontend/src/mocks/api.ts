// Mock client: same signatures the real client will have, backed by fixtures.
// Add ?mock=empty, ?mock=404 or ?mock=503 to any URL to see the other states.
import { analysisFixture, insightsFixture, profileFixture, roadmapFixture, trendsFixture } from './fixtures'
import type { Analysis, APIEnvelope, APIErrorCode, DataMode, Profile, Roadmap, TrendSnapshot } from './types'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '(mock)'

export class APIError extends Error {
  code: APIErrorCode
  status: 404 | 503
  constructor(code: APIErrorCode, status: 404 | 503, message: string) {
    super(message)
    this.code = code
    this.status = status
  }
}

type Scenario = 'ok' | 'empty' | '404' | '503'
const scenario = (): Scenario => {
  const v = new URLSearchParams(window.location.search).get('mock')
  return v === 'empty' || v === '404' || v === '503' ? v : 'ok'
}

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

async function respond<T>(data: T, empty: T, data_mode: DataMode, warnings: string[] = []): Promise<APIEnvelope<T>> {
  await wait(450 + Math.random() * 300)
  const s = scenario()
  if (s === '404') throw new APIError('PROFILE_NOT_FOUND', 404, 'We could not find that profile. It may have expired.')
  if (s === '503') throw new APIError('PROVIDER_UNAVAILABLE', 503, 'The trend provider is not responding right now.')
  return { data: s === 'empty' ? empty : data, data_mode, generated_at: new Date().toISOString(), warnings }
}

export const api = {
  getProfile: () => respond<Profile>(profileFixture, { ...profileFixture, skills: [], projects: [] }, 'live'),
  analyze: () =>
    respond<Analysis>(analysisFixture, { ...analysisFixture, matches: [] }, 'live', [
      'Alignment estimates use self-rated skills; treat them as a starting point.',
    ]),
  getTrends: () => respond<TrendSnapshot>(trendsFixture, { ...trendsFixture, signals: [] }, 'fixture', ['Some signals are older than 90 days and marked stale.']),
  getRoadmap: () => respond<Roadmap>(roadmapFixture, { ...roadmapFixture, steps: [], total_hours: 0 }, 'fixture'),
  getInsights: () => respond<typeof insightsFixture>(insightsFixture, { notes: [] }, 'fixture'),
}
