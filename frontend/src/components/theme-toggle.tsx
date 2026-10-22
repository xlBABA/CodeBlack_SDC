import { useLayoutEffect, useRef } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/use-theme'
import { gsap } from '@/lib/gsap'
import { prefersReducedMotion } from '@/lib/motion'
import { cn } from '@/lib/utils'

const OPTIONS = [
  { value: 'light', label: 'Light theme', Icon: Sun },
  { value: 'dark', label: 'Dark theme', Icon: Moon },
] as const

/**
 * Two-option switch with a knob that springs to the chosen side (Mender idea: knob travels
 * 100% of its size with back.out(1.6) over .45s). The new theme itself is revealed by a
 * circle growing out of the clicked option (see lib/theme.ts).
 */
export function ThemeToggle({
  orientation = 'horizontal',
  onDark = false,
  className,
}: {
  orientation?: 'horizontal' | 'vertical'
  /** sitting on a dark surface (the dock): use a light knob so it stays visible */
  onDark?: boolean
  className?: string
}) {
  const { theme, setTheme } = useTheme()
  const knob = useRef<HTMLSpanElement>(null)
  const first = useRef(true)
  const index = theme === 'dark' ? 1 : 0

  useLayoutEffect(() => {
    const prop = orientation === 'vertical' ? 'yPercent' : 'xPercent'
    const instant = first.current || prefersReducedMotion()
    first.current = false
    gsap.to(knob.current, { [prop]: index * 100, duration: instant ? 0 : 0.45, ease: 'back.out(1.6)' })
  }, [index, orientation])

  return (
    <div
      role="group"
      aria-label="Colour theme"
      className={cn(
        'relative inline-grid rounded-full border border-line bg-glass-2 p-1',
        orientation === 'vertical' ? 'grid-rows-2' : 'grid-cols-2',
        className,
      )}
    >
      <span ref={knob} aria-hidden className={cn('absolute top-1 left-1 size-9 rounded-full shadow-[0_6px_14px_-6px_#0006]', onDark ? 'bg-[#f6faf8]' : 'bg-ink')} />
      {OPTIONS.map(({ value, label, Icon }, i) => (
        <button
          key={value}
          type="button"
          aria-label={label}
          aria-pressed={index === i}
          onClick={(e) => setTheme(value, e.currentTarget)}
          className={cn(
            'relative grid size-9 place-items-center rounded-full transition-colors duration-200',
            index === i ? (onDark ? 'text-[#16201c]' : 'text-ink-foreground') : onDark ? 'text-white/60 hover:text-white' : 'text-muted-foreground hover:text-foreground',
          )}
        >
          <Icon className="size-[17px]" aria-hidden />
        </button>
      ))}
    </div>
  )
}
