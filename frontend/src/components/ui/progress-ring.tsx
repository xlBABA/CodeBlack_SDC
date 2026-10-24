import { CountUp } from '@/components/page/count-up'
import { cn } from '@/lib/utils'

type ProgressRingProps = {
  /** 0–100, from data */
  value: number
  size?: number
  stroke?: number
  /** text under the number, e.g. "alignment estimate" */
  caption?: string
  tone?: string
  className?: string
}

/** Circular gauge whose arc draws in on entrance while the number counts up. */
export function ProgressRing({ value, size = 104, stroke = 9, caption, tone = 'var(--coral)', className }: ProgressRingProps) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const p = Math.max(0, Math.min(100, value)) / 100
  return (
    <div className={cn('relative grid flex-none place-items-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--well)" strokeWidth={stroke} />
        <circle
          data-enter="ring"
          data-ring-c={c}
          data-ring-p={p}
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={tone}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - p)}
        />
      </svg>
      <span className="absolute grid place-items-center text-center leading-none">
        <CountUp value={value} className="text-[1.7rem] font-extrabold tracking-[-0.03em]" />
        {caption && <small className="mt-1 max-w-[9ch] text-2xs leading-tight font-semibold text-muted-foreground">{caption}</small>}
      </span>
    </div>
  )
}
