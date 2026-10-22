// Demo data only. Sources are fictional and every URL points at example.com.
import type { Analysis, Profile, Roadmap, TrendSnapshot } from './types'

export const DEMO_PROFILE_ID = 'demo-student'

export const profileFixture: Profile = {
  profile_id: DEMO_PROFILE_ID,
  display_name: 'Aina (demo student)',
  education: { level: "Bachelor's degree", degree: 'BSc Data Science', semester: 5 },
  skills: [
    { skill_id: 'excel', name: 'Excel', level: 'advanced' },
    { skill_id: 'python', name: 'Python', level: 'intermediate' },
    { skill_id: 'statistics', name: 'Statistics', level: 'intermediate' },
    { skill_id: 'sql', name: 'SQL', level: 'beginner' },
    { skill_id: 'communication', name: 'Communication', level: 'advanced' },
    { skill_id: 'presentation', name: 'Presentation', level: 'intermediate' },
    { skill_id: 'teamwork', name: 'Teamwork', level: 'advanced' },
  ],
  projects: [
    { title: 'Campus food-waste dashboard', summary: 'Cleaned canteen sales data in Excel and charted weekly waste.' },
    { title: 'Kaggle housing regression', summary: 'Python notebook predicting rent from listing features.' },
  ],
  interests: ['Sustainability', 'Finance', 'Public data'],
}

// alignment_estimate values were produced by the (mock) backend; the UI never recomputes them
export const analysisFixture: Analysis = {
  profile_id: DEMO_PROFILE_ID,
  catalog: { roles_total: 30, roles_verified: 4 },
  matches: [
    {
      role_id: 'data_analyst',
      title: 'Data analyst',
      alignment_estimate: 76,
      breakdown: { skills: 80, experience: 60, prerequisites: 90, transferable: 70 },
      matched_skills: ['Excel', 'Python', 'Statistics', 'Communication', 'Presentation'],
      missing_skills: ['SQL (intermediate)', 'Power BI', 'Data storytelling'],
      trend: 'rising',
      sdgs: [8, 9, 4],
      caveats: ['Based on self-rated skill levels, not an assessment.'],
    },
    {
      role_id: 'financial_analyst',
      title: 'Financial analyst',
      alignment_estimate: 65,
      breakdown: { skills: 62, experience: 50, prerequisites: 80, transferable: 80 },
      matched_skills: ['Excel', 'Statistics', 'Communication'],
      missing_skills: ['Financial modelling', 'Accounting basics', 'Valuation'],
      trend: 'stable',
      sdgs: [8, 17],
      caveats: ['Some employers expect an accounting or finance minor.'],
    },
    {
      role_id: 'sustainability_coordinator',
      title: 'Sustainability coordinator',
      alignment_estimate: 59,
      breakdown: { skills: 60, experience: 40, prerequisites: 60, transferable: 80 },
      matched_skills: ['Excel', 'Communication', 'Teamwork'],
      missing_skills: ['ESG reporting (GRI)', 'Carbon accounting', 'Stakeholder engagement'],
      trend: 'rising',
      sdgs: [13, 12, 7],
      caveats: ['Demand signals for this role come from a small sample.'],
    },
    {
      role_id: 'mechanical_design_engineer',
      title: 'Mechanical design engineer',
      alignment_estimate: 40,
      breakdown: { skills: 38, experience: 30, prerequisites: 40, transferable: 60 },
      matched_skills: ['Teamwork', 'Presentation'],
      missing_skills: ['CAD (SolidWorks)', 'Engineering mechanics', 'Materials selection'],
      trend: 'stable',
      sdgs: [9, 11],
      caveats: ['Usually requires an accredited engineering degree.'],
    },
  ],
}

export const trendsFixture: TrendSnapshot = {
  window: 'Last 12 months (demo)',
  signals: [
    { skill: 'AI literacy', direction: 'rising', change_pct: 41, source: 'Example Jobs Index (fictional)', source_url: 'https://example.com/jobs-index', observed_at: '2026-09-30', retrieved_at: '2026-10-20', status: 'fresh' },
    { skill: 'SQL', direction: 'rising', change_pct: 18, source: 'Example Jobs Index (fictional)', source_url: 'https://example.com/jobs-index', observed_at: '2026-09-30', retrieved_at: '2026-10-20', status: 'fresh' },
    { skill: 'ESG reporting', direction: 'rising', change_pct: 27, source: 'Demo Skills Observatory (fictional)', source_url: 'https://example.com/skills-observatory', observed_at: '2026-06-30', retrieved_at: '2026-10-20', status: 'stale' },
    { skill: 'Excel', direction: 'stable', change_pct: 2, source: 'Example Jobs Index (fictional)', source_url: 'https://example.com/jobs-index', observed_at: '2026-09-30', retrieved_at: '2026-10-20', status: 'fresh' },
    { skill: 'Manual data entry', direction: 'declining', change_pct: -33, source: 'Demo Skills Observatory (fictional)', source_url: 'https://example.com/skills-observatory', observed_at: '2026-06-30', retrieved_at: '2026-10-20', status: 'stale' },
    { skill: 'Routine bookkeeping', direction: 'declining', change_pct: -21, source: 'Example Jobs Index (fictional)', source_url: 'https://example.com/jobs-index', observed_at: '2026-09-30', retrieved_at: '2026-10-20', status: 'fresh' },
  ],
}

export const roadmapFixture: Roadmap = {
  role_id: 'data_analyst',
  total_hours: 96,
  steps: [
    { step_id: 's1', title: 'Spreadsheet modelling refresh', skill: 'Excel', hours: 6, status: 'done' },
    { step_id: 's2', title: 'SQL joins & aggregation', skill: 'SQL', hours: 20, status: 'doing' },
    { step_id: 's3', title: 'Dashboard project (public data)', skill: 'Power BI', hours: 30, status: 'todo' },
    { step_id: 's4', title: 'Data storytelling basics', skill: 'Data storytelling', hours: 12, status: 'todo' },
    { step_id: 's5', title: 'Python for analysis (pandas)', skill: 'Python', hours: 28, status: 'todo' },
  ],
}

/** Assistant notes shown on the dashboard. Phrased as things to weigh up, never as advice to follow. */
export const insightsFixture: { notes: { kind: 'skill' | 'trend' | 'fit'; text: string }[] } = {
  notes: [
    { kind: 'skill', text: 'SQL shows up as a gap in three of your four roles, so one course would move several at once.' },
    { kind: 'trend', text: 'Sustainability demand is rising, but two of its signals are older than 90 days. Check the dates before deciding.' },
    { kind: 'fit', text: 'Mechanical design usually needs an accredited engineering degree. It is listed for comparison, not as a recommendation.' },
  ],
}
