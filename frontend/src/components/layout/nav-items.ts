import { BookOpenText, BriefcaseBusiness, LayoutGrid, UserRoundPen, type LucideIcon } from 'lucide-react'

export type NavItem = {
  to: string
  label: string
  icon: LucideIcon
  /** pathname prefix that marks this item active */
  match: string
}

export const NAV: NavItem[] = [
  { to: '/dashboard', label: 'Overview', icon: LayoutGrid, match: '/dashboard' },
  { to: '/roles/data_analyst', label: 'Roles', icon: BriefcaseBusiness, match: '/roles' },
  { to: '/start', label: 'Profile', icon: UserRoundPen, match: '/start' },
  { to: '/methodology', label: 'Method', icon: BookOpenText, match: '/methodology' },
]

export const activeIndex = (pathname: string) => NAV.findIndex((n) => pathname === n.match || pathname.startsWith(`${n.match}/`))
