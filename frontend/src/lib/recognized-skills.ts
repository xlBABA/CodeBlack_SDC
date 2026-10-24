import { isCatalogSkill } from '@/content/skills'
import type { RoleMatch, StudentProfile } from '@/types/api'

/**
 * True when a ranked list of roles would mean nothing: the profile holds no catalogue skill,
 * or the API scored no skill overlap with any role. It reads the profile and the API's own
 * score breakdown; it never scores anything itself.
 */
export function lacksRecognizedSkills(profile: StudentProfile, matches: RoleMatch[]) {
  return !profile.skills.some((s) => isCatalogSkill(s.skill_id)) || (matches.length > 0 && matches.every((m) => m.score_breakdown.skills === 0))
}
