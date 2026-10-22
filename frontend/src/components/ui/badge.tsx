import { cn } from '@/lib/utils'

export type Tone =
  | 'primary' | 'emerald' | 'tomato' | 'butter' | 'sky' | 'plum' | 'teal' | 'slate'
  | 'good' | 'warn' | 'bad' | 'faint' | 'ink'

type BadgeProps = React.ComponentProps<'span'> & {
  tone?: Tone
  /** leading colour dot */
  dot?: boolean
  /** breathing dot, for live status */
  live?: boolean
  /** let enterPage() pop it in */
  enter?: boolean
}

/** Tinted pill: background is the tone mixed at --soft, text is the tone mixed into --text. */
export function Badge({ tone = 'faint', dot = false, live = false, enter = true, className, children, style, ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      data-enter={enter ? 'pop' : undefined}
      className={cn('pill', className)}
      style={{ '--c': `var(--${tone})`, ...style } as React.CSSProperties}
      {...props}
    >
      {live ? <i className="live-dot" aria-hidden /> : dot ? <i aria-hidden /> : null}
      {children}
    </span>
  )
}
