import { useEffect, useRef, useState } from 'react'
import { Check, Palette } from 'lucide-react'
import { useToast } from '@/components/ui/toast'
import { useTheme } from '@/hooks/use-theme'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion, pressPop } from '@/lib/motion'
import { ACCENTS, type Accent } from '@/lib/theme'
import { cn } from '@/lib/utils'

const LABEL: Record<Accent, string> = { emerald: 'Emerald', petrol: 'Petrol', indigo: 'Indigo', tomato: 'Tomato' }
// swatch colours are fixed so the picker shows every option, whatever the current accent
const SWATCH: Record<Accent, string> = { emerald: '#146c54', petrol: '#0f6c78', indigo: '#4549b8', tomato: '#b9431d' }

/**
 * Accent colour picker (Halden idea): a radio group of swatches; choosing one pops the swatch
 * (scale .92 → 1, back.out(3)) and bounces a preview of bars (scaleY .2 → 1, back.out(1.6)).
 */
export function AccentPicker({ side = 'right', className }: { side?: 'right' | 'top'; className?: string }) {
  const { accent, setAccent } = useTheme()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const panel = useRef<HTMLDivElement>(null)

  const bounce = () => {
    if (prefersReducedMotion() || !panel.current) return
    gsap.fromTo(panel.current.querySelectorAll('[data-preview-bar]'), { scaleY: 0.2 }, { scaleY: 1, duration: 0.7, ease: 'back.out(1.6)', stagger: 0.05, transformOrigin: '50% 100%' })
  }

  useEffect(() => {
    if (!open) return
    const onDown = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    if (!prefersReducedMotion() && panel.current) {
      gsap.fromTo(panel.current, { opacity: 0, scale: 0.94, y: side === 'top' ? 8 : 0, x: side === 'right' ? -8 : 0 }, { opacity: 1, scale: 1, x: 0, y: 0, duration: 0.35, ease: 'back.out(1.8)' })
      bounce()
    }
    panel.current?.querySelector<HTMLElement>('[aria-checked="true"]')?.focus()
    return () => {
      document.removeEventListener('pointerdown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open, side])

  const choose = (a: Accent, el: HTMLElement) => {
    setAccent(a, el)
    if (!prefersReducedMotion()) gsap.fromTo(el, { scale: 0.92 }, { scale: 1, duration: 0.5, ease: 'back.out(3)', clearProps: 'scale' })
    bounce()
    toast(`Accent set to ${LABEL[a]}`)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (!step) return
    e.preventDefault()
    const next = ACCENTS[(ACCENTS.indexOf(accent) + step + ACCENTS.length) % ACCENTS.length]
    const btn = panel.current?.querySelector<HTMLElement>(`[data-accent-pick="${next}"]`)
    if (btn) {
      choose(next, btn)
      btn.focus()
    }
  }

  return (
    <div ref={root} className={cn('relative', className)}>
      <button
        type="button"
        aria-label="Accent colour"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={(e) => {
          pressPop(e.currentTarget)
          setOpen((o) => !o)
        }}
        className="grid size-11 place-items-center rounded-full text-current opacity-80 transition hover:bg-white/10 hover:opacity-100"
      >
        <Palette className="size-[19px]" aria-hidden />
      </button>
      {open && (
        <div
          ref={panel}
          role="dialog"
          aria-label="Accent colour"
          className={cn(
            'glass absolute z-50 w-60 rounded-tile bg-raised p-4 text-foreground shadow-pop',
            side === 'right' ? 'top-1/2 left-[calc(100%+14px)] -translate-y-1/2' : 'bottom-[calc(100%+14px)] left-1/2 -translate-x-1/2',
          )}
        >
          <p className="mb-3 text-sm font-bold">Accent colour</p>
          <div role="radiogroup" aria-label="Accent colour" className="flex gap-2.5" onKeyDown={onKeyDown}>
            {ACCENTS.map((a) => (
              <button
                key={a}
                type="button"
                role="radio"
                aria-checked={accent === a}
                aria-label={LABEL[a]}
                tabIndex={accent === a ? 0 : -1}
                data-accent-pick={a}
                onClick={(e) => choose(a, e.currentTarget)}
                className="grid size-10 place-items-center rounded-full ring-offset-2 ring-offset-raised outline-none focus-visible:ring-2 focus-visible:ring-primary"
                style={{ background: SWATCH[a] }}
              >
                {accent === a && <Check className="size-4 text-white" aria-hidden />}
              </button>
            ))}
          </div>
          <div aria-hidden className="mt-4 flex h-14 items-end gap-1.5 rounded-xl bg-well p-2">
            {[0.45, 0.8, 0.6, 1, 0.7, 0.5].map((h, i) => (
              <i key={i} data-preview-bar className="flex-1 rounded-md bg-primary" style={{ height: `${h * 100}%`, opacity: 0.55 + h * 0.45 }} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
