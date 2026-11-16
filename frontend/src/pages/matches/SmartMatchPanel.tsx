import { Check, RefreshCw, Send, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { getErrorMessage } from '@/api/client'
import { useInvitePlayer, useSmartMatch, type FeatureBreakdown, type PickupMatch } from '@/api/sporthub'
import { EmptyState } from '@/components/shared/EmptyState'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from '@/lib/toast'

const FEATURES: { key: keyof FeatureBreakdown; label: string }[] = [
  { key: 'sport_match', label: 'Sport match' },
  { key: 'skill_level_proximity', label: 'Skill level' },
  { key: 'area_match', label: 'Area' },
  { key: 'availability_overlap_ratio', label: 'Availability' },
  { key: 'on_time_attendance_rate', label: 'Attendance' },
  { key: 'avg_rating', label: 'Peer rating' },
]

function pctVariant(pct: number) {
  return pct >= 75 ? 'success' : pct >= 50 ? 'warning' : 'secondary'
}

export function SmartMatchPanel({ match, canInvite }: { match: PickupMatch; canInvite: boolean }) {
  const query = useSmartMatch(match.id)
  const invite = useInvitePlayer()
  const [invited, setInvited] = useState<Set<number>>(new Set())
  const [pending, setPending] = useState<number | null>(null)

  function onInvite(userId: number, name: string) {
    setPending(userId)
    invite.mutate(
      { match, userId },
      {
        onSuccess: () => {
          setInvited((prev) => new Set(prev).add(userId))
          toast.success('Invitation sent', `${name} got a message with the match link.`)
        },
        onSettled: () => setPending(null),
      },
    )
  }

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="size-5 text-highlight" aria-hidden />
            AI Smart Match
          </CardTitle>
          <CardDescription>Players who fit this game best. Advisory only.</CardDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={() => void query.refetch()} disabled={query.isFetching} aria-label="Refresh recommendations">
          <RefreshCw className={query.isFetching ? 'animate-spin' : undefined} aria-hidden />
        </Button>
      </CardHeader>
      <CardContent>
        {query.isPending ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        ) : query.isError ? (
          <EmptyState icon={Sparkles} title="No recommendations" description={getErrorMessage(query.error)} />
        ) : query.data.length === 0 ? (
          <EmptyState icon={Sparkles} title="No candidates yet" description="Nobody with a matching sport profile is free to invite." />
        ) : (
          <ul className="divide-y">
            {query.data.map((rec) => {
              const pct = Math.round(rec.suitability_pct)
              const done = invited.has(rec.user.id)
              return (
                <li key={rec.user.id} className="flex items-center gap-3 py-3">
                  <UserAvatar name={rec.user.full_name} src={rec.user.avatar_url} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{rec.user.full_name}</p>
                    <div className="group relative inline-block">
                      <button
                        type="button"
                        className="rounded text-xs text-muted-foreground underline decoration-dotted underline-offset-2"
                        aria-label={`Why ${rec.user.full_name} matches`}
                      >
                        Why this match?
                      </button>
                      <div
                        role="tooltip"
                        className="invisible absolute left-0 top-full z-20 mt-1 w-56 rounded-lg border bg-popover p-3 text-xs opacity-0 shadow-xl transition-opacity group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100"
                      >
                        {FEATURES.map(({ key, label }) => (
                          <div key={key} className="mb-1.5 last:mb-0">
                            <div className="flex justify-between">
                              <span>{label}</span>
                              <span className="tabular-nums">{Math.round(rec.breakdown[key] * 100)}%</span>
                            </div>
                            <div className="mt-0.5 h-1 overflow-hidden rounded-full bg-muted">
                              <div className="h-full bg-primary" style={{ width: `${Math.round(rec.breakdown[key] * 100)}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <Badge variant={pctVariant(pct)} className="tabular-nums">
                    {pct}%
                  </Badge>
                  {canInvite && (
                    <Button
                      size="sm"
                      variant={done ? 'secondary' : 'outline'}
                      disabled={done || (invite.isPending && pending === rec.user.id)}
                      loading={invite.isPending && pending === rec.user.id}
                      onClick={() => onInvite(rec.user.id, rec.user.full_name)}
                    >
                      {done ? <Check aria-hidden /> : <Send aria-hidden />}
                      {done ? 'Invited' : 'Invite'}
                    </Button>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}