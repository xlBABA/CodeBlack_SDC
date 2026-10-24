import { cn } from '@/lib/utils'

const CC_BY_4 = 'https://creativecommons.org/licenses/by/4.0/'

/** Credit required by O*NET's CC BY 4.0 licence for the role and skill data (roles.json, skills.json). */
export function OnetAttribution({ className, linkClassName }: { className?: string; linkClassName?: string }) {
  return (
    <p className={cn('text-xs text-muted-foreground', className)}>
      Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (
      <a href={CC_BY_4} target="_blank" rel="noreferrer" className={cn('font-semibold underline underline-offset-2', linkClassName)}>
        {CC_BY_4}
      </a>
      ).
    </p>
  )
}
