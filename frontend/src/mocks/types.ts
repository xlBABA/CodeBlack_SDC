// Shapes mirror the backend responses. Every endpoint returns an APIEnvelope.

export type DataMode = 'live' | 'cached' | 'fixture'

export type APIEnvelope<T> = {
  data: T
  data_mode: DataMode
  generated_at: string
  warnings: string[]
}

export type APIErrorCode = 'PROFILE_NOT_FOUND' | 'PROVIDER_UNAVAILABLE'
export type APIErrorBody = { error: { code: APIErrorCode; message: string; status: 404 | 503 } }

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced'
export type RoleId = 'data_analyst' | 'financial_analyst' | 'mechanical_design_engineer' | 'sustainability_coordinator'
export type TrendDirection = 'rising' | 'stable' | 'declining'

export type Profile = {
  profile_id: string
  display_name: string
  education: { level: string; degree: string; semester: number }
  skills: { skill_id: string; name: string; level: SkillLevel }[]
  projects: { title: string; summary: string }[]
  interests: string[]
}

/** Component scores (0–100) behind the alignment estimate; weights live in the backend. */
export type ScoreBreakdown = { skills: number; experience: number; prerequisites: number; transferable: number }

export type RoleMatch = {
  role_id: RoleId
  title: string
  /** 0–100, an alignment estimate — never a chance, probability or eligibility */
  alignment_estimate: number
  breakdown: ScoreBreakdown
  matched_skills: string[]
  missing_skills: string[]
  trend: TrendDirection
  sdgs: number[]
  caveats: string[]
}

export type Analysis = {
  profile_id: string
  matches: RoleMatch[]
  catalog: { roles_total: number; roles_verified: number }
}

export type TrendSignal = {
  skill: string
  direction: TrendDirection
  /** relative change in demo demand index over the window */
  change_pct: number
  source: string
  source_url: string
  observed_at: string
  retrieved_at: string
  status: 'fresh' | 'stale' | 'unavailable'
}

export type TrendSnapshot = { window: string; signals: TrendSignal[] }

export type RoadmapStep = { step_id: string; title: string; skill: string; hours: number; status: 'todo' | 'doing' | 'done' }
export type Roadmap = { role_id: RoleId; total_hours: number; steps: RoadmapStep[] }
