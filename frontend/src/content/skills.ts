// Skill vocabulary for the intake: the backend's cached catalogue (backend/app/data/cached/skills.json),
// ids, names and aliases exactly as the API matches them.
import skillsJson from '../../../backend/app/data/cached/skills.json'
import type { SkillRef } from '@/types/api'

export type CatalogSkill = { skill_id: string; name: string; aliases: string[] }

export const SKILL_CATALOG: CatalogSkill[] = skillsJson.skills.map((s) => ({ skill_id: s.skill_id, name: s.name, aliases: s.aliases ?? [] }))

/** A search hit: the catalogue skill, plus the alias that matched when the name itself did not. */
export type SkillHit = { skill: CatalogSkill; alias?: string }

/** Catalogue skills whose name or one of its aliases contains the query (case-insensitive). */
export function searchSkills(query: string): SkillHit[] {
  const q = query.trim().toLowerCase()
  if (!q) return SKILL_CATALOG.map((skill) => ({ skill }))
  return SKILL_CATALOG.flatMap((skill): SkillHit[] => {
    if (skill.name.toLowerCase().includes(q)) return [{ skill }]
    const alias = skill.aliases.find((a) => a.toLowerCase().includes(q))
    return alias ? [{ skill, alias }] : []
  })
}

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
