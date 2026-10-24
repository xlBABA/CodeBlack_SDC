import { Check, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

export const field = 'h-11 w-full rounded-ctl border border-line-2 bg-raised px-4 text-base outline-none transition-colors focus-visible:border-primary dark:border-line'
export const labelCls = 'mb-1.5 block text-sm font-bold'

export function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors',
        active ? 'border-transparent bg-primary text-primary-foreground' : 'border-line-2 hover:bg-well',
      )}
    >
      {active ? <Check className="size-3.5" aria-hidden /> : <Plus className="size-3.5" aria-hidden />}
      {children}
    </button>
  )
}
