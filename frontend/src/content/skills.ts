// Skill vocabulary for the intake: Jawad's catalogue (data/skills.json), ids and names exactly.
// The backend has no catalogue endpoint yet, so keep this in step with that file.
import type { SkillRef } from '@/types/api'

export const SKILL_CATALOG: { skill_id: string; name: string }[] = [
  { skill_id: 'critical_thinking', name: 'Critical Thinking' },
  { skill_id: 'mathematics', name: 'Mathematics' },
  { skill_id: 'complex_problem_solving', name: 'Complex Problem Solving' },
  { skill_id: 'systems_analysis', name: 'Systems Analysis' },
  { skill_id: 'attention_to_detail', name: 'Attention to Detail' },
  { skill_id: 'excel', name: 'Excel' },
  { skill_id: 'sql', name: 'SQL' },
  { skill_id: 'python', name: 'Python' },
  { skill_id: 'data_visualization', name: 'Data Visualization' },
  { skill_id: 'cad_software', name: 'CAD Software' },
  { skill_id: 'matlab', name: 'MATLAB' },
  { skill_id: 'financial_analysis_software', name: 'Financial Analysis Software' },
  { skill_id: 'analytical_scientific_software', name: 'Analytical/Statistical Software' },
  { skill_id: 'vba', name: 'VBA' },
  { skill_id: 'programming', name: 'Programming' },
  { skill_id: 'javascript', name: 'JavaScript' },
  { skill_id: 'git', name: 'Git' },
  { skill_id: 'accounting_software', name: 'Accounting Software' },
  { skill_id: 'gis', name: 'GIS' },
  { skill_id: 'science', name: 'Science' },
]

const NAMES = new Map(SKILL_CATALOG.map((s) => [s.skill_id, s.name]))

export const isCatalogSkill = (id: string) => NAMES.has(id)

/** Display name for a skill id; uses names the API returned when we have them. */
export function skillName(id: string, known?: SkillRef[]) {
  return known?.find((s) => s.skill_id === id)?.name ?? NAMES.get(id) ?? id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export const INTEREST_SUGGESTIONS = ['Data analytics', 'Software', 'Finance', 'Accounting', 'Public health', 'Environment', 'Sustainability', 'Research', 'Public data']

export const EDUCATION_LEVELS = [
  { value: 'foundation', label: 'Foundation / matriculation' },
  { value: 'diploma', label: 'Diploma' },
  { value: 'undergraduate', label: 'Undergraduate (bachelor’s)' },
  { value: 'postgraduate', label: 'Postgraduate (master’s / PhD)' },
  { value: 'graduate', label: 'Fresh graduate' },
]
