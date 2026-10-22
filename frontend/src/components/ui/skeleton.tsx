import { cn } from '@/lib/utils'

/** Placeholder block with a shimmer sweep (static under reduced motion). */
export function Skeleton({ className, ...props }: React.ComponentProps<'div'>) {
  return <div data-slot="skeleton" aria-hidden className={cn('skeleton h-4', className)} {...props} />
}
