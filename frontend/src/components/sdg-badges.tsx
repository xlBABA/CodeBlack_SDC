import { cn } from '@/lib/utils'

const SDG_NAMES: Record<number, string> = {
  1: 'No poverty', 2: 'Zero hunger', 3: 'Good health and well-being', 4: 'Quality education', 5: 'Gender equality',
  6: 'Clean water and sanitation', 7: 'Affordable and clean energy', 8: 'Decent work and economic growth',
  9: 'Industry, innovation and infrastructure', 10: 'Reduced inequalities', 11: 'Sustainable cities and communities',
  12: 'Responsible consumption and production', 13: 'Climate action', 14: 'Life below water', 15: 'Life on land',
  16: 'Peace, justice and strong institutions', 17: 'Partnerships for the goals',
}

/** Small numbered dots in the official SDG colours, with the goal name for screen readers and tooltips. */
export function SdgBadges({ goals, className, size = 'md' }: { goals: number[]; className?: string; size?: 'sm' | 'md' }) {
  return (
    <ul className={cn('flex flex-wrap gap-1', className)} aria-label="Linked UN Sustainable Development Goals">
      {goals.map((g) => (
        <li
          key={g}
          data-enter="pop"
          title={`SDG ${g}: ${SDG_NAMES[g]}`}
          className={cn('grid place-items-center rounded-full font-extrabold text-white shadow-[inset_0_0_0_1.5px_#ffffff40]', size === 'sm' ? 'size-6 text-2xs' : 'size-7 text-xs')}
          style={{ background: `var(--sdg-${g})` }}
        >
          <span aria-hidden>{g}</span>
          <span className="sr-only">
            SDG {g}: {SDG_NAMES[g]}
          </span>
        </li>
      ))}
    </ul>
  )
}
