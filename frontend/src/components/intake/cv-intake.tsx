import { useEffect, useRef, useState } from 'react'
import { FileUp, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { DataModeBadge } from '@/components/data-mode-badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/lib/utils'
import type { APIEnvelope, CvParsePayload, StudentProfile } from '@/types/api'
import { CvReview } from './cv-review'
import { CvUpload } from './cv-upload'
import { field, labelCls } from './form'

/** manual_review and no_extractable_text: an honestly empty draft, so the student continues with the form. */
function CvFallback({ result, onRestart }: { result: APIEnvelope<CvParsePayload>; onRestart: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null)
  const preview = result.data.extracted_text_preview

  useEffect(() => heading.current?.focus(), [])

  return (
    <Card className="grid gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 ref={heading} tabIndex={-1} className="text-2xl font-extrabold tracking-[-0.02em] outline-none">
          {result.data.status === 'no_extractable_text' ? 'No text found in this PDF' : 'We couldn’t read this CV automatically'}
        </h2>
        <DataModeBadge mode={result.data_mode} />
      </div>
      <ul className="grid gap-1.5">
        {result.warnings.map((w) => (
          <li key={w} className="rounded-lg border border-line bg-well/50 px-3 py-2 text-sm">
            {w}
          </li>
        ))}
      </ul>
      {preview && (
        <div>
          <label htmlFor="cv-preview" className={labelCls}>
            Text we could read <span className="font-medium text-muted-foreground">(first 500 characters, to copy from)</span>
          </label>
          <textarea id="cv-preview" readOnly rows={7} className={cn(field, 'h-auto rounded-tile py-3 font-mono text-sm')} value={preview} />
        </div>
      )}
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link to="/start">
            <UserRoundPen />
            Fill in the form
          </Link>
        </Button>
        <Button type="button" variant="secondary" onClick={onRestart}>
          <FileUp />
          Try another PDF
        </Button>
      </div>
    </Card>
  )
}

/** The "Upload CV" path of the intake: upload → review (or fallback) → confirm, which hands the profile to onConfirm. */
export function CvIntake({ onConfirm }: { onConfirm: (profile: StudentProfile) => Promise<void> }) {
  const [result, setResult] = useState<APIEnvelope<CvParsePayload> | null>(null)
  const [restarted, setRestarted] = useState(false)
  const toast = useToast()
  const restart = () => {
    setResult(null)
    setRestarted(true)
  }

  if (!result) {
    return (
      <Card>
        <CvUpload
          autoFocus={restarted}
          onParsed={(r) => {
            if (r.data.status === 'ok') toast('CV read. Check every field before you confirm.', { icon: FileUp })
            setResult(r)
          }}
        />
      </Card>
    )
  }
  if (result.data.status === 'ok') return <CvReview result={result} onConfirm={onConfirm} onRestart={restart} />
  return <CvFallback result={result} onRestart={restart} />
}
