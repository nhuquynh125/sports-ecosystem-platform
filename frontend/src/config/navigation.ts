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
      { label: 'Find a court', to: '/courts', icon: CalendarDays, soon: true },
      { label: 'Teams', to: '/teams', icon: Users, soon: true },
      { label: 'Tournaments', to: '/tournaments', icon: Trophy, soon: true },
    ],
  },
  {
    label: 'Manage',
    items: [
      { label: 'My venues', to: '/owner/venues', icon: Building2, roles: ['venue_owner', 'admin'], soon: true },
      { label: 'My tournaments', to: '/organizer/tournaments', icon: ClipboardList, roles: ['organizer', 'admin'], soon: true },
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
