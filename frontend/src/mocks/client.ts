// Offline fallback (VITE_USE_MOCKS=true): same signatures as the HTTP client, answered from
// responses captured from the backend in fixture mode (src/mocks/v1). Inputs are ignored and
// everything is labelled data_mode "fixture" so it can never pass for live data.
import type { Api } from '@/lib/api'
import type { APIEnvelope, Health } from '@/types/api'
import analyze from './v1/analyze.json'
import match from './v1/match.json'
import projects from './v1/proj.json'
import projectSim from './v1/psim.json'
import roadmap from './v1/road.json'
import scenarioFast from './v1/scen_fast.json'
import scenarioModerate from './v1/scen_moderate.json'
import sdgs from './v1/sdgs.json'
import trends from './v1/trends.json'

const NOTE = 'Offline mock mode (VITE_USE_MOCKS=true): bundled fixture responses, not the live API.'

const wait = (signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, 350 + Math.random() * 300)
    signal?.addEventListener('abort', () => {
      clearTimeout(t)
      reject(signal.reason)
    })
  })

function reply<T>(captured: { data: unknown; warnings?: string[] }, signal?: AbortSignal): Promise<APIEnvelope<T>> {
  return wait(signal).then((): APIEnvelope<T> => ({
    data: structuredClone(captured.data) as T,
    data_mode: 'fixture',
    generated_at: new Date().toISOString(),
    warnings: [NOTE, ...(captured.warnings ?? [])],
  }))
}

export const mockApi: Api = {
  health: (o) => wait(o?.signal).then((): Health => ({ status: 'ok', version: 'mock', dependencies: { mode: 'offline fixtures' } })),
  analyzeProfile: (_profile, o) => reply(analyze, o?.signal),
  matchCareers: (_req, o) => reply(match, o?.signal),
  getTrends: (_q, o) => reply(trends, o?.signal),
  simulateScenario: (req, o) => reply(req.scenario_id === 'fast' ? scenarioFast : scenarioModerate, o?.signal),
  generateRoadmap: (_req, o) => reply(roadmap, o?.signal),
  recommendProjects: (_req, o) => reply(projects, o?.signal),
  simulateProject: (_req, o) => reply(projectSim, o?.signal),
  getSdgs: (_roleId, o) => reply(sdgs, o?.signal),
}
