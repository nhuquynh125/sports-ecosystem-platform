import { CalendarDays, MapPin } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { PickupMatch } from '@/api/sporthub'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { cn, formatDate } from '@/lib/utils'

export const LEVEL_VARIANT = { beginner: 'secondary', intermediate: 'success', advanced: 'warning', pro: 'highlight' } as const

export function formatWhen(date: string, time: string) {
  return `${date ? formatDate(`${date}T00:00:00`) : '—'}${time ? ` · ${time}` : ''}`
}

export function MatchCard({ match, footer }: { match: PickupMatch; footer?: ReactNode }) {
  const spotsLeft = Math.max(match.max_players - match.current_players, 0)
  const pct = Math.min(100, Math.round((match.current_players / Math.max(match.max_players, 1)) * 100))
  return (
    <Card className="flex h-full flex-col transition-shadow hover:shadow-lg">
      <Link to={`/matches/${match.id}`} className="block flex-1 space-y-3 rounded-lg p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold leading-tight">{match.title ?? `${match.sport_name} pickup`}</h3>
          <Badge variant={match.status === 'open' ? 'success' : 'secondary'} className="shrink-0 capitalize">
            {match.status}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline">{match.sport_name}</Badge>
          <Badge variant={LEVEL_VARIANT[match.skill_level] ?? 'secondary'} className="capitalize">
            {match.skill_level}
          </Badge>
        </div>
        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <CalendarDays className="size-4" aria-hidden />
          {formatWhen(match.match_date, match.time_slot)}
        </p>
        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <MapPin className="size-4" aria-hidden />
          {match.area}
        </p>
        <div>
          <div className="mb-1 flex justify-between text-xs">
            <span className="font-medium">
              {match.current_players} / {match.max_players} players
            </span>
            <span className={cn(spotsLeft === 0 ? 'text-destructive' : 'text-muted-foreground')}>
              {spotsLeft === 0 ? 'Full' : `${spotsLeft} spot${spotsLeft === 1 ? '' : 's'} left`}
            </span>
          </div>
          <div
            className="h-1.5 overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={match.max_players}
            aria-valuenow={match.current_players}
          >
            <div className={cn('h-full rounded-full', spotsLeft === 0 ? 'bg-destructive' : 'bg-primary')} style={{ width: `${pct}%` }} />
          </div>
        </div>
      </Link>
      {footer && <div className="border-t p-3">{footer}</div>}
    </Card>
  )
}