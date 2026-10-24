import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, FileUp, GraduationCap, Heart, ListChecks, LoaderCircle, PenLine, Sparkles, Wrench } from 'lucide-react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router'
import { ErrorNotice } from '@/components/api-states'
import { CvIntake } from '@/components/intake/cv-intake'
import { Chip, field, labelCls } from '@/components/intake/form'
import { ProjectsEditor } from '@/components/intake/projects-editor'
import { SkillPicker } from '@/components/intake/skill-picker'
import { Page } from '@/components/page/page'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { STORAGE_PREFIX } from '@/config/product'
import { DEMO_PROFILE } from '@/content/demo-profile'
import { EDUCATION_LEVELS, INTEREST_SUGGESTIONS, isCatalogSkill, SKILL_CATALOG } from '@/content/skills'
import { ApiError } from '@/lib/api'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { analyzeAndStore, getProfile, type ProfileSource } from '@/lib/profile-store'
import { cn } from '@/lib/utils'
import type { SkillRef, StudentProfile } from '@/types/api'

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
const DRAFT_KEY = `${STORAGE_PREFIX}:intake-draft`

const EMPTY: Draft = { education_level: '', degree: '', semester: '', skills: [], projects: [], experience_summary: '', interests: [] }

const fromProfile = (p: StudentProfile): Draft => ({
  education_level: p.education_level ?? '',
  degree: p.degree ?? '',
  semester: p.semester ? String(p.semester) : '',
  skills: p.skills.filter((s) => isCatalogSkill(s.skill_id)).map((s) => ({ ...s, proficiency: s.proficiency ?? 'beginner' })),
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
    if (saved) {
      const draft = { ...EMPTY, ...(JSON.parse(saved) as Draft) }
      return { ...draft, skills: draft.skills.filter((s) => isCatalogSkill(s.skill_id)) }
    }
  } catch {
    // ignore unreadable drafts
  }
  const stored = getProfile()
  return stored && !stored.demo ? fromProfile(stored.profile) : EMPTY
}

const stepValid = (d: Draft, step: number) => (step === 0 ? d.education_level !== '' : step === 1 ? d.skills.length > 0 : true)

function ProjectsStep({ draft, set }: { draft: Draft; set: (d: Partial<Draft>) => void }) {
  return (
    <div className="grid gap-6">
      <ProjectsEditor projects={draft.projects} onChange={(projects) => set({ projects })} />
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
      <div className="flex flex-wrap items-center gap-3 rounded-tile border border-dashed border-line-2 p-4">
        <FileUp className="size-5 flex-none text-muted-foreground" aria-hidden />
        <p className="flex-1 text-sm">
          <b>Have a CV?</b> <span className="text-muted-foreground">Upload a PDF and we’ll pre-fill your profile for you to check.</span>
        </p>
        <Button asChild variant="secondary" size="sm">
          <Link to="?path=cv">Upload CV (PDF)</Link>
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
        <p className="mb-3 text-sm text-muted-foreground">Interests don't change scores yet.</p>
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

function PathSwitch({ cv }: { cv: boolean }) {
  const options = [
    { to: '/start', label: 'Fill in the form', icon: PenLine, active: !cv },
    { to: '?path=cv', label: 'Upload CV (PDF)', icon: FileUp, active: cv },
  ]
  return (
    <nav aria-label="How to build your profile" data-enter="head" className="mb-4">
      <div className="flex w-fit max-w-full flex-wrap gap-1 rounded-full border border-line bg-glass-2 p-1 backdrop-blur-md">
        {options.map((o) => (
          <Link
            key={o.to}
            to={o.to}
            aria-current={o.active ? 'page' : undefined}
            className={cn('flex items-center gap-1.5 rounded-full px-4 py-2 text-md font-semibold whitespace-nowrap transition-colors', o.active ? 'bg-ink text-ink-foreground' : 'text-muted-foreground hover:text-foreground')}
          >
            <o.icon className="size-4" aria-hidden />
            {o.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}

/** Intake wizard: education → skills → projects & experience → interests → review → POST /profile/analyze. */
export default function Start() {
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const cvPath = params.get('path') === 'cv'
  const toast = useToast()
  const [draft, setDraft] = useState<Draft>(initialDraft)
  // ?step=skills reopens the skills step, e.g. from the "no recognized skills" notice
  const [step, setStep] = useState(() => (params.get('step') === 'skills' ? 1 : 0))
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

  // both paths end here: the form and a confirmed CV review
  const submit = async (profile: StudentProfile, source: ProfileSource, demo = false) => {
    await analyzeAndStore(profile, { demo, source })
    try {
      sessionStorage.removeItem(DRAFT_KEY)
    } catch {
      // ignore
    }
    toast('Profile analysed. Finding roles that fit…', { icon: Check })
    navigate('/dashboard')
  }

  const analyze = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const isDemo = JSON.stringify(toProfile(draft)) === JSON.stringify(toProfile(fromProfile(DEMO_PROFILE)))
      await submit(toProfile(draft), 'form', isDemo)
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
      crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Profile' }]}
      subtitle={
        cvPath
          ? 'Upload a PDF, check what we read, then confirm. Nothing about your age, gender or background is used.'
          : 'Five short steps. Nothing about your age, gender or background is asked or used.'
      }
      actions={
        cvPath
          ? undefined
          : [
              <Button key="demo" variant="secondary" onClick={loadDemo}>
                <Sparkles />
                Load demo student
              </Button>,
            ]
      }
    >
      {notFound && (
        <p data-enter="head" role="status" className="mb-4 rounded-tile border border-line bg-glass p-3 pl-4 text-sm">
          Your previous profile could not be found on the server, so please enter it again.
        </p>
      )}

      <PathSwitch cv={cvPath} />

      {cvPath ? (
        <CvIntake onConfirm={(profile) => submit(profile, 'cv')} resume={params.get('step') === 'review'} />
      ) : (
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
              {step === 1 && (
                <div className="grid gap-4">
                  <p className="text-sm text-muted-foreground">We match on {SKILL_CATALOG.length} core skills from O*NET. More skills are coming in Phase 2.</p>
                  <SkillPicker skills={draft.skills} onChange={(skills) => set({ skills })} />
                </div>
              )}
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
      )}
    </Page>
  )
}
