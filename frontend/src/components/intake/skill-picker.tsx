import { useId, useState } from 'react'
import { X } from 'lucide-react'
import { type CatalogSkill, searchSkills } from '@/content/skills'
import { cn } from '@/lib/utils'
import type { Proficiency, SkillRef } from '@/types/api'
import { Chip, field, labelCls } from './form'

const LEVELS: Proficiency[] = ['beginner', 'intermediate', 'advanced']

type SkillPickerProps = {
  skills: SkillRef[]
  onChange: (skills: SkillRef[]) => void
  /** quotes from the student's CV that back a skill, by skill_id */
  evidence?: Record<string, string>
}

type SkillSearchProps = {
  label: React.ReactNode
  /** skill_ids already chosen, left out of the suggestions */
  exclude: Set<string>
  onPick: (skill: CatalogSkill) => void
  autoFocus?: boolean
}

/** Search box over the skill catalogue. It can only ever return a catalogue skill. */
export function SkillSearch({ label, exclude, onPick, autoFocus }: SkillSearchProps) {
  const id = useId()
  const [query, setQuery] = useState('')
  const hits = searchSkills(query)
  const matches = hits.filter((h) => !exclude.has(h.skill.skill_id))
  const pick = (s: CatalogSkill) => {
    onPick(s)
    setQuery('')
  }

  return (
    <div>
      <label htmlFor={id} className={labelCls}>
        {label}
      </label>
      <input
        id={id}
        className={field}
        placeholder="Search, e.g. Python, Excel, GIS…"
        value={query}
        autoFocus={autoFocus}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key !== 'Enter') return
          e.preventDefault()
          if (matches[0]) pick(matches[0].skill)
        }}
      />
      <div className="mt-3 flex flex-wrap gap-2" aria-label="Suggestions">
        {matches.map(({ skill, alias }) => (
          <Chip key={skill.skill_id} active={false} onClick={() => pick(skill)}>
            {alias ? (
              <span aria-label={`${alias}, counts as ${skill.name}`}>
                {alias} <span className="text-muted-foreground">→ {skill.name}</span>
              </span>
            ) : (
              skill.name
            )}
          </Chip>
        ))}
      </div>
      {query.trim() && hits.length === 0 && (
        <p className="mt-2 text-sm text-muted-foreground">No catalogue skill matches “{query.trim()}”. Only catalogue skills count toward a role.</p>
      )}
    </div>
  )
}

/** Search the skill catalogue, add skills and set a self-reported level for each. Only catalogue ids can be added. */
export function SkillPicker({ skills, onChange, evidence }: SkillPickerProps) {
  const chosen = new Set(skills.map((s) => s.skill_id))
  const update = (id: string, proficiency: Proficiency) => onChange(skills.map((s) => (s.skill_id === id ? { ...s, proficiency } : s)))
  const remove = (id: string) => onChange(skills.filter((s) => s.skill_id !== id))

  return (
    <div className="grid gap-6">
      <SkillSearch label="Find a skill" exclude={chosen} onPick={(s) => onChange([...skills, { ...s, proficiency: 'beginner' }])} />

      <div>
        <p className={labelCls}>Your skills ({skills.length})</p>
        {skills.length === 0 ? (
          <p className="rounded-tile border border-dashed border-line-2 p-4 text-muted-foreground">Add at least one skill to continue.</p>
        ) : (
          <ul className="grid gap-2">
            {skills.map((s) => (
              <li key={s.skill_id} data-enter="item" className="flex flex-wrap items-center gap-3 rounded-tile bg-well p-2 pl-4">
                <div className="min-w-[9rem] flex-1">
                  <b>{s.name}</b>
                  {evidence?.[s.skill_id] && <span className="block text-xs text-muted-foreground">From your CV: “{evidence[s.skill_id]}”</span>}
                </div>
                <div role="radiogroup" aria-label={`${s.name} level`} className="flex rounded-full border border-line-2 bg-raised p-0.5">
                  {LEVELS.map((l) => (
                    <button
                      key={l}
                      type="button"
                      role="radio"
                      aria-checked={s.proficiency === l}
                      onClick={() => update(s.skill_id, l)}
                      className={cn('rounded-full px-3 py-1 text-xs font-bold capitalize transition-colors', s.proficiency === l ? 'bg-ink text-ink-foreground' : 'text-muted-foreground hover:text-foreground')}
                    >
                      {l}
                    </button>
                  ))}
                </div>
                <button type="button" aria-label={`Remove ${s.name}`} onClick={() => remove(s.skill_id)} className="grid size-8 place-items-center rounded-full text-muted-foreground hover:bg-raised">
                  <X className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2 text-xs text-muted-foreground">Levels are your own estimate. They are not verified and are treated that way.</p>
      </div>
    </div>
  )
}
