import { useState } from 'react'
import { X } from 'lucide-react'
import { SKILL_CATALOG } from '@/content/skills'
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

/** Search the skill catalogue, add skills and set a self-reported level for each. Only catalogue ids can be added. */
export function SkillPicker({ skills, onChange, evidence }: SkillPickerProps) {
  const [query, setQuery] = useState('')
  const chosen = new Set(skills.map((s) => s.skill_id))
  const q = query.trim().toLowerCase()
  const matches = SKILL_CATALOG.filter((s) => !chosen.has(s.skill_id) && (!q || s.name.toLowerCase().includes(q)))

  const add = (s: { skill_id: string; name: string }) => {
    onChange([...skills, { ...s, proficiency: 'beginner' }])
    setQuery('')
  }
  const update = (id: string, proficiency: Proficiency) => onChange(skills.map((s) => (s.skill_id === id ? { ...s, proficiency } : s)))
  const remove = (id: string) => onChange(skills.filter((s) => s.skill_id !== id))

  return (
    <div className="grid gap-6">
      <div>
        <label htmlFor="skill-search" className={labelCls}>
          Find a skill
        </label>
        <input
          id="skill-search"
          className={field}
          placeholder="Search, e.g. Python, Excel, GIS…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key !== 'Enter') return
            e.preventDefault()
            if (matches[0]) add(matches[0])
          }}
        />
        <div className="mt-3 flex flex-wrap gap-2" aria-label="Suggestions">
          {matches.map((s) => (
            <Chip key={s.skill_id} active={false} onClick={() => add(s)}>
              {s.name}
            </Chip>
          ))}
        </div>
        {q && !SKILL_CATALOG.some((s) => s.name.toLowerCase().includes(q)) && (
          <p className="mt-2 text-sm text-muted-foreground">No catalogue skill matches “{query.trim()}”. Only catalogue skills count toward a role.</p>
        )}
      </div>

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
