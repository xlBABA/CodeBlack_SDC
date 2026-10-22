import { MoveRight, TrendingDown, TrendingUp } from 'lucide-react'
import type { TrendDirection } from '@/mocks/types'
import { cn } from '@/lib/utils'

const META = {
  rising: { Icon: TrendingUp, label: 'Rising demand', cls: 'text-good' },
  stable: { Icon: MoveRight, label: 'Stable demand', cls: 'text-muted-foreground' },
  declining: { Icon: TrendingDown, label: 'Declining demand', cls: 'text-tomato' },
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
