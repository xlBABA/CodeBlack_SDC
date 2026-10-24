import { useRef } from 'react'
import type { LucideIcon } from 'lucide-react'
import { useLift } from '@/hooks/use-hover-fx'
import { cn, mergeRefs } from '@/lib/utils'

type CardProps = React.ComponentProps<'section'> & {
  /** rise 4px under the pointer */
  lift?: boolean
  /** take part in the page entrance (default) */
  enter?: boolean
  /** glass (default) or an opaque variant */
  variant?: 'glass' | 'solid' | 'deep'
}

const VARIANT = {
  glass: 'glass',
  solid: 'border border-line bg-raised shadow-card',
  // deep primary hero card with a fine grid texture (Halden idea)
  // the accent mixed toward the deep backdrop keeps it dark (and white text legible) in both themes
  deep: 'grid-tex bg-[linear-gradient(150deg,color-mix(in_srgb,var(--primary)_var(--deep-mix),var(--deep-b)),color-mix(in_srgb,var(--primary)_18%,color-mix(in_srgb,var(--deep-b)_55%,#000)))] text-on-deep shadow-pop [&_.text-muted-foreground]:text-on-deep/70',
}

export function Card({ lift = false, enter = true, variant = 'glass', className, ref, ...props }: CardProps) {
  const own = useRef<HTMLElement>(null)
  useLift(own, lift)
  return (
    <section
      ref={mergeRefs(own, ref)}
      data-slot="card"
      data-enter={enter ? 'card' : undefined}
      className={cn('relative min-w-0 rounded-card p-4 sm:p-5', VARIANT[variant], className)}
      {...props}
    />
  )
}

type CardHeaderProps = {
  title: React.ReactNode
  icon?: LucideIcon
  /** id for aria-labelledby on the parent card */
  id?: string
  subtitle?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export function CardHeader({ title, icon: Icon, id, subtitle, action, className }: CardHeaderProps) {
  return (
    <header className={cn('mb-4 flex flex-wrap items-start justify-between gap-x-3 gap-y-2', className)}>
      <div className="flex min-w-0 items-center gap-2.5">
        {Icon && (
          <span className="grid size-9 flex-none place-items-center rounded-full bg-well" aria-hidden>
            <Icon className="size-[17px]" />
          </span>
        )}
        <div className="min-w-0">
          <h2 id={id} className="truncate text-xl font-bold tracking-[-0.01em]">
            {title}
          </h2>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      </div>
      {action}
    </header>
  )
}
