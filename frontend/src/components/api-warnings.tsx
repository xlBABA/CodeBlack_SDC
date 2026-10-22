import { Info } from 'lucide-react'

/** The envelope's `warnings`, shown as they are: they explain fixture/cached data and limits. */
export function ApiWarnings({ items, className }: { items: string[]; className?: string }) {
  if (!items.length) return null
  return (
    <details className={className}>
      <summary className="flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground">
        <Info className="size-3.5" aria-hidden />
        {items.length} note{items.length > 1 ? 's' : ''} about this data
      </summary>
      <ul className="mt-2 grid gap-1.5">
        {items.map((w) => (
          <li key={w} className="rounded-lg bg-well px-3 py-2 text-xs leading-relaxed text-muted-foreground">
            {w}
          </li>
        ))}
      </ul>
    </details>
  )
}
