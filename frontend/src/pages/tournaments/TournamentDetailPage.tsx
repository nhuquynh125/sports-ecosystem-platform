/**
 * Public tournament detail page — /tournaments/:id
 * Tabs: Overview · Fixtures & Results · Group Standings · Top Scorers
 */
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Medal, Trophy } from 'lucide-react'
import { getErrorMessage } from '@/api/client'
import {
  teamApi,
  tournamentApi,
  type MatchOut,
  type RegistrationOut,
  type StandingRow,
  type TopScorerRow,
  type TournamentDetailOut,
  type TournamentStatus,
} from '@/api/sportarena'
import { EmptyState } from '@/components/shared/EmptyState'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/hooks/use-auth'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<TournamentStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  registration: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  ongoing: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  completed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  cancelled: 'bg-destructive/10 text-destructive',
}

const REG_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  rejected: 'bg-destructive/10 text-destructive',
}

const MATCH_STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  cancelled: 'bg-destructive/10 text-destructive',
}

// ─── Register team modal ──────────────────────────────────────────────────────

function RegisterTeamModal({
  open,
  onOpenChange,
  tournamentId,
  tournament,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  tournamentId: number
  tournament: TournamentDetailOut
}) {
  const qc = useQueryClient()
  const { user } = useAuth()

  const myTeamsQuery = useQuery({
    queryKey: ['teams', 'mine'],
    queryFn: () => teamApi.mine(),
    enabled: open && !!user,
  })

  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)

  const mutation = useMutation({
    mutationFn: () => tournamentApi.registerTeam(tournamentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tournament', tournamentId] })
      onOpenChange(false)
    },
  })

  const captainedTeams = (myTeamsQuery.data ?? []).filter(
    (t) => t.captain.id === user?.id && t.sport.id === tournament.sport.id,
  )

  const alreadyRegistered = tournament.registrations.some((r) =>
    captainedTeams.some((t) => t.id === r.team.id),
  )

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Register a team"
      description={`Register one of your ${tournament.sport.name} teams for ${tournament.name}.`}
    >
      <div className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}
        {alreadyRegistered && (
          <FormAlert message="One of your teams is already registered for this tournament." />
        )}

        {myTeamsQuery.isPending ? (
          <Skeleton className="h-9 w-full" />
        ) : captainedTeams.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            You are not the captain of any {tournament.sport.name} team. Create a team first.
          </p>
        ) : (
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="reg-team">
              Select your team
            </label>
            <Select
              id="reg-team"
              value={selectedTeamId?.toString() ?? ''}
              onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : null)}
              className="w-full"
            >
              <option value="">Choose a team…</option>
              {captainedTeams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.member_count} members)
                </option>
              ))}
            </Select>
          </div>
        )}

        <ModalActions>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!selectedTeamId || alreadyRegistered || captainedTeams.length === 0}
          >
            Register
          </Button>
        </ModalActions>
      </div>
    </Modal>
  )
}

// ─── Registration row ─────────────────────────────────────────────────────────

function RegistrationRow({ reg }: { reg: RegistrationOut }) {
  return (
    <TableRow>
      <TableCell className="font-medium">{reg.team.name}</TableCell>
      <TableCell>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${REG_STATUS_COLORS[reg.registration_status] ?? ''}`}
        >
          {reg.registration_status}
        </span>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {new Date(reg.registered_at).toLocaleDateString()}
      </TableCell>
      {reg.rejection_reason && (
        <TableCell className="text-sm text-destructive">{reg.rejection_reason}</TableCell>
      )}
    </TableRow>
  )
}

// ─── Fixtures & Results Tab ───────────────────────────────────────────────────

function FixturesTab({ tournamentId }: { tournamentId: number }) {
  const matchesQuery = useQuery({
    queryKey: ['matches', tournamentId],
    queryFn: () => tournamentApi.listMatches(tournamentId),
  })

  const matches = matchesQuery.data ?? []

  // Collect unique group names for filter
  const groups = Array.from(
    new Map(
      matches
        .filter((m) => m.group_id !== null)
        .map((m) => [m.group_id, m.group_name ?? ''])
    ).entries(),
  )

  const [filterGroup, setFilterGroup] = useState<string>('all')

  const filtered =
    filterGroup === 'all'
      ? matches
      : matches.filter((m) => String(m.group_id) === filterGroup)

  if (matchesQuery.isPending) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (matches.length === 0) {
    return (
      <EmptyState
        icon={Trophy}
        title="No fixtures yet"
        description="Fixtures will appear here once the organizer generates the schedule."
      />
    )
  }

  return (
    <div className="space-y-4">
      {/* Group filter */}
      {groups.length > 0 && (
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium shrink-0">Filter by group:</label>
          <Select
            value={filterGroup}
            onChange={(e) => setFilterGroup(e.target.value)}
            className="max-w-xs"
          >
            <option value="all">All groups</option>
            {groups.map(([id, name]) => (
              <option key={id} value={String(id)}>
                {name}
              </option>
            ))}
          </Select>
        </div>
      )}

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Group</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Court</TableHead>
              <TableHead>Home</TableHead>
              <TableHead className="text-center">Score</TableHead>
              <TableHead>Away</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((m: MatchOut) => {
              const hasResult = m.home_score !== null && m.away_score !== null
              return (
                <TableRow key={m.id}>
                  <TableCell className="text-xs text-muted-foreground">
                    {m.group_name ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                    {m.match_date ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {m.time_slot ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {m.court_id ? `#${m.court_id}` : '—'}
                  </TableCell>
                  <TableCell className="font-medium text-sm">{m.home_team_name}</TableCell>
                  <TableCell className="text-center">
                    {hasResult ? (
                      <span className="font-bold tabular-nums">
                        {m.home_score} – {m.away_score}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">vs</span>
                    )}
                  </TableCell>
                  <TableCell className="font-medium text-sm">{m.away_team_name}</TableCell>
                  <TableCell>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${MATCH_STATUS_COLORS[m.status] ?? 'bg-muted text-muted-foreground'}`}
                    >
                      {m.status}
                    </span>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}

// ─── Group Standings Tab ──────────────────────────────────────────────────────

function StandingsTab({ tournamentId }: { tournamentId: number }) {
  const standingsQuery = useQuery({
    queryKey: ['standings', tournamentId],
    queryFn: () => tournamentApi.getStandings(tournamentId),
  })

  const rows = standingsQuery.data ?? []

  if (standingsQuery.isPending) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        icon={Trophy}
        title="No standings yet"
        description="Standings update automatically as match results are recorded."
      />
    )
  }

  // Group by group_id
  const grouped = new Map<number, { name: string; rows: StandingRow[] }>()
  for (const row of rows) {
    if (!grouped.has(row.group_id)) {
      grouped.set(row.group_id, { name: row.group_name, rows: [] })
    }
    grouped.get(row.group_id)!.rows.push(row)
  }

  return (
    <div className="space-y-6">
      {Array.from(grouped.entries()).map(([gId, { name, rows: gRows }]) => (
        <Card key={gId}>
          <div className="p-4 border-b font-semibold">{name}</div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8">#</TableHead>
                <TableHead>Team</TableHead>
                <TableHead className="text-center w-10" title="Played">P</TableHead>
                <TableHead className="text-center w-10" title="Won">W</TableHead>
                <TableHead className="text-center w-10" title="Drawn">D</TableHead>
                <TableHead className="text-center w-10" title="Lost">L</TableHead>
                <TableHead className="text-center w-12" title="Goals For">GF</TableHead>
                <TableHead className="text-center w-12" title="Goals Against">GA</TableHead>
                <TableHead className="text-center w-12" title="Goal Difference">GD</TableHead>
                <TableHead className="text-center w-12 font-bold" title="Points">Pts</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {gRows.map((row, idx) => (
                <TableRow key={row.team_id} className={idx === 0 ? 'bg-green-50/50 dark:bg-green-900/10' : ''}>
                  <TableCell className="text-muted-foreground text-xs">{idx + 1}</TableCell>
                  <TableCell className="font-medium">{row.team_name}</TableCell>
                  <TableCell className="text-center tabular-nums">{row.played}</TableCell>
                  <TableCell className="text-center tabular-nums text-green-700 dark:text-green-400">{row.won}</TableCell>
                  <TableCell className="text-center tabular-nums text-muted-foreground">{row.drawn}</TableCell>
                  <TableCell className="text-center tabular-nums text-destructive">{row.lost}</TableCell>
                  <TableCell className="text-center tabular-nums">{row.goals_for}</TableCell>
                  <TableCell className="text-center tabular-nums">{row.goals_against}</TableCell>
                  <TableCell className="text-center tabular-nums">
                    {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
                  </TableCell>
                  <TableCell className="text-center tabular-nums font-bold">{row.points}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      ))}
    </div>
  )
}

// ─── Top Scorers Tab ──────────────────────────────────────────────────────────

function TopScorersTab({ tournamentId }: { tournamentId: number }) {
  const scorersQuery = useQuery({
    queryKey: ['top-scorers', tournamentId],
    queryFn: () => tournamentApi.getTopScorers(tournamentId),
  })

  const scorers = scorersQuery.data ?? []

  if (scorersQuery.isPending) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (scorers.length === 0) {
    return (
      <EmptyState
        icon={Medal}
        title="No scorers yet"
        description="Goal scorers appear here once match results with events are recorded."
      />
    )
  }

  return (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">Rank</TableHead>
            <TableHead>Player</TableHead>
            <TableHead>Team</TableHead>
            <TableHead className="text-center w-16">Goals</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scorers.map((s: TopScorerRow, idx) => (
            <TableRow key={s.player_id}>
              <TableCell className="text-muted-foreground text-sm">
                {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
              </TableCell>
              <TableCell className="font-medium">{s.player_name}</TableCell>
              <TableCell>
                <Badge variant="secondary">{s.team_name}</Badge>
              </TableCell>
              <TableCell className="text-center">
                <span className="font-bold tabular-nums text-primary">{s.goals}</span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}

// ─── Overview Tab (existing content) ─────────────────────────────────────────

function OverviewTab({ t }: { t: TournamentDetailOut }) {
  return (
    <div className="space-y-4">
      {/* Dates */}
      {(t.start_date || t.end_date || t.registration_deadline) && (
        <Card className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {t.registration_deadline && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Registration deadline</p>
                <p className="font-medium">{t.registration_deadline}</p>
              </div>
            )}
            {t.start_date && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Start date</p>
                <p className="font-medium">{t.start_date}</p>
              </div>
            )}
            {t.end_date && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">End date</p>
                <p className="font-medium">{t.end_date}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Description */}
      {t.description && (
        <Card className="p-4">
          <p className="text-sm font-medium mb-2 uppercase tracking-wide text-muted-foreground">About</p>
          <p className="text-sm whitespace-pre-wrap">{t.description}</p>
        </Card>
      )}

      {/* Rules */}
      {t.rules && (
        <Card className="p-4">
          <p className="text-sm font-medium mb-2 uppercase tracking-wide text-muted-foreground">Rules</p>
          <p className="text-sm whitespace-pre-wrap">{t.rules}</p>
        </Card>
      )}

      {/* Registered teams */}
      <Card>
        <div className="p-4 border-b">
          <h2 className="font-semibold">Registered Teams ({t.registrations.length})</h2>
        </div>
        {t.registrations.length === 0 ? (
          <EmptyState icon={Trophy} title="No registrations yet" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Team</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {t.registrations.map((reg) => (
                <RegistrationRow key={reg.id} reg={reg} />
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function TournamentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const tournamentId = Number(id)
  const { user, hasRole } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  const tQuery = useQuery({
    queryKey: ['tournament', tournamentId],
    queryFn: () => tournamentApi.get(tournamentId),
    enabled: !isNaN(tournamentId),
  })

  const t = tQuery.data

  if (tQuery.isPending) {
    return (
      <>
        <Skeleton className="h-9 w-1/2 mb-2" />
        <Skeleton className="h-4 w-1/4 mb-8" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      </>
    )
  }

  if (tQuery.isError || !t) {
    return (
      <EmptyState icon={Trophy} title="Tournament not found" description="This tournament does not exist." />
    )
  }

  const canRegister = user && t.status === 'registration' && !hasRole('organizer', 'admin')

  return (
    <>
      <PageHeader
        title={t.name}
        description={[t.sport.name, t.location].filter(Boolean).join(' · ') || undefined}
        actions={
          canRegister ? (
            <Button onClick={() => setShowRegister(true)}>Register my team</Button>
          ) : undefined
        }
      />

      {/* Meta cards */}
      <div className="grid gap-4 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: 'Status',
            value: (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[t.status]}`}>
                {t.status}
              </span>
            ),
          },
          { label: 'Format', value: t.format.replace(/_/g, ' ') },
          { label: 'Teams', value: `${t.registered_team_count}${t.max_teams ? ` / ${t.max_teams}` : ''}` },
          { label: 'Prize pool', value: t.prize_pool ?? '—' },
        ].map(({ label, value }) => (
          <Card key={label} className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1">{label}</p>
            <p className="font-semibold">{value}</p>
          </Card>
        ))}
      </div>

      {/* Tabbed content */}
      <Tabs defaultValue="overview">
        <TabsList className="mb-6 flex-wrap h-auto gap-1">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="fixtures">Fixtures &amp; Results</TabsTrigger>
          <TabsTrigger value="standings">Group Standings</TabsTrigger>
          <TabsTrigger value="scorers">Top Scorers</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab t={t} />
        </TabsContent>

        <TabsContent value="fixtures">
          <FixturesTab tournamentId={tournamentId} />
        </TabsContent>

        <TabsContent value="standings">
          <StandingsTab tournamentId={tournamentId} />
        </TabsContent>

        <TabsContent value="scorers">
          <TopScorersTab tournamentId={tournamentId} />
        </TabsContent>
      </Tabs>

      {t && (
        <RegisterTeamModal
          open={showRegister}
          onOpenChange={setShowRegister}
          tournamentId={tournamentId}
          tournament={t}
        />
      )}
    </>
  )
}
