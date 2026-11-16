import { ArrowLeft, CalendarDays, MapPin, Users } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '@/api/client'
import { useJoinMatch, useLeaveMatch, useMatch } from '@/api/sporthub'
import { EmptyState } from '@/components/shared/EmptyState'
import { PageHeader } from '@/components/shared/PageHeader'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'
import { toast } from '@/lib/toast'
import { LEVEL_VARIANT, formatWhen } from './MatchCard'
import { MatchChat } from './MatchChat'
import { SmartMatchPanel } from './SmartMatchPanel'

export function MatchDetailPage() {
  const { id } = useParams<{ id: string }>()
  const matchId = Number(id)
  const navigate = useNavigate()
  const { user, hasRole } = useAuth()
  const query = useMatch(matchId)
  const join = useJoinMatch(matchId)
  const leave = useLeaveMatch(matchId)

  if (query.isPending) return <Skeleton className="h-96" />
  if (query.isError || !query.data) {
    return (
      <EmptyState
        icon={Users}
        title="Match not found"
        description={query.isError ? getErrorMessage(query.error) : 'It may have been removed.'}
        action={<Button asChild><Link to="/matches">Back to matches</Link></Button>}
      />
    )
  }

  const match = query.data
  const meId = user?.id ?? 0
  const isHost = match.host_id === meId
  const joined = isHost || (match.players?.some((p) => p.user.id === meId) ?? false)
  const spotsLeft = Math.max(match.max_players - match.current_players, 0)
  const canJoin = !joined && match.status === 'open' && spotsLeft > 0
  const canLeave = joined && !isHost && match.status !== 'completed' && match.status !== 'cancelled'
  const roster = match.players ?? []

  return (
    <>
      <div className="mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft aria-hidden />
          Back
        </Button>
      </div>

      <PageHeader
        title={match.title ?? `${match.sport_name} pickup`}
        description={match.host ? `Hosted by ${match.host.full_name}` : undefined}
        actions={
          <>
            {canJoin && (
              <Button
                loading={join.isPending}
                onClick={() => join.mutate(undefined, { onSuccess: () => toast.success('You joined the match') })}
              >
                Join match
              </Button>
            )}
            {canLeave && (
              <Button
                variant="outline"
                loading={leave.isPending}
                onClick={() => leave.mutate(undefined, { onSuccess: () => toast.info('You left the match') })}
              >
                Leave
              </Button>
            )}
            {isHost && <Badge variant="highlight">You are the host</Badge>}
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="space-y-6">
          <Card>
            <CardContent className="space-y-3 pt-5 text-sm">
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="outline">{match.sport_name}</Badge>
                <Badge variant={LEVEL_VARIANT[match.skill_level] ?? 'secondary'} className="capitalize">
                  {match.skill_level}
                </Badge>
                <Badge variant={match.status === 'open' ? 'success' : 'secondary'} className="capitalize">
                  {match.status}
                </Badge>
              </div>
              <p className="flex items-center gap-2">
                <CalendarDays className="size-4 text-muted-foreground" aria-hidden />
                {formatWhen(match.match_date, match.time_slot)}
              </p>
              <p className="flex items-center gap-2">
                <MapPin className="size-4 text-muted-foreground" aria-hidden />
                {match.area}
              </p>
              <p className="flex items-center gap-2">
                <Users className="size-4 text-muted-foreground" aria-hidden />
                {match.current_players} / {match.max_players} players
                {spotsLeft > 0 && match.status === 'open' && ` · ${spotsLeft} open`}
              </p>
              {match.description && <p className="whitespace-pre-wrap border-t pt-3 text-muted-foreground">{match.description}</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Players ({match.current_players})</CardTitle>
            </CardHeader>
            <CardContent>
              {match.players === null ? (
                <p className="text-sm text-muted-foreground">
                  {match.host ? `${match.host.full_name} and ${Math.max(match.current_players - 1, 0)} other(s)` : `${match.current_players} joined`}
                </p>
              ) : roster.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nobody has joined yet.</p>
              ) : (
                <ul className="grid gap-3 sm:grid-cols-2">
                  {roster.map((p) => (
                    <li key={p.user.id} className="flex items-center gap-3">
                      <UserAvatar name={p.user.full_name} src={p.user.avatar_url} />
                      <span className="min-w-0 flex-1 truncate text-sm font-medium">{p.user.full_name}</span>
                      {p.user.id === match.host_id && <Badge variant="highlight">Host</Badge>}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {joined ? (
            <MatchChat roomId={match.chat_room_id} meId={meId} />
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">Join the match to open the team chat.</CardContent>
            </Card>
          )}
        </div>

        <div>
          <SmartMatchPanel match={match} canInvite={isHost || hasRole('admin')} />
        </div>
      </div>
    </>
  )
}
