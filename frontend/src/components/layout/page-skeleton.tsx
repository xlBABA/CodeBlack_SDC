import { Skeleton } from '@/components/ui/skeleton'

/** Loading state in the shape of a page: header, a row of stats, two cards. */
export function PageSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <div role="status" aria-live="polite" aria-label="Loading" className="pb-10">
      <Skeleton className="mb-3 h-4 w-40" />
      <Skeleton className="mb-3 h-10 w-[min(420px,80%)]" />
      <Skeleton className="mb-6 h-4 w-[min(560px,90%)]" />
      <div className="mb-4 grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-20 rounded-tile" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: cards }, (_, i) => (
          <div key={i} className="glass rounded-card p-5">
            <div className="mb-4 flex items-center gap-2.5">
              <Skeleton className="size-8 rounded-[10px]" />
              <Skeleton className="h-5 w-40" />
            </div>
            <Skeleton className="mb-2 h-3.5 w-full" />
            <Skeleton className="mb-2 h-3.5 w-[85%]" />
            <Skeleton className="h-3.5 w-[60%]" />
          </div>
        ))}
      </div>
    </div>
  )
}
