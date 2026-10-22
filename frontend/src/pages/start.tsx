import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, FileUp, GraduationCap, Heart, ListChecks, LoaderCircle, Plus, Sparkles, Wrench, X } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router'
import { ErrorNotice } from '@/components/api-states'
import { Page } from '@/components/page/page'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { STORAGE_PREFIX } from '@/config/product'
import { DEMO_PROFILE } from '@/content/demo-profile'
import { EDUCATION_LEVELS, INTEREST_SUGGESTIONS, isCatalogSkill, SKILL_CATALOG, slugSkill } from '@/content/skills'
import { ApiError } from '@/lib/api'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { analyzeAndStore, getProfile } from '@/lib/profile-store'
import { cn } from '@/lib/utils'
import type { Proficiency, SkillRef, StudentProfile } from '@/types/api'

type Draft = {
  education_level: string
  degree: string
  semester: string
  skills: SkillRef[]
  projects: string[]
  experience_summary: string
  interests: string[]
}

const STEPS = [
  { label: 'Education', icon: GraduationCap },
  { label: 'Skills', icon: Wrench },
  { label: 'Projects & experience', icon: Sparkles },
  { label: 'Interests', icon: Heart },
  { label: 'Review', icon: ListChecks },
]
const LEVELS: Proficiency[] = ['beginner', 'intermediate', 'advanced']
const DRAFT_KEY = `${STORAGE_PREFIX}:intake-draft`

const EMPTY: Draft = { education_level: '', degree: '', semester: '', skills: [], projects: [], experience_summary: '', interests: [] }

const fromProfile = (p: StudentProfile): Draft => ({
  education_level: p.education_level ?? '',
  degree: p.degree ?? '',
  semester: p.semester ? String(p.semester) : '',
  skills: p.skills.map((s) => ({ ...s, proficiency: s.proficiency ?? 'beginner' })),
  projects: [...p.projects],
  experience_summary: p.experience_summary ?? '',
  interests: [...p.interests],
})

const toProfile = (d: Draft): StudentProfile => ({
  education_level: d.education_level || null,
  degree: d.degree.trim() || null,
  semester: d.semester ? Number(d.semester) : null,
  skills: d.skills,
  projects: d.projects.map((p) => p.trim()).filter(Boolean),
  experience_summary: d.experience_summary.trim() || null,
  interests: d.interests,
})

function initialDraft(): Draft {
  try {
    const saved = sessionStorage.getItem(DRAFT_KEY)
    if (saved) return { ...EMPTY, ...(JSON.parse(saved) as Draft) }
  } catch {
    // ignore unreadable drafts
  }
  const stored = getProfile()
  return stored && !stored.demo ? fromProfile(stored.profile) : EMPTY
}

const stepValid = (d: Draft, step: number) => (step === 0 ? d.education_level !== '' : step === 1 ? d.skills.length > 0 : true)

const field = 'h-11 w-full rounded-ctl border border-line-2 bg-raised px-4 text-base outline-none transition-colors focus-visible:border-primary dark:border-line'
const labelCls = 'mb-1.5 block text-sm font-bold'

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors',
        active ? 'border-transparent bg-primary text-primary-foreground' : 'border-line-2 hover:bg-well',
      )}
    >
      {active ? <Check className="size-3.5" aria-hidden /> : <Plus className="size-3.5" aria-hidden />}
      {children}
    </button>
  )
}

function SkillsStep({ draft, set }: { draft: Draft; set: (d: Partial<Draft>) => void }) {
  const [query, setQuery] = useState('')
  const chosen = new Set(draft.skills.map((s) => s.skill_id))
  const q = query.trim().toLowerCase()
  const matches = SKILL_CATALOG.filter((s) => !chosen.has(s.skill_id) && (!q || s.name.toLowerCase().includes(q)))
  const custom = q && !SKILL_CATALOG.some((s) => s.name.toLowerCase() === q) && !chosen.has(slugSkill(query))

  const add = (s: { skill_id: string; name: string }) => {
    set({ skills: [...draft.skills, { ...s, proficiency: 'beginner' }] })
    setQuery('')
  }
  const update = (id: string, proficiency: Proficiency) => set({ skills: draft.skills.map((s) => (s.skill_id === id ? { ...s, proficiency } : s)) })
  const remove = (id: string) => set({ skills: draft.skills.filter((s) => s.skill_id !== id) })

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
            else if (custom) add({ skill_id: slugSkill(query), name: query.trim() })
          }}
        />
        <div className="mt-3 flex flex-wrap gap-2" aria-label="Suggestions">
          {matches.slice(0, 14).map((s) => (
            <Chip key={s.skill_id} active={false} onClick={() => add(s)}>
              {s.name}
            </Chip>
          ))}
          {custom && (
            <Chip active={false} onClick={() => add({ skill_id: slugSkill(query), name: query.trim() })}>
              Add “{query.trim()}”
            </Chip>
          )}
        </div>
      </div>

      <div>
        <p className={labelCls}>Your skills ({draft.skills.length})</p>
        {draft.skills.length === 0 ? (
          <p className="rounded-tile border border-dashed border-line-2 p-4 text-muted-foreground">Add at least one skill to continue.</p>
        ) : (
          <ul className="grid gap-2">
            {draft.skills.map((s) => (
              <li key={s.skill_id} data-enter="item" className="flex flex-wrap items-center gap-3 rounded-tile bg-well p-2 pl-4">
                <b className="min-w-[9rem] flex-1">{s.name}</b>
                {!isCatalogSkill(s.skill_id) && (
                  <Badge tone="warn" enter={false} className="text-2xs" title="Not in the role catalogue yet; it may not count toward any role">
                    not in catalogue yet
                  </Badge>
                )}
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

function ProjectsStep({ draft, set }: { draft: Draft; set: (d: Partial<Draft>) => void }) {
  const [text, setText] = useState('')
  const add = () => {
    if (!text.trim()) return
    set({ projects: [...draft.projects, text.trim()] })
    setText('')
  }
  return (
    <div className="grid gap-6">
      <div>
        <label htmlFor="project" className={labelCls}>
          Projects you have done
        </label>
        <div className="flex gap-2">
          <input
            id="project"
            className={field}
            placeholder="e.g. Sales dashboard in Excel for a club"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                add()
              }
            }}
          />
          <Button type="button" variant="secondary" onClick={add} disabled={!text.trim()}>
            <Plus />
            Add
          </Button>
        </div>
        {draft.projects.length > 0 && (
          <ul className="mt-3 grid gap-2">
            {draft.projects.map((p, i) => (
              <li key={`${p}-${i}`} data-enter="item" className="flex items-center gap-3 rounded-tile bg-well p-2 pl-4">
                <span className="flex-1">{p}</span>
                <button type="button" aria-label={`Remove ${p}`} onClick={() => set({ projects: draft.projects.filter((_, k) => k !== i) })} className="grid size-8 place-items-center rounded-full text-muted-foreground hover:bg-raised">
                  <X className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <label htmlFor="experience" className={labelCls}>
          Experience <span className="font-medium text-muted-foreground">(optional)</span>
        </label>
        <textarea
          id="experience"
          rows={4}
          className={cn(field, 'h-auto py-3')}
          placeholder="Internships, part-time work, volunteering, competitions…"
          value={draft.experience_summary}
          onChange={(e) => set({ experience_summary: e.target.value })}
        />
      </div>
      <div className="flex items-center gap-3 rounded-tile border border-dashed border-line-2 p-4 opacity-80">
        <FileUp className="size-5 flex-none text-muted-foreground" aria-hidden />
        <p className="flex-1 text-sm">
          <b>Upload a CV</b> <span className="text-muted-foreground">to fill this in for you. Coming soon, once the secure parser is ready.</span>
        </p>
        <Button type="button" variant="secondary" size="sm" disabled aria-disabled>
          Coming soon
        </Button>
      </div>
    </div>
  )
}

function InterestsStep({ draft, set }: { draft: Draft; set: (d: Partial<Draft>) => void }) {
  const [text, setText] = useState('')
  const toggle = (i: string) => set({ interests: draft.interests.includes(i) ? draft.interests.filter((x) => x !== i) : [...draft.interests, i] })
  const options = [...new Set([...INTEREST_SUGGESTIONS, ...draft.interests])]
  return (
    <div className="grid gap-5">
      <fieldset>
        <legend className={labelCls}>What draws you? Pick any that fit.</legend>
        <div className="flex flex-wrap gap-2">
          {options.map((i) => (
            <Chip key={i} active={draft.interests.includes(i)} onClick={() => toggle(i)}>
              {i}
            </Chip>
          ))}
        </div>
      </fieldset>
      <div>
        <label htmlFor="interest" className={labelCls}>
          Something else
        </label>
        <input
          id="interest"
          className={field}
          placeholder="Type and press Enter"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && text.trim()) {
              e.preventDefault()
              if (!draft.interests.includes(text.trim())) set({ interests: [...draft.interests, text.trim()] })
              setText('')
            }
          }}
        />
      </div>
    </div>
  )
}

function Review({ draft, goTo }: { draft: Draft; goTo: (s: number) => void }) {
  const level = EDUCATION_LEVELS.find((l) => l.value === draft.education_level)?.label ?? '—'
  const rows: [string, React.ReactNode, number][] = [
    ['Education', `${level}${draft.degree ? ` · ${draft.degree}` : ''}${draft.semester ? ` · semester ${draft.semester}` : ''}`, 0],
    ['Skills', draft.skills.map((s) => `${s.name} (${s.proficiency})`).join(', ') || '—', 1],
    ['Projects', draft.projects.join('; ') || '—', 2],
    ['Experience', draft.experience_summary || '—', 2],
    ['Interests', draft.interests.join(', ') || '—', 3],
  ]
  return (
    <div className="grid gap-4">
      <dl className="grid gap-2">
        {rows.map(([k, v, s]) => (
          <div key={k} data-enter="item" className="flex flex-wrap items-start gap-x-4 gap-y-1 rounded-tile bg-well p-3 pl-4">
            <dt className="w-28 flex-none text-sm font-bold text-muted-foreground">{k}</dt>
            <dd className="min-w-0 flex-1">{v}</dd>
            <button type="button" onClick={() => goTo(s)} className="text-sm font-semibold text-primary hover:underline">
              Edit
            </button>
          </div>
        ))}
      </dl>
      <p className="text-sm text-muted-foreground">
        We never ask for or use your age, gender or background. Results are alignment estimates to help you think, not decisions made for you.
      </p>
    </div>
  )
}

/** Intake wizard: education → skills → projects & experience → interests → review → POST /profile/analyze. */
export default function Start() {
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const [draft, setDraft] = useState<Draft>(initialDraft)
  const [step, setStep] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const panel = useRef<HTMLDivElement>(null)
  const direction = useRef(1)
  const notFound = (location.state as { reason?: string } | null)?.reason === 'profile-not-found'

  const set = (patch: Partial<Draft>) =>
    setDraft((d) => {
      const next = { ...d, ...patch }
      try {
        sessionStorage.setItem(DRAFT_KEY, JSON.stringify(next))
      } catch {
        // drafts are a convenience only
      }
      return next
    })

  const goTo = (s: number) => {
    direction.current = s >= step ? 1 : -1
    setError(null)
    setStep(s)
  }

  // each step slides in from the side it comes from
  useLayoutEffect(() => {
    if (!panel.current || prefersReducedMotion()) return
    gsap.fromTo(panel.current, { x: 28 * direction.current, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: 'expo.out', clearProps: 'transform,opacity' })
  }, [step])

  const canNext = stepValid(draft, step)
  const reachable = useMemo(() => STEPS.map((_, i) => STEPS.slice(0, i).every((_, k) => stepValid(draft, k))), [draft])

  const loadDemo = () => {
    setDraft(fromProfile(DEMO_PROFILE))
    goTo(4)
    toast('Demo student loaded. All of it is synthetic.', { icon: Sparkles })
  }

  const analyze = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const isDemo = JSON.stringify(toProfile(draft)) === JSON.stringify(toProfile(fromProfile(DEMO_PROFILE)))
      await analyzeAndStore(toProfile(draft), { demo: isDemo })
      try {
        sessionStorage.removeItem(DRAFT_KEY)
      } catch {
        // ignore
      }
      toast('Profile analysed. Finding roles that fit…', { icon: Check })
      navigate('/dashboard')
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError({ kind: 'http', status: 0, code: 'UNKNOWN', message: String(e) }))
    } finally {
      setSubmitting(false)
    }
  }

  const Current = STEPS[step]

  return (
    <Page
      title="Build your profile"
      crumbs={[{ label: 'Workspace', to: '/dashboard' }, { label: 'Profile' }]}
      subtitle="Five short steps. Nothing about your age, gender or background is asked or used."
      actions={[
        <Button key="demo" variant="secondary" onClick={loadDemo}>
          <Sparkles />
          Load demo student
        </Button>,
      ]}
    >
      {notFound && (
        <p data-enter="head" role="status" className="mb-4 rounded-tile border border-line bg-glass p-3 pl-4 text-sm">
          Your previous profile could not be found on the server, so please enter it again.
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
        <Card className="h-fit p-3 sm:p-3">
          <ol className="grid gap-1" aria-label="Steps">
            {STEPS.map((s, i) => {
              const done = i < step && stepValid(draft, i)
              return (
                <li key={s.label}>
                  <button
                    type="button"
                    disabled={!reachable[i]}
                    aria-current={i === step ? 'step' : undefined}
                    onClick={() => goTo(i)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-[16px] px-3 py-2.5 text-left font-semibold transition-colors disabled:opacity-40',
                      i === step ? 'bg-ink text-ink-foreground' : 'hover:bg-well',
                    )}
                  >
                    <span className={cn('grid size-8 flex-none place-items-center rounded-full text-sm', i === step ? 'bg-white/15' : done ? 'bg-primary text-primary-foreground' : 'bg-well')}>
                      {done ? <Check className="size-4" aria-hidden /> : i + 1}
                    </span>
                    {s.label}
                  </button>
                </li>
              )
            })}
          </ol>
        </Card>

        <Card>
          <div className="mb-5 flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-full bg-well" aria-hidden>
              <Current.icon className="size-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-muted-foreground">
                Step {step + 1} of {STEPS.length}
              </p>
              <h2 className="text-2xl font-extrabold tracking-[-0.02em]">{Current.label}</h2>
            </div>
          </div>

          <div ref={panel}>
            {step === 0 && (
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="level" className={labelCls}>
                    Level of study
                  </label>
                  <select id="level" className={field} value={draft.education_level} onChange={(e) => set({ education_level: e.target.value })}>
                    <option value="">Choose one…</option>
                    {EDUCATION_LEVELS.map((l) => (
                      <option key={l.value} value={l.value}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="degree" className={labelCls}>
                    Degree or programme
                  </label>
                  <input id="degree" className={field} placeholder="e.g. BSc Data Science" value={draft.degree} onChange={(e) => set({ degree: e.target.value })} />
                </div>
                <div>
                  <label htmlFor="semester" className={labelCls}>
                    Semester <span className="font-medium text-muted-foreground">(optional)</span>
                  </label>
                  <input id="semester" type="number" min={1} max={14} className={field} value={draft.semester} onChange={(e) => set({ semester: e.target.value })} />
                </div>
              </div>
            )}
            {step === 1 && <SkillsStep draft={draft} set={set} />}
            {step === 2 && <ProjectsStep draft={draft} set={set} />}
            {step === 3 && <InterestsStep draft={draft} set={set} />}
            {step === 4 && <Review draft={draft} goTo={goTo} />}
          </div>

          {error && (
            <div className="mt-5">
              <ErrorNotice error={error} onRetry={analyze} />
            </div>
          )}

          <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5">
            <Button type="button" variant="ghost" onClick={() => goTo(step - 1)} disabled={step === 0 || submitting}>
              <ArrowLeft />
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button type="button" onClick={() => goTo(step + 1)} disabled={!canNext}>
                Next
                <ArrowRight />
              </Button>
            ) : (
              <Button type="button" magnetic onClick={analyze} disabled={submitting || !reachable[4]}>
                {submitting ? <LoaderCircle className="animate-spin" /> : <Sparkles />}
                {submitting ? 'Analysing…' : 'Analyze my profile'}
              </Button>
            )}
          </div>
        </Card>
      </div>
    </Page>
  )
}
