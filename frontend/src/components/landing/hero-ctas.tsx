import { ArrowRight, Sparkles } from 'lucide-react'
import { Link } from 'react-router'
import { useCurtainLink } from '@/components/curtain'
import { Button } from '@/components/ui/button'
import { CURTAIN_LINES } from '@/content/landing'
import { cn } from '@/lib/utils'

const DEMO_ENTRY = '/dashboard?demo=1'

/** The two landing calls to action; both travel into the app through the curtain. */
export function HeroCtas({ className, size = 'lg', onDark = false }: { className?: string; size?: 'lg' | 'default'; onDark?: boolean }) {
  const toProfile = useCurtainLink('/start', CURTAIN_LINES.profile)
  const toDemo = useCurtainLink(DEMO_ENTRY, CURTAIN_LINES.demo)
  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      <Button asChild size={size} magnetic className={cn(onDark && 'bg-on-deep text-deep-ink hover:bg-white')}>
        <Link to="/start" onClick={toProfile}>
          Map my future
          <ArrowRight />
        </Link>
      </Button>
      <Button asChild size={size} variant="secondary" className={cn(onDark && 'border-white/30 bg-white/10 text-on-deep hover:bg-white/20')}>
        <Link to={DEMO_ENTRY} onClick={toDemo}>
          <Sparkles />
          Try a demo student
        </Link>
      </Button>
    </div>
  )
}
