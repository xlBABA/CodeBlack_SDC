import { House, SwatchBook, UserRoundPen } from 'lucide-react'
import { Link } from 'react-router'
import { AccentPicker } from '@/components/accent-picker'
import { ThemeToggle } from '@/components/theme-toggle'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

const ACTIONS = [
  { to: '/', label: 'Landing page', Icon: House },
  { to: '/start', label: 'Build my profile', Icon: UserRoundPen },
  { to: '/design', label: 'Design system', Icon: SwatchBook },
]

/**
 * Floating pill dock on the left (Rapport idea) with quick actions, the accent picker
 * (Halden idea) and the sliding theme switch (Mender idea). Desktop only; phones get the
 * bottom tab bar instead.
 */
export function Dock() {
  return (
    <aside
      data-shell="dock"
      aria-label="Quick actions"
      className="fixed top-0 bottom-0 left-5 z-30 my-auto hidden h-fit flex-col items-center gap-1 rounded-full bg-ink p-2 text-ink-foreground shadow-[0_20px_40px_-18px_#00000073] lg:flex dark:border dark:border-line dark:bg-glass-2 dark:text-foreground dark:backdrop-blur-xl"
    >
      {ACTIONS.map(({ to, label, Icon }) => (
        <Tooltip key={to}>
          <TooltipTrigger asChild>
            <Link to={to} aria-label={label} data-dock-item className="grid size-11 place-items-center rounded-full opacity-75 transition hover:bg-white/10 hover:opacity-100">
              <Icon className="size-[19px]" aria-hidden />
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">{label}</TooltipContent>
        </Tooltip>
      ))}
      <span aria-hidden className="my-1.5 h-px w-6 bg-current opacity-20" />
      <div data-dock-item>
        <AccentPicker side="right" />
      </div>
      <div data-dock-item className="mt-1 text-foreground">
        <ThemeToggle orientation="vertical" onDark className="border-white/10 bg-white/10" />
      </div>
    </aside>
  )
}
