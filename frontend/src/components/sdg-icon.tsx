import type { DomainSdg } from '@/content/landing'
import { cn } from '@/lib/utils'

/** The official UN icon for a goal, unmodified (public/sdg). */
export function SdgIcon({ sdg, className }: { sdg: DomainSdg; className?: string }) {
  return (
    <img
      src={`${import.meta.env.BASE_URL}sdg/E-WEB-Goal-${String(sdg.goal).padStart(2, '0')}.png`}
      alt={`SDG ${sdg.goal}: ${sdg.name}`}
      loading="lazy"
      className={cn('flex-none', className)}
    />
  )
}
