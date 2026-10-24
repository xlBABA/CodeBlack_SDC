import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { Check, type LucideIcon } from 'lucide-react'
import { gsap } from '@/lib/gsap'
import { dur, EASE } from '@/lib/motion'

type ToastOptions = { icon?: LucideIcon; undo?: () => void }
type ToastFn = (message: string, options?: ToastOptions) => void

const ToastContext = createContext<ToastFn>(() => {})

// oxlint-disable-next-line react/only-export-components
export const useToast = () => useContext(ToastContext)

/** One toast at a time, bottom centre: springs in, leaves after 2.6 s (5 s when it offers Undo). */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const el = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<{ message: string; icon: LucideIcon; undo?: () => void } | null>(null)

  const show = useCallback<ToastFn>((message, { icon = Check, undo } = {}) => {
    setState({ message, icon, undo })
    const node = el.current
    if (!node) return
    gsap.killTweensOf(node)
    gsap
      .timeline()
      .fromTo(node, { opacity: 0, y: 18, scale: 0.96, visibility: 'visible' }, { opacity: 1, y: 0, scale: 1, duration: dur(0.45), ease: EASE.toast })
      .to(node, { opacity: 0, y: 10, duration: dur(0.3), ease: EASE.in, onComplete: () => gsap.set(node, { visibility: 'hidden' }) }, undo ? '+=5' : '+=2.6')
  }, [])

  const Icon = state?.icon ?? Check
  return (
    <ToastContext.Provider value={show}>
      {children}
      <div
        ref={el}
        role="status"
        aria-live="polite"
        className="pointer-events-none invisible fixed inset-x-0 bottom-[calc(92px+env(safe-area-inset-bottom))] z-[95] mx-auto flex w-fit max-w-[calc(100vw-24px)] items-center gap-2.5 rounded-full bg-ink py-2.5 pr-3 pl-3.5 text-md font-semibold text-ink-foreground shadow-pop lg:bottom-6"
      >
        <Icon className="size-[18px] flex-none" aria-hidden />
        <span className="truncate">{state?.message}</span>
        {state?.undo && (
          <button
            type="button"
            className="pointer-events-auto rounded-full bg-tomato px-3 py-1.5 font-bold text-tomato-foreground"
            onClick={() => {
              state.undo?.()
              gsap.to(el.current, { opacity: 0, y: 10, duration: dur(0.25), onComplete: () => gsap.set(el.current, { visibility: 'hidden' }) })
            }}
          >
            Undo
          </button>
        )}
      </div>
    </ToastContext.Provider>
  )
}
