import { useEffect, useRef, useState } from 'react'
import { FileUp, LoaderCircle, RotateCcw, TriangleAlert } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { api, ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { APIEnvelope, CvParsePayload } from '@/types/api'

const MAX_BYTES = 5 * 1024 * 1024
const PDF_TYPES = ['application/pdf', 'application/x-pdf']

type Phase =
  | { name: 'idle' }
  | { name: 'uploading'; sent: number }
  | { name: 'processing' }
  | { name: 'error'; title: string; message: string; file?: File; unavailable?: boolean }

function checkFile(file: File) {
  const pdf = PDF_TYPES.includes(file.type) || (file.type === '' && /\.pdf$/i.test(file.name))
  if (!pdf) return `“${file.name}” is not a PDF. Please choose a PDF file.`
  if (file.size === 0) return `“${file.name}” is empty. Please choose another PDF.`
  // rounded up, so a file just over the limit never reads as "5.0 MB"
  if (file.size > MAX_BYTES) return `“${file.name}” is ${Math.ceil(file.size / 1024 / 102.4) / 10} MB. The limit is 5 MB.`
  return null
}

function failure(error: unknown, file: File): Extract<Phase, { name: 'error' }> {
  if (!(error instanceof ApiError)) return { name: 'error', title: 'Something went wrong', message: 'Something went wrong while reading your CV.', file }
  // the CV parser is not deployed on every server yet
  if (error.status === 404 || error.status === 405) return { name: 'error', title: 'CV upload unavailable', message: 'CV upload is not available on this server yet.', unavailable: true }
  // the file itself was rejected (INVALID_CV_FILE, FILE_TOO_LARGE, VALIDATION_ERROR); sending it again won't help
  if (error.status === 413 || error.status === 422) return { name: 'error', title: 'We couldn’t read that file', message: error.message }
  const title = error.kind === 'network' || error.kind === 'timeout' ? 'Can’t reach the server' : 'Something went wrong'
  return { name: 'error', title, message: error.message, file }
}

/** Drop zone and upload states for POST /cv/parse. The file stays in memory and is never stored. */
export function CvUpload({ onParsed, autoFocus }: { onParsed: (result: APIEnvelope<CvParsePayload>) => void; autoFocus?: boolean }) {
  const [phase, setPhase] = useState<Phase>({ name: 'idle' })
  const [dragging, setDragging] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const request = useRef<AbortController | null>(null)
  const busy = phase.name === 'uploading' || phase.name === 'processing'
  const retryFile = phase.name === 'error' ? phase.file : undefined

  useEffect(() => () => request.current?.abort(), [])

  const send = async (file: File) => {
    const problem = checkFile(file)
    if (problem) {
      setPhase({ name: 'error', title: 'We couldn’t read that file', message: problem })
      return
    }
    const controller = new AbortController()
    request.current = controller
    setPhase({ name: 'uploading', sent: 0 })
    try {
      const result = await api.parseCv(file, {
        signal: controller.signal,
        onProgress: (sent) => setPhase({ name: 'uploading', sent }),
        onUploaded: () => setPhase({ name: 'processing' }),
      })
      onParsed(result)
    } catch (e) {
      if (controller.signal.aborted) setPhase({ name: 'idle' })
      else setPhase(failure(e, file))
    }
  }

  const pick = (files: FileList | null) => {
    const file = files?.[0]
    if (file) send(file)
  }

  return (
    <div className="grid gap-4">
      <button
        type="button"
        aria-disabled={busy}
        aria-describedby="cv-hint"
        autoFocus={autoFocus}
        onClick={() => !busy && input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!busy) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          if (!busy) pick(e.dataTransfer.files)
        }}
        className={cn(
          'grid w-full place-items-center gap-2 rounded-tile border-2 border-dashed px-6 py-10 text-center transition-colors outline-none focus-visible:border-primary aria-disabled:cursor-progress',
          dragging ? 'border-primary bg-well' : 'border-line-2 hover:bg-well/60',
        )}
      >
        <span className="grid size-12 place-items-center rounded-full bg-well" aria-hidden>
          <FileUp className="size-5" />
        </span>
        <span className="text-lg font-bold">Drop your CV here, or choose a file</span>
        <span id="cv-hint" className="text-sm text-muted-foreground">
          PDF only, up to 5 MB. Scanned images can’t be read; use a PDF with selectable text.
        </span>
      </button>
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(e) => {
          pick(e.target.files)
          e.target.value = ''
        }}
      />

      <div role="status" aria-live="polite">
        {busy && (
          <div className="flex flex-wrap items-center gap-3 rounded-tile bg-well p-3 pl-4">
            <LoaderCircle className="size-5 flex-none animate-spin text-primary" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="font-semibold">{phase.name === 'uploading' ? `Uploading… ${Math.round(phase.sent * 100)}%` : 'Reading your CV…'}</p>
              <p className="text-sm text-muted-foreground">{phase.name === 'uploading' ? 'Sending the file securely.' : 'Pulling out education, skills and projects. This can take up to half a minute.'}</p>
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={() => request.current?.abort()}>
              Cancel
            </Button>
          </div>
        )}
      </div>

      {phase.name === 'error' && (
        <div role="alert" className="flex items-start gap-3 rounded-tile border border-line bg-well/50 p-4">
          <TriangleAlert className="mt-0.5 size-5 flex-none text-tomato" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="font-bold">{phase.title}</p>
            <p className="text-muted-foreground">
              {phase.message} {phase.unavailable && 'Please fill in the form instead.'}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {retryFile && (
                <Button type="button" size="sm" onClick={() => send(retryFile)}>
                  <RotateCcw />
                  Try again
                </Button>
              )}
              {phase.unavailable && (
                <Button asChild size="sm">
                  <Link to="/start">Fill in the form</Link>
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">Your PDF is only used to pre-fill your profile. It isn’t saved in your browser, and the server discards it after reading.</p>
    </div>
  )
}
