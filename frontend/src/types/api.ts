// Request/response types for the backend API (/api/v1). Mirrors the live OpenAPI schema at
// https://mustaqbal-ai.replit.app/openapi.json; optional fields are optional there too.

export type DataMode = 'live' | 'cached' | 'fixture'

export type APIEnvelope<T> = {
  data: T
  data_mode: DataMode
  generated_at: string
  /** optional in the schema; the client always fills it with [] */
  warnings: string[]
}

/** Error body for 4xx/5xx from the API. 404 for unknown routes is FastAPI's `{ detail }` instead. */
export type APIErrorBody = {
  error: { code: string; message: string; details?: unknown }
  request_id?: string
}

/** One entry of `error.details` on 422 VALIDATION_ERROR. */
export type ValidationIssue = { loc: (string | number)[]; msg: string; type: string; input?: unknown }

export type Proficiency = 'beginner' | 'intermediate' | 'advanced'

export type SkillRef = { skill_id: string; name: string; proficiency?: Proficiency | null }

export type StudentProfile = {
  profile_id?: string | null
  education_level?: string | null
  degree?: string | null
  semester?: number | null
  target_role_id?: string | null
  interests: string[]
  skills: SkillRef[]
  projects: string[]
  experience_summary?: string | null
}

export type ScoreBreakdown = { skills: number; experience: number; prerequisites: number; transferable: number }

export type RoleMatch = {
  role_id: string
  role_title: string
  /** 0–100 profile alignment estimate; display it, never recompute it */
  score: number
  score_type?: string
  matched_skills?: SkillRef[]
  missing_skills?: SkillRef[]
  score_breakdown: ScoreBreakdown
  evidence_ids?: string[]
  explanation: string
  caveats?: string[]
}

export type CatalogCoverage = { verified: number; total_target: number }

export type ScenarioId = 'moderate' | 'fast'

export type MatchRequest = { profile: StudentProfile; limit?: number; scenario_id?: ScenarioId | null }
export type MatchPayload = { matches: RoleMatch[]; catalog_coverage: CatalogCoverage; methodology_version: string }

export type ScenarioRequest = { profile: StudentProfile; scenario_id: ScenarioId }
export type ScenarioPayload = { matches: RoleMatch[]; scenario_id: ScenarioId; assumptions: string[]; uncertainty_note: string }

export type TrendDirection = 'rising' | 'stable' | 'falling' | 'unknown'

export type TrendSignal = {
  signal_id: string
  skill_id: string
  source_id: string
  signal_type: string
  metric_name: string
  metric_value?: number | null
  unit?: string | null
  observed_at: string
  retrieved_at: string
  direction: TrendDirection
  confidence_note: string
  role_ids?: string[]
}

export type TrendsQuery = { role_id?: string; limit?: number }
export type TrendsPayload = { signals?: TrendSignal[]; last_successful_refresh_at?: string | null; source_status: 'ok' | 'stale' | 'unavailable' }

export type RoleProfileRequest = {
  profile: StudentProfile
  role_id: string
  budget_limit?: number | null
  hours_per_week?: number | null
  limit?: number | null
}

export type RoadmapStep = { skill_id: string; resource_id: string; estimated_hours: number; reason: string }
export type RoadmapPayload = { steps: RoadmapStep[]; total_estimated_hours: number }

export type RecommendedProject = {
  project_id: string
  title: string
  skill_ids: string[]
  estimated_hours: number
  source_ids: string[]
  milestones: string[]
}
export type ProjectRecommendationPayload = { projects: RecommendedProject[] }

export type ProjectSimulationRequest = { profile: StudentProfile; role_id: string; project_id: string }
export type ProjectSimulationPayload = { baseline_score: number; simulated_score: number; assumed_skill_ids: string[]; disclaimer: string }

export type RoleSdgMapping = { sdg_id: number; reason: string }
export type SkillSdgMapping = { skill_id: string; sdg_id: number; reason: string }
export type SdgPayload = { role_sdg_mappings: RoleSdgMapping[]; skill_sdg_mappings: SkillSdgMapping[] }

/** POST /cv/parse (multipart, field "file"). The draft is for the student to review; it is never saved by the API. */
export type CvParseStatus = 'ok' | 'manual_review' | 'no_extractable_text'

export type CvEducation = { institution?: string | null; degree?: string | null; field_of_study?: string | null; start_date?: string | null; end_date?: string | null }
export type CvExperience = { role?: string | null; organization?: string | null; start_date?: string | null; end_date?: string | null; description?: string | null }
export type CvProject = { title: string; description?: string | null }
export type CvCertification = { name: string; issuer?: string | null; year?: string | null }

/** A skill whose quoted evidence was found in the CV text and that matched the catalogue. */
export type CvMappedSkill = { skill_id: string; name: string; raw_text: string; evidence: string }
/** Evidence found, but no catalogue match, so it has no skill_id. */
export type CvUnmappedSkill = { raw_text: string; evidence: string }
/** Named by the extractor without evidence found in the CV; never pre-added. */
export type CvSkillNeedsReview = { name: string; reason: string }

export type CvDraft = {
  name?: string | null
  summary?: string | null
  education: CvEducation[]
  mapped_skills: CvMappedSkill[]
  unmapped_skills: CvUnmappedSkill[]
  /** added after the first CV release, so older servers may leave it out */
  skills_requiring_review?: CvSkillNeedsReview[]
  projects: CvProject[]
  experience: CvExperience[]
  certifications: CvCertification[]
  /** same shape as the /profile/analyze body; skill proficiency is always null */
  suggested_profile: StudentProfile
}

export type CvParsePayload = {
  status: CvParseStatus
  draft: CvDraft
  page_count: number
  /** first 500 characters of the extracted text, only for manual_review */
  extracted_text_preview?: string | null
}

/** /health is the one endpoint without an envelope. */
export type Health = { status: string; version: string; dependencies?: Record<string, string> }
