import {
  Building2,
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  Radar,
  ShieldCheck,
  Trophy,
  UserCircle,
  Users,
  type LucideIcon,
  ListChecks,
  Swords,
} from 'lucide-react'
import type { Role } from '@/config/roles'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** Visible only to users holding at least one of these roles. Omit = every signed-in user. */
  roles?: Role[]
  /** Module not built yet: shown disabled. */
  soon?: boolean
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: 'General',
    items: [
      { label: 'Dashboard', to: '/', icon: LayoutDashboard },
      { label: 'My profile', to: '/profile', icon: UserCircle },
    ],
  },
  {
    label: 'Play',
    items: [
      { label: 'Find a court', to: '/venues', icon: CalendarDays },
      { label: 'Teams', to: '/teams', icon: Users },
      { label: 'Tournaments', to: '/tournaments', icon: Trophy },
	{ label: 'Matches', to: '/matches', icon: Swords },
	{ label: 'My matches', to: '/matches/me', icon: ListChecks },
    ],
  },
  {
    label: 'Manage',
    items: [
      { label: 'My venues', to: '/owner/venues', icon: Building2, roles: ['venue_owner', 'admin'] },
      { label: 'My tournaments', to: '/organizer/tournaments', icon: ClipboardList, roles: ['organizer', 'admin'] },
      { label: 'Scouting', to: '/scouting', icon: Radar, roles: ['coach', 'admin'], soon: true },
    ],
  },
  {
    label: 'Administration',
    items: [{ label: 'Users', to: '/admin/users', icon: ShieldCheck, roles: ['admin'] }],
  },
]

export function visibleGroups(userRoles: readonly string[]): NavGroup[] {
  return NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles || item.roles.some((role) => userRoles.includes(role))),
  })).filter((group) => group.items.length > 0)
}
