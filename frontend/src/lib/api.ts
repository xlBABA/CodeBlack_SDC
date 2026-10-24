// Typed client for the backend (/api/v1). Every call returns the API envelope with
// `warnings` always present, or throws an ApiError with a normalised code. Network errors
// and timeouts are retried automatically; 503 also raises the app-wide outage banner.
import { mockApi } from '@/mocks/client'
import type {
  APIEnvelope,
  APIErrorBody,
  CvParsePayload,
  Health,
  MatchPayload,
  MatchRequest,
  ProjectRecommendationPayload,
  ProjectSimulationPayload,
  ProjectSimulationRequest,
  RoadmapPayload,
  RoleProfileRequest,
  ScenarioPayload,
  ScenarioRequest,
  SdgPayload,
  StudentProfile,
  TrendsPayload,
  TrendsQuery,
  ValidationIssue,
} from '@/types/api'
import { clearOutage, reportOutage, trackRequest } from './api-status'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '')
export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

const TIMEOUT_MS = 20_000
const RETRY_DELAYS_MS = [700, 1600]
// The CV parser waits up to 30 s for its language model, so uploads get a longer limit.
const UPLOAD_TIMEOUT_MS = 60_000

export type ApiErrorKind = 'http' | 'validation' | 'network' | 'timeout'

export class ApiError extends Error {
  kind: ApiErrorKind
  /** HTTP status, or 0 when the server was never reached */
  status: number
  /** backend error code (PROFILE_NOT_FOUND, PROVIDER_UNAVAILABLE, VALIDATION_ERROR, …) or a local one */
  code: string
  details?: unknown
  requestId?: string

  constructor(init: { kind: ApiErrorKind; status: number; code: string; message: string; details?: unknown; requestId?: string }) {
    super(init.message)
    this.kind = init.kind
    this.status = init.status
    this.code = init.code
    this.details = init.details
    this.requestId = init.requestId
  }

  /** Field-level messages for 422 VALIDATION_ERROR, e.g. "skills: Input should be a valid list". */
  get issues(): string[] {
    if (!Array.isArray(this.details)) return []
    return (this.details as ValidationIssue[]).map((d) => {
      const field = d.loc?.filter((p) => p !== 'body').join('.') ?? ''
      return field ? `${field}: ${d.msg}` : d.msg
    })
  }
}

const FALLBACK_CODES: Record<number, string> = { 404: 'NOT_FOUND', 422: 'VALIDATION_ERROR', 503: 'PROVIDER_UNAVAILABLE' }

async function toApiError(res: Response): Promise<ApiError> {
  let body: Partial<APIErrorBody> & { detail?: unknown } = {}
  try {
    body = await res.json()
  } catch {
    // non-JSON error page (proxy, gateway): fall back to the status text
  }
  const code = body.error?.code ?? FALLBACK_CODES[res.status] ?? `HTTP_${res.status}`
  const message = body.error?.message ?? (typeof body.detail === 'string' ? body.detail : res.statusText || `Request failed (${res.status})`)
  return new ApiError({
    kind: res.status === 422 ? 'validation' : 'http',
    status: res.status,
    code,
    message,
    details: body.error?.details ?? (Array.isArray(body.detail) ? body.detail : undefined),
    requestId: body.request_id,
  })
}

const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms)
    signal?.addEventListener('abort', () => {
      clearTimeout(t)
      reject(signal.reason)
    })
  })

type Options = { signal?: AbortSignal; query?: Record<string, string | number | undefined> }

async function fetchJson<T>(method: 'GET' | 'POST', path: string, body: unknown, { signal, query }: Options = {}): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined && v !== '') url.searchParams.set(k, String(v))

  for (let attempt = 0; ; attempt++) {
    const done = trackRequest()
    const timeout = AbortSignal.timeout(TIMEOUT_MS)
    try {
      const res = await fetch(url, {
        method,
        headers: body === undefined ? { accept: 'application/json' } : { accept: 'application/json', 'content-type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
      })
      if (!res.ok) throw await toApiError(res)
      clearOutage()
      return (await res.json()) as T
    } catch (e) {
      if (signal?.aborted) throw e // caller cancelled: not an error to show
      const error =
        e instanceof ApiError
          ? e
          : timeout.aborted
            ? new ApiError({ kind: 'timeout', status: 0, code: 'TIMEOUT', message: 'The server took too long to answer.' })
            : new ApiError({ kind: 'network', status: 0, code: 'NETWORK_ERROR', message: 'Could not reach the server. Check your connection.' })
      const transient = error.kind === 'network' || error.kind === 'timeout'
      if (transient && attempt < RETRY_DELAYS_MS.length) {
        await sleep(RETRY_DELAYS_MS[attempt], signal)
        continue
      }
      throw error
    } finally {
      done()
    }
  }
}

async function envelope<T>(method: 'GET' | 'POST', path: string, body: unknown, options?: Options): Promise<APIEnvelope<T>> {
  const res = await fetchJson<APIEnvelope<T> & { warnings?: string[] }>(method, path, body, options)
  return { ...res, warnings: res.warnings ?? [] }
}

export type UploadOptions = {
  signal?: AbortSignal
  /** share of the file sent so far, 0 to 1 */
  onProgress?: (sent: number) => void
  /** the whole file has reached the server, which is now processing it */
  onUploaded?: () => void
}

/**
 * Multipart POST. Uses XHR because fetch cannot report when the upload itself is finished,
 * which is what tells "uploading" apart from "processing". Not retried: the caller offers that.
 */
function upload<T>(path: string, form: FormData, { signal, onProgress, onUploaded }: UploadOptions = {}): Promise<APIEnvelope<T>> {
  return new Promise((resolve, reject) => {
    const done = trackRequest()
    const xhr = new XMLHttpRequest()
    const fail = (error: unknown) => {
      done()
      reject(error)
    }
    xhr.open('POST', new URL(`${BASE_URL}${path}`, window.location.origin))
    xhr.setRequestHeader('accept', 'application/json')
    xhr.timeout = UPLOAD_TIMEOUT_MS
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(e.loaded / e.total)
    }
    xhr.upload.onload = () => onUploaded?.()
    xhr.onload = () => {
      const res = new Response(xhr.responseText, { status: xhr.status, statusText: xhr.statusText })
      if (!res.ok) {
        toApiError(res).then(fail)
        return
      }
      res
        .json()
        .then((body: APIEnvelope<T> & { warnings?: string[] }) => {
          clearOutage()
          done()
          resolve({ ...body, warnings: body.warnings ?? [] })
        })
        .catch(() => fail(new ApiError({ kind: 'http', status: res.status, code: 'BAD_RESPONSE', message: 'The server sent an answer that could not be read.' })))
    }
    xhr.onerror = () => fail(new ApiError({ kind: 'network', status: 0, code: 'NETWORK_ERROR', message: 'Could not reach the server. Check your connection.' }))
    xhr.ontimeout = () => fail(new ApiError({ kind: 'timeout', status: 0, code: 'TIMEOUT', message: 'The server took too long to answer.' }))
    xhr.onabort = () => fail(signal?.reason)
    signal?.addEventListener('abort', () => xhr.abort())
    xhr.send(form)
  })
}

const httpApi = {
  health: (o?: Options) => fetchJson<Health>('GET', '/health', undefined, o),
  analyzeProfile: (profile: StudentProfile, o?: Options) => envelope<StudentProfile>('POST', '/profile/analyze', profile, o),
  matchCareers: (req: MatchRequest, o?: Options) => envelope<MatchPayload>('POST', '/careers/match', req, o),
  getTrends: (q: TrendsQuery = {}, o?: Options) => envelope<TrendsPayload>('GET', '/trends', undefined, { ...o, query: q }),
  simulateScenario: (req: ScenarioRequest, o?: Options) => envelope<ScenarioPayload>('POST', '/scenarios/simulate', req, o),
  generateRoadmap: (req: RoleProfileRequest, o?: Options) => envelope<RoadmapPayload>('POST', '/roadmaps/generate', req, o),
  recommendProjects: (req: RoleProfileRequest, o?: Options) => envelope<ProjectRecommendationPayload>('POST', '/projects/recommend', req, o),
  simulateProject: (req: ProjectSimulationRequest, o?: Options) => envelope<ProjectSimulationPayload>('POST', '/projects/simulate', req, o),
  getSdgs: (roleId: string, o?: Options) => envelope<SdgPayload>('GET', `/sdgs/${encodeURIComponent(roleId)}`, undefined, o),
  parseCv: (file: File, o?: UploadOptions) => {
    const form = new FormData()
    form.append('file', file)
    return upload<CvParsePayload>('/cv/parse', form, o)
  },
}

export type Api = typeof httpApi

/** The client the app uses: real HTTP by default, bundled fixtures when VITE_USE_MOCKS=true. */
export const api: Api = USE_MOCKS ? mockApi : httpApi

/** Hands a failed request's 503 to the outage banner so the user can retry it from there. */
export function noteOutage(error: unknown, retry: () => void) {
  if (error instanceof ApiError && error.status === 503) reportOutage(error.message, retry, error.requestId)
}
