export const ROLES = ['admin', 'player', 'venue_owner', 'organizer', 'coach'] as const
export type Role = (typeof ROLES)[number]

/** `admin` can never be self-assigned at registration (backend returns 403). */
export const SELF_ASSIGNABLE_ROLES = ['player', 'venue_owner', 'organizer', 'coach'] as const satisfies readonly Role[]

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Admin',
  player: 'Player',
  venue_owner: 'Venue owner',
  organizer: 'Organizer',
  coach: 'Coach',
}

export const ROLE_DESCRIPTIONS: Record<Role, string> = {
  admin: 'Operates the platform: users, roles, catalogue',
  player: 'Books courts, keeps a profile, joins teams and matches',
  venue_owner: 'Owns venues and courts, manages bookings',
  organizer: 'Creates tournaments and reviews registrations',
  coach: 'Uses statistics and AI scouting, manages watchlists',
}

export function roleLabel(role: string): string {
  return ROLE_LABELS[role as Role] ?? role
}
