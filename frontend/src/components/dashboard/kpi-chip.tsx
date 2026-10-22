import type { LucideIcon } from 'lucide-react'
import { CountUp } from '@/components/page/count-up'
import type { CountFormat } from '@/lib/motion'

/** Header stat: round icon, a counting number and a label (Rapport idea). */
export function KpiChip({ icon: Icon, value, format = 'int', label, extra }: { icon: LucideIcon; value: number; format?: CountFormat; label: string; extra?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-12 flex-none place-items-center rounded-full border border-rim bg-glass-2 shadow-card backdrop-blur-md dark:border-line" aria-hidden>
        <Icon className="size-[19px]" />
      </span>
      <span className="grid leading-tight">
        <span className="flex items-center gap-2">
          <CountUp value={value} format={format} className="text-2xl font-extrabold tracking-[-0.03em]" />
          {extra}
        </span>
        <small className="text-sm text-muted-foreground">{label}</small>
      </span>
    </div>
  )
}
