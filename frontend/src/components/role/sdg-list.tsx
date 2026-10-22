import { SdgBadges } from '@/components/sdg-badges'
import { skillName } from '@/content/skills'
import type { RoleMatch, SdgPayload } from '@/types/api'

/** The role's own SDG links, then each skill's, marked by whether the student has the skill. */
export function SdgList({ data, match }: { data: SdgPayload; match?: RoleMatch }) {
  const have = new Set(match?.matched_skills?.map((s) => s.skill_id))
  const known = [...(match?.matched_skills ?? []), ...(match?.missing_skills ?? [])]
  return (
    <div className="grid gap-6">
      <section aria-labelledby="sdg-role">
        <p id="sdg-role" className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
          The role
        </p>
        {data.role_sdg_mappings.length ? (
          <ul className="grid gap-2">
            {data.role_sdg_mappings.map((r) => (
              <li key={r.sdg_id} data-enter="item" className="flex items-start gap-3 rounded-[16px] bg-well p-3">
                <SdgBadges goals={[r.sdg_id]} />
                <span className="text-md leading-snug">{r.reason}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No SDG link is recorded for this role yet.</p>
        )}
      </section>
      <section aria-labelledby="sdg-skills">
        <p id="sdg-skills" className="mb-2 text-xs font-bold tracking-[0.12em] text-muted-foreground uppercase">
          Its skills
        </p>
        {data.skill_sdg_mappings.length ? (
          <ul className="grid gap-2 md:grid-cols-2">
            {data.skill_sdg_mappings.map((s) => (
              <li key={`${s.skill_id}-${s.sdg_id}`} data-enter="item" className="flex items-start gap-3 rounded-[16px] border border-line p-3">
                <SdgBadges goals={[s.sdg_id]} size="sm" />
                <span className="grid gap-0.5">
                  <b className="text-sm">
                    {skillName(s.skill_id, known)}
                    {have.has(s.skill_id) && <span className="ml-2 text-xs font-semibold text-good">you have this</span>}
                  </b>
                  <span className="text-sm leading-snug text-muted-foreground">{s.reason}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No skill-level SDG links are recorded for this role yet.</p>
        )}
      </section>
    </div>
  )
}
