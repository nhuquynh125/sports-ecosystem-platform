import { Badge } from '@/components/ui/badge'
import { roleLabel } from '@/config/roles'

const VARIANTS = {
  admin: 'highlight',
  player: 'success',
  venue_owner: 'secondary',
  organizer: 'warning',
  coach: 'outline',
} as const

export function RoleBadge({ role }: { role: string }) {
  const variant = VARIANTS[role as keyof typeof VARIANTS] ?? 'secondary'
  return <Badge variant={variant}>{roleLabel(role)}</Badge>
}
