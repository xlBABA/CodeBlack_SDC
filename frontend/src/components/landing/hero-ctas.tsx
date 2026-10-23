import { ArrowRight, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { useCurtainLink } from '@/components/curtain'
import { Button } from '@/components/ui/button'
import { CURTAIN_LINES } from '@/content/landing'
import { cn } from '@/lib/utils'

export const DEMO_ENTRY = '/dashboard?demo=1'

/** The two landing calls to action; both travel into the app through the curtain. */
export function HeroCtas({ className, size = 'lg', onDark = false }: { className?: string; size?: 'lg' | 'default'; onDark?: boolean }) {
  const toDemo = useCurtainLink(DEMO_ENTRY, CURTAIN_LINES.demo)
  const toProfile = useCurtainLink('/start', CURTAIN_LINES.profile)
  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      <Button asChild size={size} magnetic className={cn(onDark && 'bg-on-deep text-deep-ink hover:bg-white')}>
        <Link to={DEMO_ENTRY} onClick={toDemo}>
          Try with a demo student
          <ArrowRight />
        </Link>
      </Button>
      <Button asChild size={size} variant="secondary" className={cn(onDark && 'border-white/30 bg-white/10 text-on-deep hover:bg-white/20')}>
        <Link to="/start" onClick={toProfile}>
          <UserRoundPen />
          Build my profile
        </Link>
      </Button>
    </div>
  )
}
