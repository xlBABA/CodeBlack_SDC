import { CircleHelp, MoveRight, TrendingDown, TrendingUp } from 'lucide-react'
import type { TrendDirection } from '@/types/api'
import { cn } from '@/lib/utils'

const META = {
  rising: { Icon: TrendingUp, label: 'Rising', cls: 'text-good' },
  stable: { Icon: MoveRight, label: 'Stable', cls: 'text-muted-foreground' },
  falling: { Icon: TrendingDown, label: 'Falling', cls: 'text-tomato' },
  unknown: { Icon: CircleHelp, label: 'Direction unknown', cls: 'text-muted-foreground' },
} satisfies Record<TrendDirection, unknown>

export function TrendArrow({ direction, withLabel = false, className }: { direction: TrendDirection; withLabel?: boolean; className?: string }) {
  const { Icon, label, cls } = META[direction]
  return (
    <span className={cn('inline-flex items-center gap-1 text-sm font-bold', cls, className)} title={label}>
      <Icon className="size-4" aria-hidden />
      {withLabel ? label : <span className="sr-only">{label}</span>}
    </span>
  )
}
