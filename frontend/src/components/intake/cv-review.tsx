import { useEffect, useRef, useState } from 'react'
import { Check, FileUp, Link2, LoaderCircle, Plus, Sparkles } from 'lucide-react'
import { ErrorNotice } from '@/components/api-states'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { EDUCATION_LEVELS, isCatalogSkill, SKILL_CATALOG } from '@/content/skills'
import { ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { APIEnvelope, CvParsePayload, SkillRef, StudentProfile } from '@/types/api'
import { field, labelCls } from './form'
import { ProjectsEditor } from './projects-editor'
import { SkillPicker, SkillSearch } from './skill-picker'

type Review = {
  education_level: string
  degree: string
  semester: string
  skills: SkillRef[]
  projects: string[]
  experience_summary: string
}

/** What the student did on the review screen; kept in memory so they can come back to it. */
export type CvReviewState = {
  review: Review
  /** CV skill text → the catalogue skill_id the student mapped it to */
  mapped: Record<string, string>
}

const joined = (...parts: (string | null | undefined)[]) => parts.filter(Boolean).join(' · ')
const span = (start?: string | null, end?: string | null) => (start || end ? `${start ?? '?'} – ${end ?? 'now'}` : null)

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="grid gap-3 border-t border-line pt-5">
      <div>
        <h3 className="text-lg font-bold">{title}</h3>
        {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </section>
  )
}

/** Read-only lines from the CV, shown beside the fields they inform. */
function FromCv({ items }: { items: string[] }) {
  if (!items.length) return null
  return (
    <ul className="grid gap-1.5" aria-label="From your CV">
      {items.map((t, i) => (
        <li key={`${t}-${i}`} className="rounded-lg bg-well px-3 py-2 text-sm">
          <span className="text-muted-foreground">From your CV: </span>
          {t}
        </li>
      ))}
    </ul>
  )
}

type MapToCatalogProps = {
  raw: string
  skills: SkillRef[]
  mappedTo?: SkillRef
  onMap: (skill: { skill_id: string; name: string }) => void
  onUndo: () => void
}

/** Lets the student point a skill we could not match at a catalogue skill. Only catalogue ids can come out of it. */
function MapToCatalog({ raw, skills, mappedTo, onMap, onUndo }: MapToCatalogProps) {
  const [open, setOpen] = useState(false)
  if (mappedTo) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="good" enter={false}>
          <Check className="size-3.5" aria-hidden />
          Mapped to {mappedTo.name}
        </Badge>
        <Button type="button" variant="ghost" size="sm" onClick={onUndo}>
          Undo
        </Button>
      </div>
    )
  }
  if (!open) {
    return (
      <Button type="button" variant="secondary" size="sm" onClick={() => setOpen(true)}>
        <Link2 />
        Map to a catalog skill
      </Button>
    )
  }
  return (
    <div className="grid w-full basis-full gap-2">
      <SkillSearch
        label={`Catalogue skill that means the same as “${raw}”`}
        exclude={new Set(skills.map((k) => k.skill_id))}
        autoFocus
        onPick={(skill) => {
          onMap(skill)
          setOpen(false)
        }}
      />
      <Button type="button" variant="ghost" size="sm" className="justify-self-start" onClick={() => setOpen(false)}>
        Cancel
      </Button>
    </div>
  )
}

type CvReviewProps = {
  result: APIEnvelope<CvParsePayload>
  /** an earlier review of the same CV, to pick up where the student left off */
  initial?: CvReviewState
  onConfirm: (profile: StudentProfile, state: CvReviewState) => Promise<void>
  onRestart: () => void
}

/**
 * Editable review of a parsed CV ("ok" status). Only catalogue skills can be added; skills the
 * parser could not back with a quote start unchecked, and skills outside the catalogue are
 * never sent unless the student maps one to a catalogue skill. Nothing is saved until the
 * student confirms. The draft stays in memory only.
 */
export function CvReview({ result, initial, onConfirm, onRestart }: CvReviewProps) {
  const { draft } = result.data
  const suggested = draft.suggested_profile
  const [review, setReview] = useState<Review>(
    () =>
      initial?.review ?? {
        education_level: suggested.education_level ?? '',
        degree: suggested.degree ?? '',
        semester: suggested.semester ? String(suggested.semester) : '',
        skills: suggested.skills.filter((s) => isCatalogSkill(s.skill_id)),
        projects: [...suggested.projects],
        experience_summary: suggested.experience_summary ?? '',
      },
  )
  const [mapped, setMapped] = useState<Record<string, string>>(() => initial?.mapped ?? {})
  const [confirmed, setConfirmed] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const heading = useRef<HTMLHeadingElement>(null)

  useEffect(() => heading.current?.focus(), [])

  const set = (patch: Partial<Review>) => setReview((r) => ({ ...r, ...patch }))
  const evidence = Object.fromEntries([
    ...draft.unmapped_skills.filter((u) => mapped[`u:${u.raw_text}`]).map((u) => [mapped[`u:${u.raw_text}`], u.evidence]),
    ...draft.mapped_skills.map((s) => [s.skill_id, s.evidence]),
  ])
  const needsReview = draft.skills_requiring_review ?? []
  const ready = review.education_level !== '' && review.skills.length > 0

  const mappedTo = (key: string) => review.skills.find((k) => k.skill_id === mapped[key])
  const mapSkill = (key: string, skill: { skill_id: string; name: string }) => {
    setMapped((m) => ({ ...m, [key]: skill.skill_id }))
    set({ skills: [...review.skills, { skill_id: skill.skill_id, name: skill.name, proficiency: null }] })
  }
  const unmap = (key: string) => {
    set({ skills: review.skills.filter((k) => k.skill_id !== mapped[key]) })
    setMapped((m) => {
      const next = { ...m }
      delete next[key]
      return next
    })
  }
  const mapControl = (key: string, raw: string) => <MapToCatalog raw={raw} skills={review.skills} mappedTo={mappedTo(key)} onMap={(skill) => mapSkill(key, skill)} onUndo={() => unmap(key)} />

  const confirm = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await onConfirm(
        {
          ...suggested,
          profile_id: null,
          education_level: review.education_level,
          degree: review.degree.trim() || null,
          semester: review.semester ? Number(review.semester) : null,
          skills: review.skills,
          projects: review.projects.map((p) => p.trim()).filter(Boolean),
          experience_summary: review.experience_summary.trim() || null,
        },
        { review, mapped },
      )
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError({ kind: 'http', status: 0, code: 'UNKNOWN', message: String(e) }))
      setSubmitting(false)
    }
  }

  return (
    <Card className="grid gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 ref={heading} tabIndex={-1} className="text-2xl font-extrabold tracking-[-0.02em] outline-none">
            Check what we read from your CV
          </h2>
          <p className="text-muted-foreground">
            {result.data.page_count} page{result.data.page_count === 1 ? '' : 's'} read. Edit anything that is wrong; nothing is saved until you confirm.
          </p>
        </div>
        <DataModeBadge mode={result.data_mode} />
      </div>

      {result.warnings.length > 0 && (
        <ul className="grid gap-1.5" aria-label="Notes from the CV reader">
          {result.warnings.map((w) => (
            <li key={w} className="rounded-lg border border-line bg-well/50 px-3 py-2 text-sm">
              {w}
            </li>
          ))}
        </ul>
      )}

      <Section title="Education" hint="A CV doesn’t say how far along you are, so choose your level of study yourself.">
        <FromCv items={draft.education.map((e) => joined(e.degree, e.field_of_study, e.institution, span(e.start_date, e.end_date))).filter(Boolean)} />
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label htmlFor="cv-level" className={labelCls}>
              Level of study
            </label>
            <select id="cv-level" className={field} value={review.education_level} onChange={(e) => set({ education_level: e.target.value })} aria-required>
              <option value="">Choose one…</option>
              {EDUCATION_LEVELS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="cv-degree" className={labelCls}>
              Degree or programme
            </label>
            <input id="cv-degree" className={field} value={review.degree} onChange={(e) => set({ degree: e.target.value })} />
          </div>
          <div>
            <label htmlFor="cv-semester" className={labelCls}>
              Semester <span className="font-medium text-muted-foreground">(optional)</span>
            </label>
            <input id="cv-semester" type="number" min={1} max={14} className={field} value={review.semester} onChange={(e) => set({ semester: e.target.value })} />
          </div>
        </div>
      </Section>

      <Section title="Skills" hint="Each skill below was quoted in your CV and matched to the catalogue. Levels start empty: set them yourself.">
        <SkillPicker skills={review.skills} onChange={(skills) => set({ skills })} evidence={evidence} />
      </Section>

      {needsReview.length > 0 && (
        <Section
          title="Skills that need your confirmation"
          hint="Your CV named these, but we couldn’t find a quote that backs them up, so they were not added. Add or map one only if it is accurate."
        >
          <ul className="grid gap-2">
            {needsReview.map((s) => {
              const match = SKILL_CATALOG.find((c) => c.name.toLowerCase() === s.name.trim().toLowerCase())
              const added = match && review.skills.some((k) => k.skill_id === match.skill_id)
              return (
                <li key={s.name} className="flex flex-wrap items-center gap-3 rounded-tile border border-[color-mix(in_srgb,var(--warn)_45%,transparent)] bg-[color-mix(in_srgb,var(--warn)_10%,transparent)] p-3 pl-4">
                  <div className="min-w-[12rem] flex-1">
                    <b>{s.name}</b>
                    <span className="block text-sm text-muted-foreground">{s.reason}</span>
                  </div>
                  {!match ? (
                    mapControl(`r:${s.name}`, s.name)
                  ) : added ? (
                    <Badge tone="good" enter={false}>
                      <Check className="size-3.5" aria-hidden />
                      Added
                    </Badge>
                  ) : (
                    <Button type="button" variant="secondary" size="sm" onClick={() => set({ skills: [...review.skills, { ...match, proficiency: null }] })}>
                      <Plus />
                      Add {match.name}
                    </Button>
                  )}
                </li>
              )
            })}
          </ul>
        </Section>
      )}

      {draft.unmapped_skills.length > 0 && (
        <Section
          title="Not in our skill catalogue"
          hint="Found in your CV, but they don’t match any catalogue skill, so they won’t be sent. If one means the same as a catalogue skill, map it and it counts as that skill."
        >
          <ul className="grid gap-2">
            {draft.unmapped_skills.map((s) => (
              <li key={s.raw_text} className="flex flex-wrap items-center gap-3 rounded-tile border border-dashed border-line-2 p-3 pl-4">
                <div className="min-w-[12rem] flex-1">
                  <b>{s.raw_text}</b>
                  <span className="block text-xs text-muted-foreground">From your CV: “{s.evidence}”</span>
                </div>
                {mapControl(`u:${s.raw_text}`, s.raw_text)}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Projects">
        <ProjectsEditor projects={review.projects} onChange={(projects) => set({ projects })} />
      </Section>

      <Section title="Experience">
        <FromCv
          items={[
            ...draft.experience.map((e) => joined(e.role, e.organization, span(e.start_date, e.end_date))).filter(Boolean),
            ...draft.certifications.map((c) => joined(c.name, c.issuer, c.year)),
          ]}
        />
        <div>
          <label htmlFor="cv-experience" className={labelCls}>
            Experience summary <span className="font-medium text-muted-foreground">(optional)</span>
          </label>
          <textarea id="cv-experience" rows={4} className={cn(field, 'h-auto py-3')} value={review.experience_summary} onChange={(e) => set({ experience_summary: e.target.value })} />
        </div>
      </Section>

      <div className="grid gap-4 border-t border-line pt-5">
        {error && <ErrorNotice error={error} onRetry={confirm} />}
        {!ready && <p className="text-sm text-muted-foreground">Choose your level of study and keep at least one skill to continue.</p>}
        <label className="flex items-start gap-3 rounded-tile bg-well p-3 pl-4">
          <input type="checkbox" className="mt-1 size-4 accent-[var(--primary)]" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
          <span>I’ve checked these details. They describe me accurately and can be used to find matching roles.</span>
        </label>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button type="button" variant="ghost" onClick={onRestart} disabled={submitting}>
            <FileUp />
            Upload a different PDF
          </Button>
          <Button type="button" magnetic onClick={confirm} disabled={!confirmed || !ready || submitting}>
            {submitting ? <LoaderCircle className="animate-spin" /> : <Sparkles />}
            {submitting ? 'Analysing…' : 'Confirm and find my roles'}
          </Button>
        </div>
      </div>
    </Card>
  )
}
